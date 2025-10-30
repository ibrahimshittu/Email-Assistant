#!/usr/bin/env python3
"""
One-time setup script to initialize storage directories and database
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_dir.parent))

from backend.config import load_config
from backend.database import Base, engine
from backend.utils.logger import setup_logger


logger = setup_logger(__name__)


def create_storage_dirs(config):
    """Create storage directories if they don't exist"""
    chroma_path = Path(config.chroma_dir)
    db_path = Path(config.sqlite_path).parent

    logger.info(f"Creating storage directory at {db_path}")
    db_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Creating Chroma directory at {chroma_path}")
    chroma_path.mkdir(parents=True, exist_ok=True)


def init_database():
    """Initialize SQLite database with all tables"""
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def verify_config(config):
    """Verify that required configuration is present"""
    required_vars = [
        "openai_api_key",
        "nylas_client_id",
        "nylas_client_secret",
    ]

    missing = []
    for var in required_vars:
        val = getattr(config, var, "")
        if not val or val == "":
            missing.append(var.upper())

    if missing:
        logger.warning(f"Missing configuration variables: {', '.join(missing)}")
        logger.warning("Please update your .env file with these values")
        return False

    logger.info("Configuration verified")
    return True


def main():
    """Run setup"""
    logger.info("=" * 60)
    logger.info("Email Assistant - One-Time Setup")
    logger.info("=" * 60)

    # Load config
    logger.info("Loading configuration...")
    config = load_config()

    # Verify config
    verify_config(config)

    # Create directories
    create_storage_dirs(config)

    # Initialize database
    init_database()

    logger.info("=" * 60)
    logger.info("Setup complete!")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Make sure your .env file has all required values")
    logger.info("2. Start the backend: uvicorn backend.api.main:app --reload --port 8000")
    logger.info("3. Start the frontend: cd frontend && npm run dev")
    logger.info("4. Open http://localhost:3000 in your browser")


if __name__ == "__main__":
    main()
