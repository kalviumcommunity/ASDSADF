#!/usr/bin/env python3
"""
Test script to verify ASDSADF system functionality
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent / "src"))

from src.asdsadf_agent import ASASSDFAgent
from src.models import UserQuery, PromptType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_system():
    """Test the complete ASDSADF system."""
    logger.info("🧪 Testing ASDSADF System")
    logger.info("=" * 30)
    
    try:
        # Initialize agent
        logger.info("1. Initializing agent...")
        agent = ASASSDFAgent()
        success = await agent.initialize()
        
        if not success:
            logger.error("❌ Agent initialization failed")
            return False
        
        logger.info("✅ Agent initialized successfully")
        
        # Test health check
        logger.info("2. Testing health check...")
        health = await agent.get_health_status()
        logger.info(f"Health status: {health['status']}")
        
        if health['status'] != 'healthy':
            logger.warning("⚠️ System not fully healthy")
        
        # Test query processing
        logger.info("3. Testing query processing...")
        test_query = UserQuery(
            message="I'm a beginner with HTML/CSS. I want to learn React in 3 months. Can you create a roadmap?",
            prompt_type=PromptType.ZERO_SHOT
        )
        
        response = await agent.process_query(test_query)
        
        # Validate response structure
        required_fields = ["user_profile", "roadmap", "milestones", "next_steps"]
        missing_fields = [field for field in required_fields if field not in response]
        
        if missing_fields:
            logger.error(f"❌ Response missing fields: {missing_fields}")
            return False
        
        logger.info("✅ Query processing test passed")
        
        # Check roadmap structure
        roadmap = response.get("roadmap", {})
        phases = roadmap.get("phases", [])
        
        if not phases:
            logger.warning("⚠️ No phases in roadmap")
        else:
            logger.info(f"✅ Roadmap generated with {len(phases)} phases")
        
        # Test knowledge base
        logger.info("4. Testing knowledge base...")
        if agent.rag_system:
            stats = await agent.rag_system.get_collection_stats()
            doc_count = stats.get("total_documents", 0)
            
            if doc_count > 0:
                logger.info(f"✅ Knowledge base has {doc_count} documents")
            else:
                logger.warning("⚠️ Knowledge base is empty")
        
        logger.info("🎉 All tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

async def main():
    """Run the test suite."""
    success = await test_system()
    
    if success:
        logger.info("✅ System test completed successfully")
        logger.info("🚀 Ready to run: python run_setup.py")
    else:
        logger.error("❌ System test failed")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())