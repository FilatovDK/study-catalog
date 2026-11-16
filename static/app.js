(() => {
  const progressKey = "study-catalog-progress-v1";
  const favoritesKey = "study-catalog-favorites-v1";

  function readStored(key, fallback) {
    try {
      const value = JSON.parse(localStorage.getItem(key));
      return value && typeof value === "object" ? value : fallback;
    } catch (_) {
      return fallback;
    }
  }

  function writeStored(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch (_) { /* private mode */ }
  }

  const progress = readStored(progressKey, {});
  const favorites = new Set(Array.isArray(readStored(favoritesKey, [])) ? readStored(favoritesKey, []) : []);

  function completedCount(slug, total) {
    let count = 0;
    for (let number = 1; number <= total; number += 1) {
      if (progress[`${slug}:${number}`]) count += 1;
    }
    return count;
  }

  function updateProgress() {
    document.querySelectorAll("[data-progress-count]").forEach((element) => {
      const slug = element.dataset.progressCount;
      const total = Number(element.dataset.total || element.textContent.split("/")[1]?.trim() || 3);
      element.dataset.total = String(total);
      const count = completedCount(slug, total);
      element.textContent = `${count} / ${total}`;
    });
    document.querySelectorAll("[data-progress-bar]").forEach((element) => {
      const slug = element.dataset.progressBar;
      const countElement = document.querySelector(`[data-progress-count="${slug}"]`);
      const total = Number(countElement?.dataset.total || 3);
      element.style.width = `${Math.round((completedCount(slug, total) / total) * 100)}%`;
    });
    document.querySelectorAll("[data-lesson-check]").forEach((element) => {
      element.classList.toggle("is-done", Boolean(progress[element.dataset.lessonCheck]));
      element.textContent = progress[element.dataset.lessonCheck] ? "✓" : "";
    });
    document.querySelectorAll("[data-completion-badge]").forEach((element) => {
      element.hidden = !progress[element.dataset.completionBadge];
    });
    document.querySelectorAll("[data-progress-course]").forEach((card) => {
      const slug = card.dataset.progressCourse;
      const total = Number(card.dataset.lessonTotal);
      const link = card.querySelector("[data-continue]");
      if (!link) return;
      const next = Array.from({ length: total }, (_, index) => index + 1).find((number) => !progress[`${slug}:${number}`]);
      link.href = next ? `/courses/${slug}/lessons/${next}` : `/courses/${slug}`;
      link.textContent = next === 1 ? "Начать курс →" : next ? "Продолжить с урока " + next + " →" : "Повторить курс →";
    });
    const totalElement = document.getElementById("total-completed");
    if (totalElement) {
      totalElement.textContent = String(document.querySelectorAll("[data-progress-course]").length
        ? Array.from(document.querySelectorAll("[data-progress-course]")).reduce((sum, card) => sum + completedCount(card.dataset.progressCourse, Number(card.dataset.lessonTotal)), 0)
        : 0);
    }
  }

  function updateFavorites() {
    document.querySelectorAll("[data-favorite]").forEach((button) => {
      const selected = favorites.has(button.dataset.favorite);
      button.setAttribute("aria-pressed", String(selected));
      if (button.classList.contains("favorite-button")) {
        button.textContent = selected ? "★" : "☆";
        button.setAttribute("aria-label", selected ? "Удалить из избранного" : "Добавить в избранное");
      } else {
        button.textContent = selected ? "★ В избранном" : "☆ В избранное";
      }
    });
  }

  document.querySelectorAll("[data-favorite]").forEach((button) => {
    button.addEventListener("click", () => {
      const slug = button.dataset.favorite;
      if (favorites.has(slug)) favorites.delete(slug); else favorites.add(slug);
      writeStored(favoritesKey, Array.from(favorites));
      updateFavorites();
      applyFilters();
    });
  });

  const search = document.getElementById("course-search");
  const categoryButtons = Array.from(document.querySelectorAll("[data-filter]"));
  const favoriteFilter = document.querySelector("[data-filter-favorites]");
  let category = "all";
  let favoritesOnly = false;

  function applyFilters() {
    const cards = Array.from(document.querySelectorAll("[data-course-card]"));
    if (!cards.length) return;
    const query = (search?.value || "").trim().toLocaleLowerCase("ru");
    let shown = 0;
    cards.forEach((card) => {
      const matches = (category === "all" || card.dataset.category === category)
        && (!favoritesOnly || favorites.has(card.dataset.slug))
        && card.dataset.search.includes(query);
      card.hidden = !matches;
      if (matches) shown += 1;
    });
    document.getElementById("empty-state").hidden = shown !== 0;
    document.getElementById("results-line").textContent = `Показано ${shown} из ${cards.length} курсов`;
  }

  search?.addEventListener("input", applyFilters);
  categoryButtons.forEach((button) => button.addEventListener("click", () => {
    category = button.dataset.filter;
    categoryButtons.forEach((item) => {
      const selected = item === button;
      item.classList.toggle("is-active", selected);
      item.setAttribute("aria-pressed", String(selected));
    });
    applyFilters();
  }));
  favoriteFilter?.addEventListener("click", () => {
    favoritesOnly = !favoritesOnly;
    favoriteFilter.classList.toggle("is-active", favoritesOnly);
    favoriteFilter.setAttribute("aria-pressed", String(favoritesOnly));
    applyFilters();
  });
  document.getElementById("reset-filters")?.addEventListener("click", () => {
    search.value = "";
    categoryButtons.find((button) => button.dataset.filter === "all")?.click();
    if (favoritesOnly) favoriteFilter.click();
    search.focus();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "/" && search && !/INPUT|TEXTAREA/.test(document.activeElement.tagName)) {
      event.preventDefault();
      search.focus();
    }
  });

  document.querySelectorAll("[data-quiz]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const feedback = form.querySelector(".quiz-feedback");
      const selected = form.querySelector('input[name="answer"]:checked');
      feedback.className = "quiz-feedback";
      if (!selected) {
        feedback.classList.add("error");
        feedback.textContent = "Сначала выбери один вариант ответа.";
      } else if (Number(selected.value) === Number(form.dataset.correct)) {
        progress[form.dataset.quiz] = true;
        writeStored(progressKey, progress);
        feedback.classList.add("success");
        feedback.textContent = "Верно! " + form.dataset.explanation;
        updateProgress();
      } else {
        feedback.classList.add("error");
        feedback.textContent = "Пока неверно. Попробуй ещё раз.";
      }
    });
  });

  const profileLessons = document.querySelector('[data-profile-stat="lessons"]');
  if (profileLessons) {
    const knownCourses = new Set(["programming", "databases", "networks", "systems"]);
    const completed = Object.entries(progress).filter(([key, done]) =>
      done && knownCourses.has(key.split(":")[0]) && /^\w+:\d+$/.test(key)
    ).length;
    profileLessons.textContent = String(completed);
    document.querySelector('[data-profile-stat="favorites"]').textContent = String(favorites.size);
    document.querySelector('[data-profile-stat="progress"]').textContent = `${completed} / 12`;
    document.querySelector("[data-profile-progress]").style.width = `${Math.min(100, Math.round(completed / 12 * 100))}%`;
  }

  const bio = document.querySelector('textarea[name="bio"]');
  bio?.addEventListener("input", () => {
    document.querySelector("[data-bio-count]").textContent = String(bio.value.length);
  });

  const avatarInput = document.getElementById("avatar-file");
  let previewUrl = null;
  avatarInput?.addEventListener("change", () => {
    const file = avatarInput.files?.[0];
    const label = document.querySelector("[data-avatar-file-name]");
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    if (!file) {
      label.textContent = "JPG, PNG или WebP · до 2 МБ";
      return;
    }
    label.textContent = file.size > 2 * 1024 * 1024 ? "Файл больше 2 МБ — выбери другое фото" : file.name;
    previewUrl = URL.createObjectURL(file);
    const preview = document.querySelector("[data-avatar-preview]");
    preview.src = previewUrl;
    preview.hidden = false;
    document.querySelector("[data-avatar-initial]").hidden = true;
  });

  updateFavorites();
  updateProgress();
  applyFilters();
})();
