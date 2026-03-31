# 🚀 Telegram Bot Status Monitor

A powerful and professional status monitoring system that continuously checks your bots (hosted on platforms like Koyeb or Render) and updates a live status message in a Telegram channel.

---

## ✨ Features

* 🔄 **Auto Update**
  Automatically edits a single Telegram message at regular intervals (default: every 5 minutes).

* 🗄️ **Persistent Storage**
  Uses MongoDB to securely store and manage your bot list.

* 🌍 **Timezone Support**
  Displays timestamps in your configured timezone (default: Asia/Kolkata).

* 🎯 **Clean Dashboard UI**
  Minimal and user-friendly web interface with no messy URLs.

* ⚡ **FastAPI + Pyrogram Integration**
  Combines web dashboard + Telegram bot in one system.

---

## 🤖 Bot Commands (Private Chat)

| Command                  | Description                                      |
| ------------------------ | ------------------------------------------------ |
| `/addbot "Bot Name" URL` | Add a new bot (use quotes for names with spaces) |
| `/removebot "Bot Name"`  | Remove a bot from monitoring                     |
| `/list`                  | View all added bots                              |
| `/status`                | Check current bot statuses                       |

---

## 🌐 Web Features

* 📊 User Dashboard: `/dashboard/{user_id}`
* 🔐 Admin Stats Panel: `/stats`
* 📡 Live bot status monitoring
* 🟢 Online / 🔴 Offline indicators

---

## ⚙️ Deployment Guide

### 1. MongoDB Setup

* Create a MongoDB Atlas cluster
* Get your connection URI

---

### 2. Telegram API Setup

Get your credentials from: https://my.telegram.org

* `API_ID`
* `API_HASH`
* `BOT_TOKEN`

---

### 3. Deploy to Koyeb / Render

* Use the provided `Dockerfile`
* Set deployment type: **Web Service**

---

### 4. Environment Variables

Set the following variables in your deployment platform:

```env
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
MONGO_URI=your_mongodb_uri
TIME_ZONE=Asia/Kolkata
WEB_ACCESS_KEY=your_secret_key
```

---

## 📁 Project Structure

```
/app (Root)
├── bot.py                # Bot initialization & monitoring loop
├── main.py               # FastAPI entry point
├── database.py           # MongoDB helpers
├── config.py             # Environment configs
├── Dockerfile            # Container setup
├── Procfile              # Deployment command
├── requirements.txt      # Dependencies
├── README.md             # Documentation
│
├── plugins/              # Bot + Web logic
│   ├── __init__.py
│   ├── commands.py       # Telegram commands
│   ├── routes.py         # FastAPI routes
│   ├── ex_mongo_manager.py
│   └── imongo_manager.py
│
└── templates/            # HTML templates
    ├── homepage.html
    ├── startup.html
    ├── stats_login.html
    ├── stats_view.html
    ├── dashboard.html
    ├── index.html
    └── denied.html
```

---

## 🔐 Security

* Admin routes are protected using `WEB_ACCESS_KEY`
* Unauthorized access returns a custom **Access Denied** page

---

## 🧠 How It Works

1. Bots are added via Telegram commands
2. URLs are stored in MongoDB
3. Background task pings each bot periodically
4. Status message in Telegram is updated
5. Dashboard reflects real-time bot status

---

## 🚀 Future Improvements

* 🔄 Live auto-refresh dashboard (AJAX)
* 🔐 Full login system (sessions/cookies)
* 📈 Analytics & uptime tracking
* 🎨 Modern UI (cards, charts, graphs)

---

## 🤝 Contributing

Pull requests are welcome!
Feel free to open issues or suggest features.

---

## 📜 License

This project is open-source and free to use.

---
