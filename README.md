# Email Assistant

A natural language interface for searching and understanding your emails. Ask questions about your inbox, and get answers backed by your actual email data.

## What it does

- Syncs your email via Nylas OAuth
- Lets you ask questions in plain English about your emails
- Uses semantic search (not just keyword matching) to find relevant messages
- Generates answers with citations so you can verify the sources
- Streams responses in real-time

Built with FastAPI, Next.js, ChromaDB, and OpenAI.

## Tech Stack

**Backend:**

- FastAPI + async Python
- OpenAI GPT-4o-mini for answers
- text-embedding-3-small for semantic search
- LangGraph for the RAG pipeline
- ChromaDB for vector storage
- Pydantic AI for structured agents
- SQLite for metadata
- Nylas v3 API for email sync

**Frontend:**

- Next.js 14 with App Router
- TypeScript
- shadcn/ui components
- Tailwind CSS
- Server-Sent Events for streaming

## Prerequisites

- Python 3.10 or newer
- Node.js 18 or newer
- OpenAI API key
- Nylas developer account

## Setup

### Install dependencies

```bash
# Backend
pip install -r backend/requirements.txt

# Frontend
cd frontend && npm install
```

### Configure environment

Copy `.env.example` to `.env` and fill in:

```bash
OPENAI_API_KEY=sk-...
NYLAS_CLIENT_ID=your_client_id
NYLAS_CLIENT_SECRET=your_client_secret
NYLAS_API_URI=https://api.us.nylas.com
FRONTEND_BASE_URL=http://localhost:3000
BACKEND_BASE_URL=http://localhost:8000
```

### Nylas OAuth setup

1. Sign up at [nylas.com](https://nylas.com)
2. Create a new app in the dashboard
3. Add callback URL: `http://localhost:8000/nylas/callback`
4. Enable `email.read-only` scope
5. Copy client ID and secret to your `.env`

### Initialize storage

```bash
python scripts/one_time_setup.py
```

## Running

### Backend

From the project root (important!):

```bash
./start_backend.sh
```

Or manually:
```bash
source backend/venv/bin/activate
uvicorn backend.api.main:app --reload --port 8000
```

API docs: <http://localhost:8000/docs>

### Frontend

```bash
cd frontend && npm run dev
```

App: <http://localhost:3000>

## Usage

1. Go to `/connect` and authorize your email account
2. Visit `/sync` and click "Sync Latest 200 Emails"
3. Head to `/chat` and start asking questions
4. Check `/eval` to run quality metrics

## Project Structure

```text
backend/
├── api/              # FastAPI routes
├── agents/           # Pydantic AI agents for chat and routing
├── orchestrator/     # LangGraph workflow for RAG
├── services/         # Email sync, embeddings, vector search
├── templates/        # Jinja2 prompt templates
└── utils/            # Helpers

frontend/
├── app/              # Next.js pages
├── components/       # UI components
└── lib/              # Client utilities
```

## How the RAG workflow works

```text
User question
    ↓
Classify intent (simple greeting vs email query)
    ↓
Retrieve relevant emails from vector DB
    ↓
Rerank results (if many)
    ↓
Generate answer with citations
    ↓
Stream response to user
```

The intent classifier routes simple questions (like "hello") directly to output, and only runs retrieval for actual email queries.

## API Endpoints

- `GET /auth/nylas/url` - Get OAuth authorization URL
- `GET /nylas/callback` - Handle OAuth callback
- `POST /sync/latest` - Sync recent emails
- `POST /chat` - Ask a question (synchronous)
- `POST /chat/stream` - Ask a question (streaming)
- `POST /eval/run` - Run evaluation suite

## Troubleshooting

**OAuth fails:** Check that your callback URL in Nylas dashboard matches exactly

**No search results:** Make sure you've synced emails first

**Import errors when running backend:** You need to run from the project root, not from inside the backend folder

**ChromaDB telemetry warnings:** Fixed in chromadb 0.5.23+

## Storage

- `./storage/app.db` - SQLite database for email metadata
- `./storage/chroma/` - ChromaDB vector embeddings

## License

MIT
