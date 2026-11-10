from datetime import datetime
from pydantic import BaseModel, Field

class EmailIntegrationCreate(BaseModel):
    imap_server: str = Field(default="imap.gmail.com")
    imap_port: int = Field(default=993)
    app_password: str = Field(..., min_length=1)

class EmailIntegrationUpdate(BaseModel):
    imap_server: str | None = None
    imap_port: int | None = None
    app_password: str | None = None
    is_active: bool | None = None

class EmailIntegrationRead(BaseModel):
    id: int
    user_id: int
    imap_server: str
    imap_port: int
    is_active: bool
    last_sync_at: datetime | None
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True

class EmailSyncResult(BaseModel):
    success: bool
    transactions_added: int
    message: str
