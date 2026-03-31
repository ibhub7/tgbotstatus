import os
import pytz
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.templating import Jinja2Templates
from database import get_user_bots, get_user_config, bots_col
from config import Config

router = APIRouter()

# Template path logic
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

# 🏠 Homepage
@router.get("/")
async def homepage(request: Request):
    # Pass 'request' as a keyword argument or as the first positional argument
    return templates.TemplateResponse(
        request=request, 
        name="homepage.html", 
        context={} 
    )

# 📊 Dashboard (Direct access via User ID)
@router.get("/dashboard/{user_id}")
async def dashboard(request: Request, user_id: int):
    IST = pytz.timezone(Config.TIME_ZONE)
    now = datetime.now(IST)
    bot_list = []
    
    try:
        cursor = await get_user_bots(user_id)
        raw_bots = await cursor.to_list(length=100)
        for b in raw_bots:
            bot_list.append({
                "name": b.get("name", "Unknown"),
                "username": b.get("username", "bot"),
                "status": b.get("status", "❌ Offline")
            })
    except Exception as e:
        print(f"Error: {e}")

    return templates.TemplateResponse("startup.html", {
        "request": request, 
        "bots": bot_list, 
        "user_id": user_id,
        "time": now.strftime("%H:%M:%S")
    })

# 📡 Stats Login (GET)
@router.get("/stats")
async def stats_page(request: Request):
    return templates.TemplateResponse("stats_login.html", {"request": request})

# 📡 Stats Verify (POST)
@router.post("/stats")
async def verify_stats(request: Request, key: str = Form(...)):
    # Check if the key matches Config.WEB_ACCESS_KEY
    if key != Config.WEB_ACCESS_KEY:
        # Proceed to return the denied.html file as requested 
        return templates.TemplateResponse("denied.html", {"request": request}, status_code=403)

    # If key matches, proceed to show stats 
    total = await bots_col.count_documents({})
    online = await bots_col.count_documents({"status": "✅ Online"})
    
    return templates.TemplateResponse("stats_view.html", {
        "request": request, 
        "total": total, 
        "online": online, 
        "offline": total - online
    })