/**
 * SkillPath AI Counsellor — Simple & Minimal Chatbot Client
 * Provides clean user input and bilingual toggle (English / मराठी).
 */

(function () {
  'use strict';

  // UI Strings for English & Marathi
  const I18N = {
    en: {
      title: "SkillPath AI Counsellor",
      subtitle: "Vocational & Skill Career Guidance",
      langToggleText: "मराठी",
      placeholder: "Type your question here...",
      sendBtnText: "Send",
      disclaimer: "AI answers are general guidance. For verified figures see the portal's data screens.",
      welcome: "Hello! I am your SkillPath AI Counsellor. Ask me any question about vocational education, ITI trades, polytechnic diplomas, or skill-based careers.",
      error: "Unable to connect right now. Please try again."
    },
    mr: {
      title: "कौशल्यमार्ग एआय समुपदेशक",
      subtitle: "व्यावसायिक शिक्षण व करिअर मार्गदर्शन",
      langToggleText: "English",
      placeholder: "येथे आपला प्रश्न विचारा...",
      sendBtnText: "पाठवा",
      disclaimer: "एआय उत्तरे सामान्य मार्गदर्शनासाठी आहेत. पडताळणी केलेल्या आकडेवारीसाठी पोर्टलचे डेटा स्क्रीन पहा.",
      welcome: "नमस्कार! मी आपला कौशल्यमार्ग एआय समुपदेशक आहे. व्यावसायिक शिक्षण, आयटीआय (ITI), तंत्रनिकेतन किंवा कौशल्याधारित करिअरबद्दल कोणताही प्रश्न विचारा.",
      error: "सध्या संपर्क होऊ शकला नाही. कृपया पुन्हा प्रयत्न करा."
    }
  };

  // State
  let currentLang = 'en';
  let history = []; // [{ role: 'user'|'model', text: '...' }]

  // DOM Elements
  const headerTitle = document.getElementById('header-title');
  const headerSubtitle = document.getElementById('header-subtitle');
  const langToggleBtn = document.getElementById('btn-lang-toggle');
  const langToggleText = document.getElementById('lang-toggle-text');
  const btnNewChat = document.getElementById('btn-new-chat');
  const messagesContainer = document.getElementById('messages-container');
  const typingIndicator = document.getElementById('typing-indicator');
  const chatForm = document.getElementById('chat-form');
  const userInput = document.getElementById('user-input');
  const sendBtnText = document.getElementById('send-btn-text');
  const disclaimerText = document.getElementById('disclaimer-text');

  // Helper: Escape HTML
  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  // Helper: Format Markdown (bold, linebreaks, bullet lists)
  function formatMarkdown(text) {
    if (!text) return '';
    let safe = escapeHtml(text);
    safe = safe.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    const lines = safe.split('\n');
    let output = [];
    let inList = false;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (line.startsWith('* ') || line.startsWith('- ')) {
        if (!inList) {
          output.push('<ul>');
          inList = true;
        }
        output.push(`<li>${line.substring(2)}</li>`);
      } else {
        if (inList) {
          output.push('</ul>');
          inList = false;
        }
        if (line) {
          output.push(`<p>${line}</p>`);
        }
      }
    }
    if (inList) output.push('</ul>');
    return output.join('');
  }

  function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  function appendMessage(role, text) {
    const row = document.createElement('div');
    row.className = `msg-row ${role === 'user' ? 'user' : 'bot'}`;

    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble';
    bubble.innerHTML = formatMarkdown(text);

    row.appendChild(bubble);
    messagesContainer.appendChild(row);
    scrollToBottom();
  }

  function updateLanguage(newLang) {
    currentLang = newLang;
    const t = I18N[currentLang];
    headerTitle.textContent = t.title;
    headerSubtitle.textContent = t.subtitle;
    langToggleText.textContent = t.langToggleText;
    userInput.placeholder = t.placeholder;
    sendBtnText.textContent = t.sendBtnText;
    disclaimerText.textContent = t.disclaimer;
    document.documentElement.lang = currentLang;
  }

  function startNewChat() {
    history = [];
    messagesContainer.innerHTML = '';
    const welcome = I18N[currentLang].welcome;
    appendMessage('bot', welcome);
    history.push({ role: 'model', text: welcome });
    userInput.value = '';
    userInput.focus();
  }

  async function handleSend() {
    const message = userInput.value.trim();
    if (!message) return;

    // Append user message
    userInput.value = '';
    appendMessage('user', message);
    history.push({ role: 'user', text: message });

    // Show typing indicator
    typingIndicator.classList.remove('hidden');
    scrollToBottom();

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: message,
          language: currentLang,
          history: history.slice(0, -1)
        })
      });

      const data = await res.json();
      typingIndicator.classList.add('hidden');

      const botReply = data && data.reply ? data.reply : I18N[currentLang].error;
      appendMessage('bot', botReply);
      history.push({ role: 'model', text: botReply });
    } catch (err) {
      typingIndicator.classList.add('hidden');
      appendMessage('bot', I18N[currentLang].error);
    }
  }

  // Event Listeners
  langToggleBtn.addEventListener('click', () => {
    const newLang = currentLang === 'en' ? 'mr' : 'en';
    updateLanguage(newLang);
    // If chat only has the greeting, refresh greeting in new language
    if (history.length <= 1) {
      startNewChat();
    }
  });

  btnNewChat.addEventListener('click', () => {
    startNewChat();
  });

  chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    handleSend();
  });

  // Check URL parameter (?lang=mr or ?lang=en)
  const params = new URLSearchParams(window.location.search);
  const urlLang = (params.get('lang') || '').toLowerCase();
  if (urlLang === 'mr' || urlLang === 'en') {
    currentLang = urlLang;
  }

  // Initialize
  updateLanguage(currentLang);
  startNewChat();

})();
