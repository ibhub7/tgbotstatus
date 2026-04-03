import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    MONGO_URI = os.getenv("MONGO_URI", "")
    OWNER_ID = int(os.getenv("OWNER_ID", 0))
    WEB_ACCESS_KEY = os.getenv("WEB_ACCESS_KEY", "ipo")
    ACCESS_KEY = os.getenv("WEB_ACCESS_KEY", "ipos") 
    
    TIME_ZONE = "Asia/Kolkata"
    CHECK_INTERVAL = 1800 #30 min
    DEFAULT_PING = 300  # 𝟻 𝙼𝚒𝚗𝚞𝚝𝚎𝚜
    DEFAULT_MSG = 900   # 𝟷5 𝙼𝚒𝚗𝚞𝚝𝚎𝚜