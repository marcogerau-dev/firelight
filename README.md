# Traffic Light API — DevRev SE Challenge Part 3

## Stack
- **Backend**: Python + FastAPI (auto Swagger at `/docs`)
- **Real-time**: Server-Sent Events (SSE)
- **Auth**: Bearer token
- **Frontend**: Single-file HTML served by FastAPI

## Local dev

```bash
pip install -r requirements.txt
uvicorn main:app --reload
# Open http://localhost:8000
```

## Deploy on Railway (recommended)

1. Push to GitHub
2. Go to railway.app → New Project → Deploy from GitHub
3. Railway auto-detects the Procfile
4. Set env var `PORT` (Railway does this automatically)
5. Done — your app is live in ~2 min

## Deploy on Render

1. New Web Service → connect repo
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

## API key

Default: `demo-api-key-devrev-2026`  
In production: load from environment variable, never hardcode.

## Endpoints

| Method | Path     | Auth | Description                 |
|--------|----------|------|-----------------------------|
| GET    | /status  | ✓    | Current light color         |
| GET    | /colors  | ✓    | List valid colors           |
| POST   | /set     | ✓    | Set color `{"color":"red"}` |
| GET    | /events  | ✗    | SSE stream (real-time)      |
| GET    | /docs    | ✗    | Swagger UI                  |

## DevRev Agent Studio — skill config

Each skill uses an HTTP node:
- **Headers**: `Authorization: Bearer demo-api-key-devrev-2026`
- **Change light**: POST `/set` with body `{"color": "{{input.color}}"}`
- **Get status**: GET `/status`
- **List colors**: GET `/colors`
