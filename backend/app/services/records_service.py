
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import datetime

from app.database.models import MedicalRecord, User
from app.database import schemas
from app.utils.encryption import encryption_service
from app.utils.hashing import generate_hash

class RecordsService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def upload_record(
        self,
        patient_id: str,
        record_data: schemas.RecordUpload
    ) -> MedicalRecord:
        
        # Verify patient exists
        patient = await self._get_user_by_id(patient_id)
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        
        # Encrypt the record content
        encrypted_content = encryption_service.encrypt(record_data.content)
        
        # Generate hash of the original content (for integrity verification)
        content_hash = generate_hash(record_data.content)
        
        # Create medical record
        new_record = MedicalRecord(
            patient_id=patient_id,
            encrypted_content=encrypted_content,
            hash=content_hash,
            record_type=record_data.record_type,
            record_metadata=record_data.metadata,
            blockchain_tx_id=None  # Will be set after blockchain transaction
        )
        
        self.db.add(new_record)
        await self.db.flush()  # Flush to get the ID, but don't commit yet
        await self.db.refresh(new_record)
        
        # Store hash on blockchain
        try:
            from app.blockchain.client import blockchain_client
            
            # Decrypt patient's private key to get public key (already have public key)
            # For blockchain, we use the public key directly
            blockchain_result = await blockchain_client.store_record_hash(
                record_id=new_record.record_id,
                record_hash=content_hash,
                patient_id=patient_id,
                public_key=patient.public_key
            )
            
            # Update record with blockchain transaction ID
            if blockchain_result.get("tx_id"):
                new_record.blockchain_tx_id = blockchain_result["tx_id"]
                await self.db.flush()
        except Exception as e:
            # Log error but don't fail the upload if blockchain is unavailable
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to store hash on blockchain: {e}. Record uploaded but not on blockchain.")
        
        return new_record
    
    async def get_record_by_id(
        self,
        record_id: str,
        user_id: str,
        user_role: str
    ) -> MedicalRecord:
        
        result = await self.db.execute(
            select(MedicalRecord).where(MedicalRecord.record_id == record_id)
        )
        record = result.scalar_one_or_none()
        
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Record not found"
            )
        
        # Check access: patient can access their own records
        if user_role == "patient" and record.patient_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only access your own records"
            )
        
        # Providers need consent to access records
        if user_role == "provider":
            from app.services.consent_service import ConsentService
            consent_service = ConsentService(self.db)
            try:
                consent = await consent_service.check_consent(user_id, record_id)
                if not consent:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied: No valid consent found. Patient must grant consent first."
                    )
            except HTTPException:
                raise
            except Exception as e:
                # Log the error and re-raise as a more user-friendly error
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error checking consent: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error checking consent: {str(e)}"
                )
        
        # Admins can access all records
        
        # Verify blockchain integrity before returning the record
        await self._verify_record_integrity(record)
        
        return record
    
    async def get_patient_records(
        self,
        patient_id: str,
        requesting_user_id: str,
        requesting_user_role: str
    ) -> List[MedicalRecord]:
        
        # Patients can only see their own records
        if requesting_user_role == "patient" and patient_id != requesting_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only view your own records"
            )
        
        # Verify patient exists
        patient = await self._get_user_by_id(patient_id)
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        
        # Get all records for this patient
        result = await self.db.execute(
            select(MedicalRecord)
            .where(MedicalRecord.patient_id == patient_id)
            .order_by(MedicalRecord.created_at.desc())
        )
        records = result.scalars().all()
        
        return list(records)
    
    async def decrypt_record_content(self, record: MedicalRecord) -> str:
        if not record.encrypted_content:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Record has no encrypted content to decrypt"
            )
        
        try:
            decrypted_content = encryption_service.decrypt(record.encrypted_content)
            recalculated_hash = generate_hash(decrypted_content)
            
            if recalculated_hash != record.hash:
                # Log content tampering to blockchain
                try:
                    from app.blockchain.client import blockchain_client
                    await blockchain_client.store_tampering_event(
                        record_id=record.record_id,
                        patient_id=record.patient_id,
                        tampering_type="content_corruption",
                        original_hash=record.hash,
                        tampered_hash=recalculated_hash,
                        original_tx_id=record.blockchain_tx_id,
                        detected_by=None
                    )
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to log content tampering event to blockchain: {e}")
                
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Record integrity verification failed: content hash mismatch. Tampering attempt has been logged."
                )
            
            return decrypted_content
        except ValueError as e:
            # Invalid padding or base64 decode error
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Decryption failed: Invalid encrypted data format. This may indicate data corruption or encryption key mismatch."
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Decryption error: {type(e).__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to decrypt record: {str(e)}"
            )
    
    async def _get_user_by_id(self, user_id: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def _verify_record_integrity(self, record: MedicalRecord) -> None:
        if not record.blockchain_tx_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Record integrity cannot be verified: missing blockchain transaction"
            )
        
        try:
            from app.blockchain.client import blockchain_client
            tx_data = await blockchain_client.query_transaction(record.blockchain_tx_id)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to query blockchain for record {record.record_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Unable to verify record integrity on blockchain"
            )
        
        if not tx_data:
            # Log tampering attempt (tx_id was changed to non-existent value)
            try:
                from app.blockchain.client import blockchain_client
                await blockchain_client.store_tampering_event(
                    record_id=record.record_id,
                    patient_id=record.patient_id,
                    tampering_type="tx_id_mismatch",
                    original_hash=record.hash,
                    original_tx_id=None,  # We don't know the original
                    tampered_tx_id=record.blockchain_tx_id,
                    detected_by=None
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to log tx_id tampering event to blockchain: {e}")
            
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Blockchain proof not found for this record. Tampering attempt has been logged."
            )
        
        asset_data = (
            tx_data.get("transaction", {})
            .get("asset", {})
            .get("data", {})
        )
        
        # Verify the transaction belongs to this record
        tx_record_id = asset_data.get("record_id")
        if tx_record_id and tx_record_id != record.record_id:
            # Log tampering attempt (tx_id points to different record)
            try:
                from app.blockchain.client import blockchain_client
                await blockchain_client.store_tampering_event(
                    record_id=record.record_id,
                    patient_id=record.patient_id,
                    tampering_type="tx_id_mismatch",
                    original_hash=record.hash,
                    original_tx_id=None,  # We don't know the original
                    tampered_tx_id=record.blockchain_tx_id,
                    detected_by=None
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to log tx_id tampering event to blockchain: {e}")
            
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Blockchain transaction does not belong to this record. Tampering attempt has been logged."
            )
        
        blockchain_hash = asset_data.get("hash")
        
        if not blockchain_hash:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Blockchain transaction missing hash data"
            )
        
        if blockchain_hash != record.hash:
            # Log tampering attempt to blockchain
            try:
                from app.blockchain.client import blockchain_client
                await blockchain_client.store_tampering_event(
                    record_id=record.record_id,
                    patient_id=record.patient_id,
                    tampering_type="hash_mismatch",
                    original_hash=blockchain_hash,
                    tampered_hash=record.hash,
                    original_tx_id=record.blockchain_tx_id,
                    detected_by=None  # Could pass user_id if available
                )
            except Exception as e:
                # Log error but don't fail the tampering detection
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to log tampering event to blockchain: {e}")
            
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Record integrity verification failed: blockchain hash mismatch. Tampering attempt has been logged."
            )
