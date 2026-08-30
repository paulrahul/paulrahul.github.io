const form = document.querySelector("[data-chat-form]");
const input = document.querySelector("[data-chat-input]");
const messages = document.querySelector("[data-messages]");
const suggestions = document.querySelector(".suggestions");
const suggestedQuestions = document.querySelectorAll("[data-question]");
const maximizeButton = document.querySelector("[data-maximize-chat]");
const closeButton = document.querySelector("[data-close-chat]");
const sendButton = form.querySelector("button[type='submit']");
// const CHAT_API_URL = "http://127.0.0.1:8000/api/chat";
const CHAT_API_URL = "https://portfolio-chatbot-kohl.vercel.app/api/chat";

const isEmbedded = new URLSearchParams(window.location.search).get("embedded") === "1";
document.body.classList.toggle("is-embedded", isEmbedded);

const applyTheme = (theme = localStorage.getItem("portfolio-theme")) => {
  document.body.classList.toggle("dark", theme === "dark");
};

applyTheme();

window.addEventListener("storage", (event) => {
  if (event.key === "portfolio-theme") applyTheme(event.newValue);
});

window.addEventListener("message", (event) => {
  if (event.origin !== window.location.origin) return;
  if (event.data?.type === "portfolio-theme") applyTheme(event.data.theme);
});

const escapeHtml = (value) =>
  value.replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  })[character]);

const scrollToLatestMessage = () => {
  messages.scrollTop = messages.scrollHeight;
};

const appendInlineMarkdown = (container, text) => {
  const tokenPattern = /(\*\*[^*\n]+\*\*|`[^`\n]+`|\[[^\]\n]+\]\(https?:\/\/[^)\s]+\))/g;
  let cursor = 0;

  text.replace(tokenPattern, (token, _capture, offset) => {
    container.append(document.createTextNode(text.slice(cursor, offset)));

    if (token.startsWith("**")) {
      const strong = document.createElement("strong");
      strong.textContent = token.slice(2, -2);
      container.append(strong);
    } else if (token.startsWith("`")) {
      const code = document.createElement("code");
      code.textContent = token.slice(1, -1);
      container.append(code);
    } else {
      const match = token.match(/^\[([^\]]+)\]\((https?:\/\/[^)]+)\)$/);
      if (match) {
        const link = document.createElement("a");
        link.textContent = match[1];
        link.href = match[2];
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        container.append(link);
      } else {
        container.append(document.createTextNode(token));
      }
    }

    cursor = offset + token.length;
    return token;
  });

  container.append(document.createTextNode(text.slice(cursor)));
};

const renderMarkdown = (container, markdown) => {
  const normalizedMarkdown = markdown
    .replace(/\r\n?/g, "\n")
    .replace(/[ \t]+-[ \t]+(?=\*\*)/g, "\n- ");
  const lines = normalizedMarkdown.split("\n");
  let paragraphLines = [];
  let activeList = null;

  const flushParagraph = () => {
    if (!paragraphLines.length) return;
    const paragraph = document.createElement("p");
    appendInlineMarkdown(paragraph, paragraphLines.join(" "));
    container.append(paragraph);
    paragraphLines = [];
  };

  const closeList = () => {
    activeList = null;
  };

  lines.forEach((rawLine) => {
    const line = rawLine.trim();
    if (!line) {
      flushParagraph();
      closeList();
      return;
    }

    const listItem = line.match(/^([-*]|\d+[.)])\s+(.+)$/);
    if (listItem) {
      flushParagraph();
      const listType = /^\d/.test(listItem[1]) ? "ol" : "ul";
      if (!activeList || activeList.tagName.toLowerCase() !== listType) {
        activeList = document.createElement(listType);
        container.append(activeList);
      }
      const item = document.createElement("li");
      appendInlineMarkdown(item, listItem[2]);
      activeList.append(item);
      return;
    }

    closeList();
    const heading = line.match(/^#{1,3}\s+(.+)$/);
    if (heading) {
      flushParagraph();
      const title = document.createElement("h3");
      appendInlineMarkdown(title, heading[1]);
      container.append(title);
      return;
    }

    paragraphLines.push(line);
  });

  flushParagraph();
};

const addMessage = (text, type) => {
  const message = document.createElement("article");
  message.className = `message message--${type}`;

  if (type === "assistant") {
    message.innerHTML = `
      <span class="message-avatar" aria-hidden="true">RP</span>
      <div class="message-content">
        <p class="message-label">Portfolio assistant</p>
        <div class="bubble"></div>
        <p class="message-time">Just now</p>
      </div>
    `;
    renderMarkdown(message.querySelector(".bubble"), text);
  } else {
    message.innerHTML = `
      <div class="message-content">
        <div class="bubble"><p>${escapeHtml(text)}</p></div>
      </div>
    `;
  }

  messages.appendChild(message);
  scrollToLatestMessage();
};

const addBusyMessage = () => {
  const message = document.createElement("article");
  message.className = "message message--assistant message--busy";
  message.innerHTML = `
    <span class="message-avatar" aria-hidden="true">RP</span>
    <div class="message-content">
      <p class="message-label">Portfolio assistant</p>
      <div class="bubble typing-indicator" aria-hidden="true">
        <span></span><span></span><span></span>
      </div>
      <p class="message-time">Thinking…</p>
      <span class="sr-only">Portfolio assistant is preparing an answer.</span>
    </div>
  `;
  messages.appendChild(message);
  messages.setAttribute("aria-busy", "true");
  scrollToLatestMessage();
  return message;
};

const submitQuestion = async (question) => {
  const value = question.trim();
  if (!value || sendButton.disabled) return;

  suggestions.hidden = true;
  addMessage(value, "user");
  input.value = "";
  input.style.height = "auto";
  input.disabled = true;
  sendButton.disabled = true;
  const busyMessage = addBusyMessage();

  try {
    const response = await fetch(CHAT_API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: value }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "The assistant could not answer right now.");
    }
    busyMessage.remove();
    addMessage(payload.answer, "assistant");
  } catch (error) {
    busyMessage.remove();
    addMessage(
      error.message || "The assistant could not answer right now. Please try again.",
      "assistant",
    );
  } finally {
    messages.removeAttribute("aria-busy");
    input.disabled = false;
    sendButton.disabled = false;
    input.focus();
  }
};

form.addEventListener("submit", (event) => {
  event.preventDefault();
  submitQuestion(input.value);
});

input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 140)}px`;
});

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    submitQuestion(input.value);
  }
});

suggestedQuestions.forEach((button) => {
  button.addEventListener("click", () => {
    input.value = button.dataset.question;
    input.focus();
  });
});

maximizeButton.addEventListener("click", () => {
  window.open(new URL("./", window.location.href), "_blank", "noopener");
});

closeButton.addEventListener("click", () => {
  window.parent.postMessage({ type: "portfolio-chat-close" }, window.location.origin);
});
