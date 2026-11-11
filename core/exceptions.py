"""
core/exceptions.py
──────────────────
Excepciones y códigos de estado desacoplados de frameworks web (FastAPI).
Permite reutilizar la lógica de servicios en la aplicación de escritorio PyQt6
sin dependencias de red o servidores HTTP.
"""


class status:
    HTTP_400_BAD_REQUEST = 400
    HTTP_401_UNAUTHORIZED = 401
    HTTP_403_FORBIDDEN = 403
    HTTP_404_NOT_FOUND = 404
    HTTP_422_UNPROCESSABLE_ENTITY = 422
    HTTP_500_INTERNAL_SERVER_ERROR = 500


class HTTPException(Exception):
    def __init__(self, status_code: int = 400, detail: str = "", headers: dict | None = None):
        self.status_code = status_code
        self.detail = detail
        self.headers = headers
        super().__init__(detail)

    def __str__(self):
        return self.detail or f"Error HTTP {self.status_code}"
