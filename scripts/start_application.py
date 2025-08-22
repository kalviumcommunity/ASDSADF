import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from populate_knowledge_base import KnowledgeBasePopulator
from src.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def setup_application():
    """Set up the application with initial data."""
    logger.info("Setting up ASDSADF application...")
    
    # Check if Gemini API key is set
    if not settings.gemini_api_key or settings.gemini_api_key == "your_gemini_api_key_here":
        logger.error("Please set your GEMINI_API_KEY in the .env file")
        return False
    
    # Populate knowledge base
    try:
        populator = KnowledgeBasePopulator()
        success_count = await populator.populate_sample_data()
        
        if success_count > 0:
            logger.info(f"✅ Knowledge base populated with {success_count} documents")
        else:
            logger.warning("⚠️ No documents were added to knowledge base")
        
        logger.info("✅ Application setup completed successfully!")
        logger.info(f"🚀 Ready to start server on {settings.app_host}:{settings.app_port}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(setup_application())
    if not success:
        sys.exit(1)