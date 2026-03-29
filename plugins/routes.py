import os
import pytz
from datetime import datetime
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from database import get_user_bots, get_user_config # New functions
from config import Config

router = APIRouter()

# Path handling logic (Safe for Koyeb/Docker)
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
template_path = os.path.join(base_dir, "web")
templates = Jinja2Templates(directory=template_path)

@router.get("/")
async def home(request: Request):
    """Main landing page (Optional: Redirect to a main help page)"""
    return {"status": "running", "message": "Visit your personal dashboard link from the bot."}

@router.get("/dashboard/{user_id}")
async def dashboard(request: Request, user_id: int):
    """Specific User ka Personal Dashboard"""
    IST = pytz.timezone(Config.TIME_ZONE)
    now = datetime.now(IST)
    current_time = now.strftime('%H:%M:%S')
    current_date = now.strftime('%d %B %Y')
    
    bot_list = []
    refresh_interval = 300 # Default 5 min
    
    try:
        # 1. Sirf is User ke bots fetch karna
        cursor = await get_user_bots(user_id)
        raw_bots = await cursor.to_list(length=100) 
        
        for bot_data in raw_bots:
            bot_list.append({
                "name": bot_data.get("name", "Unknown Bot"),
                "username": bot_data.get("username", "bot"),
                "status": bot_data.get("status", "❌ Offline")
            })
            
        # 2. User ki personal refresh settings fetch karna
        user_cfg = await get_user_config(user_id)
        if user_cfg:
            # DB mein seconds mein hai, HTML ke liye use waisa hi rehne dein
            refresh_interval = user_cfg.get("interval", 300)

    except Exception as e:
        print(f"Dashboard Error for {user_id}: {e}")

    return templates.TemplateResponse(
        request=request, 
        name="startup.html", 
        context={
            "request": request,
            "bots": bot_list, 
            "time": current_time,
            "date": current_date,
            "refresh": refresh_interval, # Dashboard refresh timer
            "user_id": user_id
        }
    )

@router.get("/health")
async def health():
    return {"status": "connected", "message": "SaaS Monitor is stable"}