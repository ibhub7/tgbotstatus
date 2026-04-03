import os
import pytz
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, Form, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from database import get_user_bots, get_user_config, bots_col
from config import Config

router = APIRouter()

# ᴛᴇᴍᴘʟᴀᴛᴇ ᴘᴀᴛʜ ʟᴏɢɪᴄ
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

# 🏠 ʜᴏᴍᴇᴘᴀɢᴇ
@router.get("/")
async def homepage(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="homepage.html", 
        context={} 
    )

# 📊 ᴅᴀꜱʜʙᴏᴀʀᴅ (ᴅɪʀᴇᴄᴛ ᴀᴄᴄᴇꜱꜱ ᴠɪᴀ ᴜꜱᴇʀ ɪᴅ)
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
                "status": b.get("status", "❌ ᴏꜰꜰʟɪɴᴇ")
            })
    except Exception as e:
        print(f"Error fetching bots: {e}")

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "bots": bot_list, 
            "user_id": user_id,
            "time": now.strftime("%H:%M:%S")
        }
    )

# 📡 ꜱᴛᴀᴛꜱ ʟᴏɢɪɴ (ɢᴇᴛ)
@router.get("/stats")
async def stats_page(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="stats_login.html", 
        context={}
    )

# 📡 ꜱᴛᴀᴛꜱ ᴠᴇʀɪꜰʏ (ᴘᴏꜱᴛ)
@router.post("/stats")
async def verify_stats(request: Request, key: str = Form(...)):
    if key != Config.WEB_ACCESS_KEY:
        return templates.TemplateResponse(
            request=request, 
            name="denied.html", 
            context={}, 
            status_code=403
        )

    total = await bots_col.count_documents({})
    online = await bots_col.count_documents({"status": "✅ ᴏɴʟɪɴᴇ"})
    
    return templates.TemplateResponse(
        request=request, 
        name="stats_view.html", 
        context={
            "total": total, 
            "online": online, 
            "offline": total - online
        }
    )

# --- ꜱᴇʀᴠᴇ ꜰᴀᴠɪᴄᴏɴ ꜰʀᴏᴍ ᴛᴇᴍᴘʟᴀᴛᴇꜱ ---
@router.get('/favicon.ico', include_in_schema=False)
async def favicon():
    # ᴜꜱɪɴɢ ʙᴀꜱᴇ_ᴅɪʀ ᴛᴏ ᴇɴꜱᴜʀᴇ ɪᴛ ᴡᴏʀᴋꜱ ᴏɴ ᴀʟʟ ᴘʟᴀᴛꜰᴏʀᴍꜱ
    favicon_path = os.path.join(base_dir, "templates", "favicon.ico")
    
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    else:
        # ɴᴏ ᴄᴏɴᴛᴇɴᴛ ꜱᴛᴀᴛᴜꜱ ᴛᴏ ꜱɪʟᴇɴᴄᴇ ᴛʜᴇ 404 ʟᴏɢꜱ
        return Response(status_code=204)