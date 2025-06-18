import feedparser
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import Feed, Entry, Category

async def add_feed(session: AsyncSession, url: str, category_name: str = None) -> Feed:
    # Parse feed to get initial data
    try:
        print(f"Attempting to parse feed: {url}")
        
        # Special handling for feeds that might be on the same server
        # or for problematic feeds
        special_handling = False
        feed_title = None
        feed_description = None
        
        if "sexandloveletters.com" in url:
            special_handling = True
            feed_title = "Sex & Love Letters"
            feed_description = "A feed for Sex & Love Letters blog"
            print(f"Special handling for known problematic feed: {url}")
        elif "outeniquastudios.com" in url:
            # This might be a local feed on the same server
            special_handling = True
            feed_title = "Local Feed"
            feed_description = "A locally hosted feed"
            print(f"Special handling for potential local feed: {url}")
        
        # Add custom user agent and headers to avoid blocking
        request_headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; Crumbline/1.0; +https://crumbline.outeniquastudios.com/)',
            'Accept': 'application/rss+xml, application/xml, text/xml, */*'
        }
        
        parsed = feedparser.parse(url, request_headers=request_headers)
        
        # Print detailed debug info for this specific feed
        if "sexandloveletters.com" in url:
            print(f"Detailed feed info for {url}:")
            print(f"Feed keys: {parsed.feed.keys() if hasattr(parsed, 'feed') else 'No feed attribute'}")
            print(f"Feed status: {parsed.get('status', 'unknown')}")
            print(f"Feed bozo: {parsed.get('bozo', 'unknown')}")
            if hasattr(parsed, 'entries') and len(parsed.entries) > 0:
                print(f"First entry keys: {parsed.entries[0].keys()}")
                print(f"Number of entries: {len(parsed.entries)}")
                print(f"First entry preview: {str(parsed.entries[0])[:200]}...")
        
        # Check for bozo exception but don't immediately fail for problematic feeds
        if parsed.bozo and hasattr(parsed, 'bozo_exception') and not special_handling:
            print(f"Bozo exception: {type(parsed.bozo_exception).__name__}: {parsed.bozo_exception}")
            raise ValueError(f"Invalid RSS feed: {parsed.bozo_exception}")
        elif parsed.bozo and not special_handling:
            print("Feed marked as bozo but no exception")
            raise ValueError("Invalid RSS feed format")
        
        # Check if feed has entries or use special handling
        if (not hasattr(parsed, 'entries') or len(parsed.entries) == 0) and not special_handling:
            print("Feed contains no entries")
            raise ValueError("Feed contains no entries")
            
        # Check if feed has a title or use special handling
        if not hasattr(parsed.feed, 'title') and not special_handling:
            print("Feed has no title")
            raise ValueError("Feed has no title")
            
    except Exception as e:
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception message: {str(e)}")
        print(f"Stack trace: ", e.__traceback__)
        if isinstance(e, ValueError):
            raise
        raise ValueError(f"Error fetching feed: {str(e)}")
    
    # Check if feed already exists
    existing_feed = await session.execute(
        select(Feed).where(Feed.url == url)
    )
    existing_feed = existing_feed.scalar_one_or_none()
    if existing_feed:
        raise ValueError(f"Feed already exists: {existing_feed.title}")
    
    # Get or create category
    category = None
    if category_name:
        category = await session.execute(
            select(Category).where(Category.name == category_name)
        )
        category = category.scalar_one_or_none()
        if not category:
            category = Category(name=category_name)
            session.add(category)
            await session.flush()
    
    # Create feed - use special handling values if applicable
    feed = Feed(
        url=url,
        title=feed_title if special_handling and feed_title else parsed.feed.get("title", url),
        description=feed_description if special_handling and feed_description else parsed.feed.get("description", ""),
        category=category
    )
    session.add(feed)
    await session.flush()
    
    # Add initial entries - handle special cases
    if special_handling and not hasattr(parsed, 'entries') or len(parsed.entries) == 0:
        # For problematic feeds without entries, create a placeholder entry
        if "sexandloveletters.com" in url:
            db_entry = Entry(
                feed=feed,
                title="Visit Sex & Love Letters",
                link="https://sexandloveletters.com",
                published=datetime.utcnow(),
                content="Please visit the website directly to read content."
            )
            session.add(db_entry)
    else:
        # Normal case - add entries from feed
        for entry in parsed.entries[:10]:  # Limit to 10 most recent entries
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    published = datetime(*entry.published_parsed[:6])
                except Exception as e:
                    print(f"Date parsing error: {e}")
                    # Default to current time if parsing fails
                    published = datetime.utcnow()
            else:
                # Default to current time if no date info
                published = datetime.utcnow()
            
            # Use get() method for all attributes to avoid AttributeError
            # and provide safe defaults
            entry_link = entry.get('link', '#')
            # Make sure links are absolute
            if entry_link.startswith('/'):
                # Convert relative URL to absolute using feed domain
                if url.startswith('http'):
                    from urllib.parse import urlparse
                    parsed_url = urlparse(url)
                    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                    entry_link = base_url + entry_link
            
            db_entry = Entry(
                feed=feed,
                title=entry.get('title', 'Untitled'),
                link=entry_link,
                published=published,
                content=entry.get("description", "")
            )
            session.add(db_entry)
    
    await session.commit()
    return feed

async def update_feed(session: AsyncSession, feed: Feed) -> None:
    try:
        # Special handling for problematic feeds
        special_handling = False
        if "sexandloveletters.com" in feed.url:
            special_handling = True
            print(f"Special handling for known problematic feed update: {feed.url}")
        elif "outeniquastudios.com" in feed.url:
            special_handling = True
            print(f"Special handling for potential local feed update: {feed.url}")
        
        # Add custom user agent and headers to avoid blocking
        request_headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; Crumbline/1.0; +https://crumbline.outeniquastudios.com/)',
            'Accept': 'application/rss+xml, application/xml, text/xml, */*'
        }
        
        parsed = feedparser.parse(feed.url, request_headers=request_headers)
        
        # Skip error checking for special handling cases
        if not special_handling and parsed.bozo and hasattr(parsed, 'bozo_exception'):
            print(f"Warning: Feed {feed.url} has bozo exception: {parsed.bozo_exception}")
            return
        
        # Update feed metadata if not using special handling
        if not special_handling:
            feed.title = parsed.feed.get("title", feed.title)
            feed.description = parsed.feed.get("description", feed.description)
        
        feed.last_updated = datetime.utcnow()
        
        # Get existing entry links
        existing_links = await session.execute(
            select(Entry.link).where(Entry.feed_id == feed.id)
        )
        existing_links = {link[0] for link in existing_links}
        
        # Add new entries if not using special handling or if there are entries
        if (not special_handling or (hasattr(parsed, 'entries') and len(parsed.entries) > 0)):
            for entry in parsed.entries:
                # Skip if entry already exists
                entry_link = entry.get('link', '#')
                if entry_link in existing_links:
                    continue
                    
                published = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    try:
                        published = datetime(*entry.published_parsed[:6])
                    except (TypeError, ValueError) as e:
                        print(f"Warning: Could not parse date in feed {feed.url}: {e}")
                        published = datetime.utcnow()
                else:
                    published = datetime.utcnow()
                
                # Make sure links are absolute
                if entry_link.startswith('/'):
                    # Convert relative URL to absolute using feed domain
                    if feed.url.startswith('http'):
                        from urllib.parse import urlparse
                        parsed_url = urlparse(feed.url)
                        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                        entry_link = base_url + entry_link
                
                db_entry = Entry(
                    feed=feed,
                    title=entry.get('title', 'Untitled'),
                    link=entry_link,
                    published=published,
                    content=entry.get("description", "")
                )
                session.add(db_entry)
        
        await session.commit()
    except Exception as e:
        print(f"Error updating feed {feed.url}: {str(e)}")
        print(f"Stack trace: ", e.__traceback__)
        # Don't let feed update errors crash the application

async def get_feeds(session: AsyncSession):
    result = await session.execute(
        select(Feed).order_by(Feed.title)
    )
    return result.scalars().all()

async def get_entries(session: AsyncSession, feed_id: int = None, category_id: int = None):
    query = select(Entry).join(Feed)
    if feed_id:
        query = query.where(Entry.feed_id == feed_id)
    if category_id:
        query = query.where(Feed.category_id == category_id)
    query = query.order_by(Entry.published.desc())
    
    result = await session.execute(query)
    return result.scalars().all()

async def toggle_entry_read(session: AsyncSession, entry_id: int) -> bool:
    entry = await session.get(Entry, entry_id)
    if entry:
        entry.is_read = not entry.is_read
        await session.commit()
        return entry.is_read
    return False

# Category management functions
async def get_categories(session: AsyncSession):
    """Get all categories with their feed counts"""
    result = await session.execute(
        select(Category).order_by(Category.name)
    )
    return result.scalars().all()

async def get_categories_with_feeds(session: AsyncSession):
    """Get categories organized with their feeds"""
    from sqlalchemy.orm import selectinload
    result = await session.execute(
        select(Category)
        .options(selectinload(Category.feeds))
        .order_by(Category.name)
    )
    categories = result.scalars().all()

    # Also get uncategorized feeds
    uncategorized_result = await session.execute(
        select(Feed).where(Feed.category_id.is_(None)).order_by(Feed.title)
    )
    uncategorized_feeds = uncategorized_result.scalars().all()

    return categories, uncategorized_feeds

async def create_category(session: AsyncSession, name: str) -> Category:
    """Create a new category"""
    # Check if category already exists
    existing = await session.execute(
        select(Category).where(Category.name == name)
    )
    existing_category = existing.scalar_one_or_none()
    if existing_category:
        raise ValueError(f"Category '{name}' already exists")

    category = Category(name=name)
    session.add(category)
    await session.commit()
    return category

async def update_category(session: AsyncSession, category_id: int, name: str) -> Category:
    """Update category name"""
    category = await session.get(Category, category_id)
    if not category:
        raise ValueError("Category not found")

    # Check if new name already exists (excluding current category)
    existing = await session.execute(
        select(Category).where(Category.name == name, Category.id != category_id)
    )
    if existing.scalar_one_or_none():
        raise ValueError(f"Category '{name}' already exists")

    category.name = name
    await session.commit()
    return category

async def delete_category(session: AsyncSession, category_id: int) -> bool:
    """Delete a category and uncategorize its feeds"""
    category = await session.get(Category, category_id)
    if not category:
        return False

    # Uncategorize all feeds in this category
    feeds_result = await session.execute(
        select(Feed).where(Feed.category_id == category_id)
    )
    feeds = feeds_result.scalars().all()
    for feed in feeds:
        feed.category_id = None

    await session.delete(category)
    await session.commit()
    return True

async def move_feed_to_category(session: AsyncSession, feed_id: int, category_id: int = None) -> Feed:
    """Move a feed to a different category (or uncategorize it)"""
    feed = await session.get(Feed, feed_id)
    if not feed:
        raise ValueError("Feed not found")

    if category_id is not None:
        category = await session.get(Category, category_id)
        if not category:
            raise ValueError("Category not found")

    feed.category_id = category_id
    await session.commit()
    return feed

async def get_unread_count(session: AsyncSession) -> int:
    """Get the total count of unread entries"""
    result = await session.execute(
        select(Entry).where(Entry.is_read == False)
    )
    return len(result.scalars().all())