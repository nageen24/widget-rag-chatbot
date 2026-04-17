# ABC Tech RAG Chatbot — Alexa

An intelligent RAG (Retrieval-Augmented Generation) chatbot for **ABC Tech**, deployed as an embeddable website widget. Powered by Groq (Llama 3.1) and BM25 retrieval — answers strictly from company documents, no hallucinations.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python · FastAPI |
| LLM | Groq API (llama-3.1-8b-instant) |
| Retrieval | BM25 (rank-bm25) |
| Document Parsing | python-docx · pypdf |
| Frontend | HTML · Tailwind CSS · Vanilla JS |
| Deployment | Vercel |

## Features

- RAG-powered Q&A strictly from company `.docx` / `.pdf` documents
- Virtual assistant named **Alexa** with brand voice enforcement
- Intent detection: specific, conversational, emotional — each handled differently
- Out-of-scope fallback with professional redirect message
- Embeddable chat widget (floating button, chat window)
- Chat history context (last 10 messages)
- Typing indicator, suggested questions, unread badge

## Project Structure

```
rag-chatbot/
├── backend/
│   ├── main.py        # FastAPI app — /chat, /ingest, /health endpoints
│   ├── rag.py         # RAG pipeline — BM25 retrieval + Groq LLM
│   ├── ingest.py      # Document ingestion → chunks.json
│   └── config.py      # Prompts, paths, model settings
├── frontend/
│   └── index.html     # Embeddable chat widget
├── data/              # Drop .docx / .pdf knowledge base files here
├── start.bat          # One-click local server start
└── vercel.json        # Vercel deployment config
```

## Setup

### Prerequisites

- Python 3.10+
- [Groq API key](https://console.groq.com) (free tier available)

### Installation

```bash
git clone https://github.com/nageen24/widget-rag-chatbot.git
cd widget-rag-chatbot
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

### Add Knowledge Base Documents

Drop your `.docx` or `.pdf` files into the `data/` folder, then run ingest:

```bash
py -m backend.ingest --force
```

### Run Locally

```bash
uvicorn backend.main:app --reload
```

Visit `http://localhost:8000` to see the chat widget.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat` | Send a question, get an answer |
| GET | `/health` | Health check |
| POST | `/ingest?force=true` | Rebuild knowledge base from docs |

### Chat Request

```json
{
  "question": "What services do you offer?",
  "history": [
    { "role": "user", "content": "Hi" },
    { "role": "assistant", "content": "Hello! What can I help you with?" }
  ]
}
```

## Deployment

Deployed on Vercel. `api/index.py` is the serverless entry point. Push to `master` triggers auto-deploy.

## License

Private — ABC Tech. All rights reserved.
