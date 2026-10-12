import asyncio
import httpx
import traceback

async def test_ollama():
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post("http://127.0.0.1:11434/api/generate", json={
                "model": "qwen3:4b",
                "prompt": "Hello",
                "stream": False
            })
            print("Status Code:", resp.status_code)
            print("Response:", resp.text)
    except Exception as e:
        print(f"Exception Type: {type(e)}")
        print(f"Exception Str: '{e}'")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ollama())
