
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.db_client import get_db
from app.database import schemas
from app.middleware.auth_middleware import get_current_user
from app.services.auth_service import AuthService

router = APIRouter()

@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: schemas.UserCreate,
    db: AsyncSession = Depends(get_db)
):
    
    # Prevent admin registration through API
    if user_data.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin accounts cannot be created through registration"
        )
    
    auth_service = AuthService(db)
    try:
        user = await auth_service.register_user(user_data)
        return schemas.UserResponse(
            user_id=user.user_id,
            email=user.email,
            role=user.role,
            name=user.name,
            is_approved=user.is_approved,
            created_at=user.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=schemas.LoginResponse)
async def login(
    credentials: schemas.LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    
    auth_service = AuthService(db)
    try:
        return await auth_service.login_user(credentials)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.get("/me", response_model=schemas.UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(current_user.get("user_id"))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return schemas.UserResponse(
        user_id=user.user_id,
        email=user.email,
        role=user.role,
        name=user.name,
        is_approved=user.is_approved,
        created_at=user.created_at
    )
