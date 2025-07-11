#!/usr/bin/env python3
"""
Test script to verify local development setup
"""
import asyncio
import sys
import os
sys.path.append('.')

from app.core.config import settings
from app.core.database import get_async_session
from app.core.graph_db import get_graph_db

async def test_postgresql():
    """Test PostgreSQL connection"""
    try:
        from sqlalchemy import text
        async with get_async_session() as session:
            result = await session.execute(text("SELECT 1"))
            print("✅ PostgreSQL: Connected successfully")
            return True
    except Exception as e:
        print(f"❌ PostgreSQL: Connection failed - {e}")
        return False

async def test_neo4j():
    """Test Neo4j connection"""
    try:
        graph_db = await get_graph_db()
        result = await graph_db.execute_query("RETURN 1 as test")
        print("✅ Neo4j: Connected successfully")
        return True
    except Exception as e:
        print(f"❌ Neo4j: Connection failed - {e}")
        return False

async def test_redis():
    """Test Redis connection"""
    try:
        import redis
        r = redis.Redis(host=settings.redis_host, port=settings.redis_port, decode_responses=True)
        r.ping()
        print("✅ Redis: Connected successfully")
        return True
    except Exception as e:
        print(f"❌ Redis: Connection failed - {e}")
        return False

def test_env_variables():
    """Test environment variables"""
    tests = [
        ("TELEGRAM_BOT_TOKEN", settings.telegram_bot_token),
        ("OPENAI_API_KEY", settings.openai_api_key),
        ("POSTGRES_HOST", settings.postgres_host),
        ("NEO4J_URI", settings.neo4j_uri),
    ]
    
    all_good = True
    for name, value in tests:
        if value and not value.startswith("your_") and not value.startswith("YOUR_"):
            print(f"✅ {name}: Configured")
        else:
            print(f"❌ {name}: Not configured or using placeholder")
            all_good = False
    
    return all_good

async def main():
    """Main test function"""
    print("🚀 Testing Local Development Setup")
    print("=" * 40)
    
    # Test environment variables
    print("\n📋 Environment Variables:")
    env_ok = test_env_variables()
    
    # Test database connections
    print("\n🗄️ Database Connections:")
    pg_ok = await test_postgresql()
    neo4j_ok = await test_neo4j()
    redis_ok = await test_redis()
    
    # Summary
    print("\n📊 Summary:")
    print("=" * 20)
    
    if env_ok and pg_ok and neo4j_ok and redis_ok:
        print("🎉 All tests passed! Your local development environment is ready.")
        print("\nNext steps:")
        print("1. Start the application: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        print("2. Visit: http://localhost:8000/docs")
        print("3. Test your Telegram bot")
        return True
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)