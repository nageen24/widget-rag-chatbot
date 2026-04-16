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
    CHUNKS_FILE, SYSTEM_PROMPT, CONVERSATIONAL_PROMPT, EMOTIONAL_PROMPT, TOP_K, LLM_PROVIDER,
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


def enforce_word_limits(response: str, answer_limit: int = 25, question_limit: int = 15) -> str:
    """Trim sentence 1 to answer_limit words and sentence 2 to question_limit words."""
    import re
    # Split into max 2 sentences on . ? !
    parts = re.split(r'(?<=[.?!])\s+', response.strip(), maxsplit=1)
    if len(parts) < 2:
        # Only one sentence — trim to answer_limit
        words = parts[0].split()
        return " ".join(words[:answer_limit])

    s1_words = parts[0].split()
    s2_words = parts[1].split()

    s1 = " ".join(s1_words[:answer_limit])
    # Ensure s1 ends with punctuation
    if s1 and s1[-1] not in ".?!":
        s1 = s1.rstrip(",;") + "."

    s2 = " ".join(s2_words[:question_limit])
    if s2 and s2[-1] not in ".?!":
        s2 = s2.rstrip(",;") + "?"

    return f"{s1} {s2}"


def build_prompt(context_chunks: list[str], question: str) -> str:
    context = "\n\n---\n\n".join(context_chunks)
    return f"""Context information from Hewmann Experience:

{context}

---

Question: {question}

Answer based only on the context above:"""




AFFIRMATIVES = {"yes", "yeah", "yep", "yup", "sure", "please", "ok", "okay", "go ahead", "tell me", "tell me more", "yes please", "of course", "absolutely"}

FAREWELLS = {"bye", "goodbye", "good bye", "see you", "see ya", "take care", "later", "cya", "farewell", "ttyl", "that's all", "thats all", "thanks bye", "thank you bye", "thanks goodbye", "thank you goodbye", "i'm done", "im done", "all done", "have a good day", "have a nice day"}

def is_affirmative(text: str) -> bool:
    clean = text.strip().lower().strip("!.,? ")
    return clean in AFFIRMATIVES

def is_farewell(text: str) -> bool:
    clean = text.strip().lower().strip("!.,? ")
    return clean in FAREWELLS or any(clean.startswith(f) for f in ("bye", "goodbye", "good bye", "see you", "take care", "farewell"))


def classify_intent(text: str) -> str:
    """
    Classify message into one of 4 intents. Single LLM call, ~5 tokens back.
    Returns: 'greeting' | 'emotional' | 'conversational' | 'specific'
    """
    try:
        system = (
            "You are an intent classifier for a neurodivergent family support chatbot called Hewmann Experience. "
            "Classify the user message into exactly one category. Reply with ONLY that one word.\n\n"
            "Categories:\n"
            "- greeting: hello, hi, hey, salutations, opening pleasantries with no question; "
            "AND bot identity questions: 'who are you', 'what are you', 'are you a bot', 'are you human', "
            "'what is your name', 'introduce yourself', 'tell me about yourself', 'are you AI', 'who am i talking to'\n"
            "- emotional: genuine emotional distress — frustration, sadness, fear, overwhelm, exhaustion, venting. "
            "NOT casual expressions like 'what the hell', 'get out', 'omg', 'seriously?' — those are conversational.\n"
            "- specific: ANY question about the company, its services, programs, pricing, staff, IEP, ADHD, autism support, "
            "coaching, workshops, scheduling, or what the company does — including vague ones like "
            "'tell me about your company', 'what do you offer', 'are you associated with a company', "
            "'what is Hewmann Experience', 'do you know about this company'. When in doubt, use specific.\n"
            "- conversational: pure small talk with zero company relevance — 'how are you', 'good morning', "
            "'what is the universe', 'tell me a joke', 'what the hell', 'get out', casual exclamations\n\n"
            "Reply ONLY with one word: greeting, emotional, conversational, or specific"
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": text}
        ]
        if LLM_PROVIDER == "groq":
            from groq import Groq
            client = Groq(api_key=GROQ_API_KEY)
            r = client.chat.completions.create(
                model=GROQ_MODEL, messages=messages,
                max_tokens=5, temperature=0.0
            )
            result = r.choices[0].message.content.strip().lower()
        elif LLM_PROVIDER == "claude":
            import anthropic
            client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
            msg = client.messages.create(
                model=CLAUDE_MODEL, max_tokens=5,
                system=system, messages=messages[1:]
            )
            result = msg.content[0].text.strip().lower()
        else:
            return "specific"
        for label in ("greeting", "emotional", "conversational", "specific"):
            if label in result:
                return label
        return "specific"
    except Exception:
        return "specific"


def call_llm(messages: list, max_tokens: int = 512) -> str:
    if LLM_PROVIDER == "groq":
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            max_tokens=max_tokens,
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
            model=CLAUDE_MODEL, max_tokens=max_tokens,
            system=messages[0]["content"],
            messages=messages[1:]
        )
        return msg.content[0].text
    return "LLM provider not configured."


def answer(question: str, history: list = None) -> dict:
    if not question.strip():
        return {"answer": "Please ask a question.", "sources": []}

    history = history or []

    # Resolve affirmative ("yes") to the last bot follow-up question
    effective_question = question
    if is_affirmative(question) and history:
        last_bot = next((m["content"] for m in reversed(history) if m["role"] == "assistant"), None)
        if last_bot:
            effective_question = f"{last_bot}\nThe user confirmed yes. Answer the follow-up question you asked."

    # --- FAREWELL (local check — no LLM call needed) ---
    if is_farewell(question):
        conversation = [
            {"role": "system", "content": CONVERSATIONAL_PROMPT},
            {"role": "user", "content": question}
        ]
        response = call_llm(conversation, max_tokens=25)
        return {"answer": response, "sources": [], "intent": "farewell"}

    # Classify intent — single LLM call, one word back
    intent = classify_intent(question)

    # --- GREETING ---
    if intent == "greeting":
        conversation = [
            {"role": "system", "content": CONVERSATIONAL_PROMPT},
            {"role": "user", "content": question}
        ]
        response = call_llm(conversation, max_tokens=40)
        return {"answer": response, "sources": [], "intent": "greeting"}

    # --- EMOTIONAL ---
    if intent == "emotional":
        conversation = [
            {"role": "system", "content": EMOTIONAL_PROMPT},
        ]
        for m in history[-4:]:
            conversation.append({"role": m["role"], "content": m["content"]})
        conversation.append({"role": "user", "content": question})
        response = call_llm(conversation, max_tokens=60)
        return {"answer": response, "sources": [], "intent": "emotional"}

    # --- CONVERSATIONAL ---
    if intent == "conversational":
        conversation = [
            {"role": "system", "content": CONVERSATIONAL_PROMPT},
        ]
        for m in history[-4:]:
            conversation.append({"role": m["role"], "content": m["content"]})
        conversation.append({"role": "user", "content": question})
        response = call_llm(conversation, max_tokens=40)
        return {"answer": response, "sources": [], "intent": "conversational"}

    # --- SPECIFIC (RAG) ---
    try:
        chunks = retrieve_context(effective_question)
    except FileNotFoundError as e:
        return {"answer": str(e), "sources": []}

    conversation = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in history[-6:]:
        conversation.append({"role": m["role"], "content": m["content"]})

    if not chunks:
        # No doc match — use fallback within system prompt rules
        conversation.append({"role": "user", "content": effective_question})
        response = call_llm(conversation, max_tokens=80)
        return {"answer": enforce_word_limits(response), "sources": [], "intent": "specific"}

    prompt = build_prompt(chunks, effective_question)
    conversation.append({"role": "user", "content": prompt})
    response = call_llm(conversation, max_tokens=80)
    return {"answer": enforce_word_limits(response), "sources": chunks, "intent": "specific"}
