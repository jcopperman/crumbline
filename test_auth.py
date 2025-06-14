#!/usr/bin/env python3
# filepath: /var/www/crumbline/test_auth.py

import asyncio
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session, init_db
from app.models import User
from app.auth import get_password_hash, verify_password

async def test_auth():
    await init_db()
    
    async for session in get_session():
        # Create test user if doesn't exist
        username = "test_user"
        email = "test@example.com"
        password = "password123"
        
        from sqlalchemy.future import select
        result = await session.execute(select(User).filter(User.username == username))
        user = result.scalars().first()
        
        if not user:
            print(f"Creating test user: {username}")
            hashed_password = get_password_hash(password)
            test_user = User(
                username=username,
                email=email,
                password=hashed_password
            )
            session.add(test_user)
            await session.commit()
            
            # Verify we can authenticate
            from app.auth import authenticate_user
            authenticated = await authenticate_user(session, username, password)
            if authenticated:
                print("✅ Authentication successful!")
            else:
                print("❌ Authentication failed!")
        else:
            print(f"Test user already exists: {username}")
            
            # Test password verification
            if verify_password(password, user.password):
                print("✅ Password verification successful!")
            else:
                print("❌ Password verification failed!")

if __name__ == "__main__":
    asyncio.run(test_auth())
