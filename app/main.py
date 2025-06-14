from fastapi import FastAPI, Depends, HTTPException, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi.security import OAuth2PasswordRequestForm

from .database import get_session, init_db
from . import services
from .models import Feed, Entry, User
from .auth import (
    authenticate_user, create_access_token, get_password_hash,
    get_current_user_from_cookie, login_required
)

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

# Custom error handlers
@app.exception_handler(status.HTTP_403_FORBIDDEN)
async def forbidden_exception_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse(
        "403.html", 
        {"request": request}, 
        status_code=status.HTTP_403_FORBIDDEN
    )

# User profile route
@app.get("/profile", response_class=HTMLResponse)
async def profile(request: Request, session: AsyncSession = Depends(get_session)):
    # Check if user is logged in
    current_user = await get_current_user_from_cookie(request, session)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    return templates.TemplateResponse(
        "profile.html",
        {"request": request, "current_user": current_user}
    )

# Authentication routes
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: AsyncSession = Depends(get_session)
):
    user = await authenticate_user(session, username, password)
    if not user:
        # For HTMX requests, return just the form with errors
        if request.headers.get("HX-Request") == "true":
            return templates.TemplateResponse(
                "login.html", 
                {"request": request, "error": "Invalid username or password"},
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        # For regular requests, redirect to login page
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "error": "Invalid username or password"},
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    access_token_expires = timedelta(minutes=60 * 24 * 7)  # 1 week
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="session",
        value=access_token,
        httponly=True,
        max_age=60 * 60 * 24 * 7,  # 1 week
        samesite="lax"
    )
    return response

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register", response_class=HTMLResponse)
async def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    session: AsyncSession = Depends(get_session)
):
    # Validate password
    if password != confirm_password:
        # For HTMX requests
        if request.headers.get("HX-Request") == "true":
            return templates.TemplateResponse(
                "register.html", 
                {"request": request, "error": "Passwords do not match"},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        return templates.TemplateResponse(
            "register.html", 
            {"request": request, "error": "Passwords do not match"},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if username or email already exists
    result = await session.execute(
        select(User).filter((User.username == username) | (User.email == email))
    )
    existing_user = result.scalars().first()
    if existing_user:
        error_message = "Username or email already exists"
        # For HTMX requests
        if request.headers.get("HX-Request") == "true":
            return templates.TemplateResponse(
                "register.html", 
                {"request": request, "error": error_message},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        return templates.TemplateResponse(
            "register.html", 
            {"request": request, "error": error_message},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Create new user
    hashed_password = get_password_hash(password)
    new_user = User(
        username=username,
        email=email,
        password=hashed_password
    )
    session.add(new_user)
    await session.commit()
    
    # Redirect to login
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="session")
    return response

# Protected routes
@app.get("/", response_class=HTMLResponse)
async def home(
    request: Request, 
    session: AsyncSession = Depends(get_session)
):
    # Check if user is logged in
    current_user = await get_current_user_from_cookie(request, session)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    feeds = await services.get_feeds(session)
    entries = await services.get_entries(session)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "feeds": feeds, "entries": entries, "current_user": current_user}
    )

@app.post("/feeds", response_class=HTMLResponse)
async def add_feed(
    request: Request,
    url: str = Form(...),
    category: str = Form(None),
    session: AsyncSession = Depends(get_session)
):
    # Check if user is logged in
    current_user = await get_current_user_from_cookie(request, session)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    try:
        feed = await services.add_feed(session, url, category)
        return templates.TemplateResponse(
            "feed_item.html",
            {"request": request, "feed": feed, "current_user": current_user}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/feeds/{feed_id}/entries", response_class=HTMLResponse)
async def get_feed_entries(
    request: Request,
    feed_id: int,
    session: AsyncSession = Depends(get_session)
):
    # Check if user is logged in
    current_user = await get_current_user_from_cookie(request, session)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    entries = await services.get_entries(session, feed_id=feed_id)
    return templates.TemplateResponse(
        "feed_entries.html",
        {"request": request, "entries": entries, "current_user": current_user}
    )

@app.post("/entries/{entry_id}/toggle", response_class=HTMLResponse)
async def toggle_entry(
    request: Request,
    entry_id: int,
    session: AsyncSession = Depends(get_session)
):
    # Check if user is logged in
    current_user = await get_current_user_from_cookie(request, session)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    entry = await session.get(Entry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    entry.is_read = not entry.is_read
    await session.commit()
    
    return templates.TemplateResponse(
        "feed_entry.html",
        {"request": request, "entry": entry, "current_user": current_user}
    )

@app.delete("/feeds/{feed_id}", response_class=HTMLResponse)
async def delete_feed(
    request: Request,
    feed_id: int,
    session: AsyncSession = Depends(get_session)
):
    # Check if user is logged in
    current_user = await get_current_user_from_cookie(request, session)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    feed = await session.get(Feed, feed_id)
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    await session.delete(feed)
    await session.commit()
    return ""