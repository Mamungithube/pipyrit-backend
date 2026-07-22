# pip install openai
# Required ENV: OPENAI_API_KEY

from os import environ
from openai import OpenAI
import json
import re

# ── Configuration ───────────────────────────────────────────────────────────
API_KEY = environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)

# Model preference list — prioritized gpt-4o-mini for maximum speed and cost efficiency
MODEL_PREFERENCE = ["gpt-4o-mini", "gpt-4o", "gpt-4", "gpt-3.5-turbo"]
DEFAULT_MODEL    = "gpt-4o-mini"   # Fallback model if discovery fails


_cached_working_model = None


# ── Model Selection ─────────────────────────────────────────────────────────
def get_working_model_name() -> str:
    """
    Finds and returns an active preferred model from the available account models.
    Caches the result in memory to eliminate unnecessary HTTP round-trips.
    """
    global _cached_working_model
    if _cached_working_model:
        return _cached_working_model

    try:
        available = {m.id for m in client.models.list().data}
        for preferred in MODEL_PREFERENCE:
            if preferred in available:
                _cached_working_model = preferred
                return _cached_working_model
        gpt_models = [m for m in available if m.startswith("gpt-")]
        _cached_working_model = sorted(gpt_models)[0] if gpt_models else DEFAULT_MODEL
        return _cached_working_model
    except Exception:
        return DEFAULT_MODEL


# ── Clean JSON ──────────────────────────────────────────────────────────────
def clean_ai_json(raw_text: str) -> dict:
    """
    Cleans raw AI response text to extract valid JSON data.
    Handles both markdown-wrapped JSON (```json ... ```) and direct JSON strings.
    """
    try:
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()
        return json.loads(raw_text)
    except json.JSONDecodeError:
        # Fallback: extract substring between the first '{' and last '}'
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError(f"AI returned invalid JSON. Raw snippet: {raw_text[:200]}")


# ── Internal Helpers ────────────────────────────────────────────────────────
def _chat(prompt: str, system_prompt: str = None) -> str:
    """
    Executes OpenAI chat completion request.
    Uses response_format={"type": "json_object"} to guarantee valid JSON response.
    Note: OpenAI requires the string "JSON" to be present in the prompt when using json_object mode.
    """
    model = get_working_model_name()
    if not system_prompt:
        system_prompt = (
            "You are an expert AI quiz generator. "
            "Your STRICT, NON-NEGOTIABLE directive is to ALWAYS return valid JSON containing EXACTLY 25 question objects in the 'question_set' array. "
            "Generating fewer or more than 25 questions is strictly forbidden."
        )

    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},   # JSON mode — most reliable
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": prompt},
        ],
        temperature=0.3,   # Lower temperature for direct token generation
        max_tokens=4096,   # Sufficient capacity for 25 questions
    )
    return response.choices[0].message.content


# ── Public Functions ────────────────────────────────────────────────────────
def generate_ai_quiz(case_type: str) -> dict:
    """Generates exactly 25 practice quiz questions for the given case type."""
    system_prompt = (
        "You are a specialized US Immigration legal quiz engine. "
        "STRICT MANDATE: You MUST output valid JSON with EXACTLY 25 questions in the 'question_set' array. "
        "Never output fewer than 25 items."
    )
    prompt = f"""
    Act as a senior US Immigration Attorney.
    Generate a practice quiz for: {case_type}.

    STRICT MANDATORY CONSTRAINTS:
    1. EXACT COUNT REQUIREMENT: You MUST generate EXACTLY 25 distinct questions in the "question_set" array (numbered 1 through 25). Generating 24, 23, or any number other than 25 is CRITICAL SYSTEM FAILURE. Verify the count before outputting.
    2. Randomize Option Positions: Ensure the correct answer index ("correct_answer_index") is randomly and evenly distributed across 0, 1, 2, and 3 (corresponding to A, B, C, D). Do NOT concentrate correct answers in index 0 (A) or 1 (B).
    3. Conciseness: Keep hints and explanations concise (maximum 1 short sentence each) to guarantee token efficiency.
    4. Objectivity & Validity: NEVER generate personal, candidate-specific, or subjective questions asking for private details. ALL questions MUST be strictly objective, factual, legal, procedural, or rule-based US immigration knowledge questions with ONE universally verifiable correct answer.

    Return ONLY a JSON object with this exact structure:
    {{
      "question_set": [
        {{
          "question": "Question 1 text",
          "options": ["Option A", "Option B", "Option C", "Option D"],
          "correct_answer_index": 0,
          "hint": "Short clue",
          "explanation": "Short explanation"
        }}
      ]
    }}
    Return ONLY JSON. No explanation outside the JSON.
    """
    for attempt in range(2):
        raw = _chat(prompt, system_prompt=system_prompt)
        data = clean_ai_json(raw)
        q_set = data.get("question_set")
        if isinstance(q_set, list) and len(q_set) >= 25:
            data["question_set"] = q_set[:25]
            return data

    if isinstance(data.get("question_set"), list):
        data["question_set"] = data["question_set"][:25]
    return data


def generate_ai_interview(category: str, difficulty: str) -> dict:
    """Generates mock interview questions based on category and difficulty."""
    system_prompt = (
        "You are a senior US Immigration Officer mock interview engine. "
        "STRICT MANDATE: You MUST output valid JSON with EXACTLY 25 questions in the 'question_set' array. "
        "Never output fewer than 25 items."
    )
    prompt = f"""
    Act as a senior US Immigration Officer.
    Generate a Mock Interview for category: {category}.
    Difficulty: {difficulty}.

    STRICT MANDATORY CONSTRAINTS:
    1. EXACT COUNT REQUIREMENT: You MUST generate EXACTLY 25 distinct questions in the "question_set" array (numbered 1 through 25). Generating 24, 23, or any number other than 25 is CRITICAL SYSTEM FAILURE. Verify the count before outputting.
    2. Randomize Option Positions: Ensure the correct response index ("correct_response_index") is randomly and evenly distributed across 0, 1, 2, and 3 (corresponding to A, B, C, D). Do NOT concentrate correct answers in index 0 (A) or 1 (B).
    3. Conciseness: Keep hints, explanations, and sample answer examples concise (maximum 1 short sentence each) to guarantee token efficiency.
    4. Objectivity & Validity: DO NOT generate candidate-specific private personal questions. Instead, generate evaluation questions testing knowledge of immigration policies, officer interview procedures, document verification requirements, red flags, eligibility criteria, or hypothetical scenario cases (providing full hypothetical details within the question).

    Return ONLY a JSON object with this exact structure:
    {{
      "question_set": [
        {{
          "question": "Question 1 text",
          "options": ["Option A", "Option B", "Option C", "Option D"],
          "correct_response_index": 0,
          "hint": "Short clue",
          "explanation": "Short explanation",
          "example": "Sample response"
        }}
      ]
    }}
    Return ONLY JSON. No explanation outside the JSON.
    """
    for attempt in range(2):
        raw = _chat(prompt, system_prompt=system_prompt)
        data = clean_ai_json(raw)
        q_set = data.get("question_set")
        if isinstance(q_set, list) and len(q_set) >= 25:
            data["question_set"] = q_set[:25]
            return data

    if isinstance(data.get("question_set"), list):
        data["question_set"] = data["question_set"][:25]
    return data


if __name__ == "__main__":
    print("Selected model:", get_working_model_name())

    quiz = generate_ai_quiz("H-1B Visa")
    print(f"Quiz questions: {len(quiz.get('question_set', []))}")

    interview = generate_ai_interview("Green Card", "intermediate")
    print(f"Interview questions: {len(interview.get('question_set', []))}")