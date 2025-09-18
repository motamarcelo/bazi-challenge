from pydantic import BaseModel, Field
import uuid
from datetime import datetime

class ReservationResponse(BaseModel):
    reservation_id: uuid.UUID
    sku: str
    expires_at: datetime

class ConfirmationRequest(BaseModel):
    reservation_id: uuid.UUID

class ConfirmationResponse(BaseModel):
    status: str
    message: str