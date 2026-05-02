#!/usr/bin/env python3
"""
Script to identify and fix users with problematic password hashes in production.
Run this script in production to rehash passwords that can't be verified.
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.user import User
from app.utils import get_password_hash, verify_password
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create a context that can handle both old and new hashes
legacy_context = CryptContext(
    schemes=["bcrypt", "pbkdf2_sha256"],
    deprecated="auto"
)

def fix_password_hashes():
    """Find users with problematic password hashes and rehash them."""

    # Database connection
    db_url = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', 3306)}/{os.getenv('DB_NAME')}"

    engine = create_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = SessionLocal()

    try:
        # Get all users
        users = db.query(User).all()
        fixed_count = 0

        for user in users:
            try:
                # Try to verify with a dummy password to check if hash is valid
                legacy_context.verify("dummy_password", user.hashed_password)
                # If we get here, the hash format is recognized, so it's probably fine
            except Exception as e:
                logger.warning(f"User {user.email} has problematic hash: {str(user.hashed_password)[:30]}... Error: {e}")

                # For production, we need to reset passwords manually
                # This script identifies the problematic users
                logger.error(f"USER REQUIRES PASSWORD RESET: {user.email} (ID: {user.id})")

        logger.info("Password hash audit completed. Check logs for users requiring password resets.")

    except Exception as e:
        logger.error(f"Error during password hash audit: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Starting password hash audit...")
    fix_password_hashes()
    logger.info("Password hash audit completed.")