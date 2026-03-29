# Python version set karein
FROM python:3.10-slim-buster

# Working directory
WORKDIR /app

# System dependencies (Pyrogram ke liye zaroori)
RUN apt-get update && apt-get install -y git

# Files copy karein
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Koyeb ka Port expose karein
EXPOSE 8080

# Start command (Web server + Bot)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]