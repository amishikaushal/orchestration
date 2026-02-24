import time
import json
import asyncio
from typing import List, Dict, Tuple
import logging
import httpx
from backend.schemas import OrchestrateRequest

logging.basicConfig(level=logging.INFO)


# OLLAMA CONFIG


OLLAMA_BASE_URL = "http://localhost:11434/v1/chat/completions"
OLLAMA_API_KEY = "ollama"

QUESTION_MODEL = "llama3.2"

COMPETITOR_MODELS = [
    "mistral:latest",
    "gemma3:1b",
    "llama3.2"
]

JUDGE_MODEL = "llama3.2"



# HTTP HELPER


async def ollama_chat(
    client: httpx.AsyncClient,
    model: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.0,
    response_format: str = None
) -> str:

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 500
    }

    if response_format == "json":
        payload["format"] = "json"

    response = await client.post(
        OLLAMA_BASE_URL,
        json=payload,
        timeout=None
    )

    response.raise_for_status()

    data = response.json()
    return data["choices"][0]["message"]["content"].strip()



# CONTEXT BUILDER


def build_context_block(conversation: List[Dict]) -> str:
    if not conversation:
        return ""

    context_text = "Previous Conversation Context:\n\n"

    for idx, turn in enumerate(conversation):
        context_text += f"Turn {idx + 1}:\n"
        context_text += f"Question: {turn.get('question')}\n"

        answers = turn.get("answers", [])
        for i, ans in enumerate(answers):
            context_text += f"Competitor {i+1}: {ans}\n"

        ranking = turn.get("ranking")
        if ranking:
            context_text += f"Ranking: {ranking}\n"

        context_text += "\n"

    return context_text



# QUESTION GENERATION


def build_initial_messages() -> List[Dict[str, str]]:
    request = (
        "Please come up with a challenging, nuanced question that I can ask "
        "a number of LLMs to evaluate their intelligence. "
        "Answer only with the question, no explanation."
    )
    return [{"role": "user", "content": request}]


async def generate_question(client: httpx.AsyncClient) -> Tuple[str, float]:
    start = time.time()

    question = await ollama_chat(
        client,
        QUESTION_MODEL,
        build_initial_messages()
    )

    return question, time.time() - start



# COMPETITOR GENERATION (CONTEXT-AWARE)


async def generate_competitor_answers(
    client: httpx.AsyncClient,
    question: str,
    conversation: List[Dict]
) -> Tuple[List[str], List[str], float]:

    start = time.time()

    context_block = build_context_block(conversation)

    full_prompt = f"""
{context_block}

Current Question:
{question}

Provide your best possible answer considering the previous context if relevant.
""".strip()

    messages = [{"role": "user", "content": full_prompt}]

    tasks = [
        ollama_chat(client, model, messages)
        for model in COMPETITOR_MODELS
    ]

    answers = await asyncio.gather(*tasks)

    return (
        COMPETITOR_MODELS,
        answers,
        time.time() - start
    )



# JUDGE PROMPT (CONTEXT-AWARE)


def build_judge_prompt(
    question: str,
    answers: List[str],
    conversation: List[Dict]
) -> str:

    context_block = build_context_block(conversation)

    combined = ""
    for i, answer in enumerate(answers):
        combined += f"Competitor {i+1}:\n{answer}\n\n"

    return f"""
You must rank the competitors from best to worst.

{context_block}

Current Question:
{question}

Responses:
{combined}

Return ONLY valid JSON in this exact structure:

{{
  "results": [list_of_competitor_numbers_in_best_to_worst_order]
}}

Rules:
- No explanations
- No markdown
- No commentary
- No extra text
- Strict JSON only
""".strip()


async def judge_answers(
    client: httpx.AsyncClient,
    question: str,
    competitors: List[str],
    answers: List[str],
    conversation: List[Dict]
) -> Tuple[List[int], float]:

    start = time.time()

    messages = [
        {
            "role": "system",
            "content": "You are a strict ranking engine. Output JSON only."
        },
        {
            "role": "user",
            "content": build_judge_prompt(question, answers, conversation)
        }
    ]

    raw_output = await ollama_chat(
        client,
        JUDGE_MODEL,
        messages,
        temperature=0.0,
        response_format="json"
    )

    logging.info("----- JUDGE RAW OUTPUT START -----")
    logging.info(raw_output)
    logging.info("----- JUDGE RAW OUTPUT END -----")

    ranking = []

    try:
        raw = raw_output.strip()

        if "{" in raw and "}" in raw:
            raw = raw[raw.find("{"): raw.rfind("}") + 1]

        parsed = json.loads(raw)
        ranking = parsed.get("results", [])

        if not isinstance(ranking, list):
            ranking = []

    except Exception as e:
        logging.error(f"Judge parsing failed: {str(e)}")
        ranking = []

    return ranking, time.time() - start

# FULL ORCHESTRATION (CONTEXT ENABLED)


async def run_orchestration(request: OrchestrateRequest) -> Dict:
    total_start = time.time()

    MAX_TURNS = 5
    conversation = request.conversation[-MAX_TURNS:] if request.conversation else []

    async with httpx.AsyncClient() as client:

        # Question generation
        question, q_latency = await generate_question(client)

        # Competitors
        competitors, answers, c_latency = await generate_competitor_answers(
            client,
            question,
            conversation
        )

        # Judge
        ranking, j_latency = await judge_answers(
            client,
            question,
            competitors,
            answers,
            conversation
        )

    total_time = round(time.time() - total_start, 3)

    # Append new turn
    updated_conversation = conversation + [{
        "question": question,
        "answers": answers,
        "ranking": ranking
    }]

    response_payload = {
        "question": question,
        "competitors": competitors,
        "answers": answers,
        "ranking": ranking,
        "latency": {
            "question_generation_sec": round(q_latency, 3),
            "competitor_generation_sec": round(c_latency, 3),
            "judge_sec": round(j_latency, 3),
            "total_sec": total_time,
        },
        "conversation": updated_conversation
    }

    return response_payload
