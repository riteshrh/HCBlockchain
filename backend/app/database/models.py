
from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()

def generate_id() -> str:
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True, default=generate_id)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)  # patient, provider, admin
    name = Column(String, nullable=True)
    public_key = Column(String, nullable=True)  # Blockchain public key
    private_key_encrypted = Column(String, nullable=True)  # Encrypted private key
    is_approved = Column(Boolean, default=False)  # For providers
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class MedicalRecord(Base):
    __tablename__ = "medical_records"
    
    record_id = Column(String, primary_key=True, default=generate_id)
    patient_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    encrypted_content = Column(Text, nullable=False)
    hash = Column(String, nullable=False, unique=True, index=True)  # SHA-256 hash
    blockchain_tx_id = Column(String, nullable=True, unique=True, index=True)
    record_type = Column(String, nullable=False)  # lab_report, prescription, etc.
    record_metadata = Column(JSON, nullable=True)  # Additional info (provider, date, etc.)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Consent(Base):
    __tablename__ = "consents"
    
    consent_id = Column(String, primary_key=True, default=generate_id)
    patient_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    provider_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    record_id = Column(String, ForeignKey("medical_records.record_id"), nullable=False, index=True)
    blockchain_tx_id = Column(String, nullable=False, unique=True, index=True)
    status = Column(String, nullable=False)  # granted, revoked, expired
    consent_type = Column(String, nullable=False, default="read")  # read, write, etc.
    granted_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

class AccessLog(Base):
    __tablename__ = "access_logs"
    
    log_id = Column(String, primary_key=True, default=generate_id)
    provider_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    patient_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    record_id = Column(String, ForeignKey("medical_records.record_id"), nullable=False, index=True)
    blockchain_tx_id = Column(String, nullable=True)  # Blockchain transaction ID
    access_type = Column(String, nullable=False, default="read")
    ip_address = Column(String, nullable=True)
    accessed_at = Column(DateTime(timezone=True), server_default=func.now())
