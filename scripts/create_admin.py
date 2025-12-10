#!/usr/bin/env python3
"""
Create a default admin user for the Healthcare Blockchain system.
"""
import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

import asyncio
from app.database.db_client import AsyncSessionLocal
from app.services.auth_service import AuthService
from app.database.models import User

async def create_admin():
    """Create default admin user."""
    admin_email = "advancesoftware@gmail.com"
    admin_password = "advancesoftware@18"
    admin_name = "System Administrator"
    
    async with AsyncSessionLocal() as db:
        auth_service = AuthService(db)
        
        # Check if admin already exists
        existing_admin = await auth_service.get_user_by_email(admin_email)
        if existing_admin:
            print(f"[INFO] Admin user already exists: {admin_email}")
            print(f"   User ID: {existing_admin.user_id}")
            return
        
        # Create admin user
        try:
            from app.database import schemas
            user_data = schemas.UserCreate(
                email=admin_email,
                password=admin_password,
                name=admin_name,
                role="admin"
            )
            
            new_user = await auth_service.register_user(user_data)
            await db.commit()
            
            print(f"[OK] Admin user created successfully!")
            print(f"   Email: {admin_email}")
            print(f"   Password: {admin_password}")
            print(f"   User ID: {new_user.user_id}")
            print(f"   Role: {new_user.role}")
            print(f"\n[WARNING] Please change the default password after first login!")
            
        except Exception as e:
            await db.rollback()
            print(f"[ERROR] Failed to create admin user: {e}")
            raise

if __name__ == "__main__":
    try:
        asyncio.run(create_admin())
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

