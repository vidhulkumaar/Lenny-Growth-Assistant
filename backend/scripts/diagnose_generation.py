import asyncio
import httpx
import re
from app.db.session import SessionLocal
from app.models.document import Document
from app.services.agent.adapters import OllamaAdapter

async def main():
    adapter = OllamaAdapter()
    url = f"{adapter.base_url}/api/generate"
    
    prompt = (
        "Context from uploaded documents:\n\n"
        "--- Document: test_data.pdf (Page 1) ---\n"
        "Lenny Growth Assistant Architecture Document\n"
        "This is the first page of the test document.\n"
        "Key Fact: The database used is PostgreSQL with pgvector.\n\n"
        "--- Document: test_data.pdf (Page 2) ---\n"
        "Testing Document Upload\n"
        "This is the second page.\n"
        "Key Fact: The embedding model used is all-MiniLM-L6-v2.\n"
        "Secret Fact: The mascot for this project is a blue penguin.\n\n"
        "User Question: According to Krithika Shankarraman, why shouldn't a company blindly follow growth frameworks?\n\n"
        "Provide a thorough, grounded answer citing specific pages and document names:"
    )
    system_prompt = (
        "You are the Lenny Growth Assistant, an AI expert in product management, growth, and startups.\n"
        "Your answers MUST be strictly grounded in the provided context from uploaded documents.\n\n"
        "CRITICAL GROUNDING RULES:\n"
        "1. Base your response ONLY on the provided document excerpts.\n"
        "2. For each key claim or fact, cite the specific source document and page number in the format: [Filename, Page X].\n"
        "3. If the provided excerpts do not contain sufficient evidence to answer the question, clearly state:\n"
        "   \"The provided documents do not contain sufficient evidence to answer this question.\"\n"
        "4. NEVER fabricate, hallucinate, or assume facts, page numbers, quotes, or sources not present in the excerpts.\n"
        "5. If providing general product context beyond the documents, explicitly distinguish it as general knowledge not supported by the document text."
    )

    payload = {
        "model": adapter.model_name,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 512,
        },
    }

    print("Posting to Ollama...")
    async with httpx.AsyncClient(timeout=60.0) as client:
        res = await client.post(url, json=payload)
        data = res.json()
        raw = data.get("response", "")
        print(f"Status Code: {res.status_code}")
        print(f"Raw length: {len(raw)}")
        print(f"Contains <think>: {'<think>' in raw}")
        print(f"Contains </think>: {'</think>' in raw}")
        print("Raw response:\n", raw)
        
        cleaned = re.sub(r"<think>[\s\S]*?</think>", "", raw).strip()
        print(f"\nCleaned length: {len(cleaned)}")
        print("Cleaned response:\n", repr(cleaned))

        # Check what happens if regex cuts off unclosed think tags
        cleaned_partial = re.sub(r"<think>[\s\S]*?(?:</think>|$)", "", raw).strip()
        print(f"\nCleaned partial unclosed length: {len(cleaned_partial)}")

if __name__ == "__main__":
    asyncio.run(main())
