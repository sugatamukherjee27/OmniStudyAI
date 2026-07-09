# ---------- utils/ai_summarizer.py ----------
import re
import os
import logging
import requests

logger = logging.getLogger(__name__)

API_URL = "https://router.huggingface.co/v1/chat/completions"
MODEL_NAME = "meta-llama/Meta-Llama-3-8B-Instruct"

PROMPTS = {
    "notes": (
        "Convert the following lecture into detailed, complete study notes. "
        "Write full paragraphs. Do not summarize. Do not truncate.\n\n"
    ),
    "summary": (
        "Provide a clear, concise, and structured summary of the following text, "
        "capturing the core arguments, main ideas, and key takeaways:\n\n"
    ),
    "quiz": (
        "Create real-world quiz questions based on the text.\n"
        "Rules:\n"
        "- Ask clear questions like in exams\n"
        "- Answers must directly answer the question\n"
        "- Do NOT repeat the same sentence\n"
        "Format strictly as:\n"
        "Q: <question>\nA: <answer>\n\n"
    ),
    "flashcards": (
        "Create study flashcards.\n"
        "Rules:\n"
        "- Front = short concept title (2–6 words)\n"
        "- Back = clear explanation\n"
        "- No pronouns, no 'Explain', no notes\n"
        "Format strictly as:\n"
        "Front: <concept>\nBack: <explanation>\n\n"
    ),
    "bullets": "Summarize the following lecture into bullet points:\n\n",
}

def clean_quiz(output: str) -> str:
    blocks = re.split(r"\n\s*\n", output.strip())
    cleaned = []
    for block in blocks:
        q_match = re.search(r"Q:\s*(.+)", block)
        a_match = re.search(r"A:\s*(.+)", block)
        if q_match and a_match:
            q_text = q_match.group(1).strip()
            a_text = a_match.group(1).strip()
            cleaned.append(f"Q: {q_text}\nA: {a_text}")
    return "\n\n".join(cleaned) if cleaned else output

def clean_flashcards(output: str) -> str:
    blocks = re.split(r"\n\s*\n", output.strip())
    cards = []
    for block in blocks:
        f_match = re.search(r"Front:\s*(.+)", block)
        b_match = re.search(r"Back:\s*(.+)", block)
        if f_match and b_match:
            front = f_match.group(1).strip()
            back = b_match.group(1).strip()
            if len(front.split()) <= 6:
                cards.append(f"Front: {front}\nBack: {back}")
    return "\n\n".join(cards) if cards else output

def generate_output(text, output_type="notes"):
    if not text or not text.strip():
        return "No input text provided."

    token = os.getenv("HF_API_KEY")
    if not token:
        return "Error: HF_API_KEY is missing from your environment setup (.env)."

    # Chunking Logic: Split text into 15,000 character segments
    CHUNK_SIZE = 15000 
    text_chunks = [text[i:i+CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]
    
    final_results = []
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        for i, chunk in enumerate(text_chunks):
            # Instruct the AI that it is processing part of a larger whole
            prompt = f"Part {i+1}/{len(text_chunks)} of a document.\n" + PROMPTS.get(output_type, PROMPTS["notes"]) + chunk
            
            payload = {
                "model": MODEL_NAME,
                "messages": [{"role": "system", "content": "Assistant"}, {"role": "user", "content": prompt}],
                "temperature": 0.4,
            }
            
            response = requests.post(API_URL, headers=headers, json=payload, timeout=90)
            response.raise_for_status()
            
            chunk_result = response.json()["choices"][0]["message"]["content"].strip()
            final_results.append(chunk_result)

        # Join all processed chunks together
        result = "\n\n---\n\n".join(final_results)

        # Post-process specific output types
        if output_type == "quiz": 
            result = clean_quiz(result)
        elif output_type == "flashcards": 
            result = clean_flashcards(result)
            
        return result
        
    except Exception as e:
        logger.error(f"HF API failed: {e}")
        return f"AI Processing Error: Hugging Face API call failed. Details: {str(e)[:60]}"