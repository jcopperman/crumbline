import feedparser
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import Feed, Entry, Category

async def add_feed(session: AsyncSession, url: str, category_name: str = None) -> Feed:
    # Parse feed to get initial data
    try:
        parsed = feedparser.parse(url)
        if parsed.bozo and hasattr(parsed, 'bozo_exception'):
            raise ValueError(f"Invalid RSS feed: {parsed.bozo_exception}")
        elif parsed.bozo:
            raise ValueError("Invalid RSS feed format")
        
        # Check if feed has entries
        if not hasattr(parsed, 'entries') or len(parsed.entries) == 0:
            raise ValueError("Feed contains no entries")
            
        # Check if feed has a title
        if not hasattr(parsed.feed, 'title'):
            raise ValueError("Feed has no title")
    except Exception as e:
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
    
    # Create feed
    feed = Feed(
        url=url,
        title=parsed.feed.get("title", url),
        description=parsed.feed.get("description", ""),
        category=category
    )
    session.add(feed)
    await session.flush()
    
    # Add initial entries
    for entry in parsed.entries[:10]:  # Limit to 10 most recent entries
        published = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                published = datetime(*entry.published_parsed[:6])
            except:
                pass
        
        db_entry = Entry(
            feed=feed,
            title=entry.title,
            link=entry.link,
            published=published,
            content=entry.get("description", "")
        )
        session.add(db_entry)
    
    await session.commit()
    return feed

async def update_feed(session: AsyncSession, feed: Feed) -> None:
    parsed = feedparser.parse(feed.url)
    if parsed.bozo:
        return
    
    # Update feed metadata
    feed.title = parsed.feed.get("title", feed.title)
    feed.description = parsed.feed.get("description", feed.description)
    feed.last_updated = datetime.utcnow()
    
    # Get existing entry links
    existing_links = await session.execute(
        select(Entry.link).where(Entry.feed_id == feed.id)
    )
    existing_links = {link[0] for link in existing_links}
    
    # Add new entries
    for entry in parsed.entries:
        if entry.link in existing_links:
            continue
            
        published = None
        if hasattr(entry, "published_parsed"):
            published = datetime(*entry.published_parsed[:6])
        
        db_entry = Entry(
            feed=feed,
            title=entry.title,
            link=entry.link,
            published=published,
            content=entry.get("description", "")
        )
        session.add(db_entry)
    
    await session.commit()

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