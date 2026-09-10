"""
Test script to send sample_request.json to the LLM Gateway.
Run this in terminal after starting main.py:
  python test_api.py
"""
import json
import urllib.request
import urllib.error

API_URL = "http://127.0.0.1:8000/v1/chat/completions"

def main():
    print("🚀 Reading sample_request.json...")
    with open("sample_request.json", "r", encoding="utf-8") as f:
        payload = json.load(f)

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer llmg-dev-demo-key-12345"
    }

    print(f"📡 Sending request to {API_URL}...")
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            print("\n✅ Response Received Successfully!")
            print("--------------------------------------------------")
            print("Model Used :", data.get("model"))
            print("Provider   :", data.get("provider"))
            print("Cost (USD) :", f"${data['usage']['cost_usd']:.8f}")
            print("Cached Hit :", data['usage']['cached'])
            print("Tokens Used:", data['usage']['total_tokens'])
            print("--------------------------------------------------")
            print("AI Response:\n", data["choices"][0]["message"]["content"])
    except urllib.error.URLError as e:
        print(f"\n❌ Could not connect to gateway: {e}")
        print("💡 Make sure the gateway server is running! Run 'python main.py' in another terminal.")

if __name__ == "__main__":
    main()
