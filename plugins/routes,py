import os
import pytz
from datetime import datetime
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from database import get_all_bots
from config import Config

# Router initialize kiya
router = APIRouter()

# Path handling: Ye current file se 1 level upar jaakar 'web' folder dhundega
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
template_path = os.path.join(base_dir, "web")
templates = Jinja2Templates(directory=template_path)

@router.get("/")
async def dashboard(request: Request):
    """Browser Dashboard Logic"""
    IST = pytz.timezone(Config.TIME_ZONE)
    current_time = datetime.now(IST).strftime('%H:%M:%S')
    current_date = datetime.now(IST).strftime('%d %B %Y')
    
    bot_list = []
    # Database se saare bots ka data fetch karna
    cursor = await get_all_bots()
    
    async for bot_data in cursor:
        bot_list.append({
            "name": bot_data.get("name", "Unknown"),
            "username": bot_data.get("username", "bot"),
            "url": bot_data.get("url", "#"),
            "status": bot_data.get("status", "❌ Offline")
        })
    
    # HTML template render karna aur data bhejna
    return templates.TemplateResponse("startup.html", {
        "request": request, 
        "bots": bot_list, 
        "time": current_time,
        "date": current_date
    })

@router.get("/health")
async def health_check():
    """Koyeb Health Check Endpoint"""
    return {"status": "healthy", "uptime": "running"}