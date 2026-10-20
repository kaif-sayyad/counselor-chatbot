# SkillPath AI Counsellor

> A resilient, standalone AI career counselling chatbot web app powered by Groq (Qwen model) with a multi-tier offline fallback chain, designed for vocational education, ITI trades, apprenticeships, and polytechnic pathways for students and parents in India.

This project is designed to be deployed independently (e.g. on Vercel) and opened or embedded from the **SkillPath Family Counselling Portal**.

---

## 🚀 Key Features

- **Empathetic & Simple Career Guidance**: Explains vocational qualifications and skill pathways in simple language (Class 6–8 reading level, no jargon).
- **AI Provider — Groq with Qwen**: Powered by Groq's high-speed OpenAI-compatible completions API using `qwen/qwen3-32b` with reasoning tokens hidden.
- **Strict Accuracy & Anti-Hallucination**:
  - Never invents statistics, placement percentages, specific salary figures, or course fees.
  - Transparently directs users to verified local data on the portal's Recommendations screen.
  - Built-in **Number Guard**: Any unverified numbers in AI responses trigger an automatic fallback to verified knowledge base answers.
- **Multi-Tier Relatable Fallback Chain**:
  - The user never sees an error screen, blank reply, or raw error.
  - **Tier 1 (Groq API)**: Short timeout with automatic single retry on network/5xx errors.
  - **Tier 2 (Local FAQ Match)**: Searches 48+ bilingual FAQ entries from `knowledge/faq.json` using keyword and text similarity, returning the best answer plus 2 related suggestions.
  - **Tier 3 (Concern Category Templates)**: Detects 8 key family concerns (*income, job security, social perception, career growth, safety, further education, training cost, local jobs*) and replies with warm, verified templates in English or Marathi.
  - **Tier 4 (General Guidance & Chips)**: Returns a friendly message and clickable concern chips.
- **Bilingual Support**: Fully fluent in **English** and **Marathi (मराठी)** with instant one-click toggle.
- **Accessibility & Voice Support**:
  - **Voice Input** (Web Speech API) supporting Indian English (`en-IN`) and Marathi (`mr-IN`).
  - **Read-Aloud Button (🔊)** on every response with speech synthesis.
  - High-contrast visual identity: Navy (`#14305c`), Saffron (`#e8801a`), tricolour accent, clean cards.
- **Embedding & Security**:
  - Configurable `ALLOWED_ORIGINS` for Content Security Policy (`frame-ancestors`) and CORS.
  - Safe against prompt-injections; rejects instruction tampering and API key queries.
  - Context via URL query parameters (`?lang=mr&trade=Electrician&location=Nagpur&concern=income`).
  - Cross-window `postMessage` support for dynamic parent-portal communication.

---

## 📁 Project Structure

```
skillpath-chatbot/
├── api/
│   └── index.py            # Flask application, Groq completions, fallback chain & security
├── knowledge/
│   └── faq.json            # 48+ bilingual FAQ entries with keywords and verified answers
├── public/
│   ├── index.html          # Responsive, accessible chat interface
│   ├── style.css           # Styling, themes, badges, chips, and animations
│   └── app.js              # Bilingual state, speech input/output, chips, and postMessage
├── knowledge.md            # Verified facts file (NSQF levels, schemes, guidelines)
├── requirements.txt        # Pinned minimal Python dependencies (Flask, requests, python-dotenv)
├── vercel.json             # Vercel serverless configuration and routing
├── .env.example            # Template for environment variables
└── README.md               # Documentation and integration guide
```

---

## ⚙️ Environment Variables

Configure these variables server-side (in your `.env` file for local development or Vercel Environment Variables):

| Variable | Required | Default | Description |
| :--- | :---: | :---: | :--- |
| `GROQ_API_KEY` | Recommended | `""` | Your Groq API key from [Groq Console](https://console.groq.com/). If missing or unavailable, the chatbot seamlessly operates in **Basic mode** using local knowledge. |
| `GROQ_MODEL` | Optional | `qwen/qwen3-32b` | Groq chat model identifier (default: `qwen/qwen3-32b`). |
| `ALLOWED_ORIGINS` | Optional | `""` | Comma-separated list of parent domains for CSP `frame-ancestors` and CORS (e.g. `https://skillpath-portal.vercel.app,http://localhost:3000`). |
| `HUMAN_COUNSELLOR_URL` | Optional | `""` | Link to human counsellor scheduling or helpdesk. |

> **Security Note**: Never expose API keys in frontend code, git commits, or client-side responses. The `/api/health` endpoint only reports `"mode": "groq"` or `"mode": "offline"` and never discloses the key.

---

## 🔄 How the Fallback Chain Works

1. **Groq API Call**:
   The backend sends the user query along with the system instruction and up to 10 previous messages to Groq with a 10-second timeout. If a network error, timeout, or 5xx occurs, it retries once.
2. **Number Guard**:
   If Groq returns a response containing numbers not present in the verified knowledge files (`knowledge.md` and `knowledge/faq.json`), the answer is rejected and replaced by a verified local answer.
3. **Local FAQ Search (`knowledge/faq.json`)**:
   If Groq fails, is rate-limited (429), unauthorized (401/403), or returns invalid output, the system matches the question against `knowledge/faq.json` using weighted keyword and token overlap in the user's language. It returns the verified answer and up to 2 related follow-up suggestions.
4. **Concern Category Templates**:
   If no exact FAQ matches, the system detects which of the 8 parent concerns is being asked (*income, job security, social perception, career growth, safety, further education, training cost, local jobs*) and replies with a warm, empathetic template in English or Marathi.
5. **General Friendly Message & Chips**:
   If no concern is detected, it responds with a reassuring message and displays the 8 concern chips so the user can easily explore.
6. **Chat UI Presentation**:
   When operating via fallback, the chat displays the answer normally with a subtle **"Basic mode"** badge. The user never encounters an error banner or blank response.

---

## 📝 How to Edit or Add Entries to `knowledge/faq.json`

The file `knowledge/faq.json` contains structured question-and-answer pairs in JSON format:

```json
{
  "id": "faq_49",
  "concern": "income",
  "keywords_en": ["salary", "starting wages", "earn"],
  "keywords_mr": ["पगार", "उत्पन्न", "वेतन"],
  "question": "What is the starting income after ITI?",
  "answer_en": "Starting income depends on your trade and regional industry demand...",
  "answer_mr": "आयटीआय नंतर मिळणारे उत्पन्न निवडलेला ट्रेड आणि स्थानिक मागणीवर अवलंबून असते..."
}
```

To add or update an entry:
1. Open [knowledge/faq.json](file:///knowledge/faq.json).
2. Add a new object with unique `id`, `concern` category, keyword lists in English (`keywords_en`) and Marathi (`keywords_mr`), the question text, and verified responses (`answer_en`, `answer_mr`).
3. Ensure no invented numbers or false guarantees are added.
4. Save the file. The changes are loaded immediately on the next request without needing a server rebuild.

---

## 🛠️ Local Development

### 1. Setup Environment
```bash
# Clone the repository and enter directory
cd counselor-chatbot

# Create and activate a virtual environment
python -m venv venv
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
copy .env.example .env
```
Edit `.env`:
```ini
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=qwen/qwen3-32b
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:5000
HUMAN_COUNSELLOR_URL=https://skillpath-portal.example.com/counsellor
```

### 3. Run Application
```bash
python api/index.py
```
Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

### 4. Run Test Suite
```bash
python -m unittest discover -s tests -v
```

---

## ☁️ Deploying to Vercel

1. Commit and push your changes to your GitHub repository:
   ```bash
   git add .
   git commit -m "Switch chatbot to Groq Qwen and add offline fallback answers"
   git push origin main
   ```
2. In the [Vercel Dashboard](https://vercel.com/):
   - Go to your Project **Settings → Environment Variables**.
   - Add `GROQ_API_KEY` (your Groq API key).
   - Add `GROQ_MODEL` with value `qwen/qwen3-32b`.
   - Remove any previous AI provider keys and variables.
   - Click **Redeploy** on the latest deployment if needed.
3. Test the deployment:
   - Check `GET https://<your-project>.vercel.app/api/health`
   - Send a chat message via `POST https://<your-project>.vercel.app/api/chat`
