
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database.db_client import get_db
from app.database import schemas
from app.database.models import User
from app.middleware.auth_middleware import get_current_user, require_role

router = APIRouter()

@router.get("/providers", response_model=List[schemas.UserResponse])
async def get_providers(
    current_user: dict = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    
    result = await db.execute(
        select(User).where(User.role == "provider").order_by(User.created_at.desc())
    )
    providers = result.scalars().all()
    
    return [
        schemas.UserResponse(
            user_id=provider.user_id,
            email=provider.email,
            role=provider.role,
            name=provider.name,
            is_approved=provider.is_approved,
            created_at=provider.created_at
        )
        for provider in providers
    ]

@router.post("/providers/{provider_id}/approve", response_model=schemas.UserResponse)
async def approve_provider(
    provider_id: str,
    current_user: dict = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    
    result = await db.execute(
        select(User).where(User.user_id == provider_id)
    )
    provider = result.scalar_one_or_none()
    
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
    
    if provider.is_approved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provider is already approved"
        )
    
    provider.is_approved = True
    await db.commit()
    await db.refresh(provider)
    
    return schemas.UserResponse(
        user_id=provider.user_id,
        email=provider.email,
        role=provider.role,
        name=provider.name,
        is_approved=provider.is_approved,
        created_at=provider.created_at
    )

@router.post("/providers/{provider_id}/reject", response_model=schemas.UserResponse)
async def reject_provider(
    provider_id: str,
    current_user: dict = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    
    result = await db.execute(
        select(User).where(User.user_id == provider_id)
    )
    provider = result.scalar_one_or_none()
    
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
    
    provider.is_approved = False
    await db.commit()
    await db.refresh(provider)
    
    return schemas.UserResponse(
        user_id=provider.user_id,
        email=provider.email,
        role=provider.role,
        name=provider.name,
        is_approved=provider.is_approved,
        created_at=provider.created_at
    )
