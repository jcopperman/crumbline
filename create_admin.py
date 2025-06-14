#!/usr/bin/env python3
# filepath: /var/www/crumbline/create_admin.py

import asyncio
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session, init_db
from app.models import User
from app.auth import get_password_hash

async def create_admin_user(username, email, password):
    await init_db()
    
    async for session in get_session():
        # Check if user already exists
        existing_user = await session.get(User, 1)
        if existing_user:
            print(f"Admin user already exists: {existing_user.username}")
            return
        
        # Create admin user
        hashed_password = get_password_hash(password)
        admin_user = User(
            username=username,
            email=email,
            password=hashed_password
        )
        session.add(admin_user)
        await session.commit()
        print(f"Admin user created: {username}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python create_admin.py <username> <email> <password>")
        sys.exit(1)
    
    username = sys.argv[1]
    email = sys.argv[2]
    password = sys.argv[3]
    
    asyncio.run(create_admin_user(username, email, password))
