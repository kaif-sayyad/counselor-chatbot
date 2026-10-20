/**
 * SkillPath AI Counsellor — Interactive & Accessible Chatbot Client
 * Provides bilingual toggle (English / मराठी), Groq mode status,
 * resilient offline fallback rendering, voice input/output, and iframe integration.
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
      error: "Unable to connect right now. Please try again or consult a human counsellor.",
      basicMode: "Basic mode",
      readAloud: "Read aloud",
      voiceListening: "Listening... speak now",
      voiceError: "Voice input could not be processed. Please type your message."
    },
    mr: {
      title: "कौशल्यमार्ग एआय समुपदेशक",
      subtitle: "व्यावसायिक शिक्षण व करिअर मार्गदर्शन",
      langToggleText: "English",
      placeholder: "येथे आपला प्रश्न विचारा...",
      sendBtnText: "पाठवा",
      disclaimer: "एआय उत्तरे सामान्य मार्गदर्शनासाठी आहेत. पडताळणी केलेल्या आकडेवारीसाठी पोर्टलचे डेटा स्क्रीन पहा.",
      welcome: "नमस्कार! मी आपला कौशल्यमार्ग एआय समुपदेशक आहे. व्यावसायिक शिक्षण, आयटीआय (ITI), तंत्रनिकेतन किंवा कौशल्याधारित करिअरबद्दल कोणताही प्रश्न विचारा.",
      error: "सध्या संपर्क होऊ शकला नाही. कृपया पुन्हा प्रयत्न करा किंवा मानवी समुपदेशकांशी बोला.",
      basicMode: "मूलभूत मोड",
      readAloud: "ऐका",
      voiceListening: "ऐकत आहे... बोला",
      voiceError: "आवाज समजला नाही. कृपया टाईप करा."
    }
  };

  // State
  let currentLang = 'en';
  let history = []; // [{ role: 'user'|'model'|'assistant', text: '...' }]
  let userContext = {
    trade: '',
    location: '',
    concern: ''
  };

  // DOM Elements
  const headerTitle = document.getElementById('header-title');
  const headerSubtitle = document.getElementById('header-subtitle');
  const headerBadge = document.getElementById('header-badge');
  const langToggleBtn = document.getElementById('btn-lang-toggle');
  const langToggleText = document.getElementById('lang-toggle-text');
  const btnNewChat = document.getElementById('btn-new-chat');
  const messagesContainer = document.getElementById('messages-container');
  const typingIndicator = document.getElementById('typing-indicator');
  const chatForm = document.getElementById('chat-form');
  const userInput = document.getElementById('user-input');
  const btnVoice = document.getElementById('btn-voice');
  const sendBtnText = document.getElementById('send-btn-text');
  const disclaimerText = document.getElementById('disclaimer-text');

  // Helper: Escape HTML
  function escapeHtml(str) {
    if (!str) return '';
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

  // Speech Synthesis (Read-aloud)
  function speakText(text) {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    // Strip markdown formatting for cleaner speech
    const cleanText = text.replace(/[*_#`]/g, '');
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = currentLang === 'mr' ? 'mr-IN' : 'en-IN';
    utterance.rate = 0.95;
    window.speechSynthesis.speak(utterance);
  }

  function appendMessage(role, text, mode, suggestions, chips) {
    const row = document.createElement('div');
    row.className = `msg-row ${role === 'user' ? 'user' : 'bot'}`;

    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble';

    // If bot and in basic/fallback mode, show small "Basic mode" badge
    if (role === 'bot') {
      const headerRow = document.createElement('div');
      headerRow.className = 'msg-bubble-header';

      if (mode === 'basic') {
        const badge = document.createElement('span');
        badge.className = 'badge-basic-mode';
        badge.textContent = I18N[currentLang].basicMode;
        headerRow.appendChild(badge);
      } else {
        headerRow.appendChild(document.createElement('span'));
      }

      // Add read-aloud button if speech synthesis is supported
      if ('speechSynthesis' in window) {
        const ttsBtn = document.createElement('button');
        ttsBtn.type = 'button';
        ttsBtn.className = 'btn-tts';
        ttsBtn.title = I18N[currentLang].readAloud;
        ttsBtn.setAttribute('aria-label', I18N[currentLang].readAloud);
        ttsBtn.textContent = '🔊';
        ttsBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          speakText(text);
        });
        headerRow.appendChild(ttsBtn);
      }

      bubble.appendChild(headerRow);
    }

    const contentDiv = document.createElement('div');
    contentDiv.innerHTML = formatMarkdown(text);
    bubble.appendChild(contentDiv);
    row.appendChild(bubble);

    // If suggestions are provided, render clickable suggestion pills
    if (role === 'bot' && suggestions && suggestions.length > 0) {
      const suggContainer = document.createElement('div');
      suggContainer.className = 'suggestions-container';
      suggestions.forEach(sugg => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'suggestion-btn';
        btn.textContent = `💡 ${sugg}`;
        btn.addEventListener('click', () => {
          userInput.value = sugg;
          handleSend();
        });
        suggContainer.appendChild(btn);
      });
      row.appendChild(suggContainer);
    }

    // If concern chips are provided (e.g. when concern could not be detected), render chips
    if (role === 'bot' && chips && chips.length > 0) {
      const chipsContainer = document.createElement('div');
      chipsContainer.className = 'chips-container';
      chips.forEach(chip => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'chip-btn';
        const label = currentLang === 'mr' ? chip.label_mr : chip.label_en;
        btn.textContent = label;
        btn.addEventListener('click', () => {
          userInput.value = label;
          handleSend();
        });
        chipsContainer.appendChild(btn);
      });
      row.appendChild(chipsContainer);
    }

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
    appendMessage('bot', welcome, 'groq', null, null);
    history.push({ role: 'assistant', text: welcome });
    userInput.value = '';
    userInput.focus();
  }

  // Health check to update header badge
  async function checkHealth() {
    try {
      const res = await fetch('/api/health');
      if (res.ok) {
        const data = await res.json();
        if (headerBadge) {
          if (data.mode === 'groq' || data.configured) {
            headerBadge.textContent = 'Groq Qwen';
            headerBadge.className = 'header-badge badge-groq';
          } else {
            headerBadge.textContent = 'Basic mode';
            headerBadge.className = 'header-badge badge-offline';
          }
        }
      }
    } catch (e) {
      if (headerBadge) {
        headerBadge.textContent = 'Basic mode';
        headerBadge.className = 'header-badge badge-offline';
      }
    }
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
          context: userContext,
          history: history.slice(0, -1)
        })
      });

      const data = await res.json();
      typingIndicator.classList.add('hidden');

      const botReply = data && data.reply ? data.reply : I18N[currentLang].error;
      const mode = data && data.mode ? data.mode : 'basic';
      const suggestions = data && data.suggestions ? data.suggestions : null;
      const chips = data && data.chips ? data.chips : null;

      appendMessage('bot', botReply, mode, suggestions, chips);
      history.push({ role: 'assistant', text: botReply });
    } catch (err) {
      typingIndicator.classList.add('hidden');
      // Even on local network error, show relatable fallback instead of raw error
      appendMessage('bot', I18N[currentLang].error, 'basic', null, null);
    }
  }

  // Speech Recognition (Voice Input)
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  let recognition = null;
  let isListening = false;

  if (SpeechRecognition && btnVoice) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
      isListening = true;
      btnVoice.classList.add('listening');
      userInput.placeholder = I18N[currentLang].voiceListening;
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      userInput.value = transcript;
      handleSend();
    };

    recognition.onerror = () => {
      isListening = false;
      btnVoice.classList.remove('listening');
      userInput.placeholder = I18N[currentLang].placeholder;
    };

    recognition.onend = () => {
      isListening = false;
      btnVoice.classList.remove('listening');
      userInput.placeholder = I18N[currentLang].placeholder;
    };

    btnVoice.addEventListener('click', () => {
      if (!recognition) return;
      if (isListening) {
        recognition.stop();
      } else {
        recognition.lang = currentLang === 'mr' ? 'mr-IN' : 'en-IN';
        try {
          recognition.start();
        } catch (e) {
          // Already active
        }
      }
    });
  } else if (btnVoice) {
    // If browser doesn't support Web Speech API, hide voice button
    btnVoice.style.display = 'none';
  }

  // Event Listeners
  langToggleBtn.addEventListener('click', () => {
    const newLang = currentLang === 'en' ? 'mr' : 'en';
    updateLanguage(newLang);
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

  // URL parameters (?lang=mr&trade=Electrician&location=Nagpur&concern=income)
  const params = new URLSearchParams(window.location.search);
  const urlLang = (params.get('lang') || '').toLowerCase();
  if (urlLang === 'mr' || urlLang === 'en') {
    currentLang = urlLang;
  }
  userContext.trade = params.get('trade') || '';
  userContext.location = params.get('location') || '';
  userContext.concern = params.get('concern') || '';

  // Cross-window postMessage listener for embedded iframes
  window.addEventListener('message', (event) => {
    if (event.data && typeof event.data === 'object') {
      if (event.data.type === 'SET_CONTEXT') {
        if (event.data.trade) userContext.trade = event.data.trade;
        if (event.data.location) userContext.location = event.data.location;
        if (event.data.concern) userContext.concern = event.data.concern;
        if (event.data.lang && (event.data.lang === 'mr' || event.data.lang === 'en')) {
          updateLanguage(event.data.lang);
        }
      }
    }
  });

  // Initialize
  updateLanguage(currentLang);
  startNewChat();
  checkHealth();

})();
