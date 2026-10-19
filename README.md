# SkillPath AI Counsellor

> A simple, standalone AI career counselling chatbot web app powered by Google Gemini, designed for vocational education, ITI trades, apprenticeships, and polytechnic pathways for students and parents in India.

This project is designed to be deployed independently (e.g. on Vercel) and opened or embedded from the **SkillPath Family Counselling Portal**.

---

## 🚀 Features

- **Empathetic & Simple Career Guidance**: Explains vocational qualifications and skill pathways in simple language (Class 6–8 reading level, no jargon).
- **Strict Accuracy & Anti-Hallucination**:
  - Never invents statistics, placement percentages, specific salary figures, or course fees.
  - Transparently directs users to verified local data on the portal's Recommendations screen.
  - Quotes numbers only from the verified `knowledge.md` file.
- **Bilingual Support**: Fully fluent in **English** and **Marathi (मराठी)** with instant one-click toggle.
- **Accessibility & Low-Literacy Friendly**:
  - **Voice Input** (Web Speech API) supporting Indian English (`en-IN`) and Marathi (`mr-IN`).
  - **Read-Aloud Button (🔊)** on every response with speech synthesis.
  - Text-size toggle (`A-` / `A` / `A+`).
  - Government-portal visual identity: Navy (`#14305c`), Saffron (`#e8801a`), tricolour accent, high contrast, clean white cards.
- **Common Parent Concern Chips**:
  - 💰 Income
  - 🏢 Job Security
  - 👪 Social Perception
  - 📈 Career Growth
  - 🛡️ Workplace Safety
  - 🎓 Further Education (NSQF levels, lateral entry to diploma & degree)
  - 🧾 Training Cost
  - 📍 Local Jobs
- **Human Counsellor Handoff**: Dedicated handoff button and modal whenever parents need personalized help or local seat allocation.
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
│   └── index.py        # Flask application (exports `app`), Gemini integration & security
├── public/
│   ├── index.html      # Responsive, accessible chat page
│   ├── style.css       # Portal styling, theme, animations, and high contrast layout
│   └── app.js          # Bilingual state, speech input/output, chips, and postMessage
├── knowledge.md        # Verified facts file (NSQF levels, schemes, guidelines)
├── requirements.txt    # Pinned minimal Python dependencies
├── vercel.json         # Vercel serverless configuration and routing
├── .env.example        # Template for environment variables
└── README.md           # Documentation and integration guide
```

---

## 🛠️ Local Development

### 1. Prerequisites
- Python 3.10+ (tested up to 3.13)
- A Google Gemini API Key from [Google AI Studio](https://aistudio.google.com/)

### 2. Setup Environment
```bash
# Clone the repository and enter directory
cd skillpath-chatbot

# Create a virtual environment (optional but recommended)
python -m venv venv

# Activate the virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
copy .env.example .env
```
Edit `.env` with your actual Gemini API key:
```ini
GEMINI_API_KEY=AIzaSy...your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:5000
HUMAN_COUNSELLOR_URL=https://skillpath-portal.example.com/counsellor
```

### 4. Run the Application
```bash
python api/index.py
```
Or with Flask CLI:
```bash
flask --app api/index.py run --port 5000
```
Open your browser at `http://127.0.0.1:5000`.

---

## ☁️ Deploying to Vercel

1. Push this repository to GitHub, GitLab, or Bitbucket.
2. Log in to [Vercel](https://vercel.com/) and click **"Add New Project"**.
3. Import the repository.
4. Under **Settings → Environment Variables**, add:
   - `GEMINI_API_KEY`: Your Gemini API key.
   - `GEMINI_MODEL`: `gemini-2.5-flash` (or your preferred model).
   - `ALLOWED_ORIGINS`: Comma-separated domains of your main portal (e.g. `https://skillpath-portal.vercel.app`).
   - `HUMAN_COUNSELLOR_URL`: Link to your human counsellor desk or booking screen (optional).
5. Click **Deploy**. Vercel will build the serverless function and static assets automatically.

---

## 🔗 Linking to the Main Portal

The main project's **"AI Counsellor"** button can open the chatbot either in a new tab or embedded in an iframe or side panel.

### 1. Plain Link (Opens in New Tab)
```html
<a
  href="https://YOUR-CHATBOT.vercel.app/?lang=en&trade=Electrician&location=Nagpur"
  target="_blank"
  rel="noopener"
  class="btn-ai-counsellor"
>
  AI Counsellor
</a>
```

### 2. Embedded Iframe
> **Important**: When embedding in an iframe, the `allow="microphone"` attribute is **required** by modern browsers so the user can use voice speech recognition inside the frame.

```html
<iframe
  src="https://YOUR-CHATBOT.vercel.app/?lang=en&trade=Electrician&location=Nagpur"
  title="SkillPath AI Counsellor"
  allow="microphone"
  style="width: 100%; height: 600px; border: 0; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);"
></iframe>
```

### 3. Dynamic Context via `postMessage`
If the user selects a new trade or district on your main portal while the iframe is open, you can update the chatbot's context without reloading the page:

```javascript
const iframe = document.querySelector('iframe');
iframe.contentWindow.postMessage({
  type: 'SET_CONTEXT',
  trade: 'Solar Technician',
  location: 'Pune',
  lang: 'mr'
}, 'https://YOUR-CHATBOT.vercel.app');
```

---

## 📝 Updating `knowledge.md`

`knowledge.md` is loaded dynamically on each request. You can add verified government schemes, stipend details, or NSQF updates to this file:
1. Open `knowledge.md`.
2. Add verified facts or trade guidelines under the appropriate heading.
3. Save or redeploy.
4. The AI Counsellor will immediately incorporate these facts and may quote numbers from this section.

---

## 🛡️ Rate Limiting & Privacy Note

- **Rate Limiting**: Includes built-in sliding-window rate limiting per IP (25 requests/minute).
  *Note on Serverless*: Because Vercel serverless instances are stateless and do not share in-memory state across multiple concurrent worker instances, this provides per-instance protection. If distributed persistent rate limiting across all instances is required in production, an external Redis store (such as Upstash Redis or Supabase) can easily be integrated.
- **Privacy First**: Conversations and user messages are never stored in databases or logged to console logs. No personal student identifiers are requested or retained.
