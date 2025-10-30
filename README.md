# Email Assistant: Nylas + RAG + Next.js

An intelligent email assistant powered by RAG (Retrieval-Augmented Generation) that helps you query and understand your emails using natural language.

## Features

- **Email Sync**: Connect your email via Nylas OAuth and sync messages
- **RAG-Powered Search**: Ask questions about your emails in natural language
- **Vector Search**: ChromaDB-powered semantic search with optional HyDE
- **Streaming Responses**: Real-time answer generation with Server-Sent Events
- **Citations**: All answers include source email references
- **Evaluation**: Built-in evaluation framework for RAG quality metrics
- **Modern UI**: Next.js 14 with shadcn/ui components

## Tech Stack

### Backend
- **Framework**: FastAPI with async/await support
- **LLM**: OpenAI GPT-4o-mini for generation
- **Embeddings**: OpenAI text-embedding-3-small
- **Orchestration**: LangGraph for agentic RAG workflow
- **Vector DB**: ChromaDB (persistent storage)
- **Database**: SQLite with SQLAlchemy ORM
- **Email**: Nylas v3 API with Hosted OAuth
- **AI Framework**: Pydantic AI for structured agent interactions

### Frontend
- **Framework**: Next.js 14 (App Router)
- **UI**: shadcn/ui + Tailwind CSS
- **Language**: TypeScript
- **Streaming**: EventSource (SSE)

## Prerequisites

- Python 3.10+
- Node.js 18+
- OpenAI API key
- Nylas account with OAuth app configured

## Setup

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r backend/requirements.txt

# Install frontend dependencies
cd frontend && npm install
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your credentials
```

Required environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `NYLAS_CLIENT_ID` | Nylas OAuth client ID | From Nylas dashboard |
| `NYLAS_CLIENT_SECRET` | Nylas OAuth client secret | From Nylas dashboard |
| `NYLAS_API_URI` | Nylas API endpoint | `https://api.us.nylas.com` |
| `FRONTEND_BASE_URL` | Frontend URL | `http://localhost:3000` |
| `BACKEND_BASE_URL` | Backend URL | `http://localhost:8000` |

### 3. Nylas OAuth Setup

1. Create a Nylas account at [https://nylas.com](https://nylas.com)
2. Create a new application in the Nylas dashboard
3. Configure OAuth:
   - Add callback URL: `http://localhost:8000/nylas/callback`
   - Enable email scopes: `email.read-only`
4. Copy Client ID and Client Secret to `.env`

### 4. Initialize Storage & Database

```bash
python scripts/one_time_setup.py
```

## Running the Application

### Start Backend

```bash
uvicorn backend.api.main:app --reload --port 8000
```

API docs: `http://localhost:8000/docs`

### Start Frontend

```bash
cd frontend && npm run dev
```

UI: `http://localhost:3000`

## Usage Flow

1. **Connect**: Navigate to `/connect` and authorize your email
2. **Sync**: Go to `/sync` and click "Sync Latest 200 Emails"
3. **Chat**: Ask questions on `/chat` page
4. **Eval**: Run evaluation on `/eval` page

## Architecture

```
backend/
├── api/                    # FastAPI routers
│   ├── main.py
│   └── routers/           # auth, sync, chat, eval
├── agents/                # Pydantic AI agents
│   ├── chat_agent.py
│   └── models/
├── orchestrator/         # LangGraph workflows
│   ├── chat_workflow.py  # RAG pipeline
│   └── models/
├── utils/                # Helpers
├── templates/            # Jinja2 prompts
├── config.py
├── models.py             # SQLAlchemy models
├── nylas_client.py       # Nylas v3 client
├── ingest.py             # Chunking & embedding
├── vectorstore.py        # ChromaDB wrapper
└── eval.py
```

### RAG Workflow

```
classify_intent → maybe_hyde → retrieve → rerank → generate → finalize
```

## API Endpoints

- `GET /auth/nylas/url` - Get OAuth URL
- `GET /nylas/callback` - OAuth callback
- `POST /sync/latest` - Sync emails
- `POST /chat` - Synchronous chat
- `GET /chat/stream` - Streaming chat (SSE)
- `POST /eval/run` - Run evaluation

## Troubleshooting

**Nylas OAuth Fails**: Verify callback URL and credentials in `.env`

**No Search Results**: Run `python scripts/run_sync.py` to sync emails

**Import Errors**: Ensure running from project root

## Storage

- SQLite: `./storage/app.db`
- ChromaDB: `./storage/chroma/`

## License

MIT
