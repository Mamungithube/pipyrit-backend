import google.generativeai as genai
import json
import re

# আপনার API Key
API_KEY = "AIzaSyCmipbwD_loqA1pcPxSyjjwOdDORvRVdWI"
genai.configure(api_key=API_KEY)

def get_working_model_name():
    """আপনার অ্যাকাউন্টে সচল থাকা মডেলটি অটোমেটিক খুঁজে বের করবে।"""
    try:
        available_models = [
            m.name for m in genai.list_models() 
            if 'generateContent' in m.supported_generation_methods
        ]
        for preferred in ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']:
            if preferred in available_models:
                return preferred
        return available_models[0]
    except Exception:
        return 'gemini-1.5-flash'

def clean_ai_json(raw_text):
    """AI রেসপন্স থেকে ময়লা পরিষ্কার করে শুধু JSON টুকু বের করা।"""
    try:
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()
        return json.loads(raw_text)
    except Exception as e:
        raise ValueError(f"AI returned invalid JSON: {str(e)}")

def generate_ai_quiz(case_type):
    """specification অনুযায়ী ২৫টি কুইজ প্রশ্ন তৈরি করবে।"""
    model_name = get_working_model_name()
    config = {"response_mime_type": "application/json"} if '1.5' in model_name else None
    model = genai.GenerativeModel(model_name, generation_config=config)
    
    prompt = f"""
    Act as a senior US Immigration Attorney. Generate a practice quiz (25 questions) for: {case_type}.
    Structure: {{"question_set": [{{"question": "text", "options": ["a", "b", "c", "d"], "correct_answer_index": 0, "hint": "clue", "explanation": "why"}}]}}
    Return ONLY JSON.
    """
    response = model.generate_content(prompt)
    return clean_ai_json(response.text)

def generate_ai_interview(category, difficulty):
    """ইন্টারভিউ ক্যাটাগরি এবং ডিফিকাল্টি অনুযায়ী প্রশ্ন তৈরি করবে।"""
    model_name = get_working_model_name()
    config = {"response_mime_type": "application/json"} if '1.5' in model_name else None
    model = genai.GenerativeModel(model_name, generation_config=config)
    
    prompt = f"""
    Act as a senior US Immigration Officer. Generate a Mock Interview (25 questions) for: {category}.
    Difficulty: {difficulty}.
    Structure: {{"question_set": [{{"question": "text", "options": ["a", "b", "c", "d"], "correct_response_index": 0, "hint": "clue", "explanation": "why", "example": "sample answer"}}]}}
    Return ONLY JSON.
    """
    response = model.generate_content(prompt)
    return clean_ai_json(response.text)