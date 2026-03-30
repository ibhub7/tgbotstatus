import os, pytz
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates
from database import get_user_bots, get_user_config, bots_col 
from config import Config

router = APIRouter()

# --- TEMPLATE CONFIGURATION ---
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

# --- 1. PUBLIC HOMEPAGE ---
@router.get("/")
async def homepage(request: Request):
    """Base URL landing page - Corrected TemplateResponse"""
    return templates.TemplateResponse(
        name="homepage.html", 
        context={"request": request}
    )

# --- 2. SECURE DASHBOARD ---
@router.get("/dashboard/{user_id}")
async def dashboard(request: Request, user_id: int, key: str = None):
    # Security check: Ensure the key matches our Config
    if key != Config.WEB_ACCESS_KEY:
        raise HTTPException(status_code=403, detail="Access Denied")

    IST = pytz.timezone(Config.TIME_ZONE)
    now = datetime.now(IST)
    bot_list = []
    refresh_interval = 300
    
    try:
        # Fetch bot data from MongoDB
        cursor = await get_user_bots(user_id)
        raw_bots = await cursor.to_list(length=100)
        
        for b in raw_bots:
            bot_list.append({
                "name": b.get('name', 'Unknown'), 
                "username": b.get('username', 'bot'), 
                "status": b.get('status', '❌ Offline')
            })
            
        # Fetch user configuration (interval/link)
        cfg = await get_user_config(user_id)
        if cfg: 
            refresh_interval = cfg.get("interval", 300)
            
    except Exception as e:
        # Log error to console for debugging
        print(f"Web Dashboard Error: {e}")

    # FIXED: Using explicit 'context' keyword to prevent unhashable dict error
    return templates.TemplateResponse(
        name="startup.html", 
        context={
            "request": request, 
            "bots": bot_list, 
            "time": now.strftime('%H:%M:%S'), 
            "date": now.strftime('%d %B %Y'), 
            "refresh": refresh_interval, 
            "user_id": user_id,
            "key": key 
        }
    )

# --- 3. SECURE STATS API ---
@router.get("/api/stats")
async def get_web_stats(key: str = None):
    """Stats API - Locked with Key for internal monitoring"""
    if key != Config.WEB_ACCESS_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    total_bots = await bots_col.count_documents({})
    online_bots = await bots_col.count_documents({"status": "✅ Online"})
    
    return {
        "total_bots": total_bots,
        "online_bots": online_bots
    }