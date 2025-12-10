
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from datetime import datetime

# User Schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: str = Field(..., pattern="^(patient|provider|admin)$")
    name: Optional[str] = None

class UserResponse(BaseModel):
    user_id: str
    email: str
    role: str
    name: Optional[str] = None
    is_approved: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    user: UserResponse

# Record Schemas
class RecordUpload(BaseModel):
    record_type: str
    content: str  # Base64 encoded or JSON string
    metadata: Optional[Dict[str, Any]] = None

class RecordResponse(BaseModel):
    record_id: str
    patient_id: str
    hash: str
    blockchain_tx_id: Optional[str] = None
    record_type: str
    record_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Consent Schemas
class ConsentGrant(BaseModel):
    provider_id: str
    record_id: str
    consent_type: str = "read"
    expires_at: Optional[datetime] = None

class ConsentResponse(BaseModel):
    consent_id: str
    patient_id: str
    provider_id: str
    record_id: str
    blockchain_tx_id: str
    status: str
    consent_type: str
    granted_at: datetime
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Audit Schemas
class AuditEntry(BaseModel):
    log_id: str
    provider_id: str
    patient_id: str
    record_id: str
    blockchain_tx_id: Optional[str] = None
    access_type: str
    ip_address: Optional[str] = None
    accessed_at: datetime
    
    class Config:
        from_attributes = True
