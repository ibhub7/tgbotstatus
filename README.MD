# Telegram Bot Status Monitor

A professional status monitor that pings your bots hosted on Koyeb/Render and updates a live status message in a Telegram channel.

## Features
- **Auto-Update**: Edits a single message every 5 minutes.
- **Persistent Storage**: Uses MongoDB to store your bot list.
- **Timezone Support**: Displays updates in Asia/Kolkata time.
- **Clean UI**: Minimalist status report without messy URLs.

## Commands (Private Chat)
- `/addbot "Bot Name" URL` - Add a new bot (use quotes for names with spaces).
- `/removebot "Bot Name"` - Remove a bot from monitoring.

## Deployment
1. Set up a MongoDB Atlas cluster.
2. Get your `API_ID` and `API_HASH` from my.telegram.org.
3. Deploy to Koyeb using the provided `Dockerfile`.
4. Set all Environment Variables in the Koyeb dashboard.

/app (Root)
├── bot.py                # Bot initialization & background monitoring logic 
├── main.py               # FastAPI entry point & lifespan manager 
├── database.py           # MongoDB collections & helper functions 
├── config.py             # Environment variables & configuration 
├── Dockerfile            # Containerization instructions [cite: 1, 2]
├── Procfile              # Deployment command for web/worker [cite: 4]
├── requirements.txt      # Python dependencies [cite: 5]
├── .dockerignore         # Files excluded from Docker builds 
├── README.MD             # Project documentation & command guide 
│
├── plugins/              # Pyrogram Smart-Plugins & Web Routes 
│   ├──--inity--.py 
│   ├── commands.py       # Bot command handlers (/start, /list, /addbot) 
│   ├── routes.py         # FastAPI APIRouter for web endpoints 
│   ├──ex_mongo_manager.py
│   └── imongo_manager.py  # Administrative MongoDB utility script 
│
└── templates/                  # Frontend HTML Templates 
    ├── homepage.html     # Main landing page 
    ├── startup.html      # Dynamic user status dashboard 
    ├── stats_login.html  # Admin statistics login page 
    ├── stats_view.html   # Global network statistics view 
    ├── dashboard.html
    ├── index.html
    └── denied.html       # Access denied error page
