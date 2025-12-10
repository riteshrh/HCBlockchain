
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from passlib.context import CryptContext
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import base64
from typing import Optional
from datetime import datetime

from app.database.models import User
from app.database import schemas
from app.utils.jwt_utils import create_access_token, create_refresh_token

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    def generate_key_pair(self) -> tuple[str, str]:
        # Generate RSA key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        
        # Serialize keys
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        # Encode as base64 strings for storage
        private_key_b64 = base64.b64encode(private_pem).decode('utf-8')
        public_key_b64 = base64.b64encode(public_pem).decode('utf-8')
        
        return public_key_b64, private_key_b64
    
    async def register_user(self, user_data: schemas.UserCreate) -> User:
        # Check if user already exists
        existing_user = await self.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        password_hash = self.hash_password(user_data.password)
        
        # Generate cryptographic key pair
        public_key, private_key = self.generate_key_pair()
        
        # Encrypt private key using master encryption key from settings
        # Note: In production, consider using a key management service (KMS) like AWS KMS or HashiCorp Vault
        # We use the master key so we can decrypt it later for blockchain operations
        # This protects private keys if database is compromised (but master key must be kept secure)
        from app.utils.encryption import encryption_service
        encrypted_private_key = encryption_service.encrypt(private_key)
        
        # Create user
        new_user = User(
            email=user_data.email,
            password_hash=password_hash,
            role=user_data.role,
            name=user_data.name,
            public_key=public_key,
            private_key_encrypted=encrypted_private_key,  # Now encrypted!
            is_approved=(user_data.role == "admin")  # Admins auto-approved, providers need approval
        )
        
        self.db.add(new_user)
        await self.db.flush()  # Flush to get the ID, but don't commit yet
        await self.db.refresh(new_user)
        
        return new_user
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = await self.get_user_by_email(email)
        if not user:
            return None
        
        if not self.verify_password(password, user.password_hash):
            return None
        
        return user
    
    async def login_user(self, credentials: schemas.LoginRequest) -> dict:
        user = await self.authenticate_user(credentials.email, credentials.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if provider is approved
        if user.role == "provider" and not user.is_approved:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Provider account pending approval"
            )
        
        # Generate JWT tokens
        token_data = {
            "user_id": user.user_id,
            "email": user.email,
            "role": user.role
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": 3600,  # 1 hour
            "user": schemas.UserResponse(
                user_id=user.user_id,
                email=user.email,
                role=user.role,
                name=user.name,
                is_approved=user.is_approved,
                created_at=user.created_at
            )
        }
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.user_id == user_id)
        )
        return result.scalar_one_or_none()
