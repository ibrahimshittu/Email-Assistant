# Email Assistant: Nylas + RAG + Next.js (shadcn/ui)

## Prereqs

- Python 3.10+
- Node.js 18+

## Setup

1. Copy `.env.example` to `.env` and fill values.
2. Install Python deps:
   ```bash
   pip install -r requirements.txt
   python scripts/one_time_setup.py
   ```
3. Install web deps:
   ```bash
   cd web && npm install
   ```

## Run

- Backend:
  ```bash
  uvicorn server.main:app --reload --port 8000
  ```
- Frontend:
  ```bash
  cd web && npm run dev
  ```

## Flow

- Connect on `/connect` → redirects to Nylas
- Sync on `/sync` → fetches last 200 emails and indexes
- Chat on `/chat` → streaming answers with citations
- Eval on `/eval` → placeholder (expand with `server/eval.py`)

## Notes

- SQLite at `./storage/app.db`, Chroma at `./storage/chroma`
- Models: OpenAI `gpt-4o-mini` and `text-embedding-3-small`
