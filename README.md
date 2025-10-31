# Email Assistant

Ask questions about your inbox in plain English and get answers backed by your actual email data with citations.

## Features

- **Smart Email Search**: Uses semantic search to find relevant messages
- **Email Sync**: Securely sync your emails via Nylas OAuth integration
- **Answer Citations**: Every answer includes source citations so you can verify the information

## Tech Stack

### Backend

- **FastAPI** - Modern async Python web framework
- **OpenAI GPT-4.1** - Answer generation (configurable model)
- **OpenAI GPT-4.1-mini** - Intent routing and classification
- **OpenAI text-embedding-3-small** - Semantic search embeddings
- **LangGraph** - RAG pipeline orchestration
- **Pydantic AI** - Structured AI agents
- **ChromaDB** - Vector storage for email embeddings
- **DeepEval** - Comprehensive RAG evaluation metrics
- **SQLite** - Email metadata storage
- **Nylas v3 API** - Email provider integration

### Frontend

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe JavaScript
- **shadcn/ui** - Beautiful UI components
- **Tailwind CSS** - Utility-first styling
- **Server-Sent Events** - Real-time streaming

## Prerequisites

- **Python 3.10+** (3.13 recommended)
- **Node.js 18+** (20+ recommended)
- **OpenAI API key** - [Get one here](https://platform.openai.com/api-keys)
- **Nylas developer account** - [Sign up here](https://nylas.com)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd email_assistant
```

### 2. Backend Setup

#### Create a Virtual Environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Install Dependencies

```bash
pip install -r requirements.txt
```

#### Configure Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
cp .env.example .env
```

Edit `backend/.env` and fill in the required values:

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here

# Nylas Configuration
NYLAS_CLIENT_ID=your-nylas-client-id
NYLAS_CLIENT_SECRET=your-nylas-client-secret
NYLAS_API_URI=https://api.us.nylas.com

# Application URLs
FRONTEND_BASE_URL=http://localhost:3000
BACKEND_BASE_URL=http://localhost:8000

# Storage Configuration
CHROMA_DIR=./storage/chroma
SQLITE_PATH=./storage/app.db

# Model Configuration
INTENT_ROUTER_MODEL=gpt-4.1-mini-2025-04-14
ANSWER_MODEL=gpt-4.1-2025-04-14
EVAL_MODEL=gpt-4.1
EMBEDDING_MODEL=text-embedding-3-small
TOP_K=6

# Optional: Logging
LOG_LEVEL=INFO
```

### 3. Frontend Setup

#### Install Dependencies

```bash
cd frontend
npm install
```

#### Configure Environment Variables

Create a `.env.local` file in the `frontend/` directory:

```bash
echo "NEXT_PUBLIC_BACKEND_BASE_URL=http://localhost:8000" > .env.local
```

## Nylas OAuth Setup

To connect your email account, you need to configure Nylas:

### 1. Create a Nylas Account

1. Go to [nylas.com](https://nylas.com) and sign up
2. Verify your email and complete the onboarding

### 2. Create a New Application

1. From the Nylas dashboard, create a new application
2. Choose **API v3** (not legacy v2)
3. Give it a name (e.g., "Email Assistant")

### 3. Configure OAuth Settings

1. In your Nylas app settings, go to **"App Settings"** → **"Callback URIs"**
2. Add the callback URL: `http://localhost:8000/nylas/callback`
3. Under **"Scopes"**, enable: `email.read_only`
4. Save your changes

### 4. Get Your Credentials

1. Copy your **Client ID** and **Client Secret**
2. Add them to your `backend/.env` file:
   ```env
   NYLAS_CLIENT_ID=your-client-id-here
   NYLAS_CLIENT_SECRET=your-client-secret-here
   ```

## Running the Application

### Start the Backend

From the project root directory:

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn api.main:app --reload --port 8000
```

The API will be available at:

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Start the Frontend

In a new terminal:

```bash
cd frontend
npm run dev
```

The web app will be available at: http://localhost:3000

## Usage Guide

### 1. Connect Your Email Account

1. Navigate to http://localhost:3000/connect
2. Click "Connect Email Account"
3. Authorize your email provider through Nylas
4. You'll be redirected back to the app once connected

### 2. Sync Your Emails

1. Go to http://localhost:3000/sync
2. Click "Sync Emails"
3. Wait for the sync to complete (you'll see a progress message)
4. Your emails are now indexed and searchable

### 3. Ask Questions

1. Navigate to http://localhost:3000/chat
2. Type questions in plain English, such as:
   - "What are my unread emails from yesterday?"
   - "Show me all emails from John about the project"
   - "When is my next meeting?"
   - "What did Sarah say about the budget?"
3. Get instant answers with citations from your actual emails

### 4. Run Quality Metrics (Optional)

1. Visit http://localhost:3000/eval
2. Choose evaluation mode:
   - **LLM Judge**: Fast binary metrics (faithfulness 0/1, relevance 0/1)
   - **DeepEval**: Comprehensive metrics with detailed scoring
3. Review detailed metrics including:
   - Answer Relevancy (0.0-1.0, higher is better)
   - Faithfulness (0.0-1.0, higher is better)
   - Contextual Relevancy (0.0-1.0, higher is better)
   - Contextual Recall (0.0-1.0, higher is better)
   - Hallucination Score (0.0-1.0, lower is better)
   - Response Time (ms)

## Project Structure

```
email_assistant/
├── backend/
│   ├── api/                    # FastAPI routes and endpoints
│   │   ├── main.py            # App initialization
│   │   └── routers/           # Route handlers
│   │       ├── auth.py        # OAuth authentication
│   │       ├── sync.py        # Email sync
│   │       ├── chat.py        # Q&A endpoints
│   │       ├── eval_llm_judge.py   # LLM-as-a-Judge evaluation
│   │       └── eval_deepeval.py    # DeepEval comprehensive evaluation
│   ├── agents/                # Pydantic AI agents
│   │   └── chat_agent.py      # Intent routing and answer generation
│   ├── orchestrator/          # LangGraph workflow
│   │   └── chat_workflow.py   # RAG pipeline orchestration
│   ├── services/              # Core business logic
│   │   ├── eval/              # Evaluation services
│   │   │   ├── llm_judge.py   # Binary metric evaluation
│   │   │   └── deepeval.py    # Comprehensive RAG metrics
│   │   ├── nylas_client.py    # Email provider integration
│   │   ├── ingest.py          # Email processing and embedding
│   │   └── vectorstore.py     # ChromaDB operations
│   ├── templates/             # Jinja2 prompt templates
│   ├── config.py              # Configuration management
│   ├── database/              # SQLAlchemy database models
│   └── requirements.txt       # Python dependencies
│
└── frontend/
    ├── app/                   # Next.js pages (App Router)
    │   ├── connect/           # OAuth connection flow
    │   ├── sync/              # Email sync interface
    │   ├── chat/              # Q&A interface
    │   └── eval/              # Evaluation dashboard
    ├── components/            # React UI components
    │   └── ui/                # shadcn/ui components
    └── lib/                   # Client utilities
```

## How It Works

The application uses a Retrieval-Augmented Generation (RAG) pipeline:

```
User Question
    ↓
Intent Classification (simple greeting vs email query)
    ↓
Generate Query Embedding
    ↓
Semantic Search in ChromaDB (retrieve top-k relevant emails)
    ↓
Generate Answer with GPT-4.1 + Context
    ↓
Stream Response to User (with citations)
```

**Key Features:**

- **Intent Routing**: Simple questions like "hello" skip retrieval and go straight to response
- **Semantic Search**: Uses embeddings to find conceptually similar emails, not just keyword matches
- **Context Window**: Includes conversation history for multi-turn conversations
- **Citations**: Every answer references specific emails so you can verify sources

## API Endpoints

### Authentication

- `GET /auth/nylas/url` - Get OAuth authorization URL
- `GET /nylas/callback` - Handle OAuth callback from Nylas

### Email Sync

- `POST /sync/latest` - Sync recent emails from connected account

### Chat

- `POST /chat` - Ask a question (returns complete response)
- `POST /chat/stream` - Ask a question (streams response in real-time)

### Evaluation

- `POST /eval/llm-judge` - Run LLM-as-a-Judge evaluation (binary metrics: faithfulness, relevance)
- `POST /eval/deepeval` - Run comprehensive DeepEval evaluation (5 metrics with scoring)

## Environment Variables Reference

### Backend (`backend/.env`)

| Variable              | Description                     | Example                    |
| --------------------- | ------------------------------- | -------------------------- |
| `OPENAI_API_KEY`      | Your OpenAI API key             | `sk-...`                   |
| `NYLAS_CLIENT_ID`     | Nylas OAuth client ID           | `abc123...`                |
| `NYLAS_CLIENT_SECRET` | Nylas OAuth client secret       | `xyz789...`                |
| `NYLAS_API_URI`       | Nylas API endpoint              | `https://api.us.nylas.com` |
| `FRONTEND_BASE_URL`   | Frontend URL for CORS           | `http://localhost:3000`    |
| `BACKEND_BASE_URL`    | Backend URL for callbacks       | `http://localhost:8000`    |
| `CHROMA_DIR`          | ChromaDB storage directory      | `./storage/chroma`         |
| `SQLITE_PATH`         | SQLite database path            | `./storage/app.db`         |
| `INTENT_ROUTER_MODEL` | Model for intent classification | `gpt-4.1-mini-2025-04-14`  |
| `ANSWER_MODEL`        | Model for answer generation     | `gpt-4.1-2025-04-14`       |
| `EVAL_MODEL`          | Model for evaluation metrics    | `gpt-4.1`                  |
| `EMBEDDING_MODEL`     | Model for embeddings            | `text-embedding-3-small`   |
| `TOP_K`               | Number of emails to retrieve    | `6`                        |

### Frontend (`frontend/.env.local`)

| Variable                       | Description     | Example                 |
| ------------------------------ | --------------- | ----------------------- |
| `NEXT_PUBLIC_BACKEND_BASE_URL` | Backend API URL | `http://localhost:8000` |

## Troubleshooting

### OAuth Authorization Fails

**Problem**: Getting errors during email connection

**Solutions**:

- Verify callback URL in Nylas dashboard matches exactly: `http://localhost:8000/nylas/callback`
- Ensure `email.read_only` scope is enabled
- Check that `NYLAS_CLIENT_ID` and `NYLAS_CLIENT_SECRET` in `.env` are correct
- Make sure you're using Nylas API v3 (not v2)

### No Search Results

**Problem**: Questions return empty results

**Solutions**:

- Make sure you've synced emails first (go to `/sync`)
- Check that sync completed successfully (look for success message)
- Verify `OPENAI_API_KEY` is valid and has credits
- Check backend logs for embedding errors

### Import Errors When Running Backend

**Problem**: `ModuleNotFoundError` or import errors

**Solutions**:

- Activate the virtual environment: `source backend/venv/bin/activate`
- Ensure you're in the correct directory (should be `backend/` when running uvicorn)
- Reinstall dependencies: `pip install -r requirements.txt`

### Frontend Can't Connect to Backend

**Problem**: Network errors or API calls failing

**Solutions**:

- Verify backend is running on port 8000
- Check `NEXT_PUBLIC_BACKEND_BASE_URL` in `frontend/.env.local`
- Ensure CORS is configured correctly in backend
- Check that `FRONTEND_BASE_URL` in backend `.env` matches your frontend URL

## Storage

The application stores data locally:

- **`./storage/app.db`** - SQLite database containing email metadata (sender, subject, date, etc.)
- **`./storage/chroma/`** - ChromaDB vector database containing email embeddings for semantic search

To reset your data, simply delete the `storage/` directory and re-sync your emails.

## Development

### Running in Development Mode

Both frontend and backend support hot-reloading:

**Backend**: Uses `--reload` flag with uvicorn

```bash
uvicorn api.main:app --reload --port 8000
```

**Frontend**: Uses Next.js dev server

```bash
npm run dev
```

## License

MIT
