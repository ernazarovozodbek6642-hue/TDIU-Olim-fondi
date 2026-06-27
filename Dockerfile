FROM python:3.11.15-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir \
    aiogram==2.25.2 \
    aiohttp==3.8.6 \
    asyncpg==0.30.0 \
    environs \
    python-dotenv \
    pytz \
    python-docx \
    apscheduler==3.10.4 \
    gspread==6.1.4 \
    google-auth==2.38.0 \
    google-auth-oauthlib==1.2.1

CMD ["python", "app.py"]
