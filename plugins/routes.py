import os, pytz
from datetime import datetime
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from database import get_user_bots, get_user_config
from config import Config

router = APIRouter()
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(base_dir, "web"))

@router.get("/")
async def homepage(request: Request):
    """Base URL landing page"""
    return templates.TemplateResponse(
        request=request, 
        name="homepage.html", 
        context={"request": request}
    )

@router.get("/dashboard/{user_id}")
async def dashboard(request: Request, user_id: int):
    IST = pytz.timezone(Config.TIME_ZONE)
    now = datetime.now(IST)
    bot_list = []
    refresh_interval = 300
    
    try:
        cursor = await get_user_bots(user_id)
        raw_bots = await cursor.to_list(length=100)
        for b in raw_bots:
            bot_list.append({
                "name": b['name'], 
                "username": b['username'], 
                "status": b['status']
            })
        cfg = await get_user_config(user_id)
        if cfg: 
            refresh_interval = cfg.get("interval", 300)
    except Exception as e:
        print(f"DB Fetch Error: {e}")

    # --- FIXED TEMPLATE RESPONSE ---
    return templates.TemplateResponse(
        request=request, 
        name="startup.html", 
        context={
            "request": request, 
            "bots": bot_list, 
            "time": now.strftime('%H:%M:%S'), 
            "date": now.strftime('%d %B %Y'), 
            "refresh": refresh_interval, 
            "user_id": user_id
        }
    )