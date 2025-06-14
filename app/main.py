from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from typing import List

from .database import get_session, init_db
from . import services
from .models import Feed, Entry

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Background scheduler for feed updates
scheduler = AsyncIOScheduler()

async def update_all_feeds():
    async for session in get_session():
        feeds = await services.get_feeds(session)
        for feed in feeds:
            await services.update_feed(session, feed)

@app.on_event("startup")
async def startup_event():
    await init_db()
    scheduler.add_job(update_all_feeds, 'interval', minutes=30)
    scheduler.start()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, session: AsyncSession = Depends(get_session)):
    feeds = await services.get_feeds(session)
    entries = await services.get_entries(session)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "feeds": feeds, "entries": entries}
    )

@app.post("/feeds", response_class=HTMLResponse)
async def add_feed(
    request: Request,
    url: str = Form(...),
    category: str = Form(None),
    session: AsyncSession = Depends(get_session)
):
    try:
        feed = await services.add_feed(session, url, category)
        return templates.TemplateResponse(
            "feed_item.html",
            {"request": request, "feed": feed}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/feeds/{feed_id}/entries", response_class=HTMLResponse)
async def get_feed_entries(
    request: Request,
    feed_id: int,
    session: AsyncSession = Depends(get_session)
):
    entries = await services.get_entries(session, feed_id=feed_id)
    return templates.TemplateResponse(
        "feed_entries.html",
        {"request": request, "entries": entries}
    )

@app.post("/entries/{entry_id}/toggle", response_class=HTMLResponse)
async def toggle_entry(
    request: Request,
    entry_id: int,
    session: AsyncSession = Depends(get_session)
):
    entry = await session.get(Entry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    entry.is_read = not entry.is_read
    await session.commit()
    
    return templates.TemplateResponse(
        "feed_entry.html",
        {"request": request, "entry": entry}
    )

@app.delete("/feeds/{feed_id}", response_class=HTMLResponse)
async def delete_feed(
    request: Request,
    feed_id: int,
    session: AsyncSession = Depends(get_session)
):
    feed = await session.get(Feed, feed_id)
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    await session.delete(feed)
    await session.commit()
    return "" 