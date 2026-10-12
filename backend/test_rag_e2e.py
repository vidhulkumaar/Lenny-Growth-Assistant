import httpx
import time
import uuid

BASE_URL = "http://localhost:8001/api/v1"

def test_rag_e2e():
    print("Testing RAG End-to-End Workflow...")
    
    # 1. Check health
    print("Waiting for server to start...")
    for _ in range(15):
        try:
            r = httpx.get(f"{BASE_URL}/health")
            if r.status_code == 200:
                print("Server is up!")
                break
        except httpx.ConnectError:
            pass
        time.sleep(2)
    else:
        print("Server did not start in time.")
        return
    
    # 2. Upload Document
    with open("test_data.pdf", "rb") as f:
        r = httpx.post(f"{BASE_URL}/documents/upload", files={"file": ("test_data.pdf", f, "application/pdf")})
    
    print(f"Upload Response: {r.status_code}")
    if r.status_code != 200:
        print(f"Upload Failed: {r.text}")
        return
        
    doc = r.json()
    doc_id = doc["id"]
    print(f"Document ID: {doc_id}")
    
    # 3. Poll for processing to complete
    print("Waiting for document processing...")
    timeout = 60
    start = time.time()
    while True:
        r = httpx.get(f"{BASE_URL}/documents/")
        docs = r.json()
        target_doc = next((d for d in docs if d["id"] == doc_id), None)
        
        if not target_doc:
            print("Document disappeared!")
            return
            
        print(f"Status: {target_doc['status']}")
        if target_doc["status"] == "indexed":
            print("Document indexed successfully!")
            break
        elif target_doc["status"] == "failed":
            print(f"Document processing failed: {target_doc.get('error_message')}")
            return
            
        if time.time() - start > timeout:
            print("Timeout waiting for processing")
            return
            
        time.sleep(2)
        
    # 4. Ask a question
    question = "What is the mascot for this project?"
    print(f"Asking question: {question}")
    
    r = httpx.post(
        f"{BASE_URL}/chat/message", 
        json={
            "content": question,
            "document_ids": [doc_id]
        },
        timeout=120.0
    )
    
    print(f"Chat Response Code: {r.status_code}")
    if r.status_code != 200:
        print(f"Chat failed: {r.text}")
        return
        
    chat_resp = r.json()
    response = chat_resp["response"]
    print(f"Assistant: {response['content']}")
    if response.get("citations"):
        print("Citations:")
        for c in response["citations"]:
            print(f" - {c['title']} (Page {c['page_number']})")
    else:
        print("No citations provided.")
        
    # 5. Clean up
    r = httpx.delete(f"{BASE_URL}/documents/{doc_id}")
    print(f"Cleanup Response: {r.status_code}")
    
if __name__ == "__main__":
    test_rag_e2e()
