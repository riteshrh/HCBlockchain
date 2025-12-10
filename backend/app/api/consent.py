
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database.db_client import get_db
from app.database import schemas
from app.middleware.auth_middleware import get_current_user
from app.services.consent_service import ConsentService

router = APIRouter()

@router.post("/grant", response_model=schemas.ConsentResponse, status_code=status.HTTP_201_CREATED)
async def grant_consent(
    consent_data: schemas.ConsentGrant,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    
    if current_user.get("role") != "patient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patients can grant consent"
        )
    
    consent_service = ConsentService(db)
    consent = await consent_service.grant_consent(
        patient_id=current_user.get("user_id"),
        provider_id=consent_data.provider_id,
        record_id=consent_data.record_id,
        consent_type=consent_data.consent_type,
        expires_at=consent_data.expires_at
    )
    
    return schemas.ConsentResponse(
        consent_id=consent.consent_id,
        patient_id=consent.patient_id,
        provider_id=consent.provider_id,
        record_id=consent.record_id,
        blockchain_tx_id=consent.blockchain_tx_id,
        status=consent.status,
        consent_type=consent.consent_type,
        granted_at=consent.granted_at,
        expires_at=consent.expires_at,
        revoked_at=consent.revoked_at
    )

@router.post("/revoke", response_model=schemas.ConsentResponse)
async def revoke_consent(
    consent_data: schemas.ConsentGrant,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    
    if current_user.get("role") != "patient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patients can revoke consent"
        )
    
    consent_service = ConsentService(db)
    consent = await consent_service.revoke_consent(
        patient_id=current_user.get("user_id"),
        provider_id=consent_data.provider_id,
        record_id=consent_data.record_id
    )
    
    return schemas.ConsentResponse(
        consent_id=consent.consent_id,
        patient_id=consent.patient_id,
        provider_id=consent.provider_id,
        record_id=consent.record_id,
        blockchain_tx_id=consent.blockchain_tx_id,
        status=consent.status,
        consent_type=consent.consent_type,
        granted_at=consent.granted_at,
        expires_at=consent.expires_at,
        revoked_at=consent.revoked_at
    )

@router.get("/my-consents", response_model=List[schemas.ConsentResponse])
async def get_my_consents(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    
    consent_service = ConsentService(db)
    user_id = current_user.get("user_id")
    role = current_user.get("role")
    
    if role == "patient":
        consents = await consent_service.get_patient_consents(user_id)
    elif role == "provider":
        consents = await consent_service.get_provider_consents(user_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patients and providers can view consents"
        )
    
    return [
        schemas.ConsentResponse(
            consent_id=c.consent_id,
            patient_id=c.patient_id,
            provider_id=c.provider_id,
            record_id=c.record_id,
            blockchain_tx_id=c.blockchain_tx_id,
            status=c.status,
            consent_type=c.consent_type,
            granted_at=c.granted_at,
            expires_at=c.expires_at,
            revoked_at=c.revoked_at
        )
        for c in consents
    ]

@router.get("/check/{provider_id}/{record_id}")
async def check_consent(
    provider_id: str,
    record_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    
    consent_service = ConsentService(db)
    consent = await consent_service.check_consent(provider_id, record_id)
    
    if not consent:
        return {
            "has_consent": False,
            "message": "No valid consent found"
        }
    
    return {
        "has_consent": True,
        "consent_id": consent.consent_id,
        "consent_type": consent.consent_type,
        "granted_at": consent.granted_at,
        "expires_at": consent.expires_at
    }
