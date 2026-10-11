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
