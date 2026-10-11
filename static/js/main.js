(() => {
  const groups = document.querySelectorAll(".reveal-group");
  if (!groups.length || !("IntersectionObserver" in window)) {
    groups.forEach((group) => group.classList.add("is-visible"));
    return;
  }

  groups.forEach((group) => {
    [...group.children].forEach((child, index) => child.style.setProperty("--i", index));
  });

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.15, rootMargin: "0px 0px -40px 0px" }
  );

  groups.forEach((group) => observer.observe(group));
})();

(() => {
  const toggle = document.querySelector("[data-nav-toggle]");
  const panel = document.querySelector("[data-nav-panel]");
  if (!toggle || !panel) return;

  toggle.addEventListener("click", () => {
    const open = !panel.classList.contains("is-open");
    panel.classList.toggle("is-open", open);
    toggle.setAttribute("aria-expanded", String(open));
  });
})();

(() => {
  document.querySelectorAll("[data-dropdown]").forEach((root) => {
    const toggle = root.querySelector("[data-dropdown-toggle]");
    const panel = root.querySelector("[data-dropdown-panel]");
    if (!toggle || !panel) return;

    const close = () => {
      panel.setAttribute("hidden", "");
      toggle.setAttribute("aria-expanded", "false");
    };

    toggle.addEventListener("click", (event) => {
      event.stopPropagation();
      const open = panel.hasAttribute("hidden");
      panel.toggleAttribute("hidden", !open);
      toggle.setAttribute("aria-expanded", String(open));
    });

    document.addEventListener("click", (event) => {
      if (!root.contains(event.target)) close();
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") close();
    });
  });
})();
