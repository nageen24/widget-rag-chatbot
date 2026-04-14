"""
RAG query pipeline using BM25 (pure Python, no ML dependencies):
  1. Load chunks from JSON
  2. BM25 search to find relevant chunks
  3. Send context + question to Groq
  4. Return answer
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rank_bm25 import BM25Okapi
from backend.config import (
    CHUNKS_FILE, SYSTEM_PROMPT, TOP_K, LLM_PROVIDER,
    GROQ_API_KEY, GROQ_MODEL,
    OLLAMA_MODEL,
    CLAUDE_API_KEY, CLAUDE_MODEL
)

# Singletons
_chunks = None
_bm25 = None


def load_index():
    global _chunks, _bm25
    if _chunks is None:
        if not os.path.exists(CHUNKS_FILE):
            raise FileNotFoundError(
                f"Knowledge base not found at {CHUNKS_FILE}. Run ingest first."
            )
        with open(CHUNKS_FILE, encoding="utf-8") as f:
            _chunks = json.load(f)
        tokenized = [c.lower().split() for c in _chunks]
        _bm25 = BM25Okapi(tokenized)
    return _chunks, _bm25


def retrieve_context(question: str) -> list[str]:
    chunks, bm25 = load_index()
    tokens = question.lower().split()
    scores = bm25.get_scores(tokens)
    # Get top-K indices sorted by score
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:TOP_K]
    return [chunks[i] for i in top_indices if scores[i] > 0]


def build_prompt(context_chunks: list[str], question: str) -> str:
    context = "\n\n---\n\n".join(context_chunks)
    return f"""Context information from Hewmann Experience:

{context}

---

Question: {question}

Answer based only on the context above:"""




GREETINGS = {
    "hi", "hello", "hey", "hiya", "howdy", "greetings",
    "good morning", "good afternoon", "good evening", "good day",
    "sup", "what's up", "hi there", "hello there", "hey there",
    "hi sarah", "hello sarah", "hey sarah", "salaam", "salam", "assalam"
}

AFFIRMATIVES = {"yes", "yeah", "yep", "yup", "sure", "please", "ok", "okay", "go ahead", "tell me", "tell me more", "yes please", "of course", "absolutely"}

EMOTIONAL_PHRASES = [
    "frustrated", "frustrating", "so frustrated", "i'm frustrated",
    "annoyed", "exhausted", "overwhelmed", "burned out", "burnt out",
    "i give up", "don't know what to do", "don't know where to turn",
    "nobody helps", "no one helps", "no one listens", "nobody listens",
    "tired of", "fed up", "struggling", "i can't", "can't cope",
    "lost", "hopeless", "helpless", "scared", "worried", "anxious",
    "not fair", "so hard", "this is hard", "it's hard", "so difficult",
    "falling apart", "breaking down", "at my wit", "stressed",
    "upset", "angry", "furious", "heartbroken", "devastated",
    "my child", "my son", "my daughter", "my kid",  # emotional context
]

def is_greeting(text: str) -> bool:
    clean = text.strip().lower().strip("!.,? ")
    if clean in GREETINGS:
        return True
    first_word = clean.split()[0] if clean.split() else ""
    return first_word in {"hi", "hello", "hey", "howdy"} and len(clean.split()) <= 4 and "?" not in text

def is_affirmative(text: str) -> bool:
    clean = text.strip().lower().strip("!.,? ")
    return clean in AFFIRMATIVES

def is_emotional(text: str) -> bool:
    low = text.lower()
    return any(phrase in low for phrase in EMOTIONAL_PHRASES)


def call_llm(messages: list) -> str:
    if LLM_PROVIDER == "groq":
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            max_tokens=512,
            temperature=0.2
        )
        return response.choices[0].message.content
    elif LLM_PROVIDER == "ollama":
        import ollama
        response = ollama.chat(model=OLLAMA_MODEL, messages=messages)
        return response["message"]["content"]
    elif LLM_PROVIDER == "claude":
        import anthropic
        client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
        msg = client.messages.create(
            model=CLAUDE_MODEL, max_tokens=512,
            system=messages[0]["content"],
            messages=messages[1:]
        )
        return msg.content[0].text
    return "LLM provider not configured."


def answer(question: str, history: list = None) -> dict:
    if not question.strip():
        return {"answer": "Please ask a question.", "sources": []}

    history = history or []

    # If user said "yes" to a follow-up, extract topic from last bot message
    effective_question = question
    if is_affirmative(question) and history:
        # Find last assistant message to use as context for what "yes" refers to
        last_bot = next((m["content"] for m in reversed(history) if m["role"] == "assistant"), None)
        if last_bot:
            effective_question = f"{last_bot}\nThe user said yes to the above. Answer the follow-up question you asked."

    # Build message history for LLM (last 6 turns max)
    conversation = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in history[-6:]:
        conversation.append({"role": m["role"], "content": m["content"]})

    # Handle greetings
    if is_greeting(question):
        conversation.append({"role": "user", "content": question})
        response = call_llm(conversation)
        return {"answer": response, "sources": [], "is_greeting": True}

    # Handle emotional / venting messages — respond with empathy, no RAG needed
    if is_emotional(question):
        emotional_prompt = (
            f"{question}\n\n"
            "The user is expressing frustration, stress, or an emotional struggle. "
            "Do NOT redirect them to contact the team. "
            "Respond with genuine warmth and empathy — acknowledge their feelings first, "
            "then gently connect it to how Hewmann Experience can support them. "
            "Keep to 2 sentences: sentence 1 validates their emotion, "
            "sentence 2 offers a soft, helpful next step or reassurance."
        )
        conversation.append({"role": "user", "content": emotional_prompt})
        response = call_llm(conversation)
        return {"answer": response, "sources": [], "is_emotional": True}

    try:
        chunks = retrieve_context(effective_question)
    except FileNotFoundError as e:
        return {"answer": str(e), "sources": []}

    if not chunks:
        conversation.append({"role": "user", "content": effective_question})
        response = call_llm(conversation)
        return {"answer": response, "sources": []}

    prompt = build_prompt(chunks, effective_question)
    conversation.append({"role": "user", "content": prompt})
    response = call_llm(conversation)
    return {"answer": response, "sources": chunks}
