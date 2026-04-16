# Widget RAG Chatbot

An intelligent RAG (Retrieval-Augmented Generation) chatbot for [Hewmann Experience](https://hewmannexperience.com/), embedded as a website widget.

## Overview

This chatbot answers user questions strictly based on Hewmann Experience company information using RAG — no hallucinated or out-of-scope responses. Built for accuracy, speed, and easy website integration.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python (FastAPI) |
| LLM | Claude (Anthropic) |
| Vector Store | Pinecone |
| Embeddings | OpenAI / Cohere |
| Frontend | HTML/CSS/JS Widget |
| Deployment | Vercel |

## Features

- RAG-powered Q&A from company documents and website content
- Out-of-scope query handling with professional fallback messages
- PDF document ingestion
- Embeddable widget for any website
- Low-latency responses

## Project Structure

```
widget-rag-chatbot/
├── backend/
│   ├── main.py          # FastAPI app entry point
│   ├── rag.py           # RAG pipeline logic
│   ├── config.py        # Configuration & environment variables
│   └── ingest.py        # Document ingestion
├── frontend/
│   └── widget/          # Embeddable chat widget
├── docs/                # Company documents for ingestion
└── vercel.json          # Vercel deployment config
```

## Setup

### Prerequisites

- Python 3.10+
- API keys: Anthropic, Pinecone, OpenAI (or Cohere)

### Installation

```bash
git clone https://github.com/nageen24/widget-rag-chatbot.git
cd widget-rag-chatbot
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file:

```env
ANTHROPIC_API_KEY=your_key
PINECONE_API_KEY=your_key
PINECONE_INDEX=your_index
OPENAI_API_KEY=your_key
```

### Run Locally

```bash
uvicorn backend.main:app --reload
```

## Deployment

Deployed on Vercel. Push to `master` triggers auto-deploy.

## License

Private — Hewmann Experience. All rights reserved.
