# pip install openai
# Required ENV: OPENAI_API_KEY

from os import environ
from openai import OpenAI
import json
import re

# ── কনফিগারেশন ──────────────────────────────────────────────────────────────
API_KEY = environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)

# মডেল অগ্রাধিকার তালিকা — প্রয়োজনে পরিবর্তন করুন
MODEL_PREFERENCE = ["gpt-4o", "gpt-4o-mini", "gpt-4", "gpt-3.5-turbo"]
DEFAULT_MODEL    = "gpt-4o-mini"   # fallback যদি discovery ব্যর্থ হয়


# ── মডেল নির্বাচন ────────────────────────────────────────────────────────────
def get_working_model_name() -> str:
    """
    অ্যাকাউন্টে সচল থাকা পছন্দের মডেলটি খুঁজে বের করবে।
    Gemini-র list_models() র মতো — OpenAI models.list() দিয়ে করা হয়েছে।
    """
    try:
        available = {m.id for m in client.models.list().data}
        for preferred in MODEL_PREFERENCE:
            if preferred in available:
                return preferred
        # তালিকায় না থাকলে যেকোনো gpt মডেল নাও
        gpt_models = [m for m in available if m.startswith("gpt-")]
        return sorted(gpt_models)[0] if gpt_models else DEFAULT_MODEL
    except Exception:
        return DEFAULT_MODEL


# ── JSON পরিষ্কার ─────────────────────────────────────────────────────────────
def clean_ai_json(raw_text: str) -> dict:
    """
    AI রেসপন্স থেকে ময়লা পরিষ্কার করে শুধু JSON টুকু বের করা।
    OpenAI মাঝেমাঝে ```json ব্লকে দেয়, মাঝেমাঝে সরাসরি — দুটোই হ্যান্ডেল করা হয়েছে।
    """
    try:
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()
        return json.loads(raw_text)
    except json.JSONDecodeError:
        # শেষ চেষ্টা: প্রথম { থেকে শেষ } পর্যন্ত কেটে নাও
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError(f"AI returned invalid JSON. Raw snippet: {raw_text[:200]}")


# ── ইন্টারনাল হেল্পার ────────────────────────────────────────────────────────
def _chat(prompt: str) -> str:
    """
    OpenAI chat completion কল — Gemini-র generate_content()-এর সমতুল্য।
    response_format=json_object দিলে OpenAI সবসময় valid JSON দেয়।
    তবে তখন prompt-এ "JSON" শব্দ থাকা বাধ্যতামূলক।
    """
    model = get_working_model_name()
    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},   # JSON mode — সবচেয়ে নির্ভরযোগ্য
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Always return valid JSON."},
            {"role": "user",   "content": prompt},
        ],
        temperature=0.7,   # সামান্য ভ্যারিয়েশন রাখে; 0 দিলে একঘেঁয়ে হয়
        max_tokens=4096,   # 25 প্রশ্নের জন্য যথেষ্ট; প্রয়োজনে বাড়ান
    )
    return response.choices[0].message.content


# ── পাবলিক ফাংশন ─────────────────────────────────────────────────────────────
def generate_ai_quiz(case_type: str) -> dict:
    """specification অনুযায়ী ২৫টি কুইজ প্রশ্ন তৈরি করবে।"""
    prompt = f"""
    Act as a senior US Immigration Attorney.
    Generate a practice quiz (25 questions) for: {case_type}.
    Return ONLY a JSON object with this exact structure:
    {{
      "question_set": [
        {{
          "question": "text",
          "options": ["a", "b", "c", "d"],
          "correct_answer_index": 0,
          "hint": "clue",
          "explanation": "why"
        }}
      ]
    }}
    Return ONLY JSON. No explanation outside the JSON.
    """
    raw = _chat(prompt)
    return clean_ai_json(raw)


def generate_ai_interview(category: str, difficulty: str) -> dict:
    """ইন্টারভিউ ক্যাটাগরি এবং ডিফিকাল্টি অনুযায়ী প্রশ্ন তৈরি করবে।"""
    prompt = f"""
    Act as a senior US Immigration Officer.
    Generate a Mock Interview (25 questions) for category: {category}.
    Difficulty: {difficulty}.
    Return ONLY a JSON object with this exact structure:
    {{
      "question_set": [
        {{
          "question": "text",
          "options": ["a", "b", "c", "d"],
          "correct_response_index": 0,
          "hint": "clue",
          "explanation": "why",
          "example": "sample answer"
        }}
      ]
    }}
    Return ONLY JSON. No explanation outside the JSON.
    """
    raw = _chat(prompt)
    return clean_ai_json(raw)


if __name__ == "__main__":
    print("Selected model:", get_working_model_name())

    quiz = generate_ai_quiz("H-1B Visa")
    print(f"Quiz questions: {len(quiz.get('question_set', []))}")

    interview = generate_ai_interview("Green Card", "intermediate")
    print(f"Interview questions: {len(interview.get('question_set', []))}")