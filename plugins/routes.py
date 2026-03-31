import os
import pytz
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates

from database import get_user_bots, get_user_config, bots_col
from config import Config

router = APIRouter()

# --- TEMPLATE CONFIGURATION ---
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))


# -------------------------------
# 🏠 Homepage
# -------------------------------
@router.get("/")
async def homepage(request: Request):
    return templates.TemplateResponse(
        "homepage.html",
        {"request": request}
    )


# -------------------------------
# 📊 Dashboard
# -------------------------------
@router.get("/dashboard/{user_id}")
async def dashboard(request: Request, user_id: int, key: str = None):

    # 🔐 सुरक्षा (basic protection)
    if key != Config.WEB_ACCESS_KEY:
        raise HTTPException(status_code=403, detail="Access Denied")

    IST = pytz.timezone(Config.TIME_ZONE)
    now = datetime.now(IST)

    bot_list = []
    refresh_interval = 300

    try:
        # 🔄 Fetch user bots
        cursor = await get_user_bots(user_id)
        raw_bots = await cursor.to_list(length=100)

        for b in raw_bots:
            bot_list.append({
                "name": b.get("name", "Unknown"),
                "username": b.get("username", "bot"),
                "status": b.get("status", "❌ Offline")
            })

        # ⚙️ Fetch config
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
            "user_id": user_id,
            "key": key
        }
    )


# -------------------------------
# 📡 API Stats
# -------------------------------
@router.get("/api/stats")
async def get_web_stats(key: str = None):

    if key != Config.WEB_ACCESS_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")

    total_bots = await bots_col.count_documents({})
    online_bots = await bots_col.count_documents({"status": "✅ Online"})

    return {
        "total_bots": total_bots,
        "online_bots": online_bots,
        "offline_bots": total_bots - online_bots
    }