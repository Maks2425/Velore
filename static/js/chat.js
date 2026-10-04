(() => {
  const POLL_MS = 4000;

  const csrfToken = (root) => root.querySelector("input[name=csrfmiddlewaretoken]")?.value || "";

  async function postJson(url, payload, token) {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": token },
      body: JSON.stringify(payload || {}),
      credentials: "same-origin",
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || "Сталася помилка. Спробуйте ще раз.");
    return data;
  }

  function appendBubble(log, text, variant) {
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble chat-bubble--${variant}`;
    bubble.textContent = text;
    log.appendChild(bubble);
    log.scrollTop = log.scrollHeight;
    return bubble;
  }

  function setStatus(root, text) {
    const status = root.querySelector("[data-chat-status]");
    if (status) status.textContent = text || "";
  }

  function initAI(root) {
    const log = root.querySelector("[data-chat-log='ai']");
    const form = root.querySelector("[data-chat-form='ai']");
    const input = form.querySelector("textarea");
    const url = root.dataset.aiUrl;
    const history = [];

    appendBubble(log, "Привіт! Я помічник Velore. Питайте про бренди, розміри, замовлення чи магазин.", "bot");

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const text = input.value.trim();
      if (!text) return;
      input.value = "";
      appendBubble(log, text, "me");
      history.push({ role: "user", content: text });
      const pending = appendBubble(log, "Думаю…", "bot");
      pending.classList.add("is-pending");
      try {
        const data = await postJson(url, { messages: history.slice(-12) }, csrfToken(root));
        history.push({ role: "assistant", content: data.reply });
        pending.textContent = data.reply;
      } catch (error) {
        history.pop();
        pending.textContent = error.message;
        pending.classList.add("is-error");
      } finally {
        pending.classList.remove("is-pending");
        log.scrollTop = log.scrollHeight;
      }
    });
  }

  function createConsultantSession(root, log, form, threadId, selfSender) {
    const input = form.querySelector("textarea");
    const base = root.dataset.threadBase;
    let lastId = 0;
    let timer = null;
    let consultantName = null;

    function render(messages) {
      messages.forEach((message) => {
        const mine = message.sender === selfSender;
        appendBubble(log, message.body, mine ? "me" : "agent");
        lastId = Math.max(lastId, message.id);
      });
    }

    async function poll() {
      try {
        const response = await fetch(`${base}${threadId}/messages/?after=${lastId}`, { credentials: "same-origin" });
        if (!response.ok) throw new Error("forbidden");
        const data = await response.json();
        render(data.messages);
        if (data.consultant && data.consultant !== consultantName) {
          consultantName = data.consultant;
          setStatus(root, `Консультант: ${consultantName}`);
        }
        if (!data.is_open) setStatus(root, "Чат закрито");
      } catch (error) {
        setStatus(root, "Немає зв'язку. Оновлюємо…");
      }
    }

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const text = input.value.trim();
      if (!text) return;
      input.value = "";
      try {
        await postJson(`${base}${threadId}/send/`, { body: text }, csrfToken(root));
        await poll();
      } catch (error) {
        appendBubble(log, error.message, "error");
      }
    });

    poll();
    timer = setInterval(poll, POLL_MS);
    return () => clearInterval(timer);
  }

  function initConsultant(root) {
    const log = root.querySelector("[data-chat-log='agent']");
    const form = root.querySelector("[data-chat-form='agent']");
    const openUrl = root.dataset.openUrl;
    let stopPolling = null;
    let started = false;

    async function start() {
      if (started) return;
      started = true;
      setStatus(root, "Під'єднуємо консультанта…");
      try {
        const data = await postJson(openUrl, {}, csrfToken(root));
        setStatus(root, "Очікуйте відповіді консультанта");
        stopPolling = createConsultantSession(root, log, form, data.thread_id, "customer");
      } catch (error) {
        started = false;
        setStatus(root, error.message);
      }
    }

    root.stop = () => stopPolling && stopPolling();
    return start;
  }

  function initStaffThread(root) {
    const log = root.querySelector("[data-chat-log='agent']");
    const form = root.querySelector("[data-chat-form='agent']");
    createConsultantSession(root, log, form, root.dataset.threadId, "consultant");
  }

  document.querySelectorAll("[data-chat]").forEach((root) => {
    if (root.dataset.mode === "staff") {
      initStaffThread(root);
      return;
    }

    const toggles = root.querySelectorAll("[data-chat-toggle]");
    const panel = root.querySelector("[data-chat-panel]");
    const tabs = root.querySelectorAll("[data-chat-tab]");
    const views = root.querySelectorAll("[data-chat-view]");
    const startConsultant = root.dataset.authenticated === "true" ? initConsultant(root) : null;

    initAI(root);

    function show(name) {
      views.forEach((view) => { view.hidden = view.dataset.chatView !== name; });
      tabs.forEach((tab) => {
        const active = tab.dataset.chatTab === name;
        tab.setAttribute("aria-selected", String(active));
      });
      if (name === "agent" && startConsultant) startConsultant();
    }

    toggles.forEach((toggle) => toggle.addEventListener("click", () => {
      const open = panel.hasAttribute("hidden");
      panel.toggleAttribute("hidden", !open);
      root.querySelector(".chat__toggle")?.setAttribute("aria-expanded", String(open));
    }));

    tabs.forEach((tab) => tab.addEventListener("click", () => show(tab.dataset.chatTab)));
  });
})();
