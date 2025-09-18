# PriceCompare (MVP)


### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env # edit MSSQL_DSN & SMTP
uvicorn app.main:app --reload --port 8000