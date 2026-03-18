import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    print("❌ GROQ_API_KEY index not found in .env")
else:
    print(f"✅ Key found: {api_key[:10]}...{api_key[-10:]} (Length: {len(api_key)})")
    
    # Test OCR Dependencies
    print("--- Testing Invoice Dependencies ---")
    try:
        import pdfplumber
        print("✅ pdfplumber: Installed & Working")
    except ImportError:
        print("❌ pdfplumber: Missing!")
        
    try:
        from rapidocr_onnxruntime import RapidOCR
        print("✅ rapidocr_onnxruntime: Installed & Working")
    except ImportError:
        print("❌ rapidocr_onnxruntime: Missing!")
    print("------------------------------------")
    # Test a simple request with a known valid model
    client = Groq(api_key=api_key)
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": "Say hello world",
                }
            ],
            model="llama3-8b-8192", # Testing with a known stable model
        )
        print("✅ Connectivity Test: SUCCESS!")
        print(f"Reply: {chat_completion.choices[0].message.content}")
    except Exception as e:
        print(f"❌ Connectivity Test: FAILED")
        print(f"Error: {e}")
