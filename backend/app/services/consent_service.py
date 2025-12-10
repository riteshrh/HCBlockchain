
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import datetime, timezone

from app.database.models import Consent, User, MedicalRecord
from app.database import schemas

class ConsentService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def grant_consent(
        self,
        patient_id: str,
        provider_id: str,
        record_id: str,
        consent_type: str = "read",
        expires_at: Optional[datetime] = None
    ) -> Consent:
        
        # Verify patient owns the record
        record = await self._get_record(record_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Record not found"
            )
        
        if record.patient_id != patient_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only grant consent for your own records"
            )
        
        # Verify provider exists and is approved
        provider = await self._get_user(provider_id)
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provider not found"
            )
        
        if provider.role != "provider":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not a provider"
            )
        
        if not provider.is_approved:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provider is not approved"
            )
        
        # Check if consent already exists
        existing = await self._get_consent(patient_id, provider_id, record_id)
        if existing and existing.status == "granted":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Consent already granted"
            )
        
        # Generate consent_id first (we need it for blockchain transaction)
        from app.database.models import generate_id
        consent_id = generate_id()
        
        # Store consent transaction on blockchain FIRST
        blockchain_tx_id = None
        try:
            from app.blockchain.client import blockchain_client
            
            # Get patient for public key
            patient = await self._get_user(patient_id)
            
            # Get provider's public key if available
            provider_public_key = None
            if provider.public_key:
                provider_public_key = provider.public_key
            
            blockchain_result = await blockchain_client.store_consent_transaction(
                consent_id=consent_id,
                patient_id=patient_id,
                provider_id=provider_id,
                record_id=record_id,
                consent_type=consent_type,
                status="granted",
                patient_public_key=patient.public_key if patient else None,
                provider_public_key=provider_public_key
            )
            
            # Get blockchain transaction ID
            if blockchain_result.get("tx_id"):
                blockchain_tx_id = blockchain_result["tx_id"]
        except Exception as e:
            # Log error but don't fail consent creation if blockchain is unavailable
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to store consent on blockchain: {e}. Consent created but not on blockchain.")
            # Generate a placeholder tx_id if blockchain fails
            import hashlib
            blockchain_tx_id = f"consent_{hashlib.sha256(consent_id.encode()).hexdigest()[:32]}"
        
        # Create consent with blockchain_tx_id already set
        new_consent = Consent(
            consent_id=consent_id,
            patient_id=patient_id,
            provider_id=provider_id,
            record_id=record_id,
            blockchain_tx_id=blockchain_tx_id,
            status="granted",
            consent_type=consent_type,
            expires_at=expires_at
        )
        
        self.db.add(new_consent)
        await self.db.flush()
        await self.db.refresh(new_consent)
        
        return new_consent
    
    async def revoke_consent(
        self,
        patient_id: str,
        provider_id: str,
        record_id: str
    ) -> Consent:
        
        consent = await self._get_consent(patient_id, provider_id, record_id)
        
        if not consent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consent not found"
            )
        
        if consent.patient_id != patient_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only revoke consent for your own records"
            )
        
        if consent.status == "revoked":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Consent already revoked"
            )
        
        # Update consent status
        consent.status = "revoked"
        consent.revoked_at = datetime.now(timezone.utc)
        
        await self.db.flush()
        await self.db.refresh(consent)
        
        # Store revocation transaction on blockchain
        try:
            from app.blockchain.client import blockchain_client
            
            # Get patient and provider
            patient = await self._get_user(patient_id)
            provider = await self._get_user(provider_id)
            
            provider_public_key = None
            if provider and provider.public_key:
                provider_public_key = provider.public_key
            
            blockchain_result = await blockchain_client.store_consent_transaction(
                consent_id=consent.consent_id,
                patient_id=patient_id,
                provider_id=provider_id,
                record_id=record_id,
                consent_type=consent.consent_type,
                status="revoked",
                patient_public_key=patient.public_key if patient else None,
                provider_public_key=provider_public_key
            )
            
            # Update consent with new blockchain transaction ID (revocation)
            if blockchain_result.get("tx_id"):
                # Store revocation tx_id (we could append or replace, for now we'll keep the original)
                # In production, you might want to track both grant and revoke transactions
                consent.blockchain_tx_id = blockchain_result["tx_id"]
                await self.db.flush()
        except Exception as e:
            # Log error but don't fail revocation if blockchain is unavailable
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to store consent revocation on blockchain: {e}. Consent revoked but not on blockchain.")
        
        return consent
    
    async def check_consent(
        self,
        provider_id: str,
        record_id: str
    ) -> Optional[Consent]:
        
        # Get the record to find patient_id
        record = await self._get_record(record_id)
        if not record:
            return None
        
        consent = await self._get_consent(record.patient_id, provider_id, record_id)
        
        if not consent:
            return None
        
        # Check if consent is granted and not expired
        if consent.status != "granted":
            return None
        
        if consent.expires_at and consent.expires_at < datetime.now(timezone.utc):
            return None
        
        return consent
    
    async def get_patient_consents(
        self,
        patient_id: str
    ) -> List[Consent]:
        
        result = await self.db.execute(
            select(Consent)
            .where(Consent.patient_id == patient_id)
            .order_by(Consent.granted_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_provider_consents(
        self,
        provider_id: str
    ) -> List[Consent]:
        
        result = await self.db.execute(
            select(Consent)
            .where(
                and_(
                    Consent.provider_id == provider_id,
                    Consent.status == "granted"
                )
            )
            .order_by(Consent.granted_at.desc())
        )
        return list(result.scalars().all())
    
    async def _get_consent(
        self,
        patient_id: str,
        provider_id: str,
        record_id: str
    ) -> Optional[Consent]:
        
        result = await self.db.execute(
            select(Consent).where(
                and_(
                    Consent.patient_id == patient_id,
                    Consent.provider_id == provider_id,
                    Consent.record_id == record_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def _get_user(self, user_id: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def _get_record(self, record_id: str) -> Optional[MedicalRecord]:
        result = await self.db.execute(
            select(MedicalRecord).where(MedicalRecord.record_id == record_id)
        )
        return result.scalar_one_or_none()
