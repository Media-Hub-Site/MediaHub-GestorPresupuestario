"""
Supported currencies with locale metadata for formatting.
"""

CURRENCIES: dict[str, dict] = {
    "CLP": {
        "name": "Peso Chileno",
        "symbol": "$",
        "decimals": 0,
        "locale": "es-CL",
        "flag": "🇨🇱",
        "country": "Chile",
    },
    "ARS": {
        "name": "Peso Argentino",
        "symbol": "$",
        "decimals": 2,
        "locale": "es-AR",
        "flag": "🇦🇷",
        "country": "Argentina",
    },
    "USD": {
        "name": "Dólar Estadounidense",
        "symbol": "$",
        "decimals": 2,
        "locale": "en-US",
        "flag": "🇺🇸",
        "country": "Estados Unidos",
    },
    "EUR": {
        "name": "Euro",
        "symbol": "€",
        "decimals": 2,
        "locale": "es-ES",
        "flag": "🇪🇺",
        "country": "Europa",
    },
    "MXN": {
        "name": "Peso Mexicano",
        "symbol": "$",
        "decimals": 2,
        "locale": "es-MX",
        "flag": "🇲🇽",
        "country": "México",
    },
    "COP": {
        "name": "Peso Colombiano",
        "symbol": "$",
        "decimals": 0,
        "locale": "es-CO",
        "flag": "🇨🇴",
        "country": "Colombia",
    },
    "PEN": {
        "name": "Sol Peruano",
        "symbol": "S/",
        "decimals": 2,
        "locale": "es-PE",
        "flag": "🇵🇪",
        "country": "Perú",
    },
    "BRL": {
        "name": "Real Brasileño",
        "symbol": "R$",
        "decimals": 2,
        "locale": "pt-BR",
        "flag": "🇧🇷",
        "country": "Brasil",
    },
    "UYU": {
        "name": "Peso Uruguayo",
        "symbol": "$U",
        "decimals": 2,
        "locale": "es-UY",
        "flag": "🇺🇾",
        "country": "Uruguay",
    },
}


def get_currency(code: str) -> dict | None:
    """Get currency metadata by ISO code."""
    return CURRENCIES.get(code.upper())


def list_currencies() -> list[dict]:
    """Return all supported currencies with their codes."""
    return [
        {"code": code, **data}
        for code, data in CURRENCIES.items()
    ]
