# test_feed_error.py
import asyncio
import sys
import feedparser
from app.services import add_feed
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session, init_db

async def test_feed_error():
    print("Starting feed error test...")
    try:
        await init_db()
        
        async for session in get_session():
            # Test with an invalid feed URL
            try:
                print("Testing invalid feed URL...")
                await add_feed(session, "https://example.com/not-a-feed")
                print("❌ Test failed - should have raised an error")
            except ValueError as e:
                print(f"✅ Test passed: {str(e)}")
            
            # Test with a nonexistent URL
            try:
                print("Testing nonexistent URL...")
                await add_feed(session, "https://nonexistent-site-that-doesnt-exist.xyz/feed")
                print("❌ Test failed - should have raised an error")
            except ValueError as e:
                print(f"✅ Test passed: {str(e)}")
            
            # Test with a well-formed feed
            try:
                print("Testing well-formed feed...")
                # Use a known good feed URL
                result = await add_feed(session, "https://news.ycombinator.com/rss")
                print(f"✅ Test passed - added feed: {result.title}")
            except ValueError as e:
                print(f"❌ Test failed: {str(e)}")
    except Exception as e:
        print(f"Error during test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Running feed error test")
    asyncio.run(test_feed_error())
    print("Test completed")
