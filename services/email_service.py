import os
import imaplib
import email
import re
from datetime import datetime, timezone, timedelta
from email.header import decode_header
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet

from models.models import User, EmailIntegration, Account, Transaction
from schemas.email_integration import EmailIntegrationCreate, EmailIntegrationUpdate, EmailSyncResult
from schemas.schemas import TransactionCreate
from services import transaction_service

# Default encryption key (for development/local only). In production, set ENCRYPTION_KEY in environment.
_ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "nNeaIGo7Mq2IfzDhX68B8Y3PfKx-HTtJaKcMb_UMGZ4=")
_cipher_suite = Fernet(_ENCRYPTION_KEY.encode())

def encrypt_password(password: str) -> str:
    return _cipher_suite.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password: str) -> str:
    return _cipher_suite.decrypt(encrypted_password.encode()).decode()

def get_integration(db: Session, user_id: int) -> EmailIntegration | None:
    return db.query(EmailIntegration).filter(EmailIntegration.user_id == user_id).first()

def save_integration(db: Session, user_id: int, data: EmailIntegrationCreate) -> EmailIntegration:
    integration = get_integration(db, user_id)
    encrypted_pw = encrypt_password(data.app_password)
    
    if integration:
        integration.imap_server = data.imap_server
        integration.imap_port = data.imap_port
        integration.encrypted_password = encrypted_pw
        integration.is_active = True
    else:
        integration = EmailIntegration(
            user_id=user_id,
            imap_server=data.imap_server,
            imap_port=data.imap_port,
            encrypted_password=encrypted_pw,
            is_active=True
        )
        db.add(integration)
    
    db.commit()
    db.refresh(integration)
    return integration

def _parse_amount(text: str) -> float | None:
    # Match patterns like $ 15.000, $15,000, $15000, $1.500.000
    match = re.search(r'\$\s*([\d\.\,]+)', text)
    if not match:
        return None
    raw = match.group(1).strip()
    
    # Check if formatted with dots as thousands separator (typical in CLP / Spanish e.g. 15.000 or 1.250.000)
    if '.' in raw and ',' not in raw:
        parts = raw.split('.')
        # If segments after first dot are 3 digits, treat as thousand separators
        if len(parts) > 1 and all(len(p) == 3 for p in parts[1:]):
            raw = "".join(parts)
    elif '.' in raw and ',' in raw:
        if raw.rfind(',') > raw.rfind('.'):
            # Format: 1.500,50 (dots for thousands, comma for decimals)
            raw = raw.replace('.', '').replace(',', '.')
        else:
            # Format: 1,500.50 (commas for thousands, dot for decimals)
            raw = raw.replace(',', '')
    elif ',' in raw and '.' not in raw:
        parts = raw.split(',')
        if len(parts) > 1 and all(len(p) == 3 for p in parts[1:]):
            raw = "".join(parts)
        else:
            raw = raw.replace(',', '')

    try:
        val = float(raw)
        return val if val > 0 else None
    except ValueError:
        return None

def _match_account(accounts: list[Account], from_header: str, subject: str, body: str) -> Account | None:
    """
    Intelligently match an email notification to the correct user account.
    Checks sender (From), subject, and body text against known Chilean banks/fintechs
    and account names.
    """
    if not accounts:
        return None
    if len(accounts) == 1:
        return accounts[0]

    bank_patterns: dict[str, list[str]] = {
        'bancoestado': ['bancoestado', 'banco estado', 'cuentarut', 'cuenta rut', 'bancoestado.cl'],
        'bancochile': ['bancochile', 'banco de chile', 'banco chile', 'edwards', 'bancochile.cl'],
        'mercadopago': ['mercadopago', 'mercado pago', 'mercadolibre', 'mercadopago.cl'],
        'coopeuch': ['coopeuch', 'coopeuch.cl'],
        'santander': ['santander', 'santander.cl'],
        'falabella': ['falabella', 'bancofalabella', 'cmr'],
        'bci': ['bci', 'mach', 'bci.cl'],
        'scotiabank': ['scotiabank', 'scotia'],
        'itau': ['itau', 'itaú', 'itau.cl'],
        'tenpo': ['tenpo', 'tenpo.cl']
    }

    text = f"{from_header} {subject} {body[:1000]}".lower()
    from_lower = from_header.lower()
    subject_lower = subject.lower()

    best_acc = None
    best_score = -1

    for acc in accounts:
        clean_name = acc.name.lower().replace(' ', '').replace('_', '').replace('-', '')
        score = 0

        # Exact account name matches
        if acc.name.lower() in from_lower or clean_name in from_lower.replace(' ', ''):
            score += 25
        elif acc.name.lower() in subject_lower:
            score += 15
        elif acc.name.lower() in text:
            score += 8

        # Bank pattern matches
        for bkey, kws in bank_patterns.items():
            acc_matches_bank = any(kw in acc.name.lower() for kw in kws) or (bkey in clean_name)
            if acc_matches_bank:
                # If sender is from this bank
                if any(kw in from_lower for kw in kws):
                    score += 30
                # If subject mentions this bank
                if any(kw in subject_lower for kw in kws):
                    score += 15
                # If body mentions this bank as destination or origin
                if any(kw in text for kw in kws):
                    score += 10

        if score > best_score:
            best_score = score
            best_acc = acc

    # Return best matching account if score > 0, else fallback to first account
    return best_acc if (best_acc and best_score > 0) else accounts[0]


def sync_emails(db: Session, user: User) -> EmailSyncResult:
    integration = get_integration(db, user.id)
    if not integration or not integration.is_active:
        return EmailSyncResult(success=False, transactions_added=0, message="La integración de correo no está configurada o está inactiva.")
    
    # Load all user accounts to match dynamically
    accounts = db.query(Account).filter(Account.user_id == user.id).all()
    if not accounts:
        return EmailSyncResult(success=False, transactions_added=0, message="No tienes cuentas creadas para asignar transacciones. Crea una cuenta primero en la sección Cuentas.")

    try:
        password = decrypt_password(integration.encrypted_password)
        mail = imaplib.IMAP4_SSL(integration.imap_server, integration.imap_port)
        mail.login(user.email, password)
        mail.select("inbox")

        # Search for emails in the last 7 days
        since_date = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
        status, messages = mail.search(None, f'(SINCE "{since_date}")')
        
        if status != "OK":
            return EmailSyncResult(success=False, transactions_added=0, message="Error buscando correos en IMAP.")

        email_ids = messages[0].split()
        transactions_added = 0
        affected_account_ids: set[int] = set()

        # Keywords that indicate a banking notification or transaction
        keywords = [
            "transferencia", "compra", "cargo", "abono", "pago", 
            "notificación de uso", "comprobante", "recibiste", "enviaste", 
            "tarjeta", "transacción"
        ]

        # Only process up to the last 20 emails to avoid timeouts on sync
        for e_id in email_ids[-20:]:
            res, msg_data = mail.fetch(e_id, '(RFC822)')
            if res != "OK":
                continue

            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    # Decode subject
                    subject = ""
                    if msg["Subject"]:
                        decoded_list = decode_header(msg["Subject"])
                        for text, charset in decoded_list:
                            if isinstance(text, bytes):
                                subject += text.decode(charset or 'utf-8', errors='ignore')
                            else:
                                subject += text

                    # Decode from header
                    from_header = ""
                    if msg["From"]:
                        decoded_from = decode_header(msg["From"])
                        for text, charset in decoded_from:
                            if isinstance(text, bytes):
                                from_header += text.decode(charset or 'utf-8', errors='ignore')
                            else:
                                from_header += str(text)

                    subject_lower = subject.lower()
                    is_transaction = any(kw in subject_lower for kw in keywords)

                    if is_transaction:
                        # Extract body text to find amount and bank details
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                if content_type == "text/plain":
                                    body_bytes = part.get_payload(decode=True)
                                    if body_bytes:
                                        body += body_bytes.decode(errors='ignore')
                        else:
                            body_bytes = msg.get_payload(decode=True)
                            if body_bytes:
                                body += body_bytes.decode(errors='ignore')

                        amount = _parse_amount(subject + " " + body)
                        if amount and amount > 0:
                            # Match the correct account for this bank email
                            target_account = _match_account(accounts, from_header, subject, body)
                            if not target_account:
                                target_account = accounts[0]

                            # Income detection: abono, recibiste, te transfirieron
                            is_income = any(k in subject_lower for k in ["abono", "recibiste", "recibida", "te transfirieron", "depósito", "deposito"])
                            tx_type = "INCOME" if is_income else "EXPENSE"
                            clean_description = subject.strip()[:100]

                            # Avoid duplicate transactions: check if identical tx exists in target account
                            existing = db.query(Transaction).filter(
                                Transaction.account_id == target_account.id,
                                Transaction.amount == amount,
                                Transaction.description == clean_description
                            ).first()

                            if existing:
                                continue

                            tx_create = TransactionCreate(
                                account_id=target_account.id,
                                type=tx_type,
                                amount=amount,
                                description=clean_description,
                                transaction_date=None
                            )
                            try:
                                transaction_service.ingest_transaction(db, user, tx_create)
                                transactions_added += 1
                                affected_account_ids.add(target_account.id)
                            except Exception:
                                pass
        
        mail.logout()

        # Update last sync time
        integration.last_sync_at = datetime.now(timezone.utc)
        db.commit()

        # Recalculate balances for all accounts that received transactions
        for acc_id in affected_account_ids:
            transaction_service.recalculate_balance(db, acc_id)
        db.commit()

        return EmailSyncResult(
            success=True, 
            transactions_added=transactions_added, 
            message=f"Sincronización exitosa. Se añadieron {transactions_added} movimientos nuevos."
        )

    except imaplib.IMAP4.error as e:
        return EmailSyncResult(success=False, transactions_added=0, message=f"Error de autenticación IMAP. Revisa tu contraseña de aplicación. Detalles: {str(e)}")
    except Exception as e:
        return EmailSyncResult(success=False, transactions_added=0, message=f"Error inesperado al sincronizar correos: {str(e)}")
