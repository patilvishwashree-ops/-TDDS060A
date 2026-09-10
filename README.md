# ⚡ LLM Cost Optimization Gateway

> A production-grade API gateway that routes LLM requests to the cheapest capable provider, caches semantically similar prompts using vector embeddings, tracks real-time costs, and enforces per-key budgets.

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green?style=flat-square)
![OpenAI Compatible](https://img.shields.io/badge/API-OpenAI%20Compatible-412991?style=flat-square)

---

## 🚀 Quick Start (Run in Terminal)

### 1. Run the Server

If PowerShell blocks script execution, run this command **once** in PowerShell:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```

Then activate and run:
```powershell
.\venv\Scripts\activate
uvicorn main:app --reload
```

> **Direct execution (without activating venv):**
> ```powershell
> .\venv\Scripts\python.exe -m uvicorn main:app --reload
> ```

---

### 2. Test the API

In a second terminal window, run the test request using `sample_request.json`:

```powershell
python test_api.py
```

Or using `curl`:
```powershell
curl -X POST "http://127.0.0.1:8000/v1/chat/completions" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer llmg-dev-demo-key-12345" `
  -d "@sample_request.json"
```

---

### 3. Open Web Dashboard & Docs

- 📊 **Cost Analytics Dashboard**: [http://localhost:8000/dashboard](http://localhost:8000/dashboard)
- 📖 **Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- ❤️ **System Health**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 🛠️ Optional Setup Commands

- **Seed/Reset Sample Data**: `python seed.py`
- **Environment Setup**: Copy `.env.example` to `.env`. Set `MOCK_PROVIDERS=true` if you don't have live API keys.

---

## 🔑 Key Features

| Feature | Description |
|---|---|
| **Drop-in OpenAI API** | Compatible with standard OpenAI SDKs (`base_url="http://localhost:8000/v1"`) |
| **Smart Routing** | Dynamic routing to cheapest model based on prompt complexity |
| **Semantic Caching** | Vector embeddings (`all-MiniLM-L6-v2`) for 92%+ similarity matching |
| **Multi-Provider** | OpenAI, Anthropic Claude, Google Gemini, and Mock Mode |
| **Cost Tracking** | Real-time USD cost and token calculations stored in SQLite |
| **Budget Enforcement** | Monthly budget limits with hard stops per API key |

---

## 📜 License

MIT License — free to use and modify.