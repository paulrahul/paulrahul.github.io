const form = document.querySelector("[data-chat-form]");
const input = document.querySelector("[data-chat-input]");
const messages = document.querySelector("[data-messages]");
const suggestions = document.querySelector(".suggestions");
const suggestedQuestions = document.querySelectorAll("[data-question]");
const maximizeButton = document.querySelector("[data-maximize-chat]");
const closeButton = document.querySelector("[data-close-chat]");

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

const addMessage = (text, type) => {
  const message = document.createElement("article");
  message.className = `message message--${type}`;

  if (type === "assistant") {
    message.innerHTML = `
      <span class="message-avatar" aria-hidden="true">RP</span>
      <div class="message-content">
        <p class="message-label">Portfolio assistant</p>
        <div class="bubble"><p>${escapeHtml(text)}</p></div>
        <p class="message-time">Preview response</p>
      </div>
    `;
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

const submitQuestion = (question) => {
  const value = question.trim();
  if (!value) return;

  suggestions.hidden = true;
  addMessage(value, "user");
  input.value = "";
  input.style.height = "auto";

  window.setTimeout(() => {
    addMessage(
      "This is a UI-only preview. Once the RAG service is connected, this space will return an answer grounded in Rahul’s portfolio.",
      "assistant",
    );
  }, 350);
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
