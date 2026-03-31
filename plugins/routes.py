import os
import pytz
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from database import get_user_bots, get_user_config, bots_col
from config import Config

router = APIRouter()

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

@router.get("/")
async def homepage(request: Request):
    return templates.TemplateResponse("homepage.html", {"request": request})

# -------------------------------
# 📊 Dashboard (Key Removed from URL)
# -------------------------------
@router.get("/dashboard/{user_id}")
async def dashboard(request: Request, user_id: int):
    IST = pytz.timezone(Config.TIME_ZONE)
    now = datetime.now(IST)

    bot_list = []
    refresh_interval = 300

    try:
        # Fetch user bots using your database helper
        cursor = await get_user_bots(user_id)
        raw_bots = await cursor.to_list(length=100)

        for b in raw_bots:
            bot_list.append({
                "name": b.get("name", "Unknown"),
                "username": b.get("username", "bot"),
                "status": b.get("status", "❌ Offline")
            })

        # Fetch config using your database helper
        cfg = await get_user_config(user_id)
        if cfg:
            refresh_interval = cfg.get("interval", 300)

    except Exception as e:
        print(f"Web Dashboard Error: {e}")

    return templates.TemplateResponse(
        "startup.html",
        {
            "request": request,
            "bots": bot_list,
            "time": now.strftime("%H:%M:%S"),
            "date": now.strftime("%d %B %Y"),
            "refresh": refresh_interval,
            "user_id": user_id
        }
    )

# -------------------------------
# 📡 Stats (Key Entry & Logic)
# -------------------------------
@router.get("/stats")
async def stats_login_page(request: Request):
    # This renders the key input form
    return templates.TemplateResponse("stats_login.html", {"request": request})

@router.post("/stats")
async def verify_stats_access(request: Request, key: str = Form(...)):
    # 🔐 Security Check using Config key
    if key != Config.WEB_ACCESS_KEY:
        # If wrong, show the denied.html from your specific path
        return templates.TemplateResponse("denied.html", {"request": request}, status_code=403)

    # If key is correct, fetch global stats
    total_bots = await bots_col.count_documents({})
    online_bots = await bots_col.count_documents({"status": "✅ Online"})
    
    return templates.TemplateResponse(
        "stats_view.html", 
        {
            "request": request,
            "total": total_bots,
            "online": online_bots,
            "offline": total_bots - online_bots
        }
    )

@router.get("/stats")
async def stats_page(request: Request):
    return templates.TemplateResponse("stats_login.html", {"request": request})

@router.post("/stats")
async def verify_stats(request: Request, key: str = Form(...)):
    if key != Config.WEB_ACCESS_KEY:
        return templates.TemplateResponse("denied.html", {"request": request}, status_code=403)

    # If key is correct, fetch stats from DB
    total_bots = await bots_col.count_documents({})
    online_bots = await bots_col.count_documents({"status": "✅ Online"})
    
    return templates.TemplateResponse(
        "stats_view.html", 
        {
            "request": request,
            "total_bots": total_bots,
            "online_bots": online_bots,
            "offline_bots": total_bots - online_bots
        }
    )