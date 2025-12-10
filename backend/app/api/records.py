
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database.db_client import get_db
from app.database import schemas
from app.middleware.auth_middleware import get_current_user
from app.services.records_service import RecordsService

router = APIRouter()

@router.post("/upload", response_model=schemas.RecordResponse, status_code=status.HTTP_201_CREATED)
async def upload_record(
    record_data: schemas.RecordUpload,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    
    # Only patients can upload records
    if current_user.get("role") != "patient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patients can upload records"
        )
    
    records_service = RecordsService(db)
    record = await records_service.upload_record(
        patient_id=current_user.get("user_id"),
        record_data=record_data
    )
    
    return schemas.RecordResponse(
        record_id=record.record_id,
        patient_id=record.patient_id,
        hash=record.hash,
        blockchain_tx_id=record.blockchain_tx_id,
        record_type=record.record_type,
        record_metadata=record.record_metadata,
        created_at=record.created_at
    )

@router.get("/my-records", response_model=List[schemas.RecordResponse])
async def get_my_records(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    
    if current_user.get("role") != "patient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patients can view their own records"
        )
    
    records_service = RecordsService(db)
    records = await records_service.get_patient_records(
        patient_id=current_user.get("user_id"),
        requesting_user_id=current_user.get("user_id"),
        requesting_user_role=current_user.get("role")
    )
    
    return [
        schemas.RecordResponse(
            record_id=record.record_id,
            patient_id=record.patient_id,
            hash=record.hash,
            blockchain_tx_id=record.blockchain_tx_id,
            record_type=record.record_type,
            record_metadata=record.record_metadata,
            created_at=record.created_at
        )
        for record in records
    ]

@router.get("/{record_id}", response_model=schemas.RecordResponse)
async def get_record(
    record_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    
    records_service = RecordsService(db)
    record = await records_service.get_record_by_id(
        record_id=record_id,
        user_id=current_user.get("user_id"),
        user_role=current_user.get("role")
    )
    
    return schemas.RecordResponse(
        record_id=record.record_id,
        patient_id=record.patient_id,
        hash=record.hash,
        blockchain_tx_id=record.blockchain_tx_id,
        record_type=record.record_type,
        record_metadata=record.record_metadata,
        created_at=record.created_at
    )

@router.get("/{record_id}/content")
async def get_record_content(
    record_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    
    records_service = RecordsService(db)
    record = await records_service.get_record_by_id(
        record_id=record_id,
        user_id=current_user.get("user_id"),
        user_role=current_user.get("role")
    )
    
    # Decrypt the content
    try:
        decrypted_content = await records_service.decrypt_record_content(record)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to decrypt record content: {str(e)}"
        )
    
    return {
        "record_id": record.record_id,
        "content": decrypted_content,
        "record_type": record.record_type,
        "metadata": record.record_metadata
    }
