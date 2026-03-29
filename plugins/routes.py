import os
import pytz
from datetime import datetime
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from database import get_all_bots
from config import Config

router = APIRouter()

# Path handling logic (Safe for Koyeb/Render)
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
template_path = os.path.join(base_dir, "web")
templates = Jinja2Templates(directory=template_path)

@router.get("/")
async def dashboard(request: Request):
    """Browser Dashboard with Fixed TemplateResponse"""
    IST = pytz.timezone(Config.TIME_ZONE)
    now = datetime.now(IST)
    current_time = now.strftime('%H:%M:%S')
    current_date = now.strftime('%d %B %Y')
    
    bot_list = []
    # Database se bots fetch karna
    cursor = await get_all_bots()
    
    async for bot_data in cursor:
        bot_list.append({
            "name": bot_data.get("name", "Unknown Bot"),
            "username": bot_data.get("username", "bot"),
            "status": bot_data.get("status", "❌ Offline")
        })
    
    # --- FIXED RETURN STATEMENT ---
    # Starlette/FastAPI expects 'request' as a separate keyword or inside context
    return templates.TemplateResponse(
        request=request, 
        name="startup.html", 
        context={
            "bots": bot_list, 
            "time": current_time,
            "date": current_date
        }
    )

@router.get("/health")
async def health():
    return {"status": "connected", "message": "Monitor is stable"}