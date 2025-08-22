#!/usr/bin/env python3
"""
ASDSADF Application Setup and Launcher
Run this script to set up and start the ASDSADF application.
"""

import asyncio
import logging
import subprocess
import sys
from pathlib import Path
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_requirements():
    """Check if all required packages are installed."""
    logger.info("📦 Checking requirements...")
    
    try:
        import google.generativeai
        import chromadb
        import fastapi
        import uvicorn
        import pydantic
        import sentence_transformers
        logger.info("✅ All required packages are installed")
        return True
    except ImportError as e:
        logger.error(f"❌ Missing required package: {e}")
        logger.info("💡 Run: pip install -r requirements.txt")
        return False

def check_environment():
    """Check environment configuration."""
    logger.info("🔧 Checking environment configuration...")
    
    # Check .env file
    env_file = Path(".env")
    if not env_file.exists():
        logger.error("❌ .env file not found")
        logger.info("💡 Copy .env.example to .env and configure your API keys")
        return False
    
    # Check Gemini API key
    with open(env_file) as f:
        content = f.read()
        if "your_gemini_api_key_here" in content:
            logger.error("❌ Please set your GEMINI_API_KEY in .env file")
            return False
    
    logger.info("✅ Environment configuration looks good")
    return True

async def setup_knowledge_base():
    """Set up the knowledge base with sample data."""
    logger.info("🧠 Setting up knowledge base...")
    
    try:
        # Import and run knowledge base setup
        sys.path.append("scripts")
        from populate_knowledge_base import KnowledgeBasePopulator
        
        populator = KnowledgeBasePopulator()
        success_count = await populator.populate_sample_data()
        
        if success_count > 0:
            logger.info(f"✅ Knowledge base populated with {success_count} documents")
            return True
        else:
            logger.warning("⚠️ No documents were added to knowledge base")
            return False
            
    except Exception as e:
        logger.error(f"❌ Knowledge base setup failed: {e}")
        return False

def start_server():
    """Start the FastAPI server."""
    logger.info("🚀 Starting ASDSADF server...")
    
    try:
        import uvicorn
        from src.config import settings
        
        logger.info(f"🌐 Server will be available at: http://{settings.app_host}:{settings.app_port}")
        logger.info("📚 API documentation: http://localhost:8000/docs")
        logger.info("💬 Chat interface: http://localhost:8000/")
        
        uvicorn.run(
            "src.api:app",
            host=settings.app_host,
            port=settings.app_port,
            reload=settings.debug
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        return False

async def main():
    """Main setup and launch function."""
    logger.info("🎯 ASDSADF Application Setup")
    logger.info("=" * 50)
    
    # Step 1: Check requirements
    if not check_requirements():
        logger.error("❌ Requirements check failed")
        return False
    
    # Step 2: Check environment
    if not check_environment():
        logger.error("❌ Environment check failed")
        return False
    
    # Step 3: Setup knowledge base
    if not await setup_knowledge_base():
        logger.error("❌ Knowledge base setup failed")
        return False
    
    logger.info("✅ Setup completed successfully!")
    logger.info("🚀 Starting server...")
    
    # Step 4: Start server
    start_server()
    
    return True

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Shutting down ASDSADF application")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)