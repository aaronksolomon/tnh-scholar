(function () {
  const data = window.FACSIMILE_DATA;
  const image = document.querySelector("[data-page-image]");
  const regionsEl = document.querySelector("[data-regions]");
  const detailEl = document.querySelector("[data-detail]");
  const contextMenu = document.querySelector("[data-context-menu]");
  const labelsButton = document.querySelector("[data-toggle-labels]");
  const modeButtons = document.querySelectorAll("[data-mode]");

  let selectedRegionId = null;
  let displayMode = "both";

  function renderDetail(region) {
    if (!region) {
      detailEl.innerHTML = [
        '<p class="empty">Select a region on the page to inspect its Vietnamese source text and translation segments.</p>',
        '<p class="empty">Right-click a region to switch the panel between Vietnamese, English, or both views.</p>',
      ].join("");
      return;
    }

    const segments = region.segments
      .map((segment) => {
        const parts = [];
        if (displayMode !== "en") {
          parts.push(`<dt>Vietnamese</dt><dd>${escapeHtml(segment.vi)}</dd>`);
        }
        if (displayMode !== "vi") {
          parts.push(`<dt>English</dt><dd>${escapeHtml(segment.en)}</dd>`);
        }
        return `<div class="segment"><dl>${parts.join("")}</dl></div>`;
      })
      .join("");

    detailEl.innerHTML = `
      <article class="detail-card">
        <h2>${escapeHtml(region.label)}</h2>
        <div class="tag">${escapeHtml(region.type)}</div>
        ${segments}
      </article>
    `;
  }

  function setActiveRegion(id) {
    selectedRegionId = id;
    document.querySelectorAll(".region").forEach((el) => {
      el.classList.toggle("is-active", el.dataset.regionId === id);
    });
    const region = data.regions.find((item) => item.id === id) || null;
    renderDetail(region);
  }

  function setDisplayMode(mode) {
    displayMode = mode;
    modeButtons.forEach((button) => {
      button.classList.toggle("is-active", button.dataset.mode === mode);
    });
    if (selectedRegionId) {
      setActiveRegion(selectedRegionId);
    } else {
      renderDetail(null);
    }
  }

  function hideContextMenu() {
    contextMenu.style.display = "none";
  }

  function placeContextMenu(event, regionId) {
    contextMenu.style.left = `${event.clientX}px`;
    contextMenu.style.top = `${event.clientY}px`;
    contextMenu.dataset.regionId = regionId;
    contextMenu.style.display = "block";
  }

  function renderRegions() {
    const { width, height } = data.page;
    regionsEl.innerHTML = "";

    data.regions.forEach((region) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `region region--${region.type}`;
      button.dataset.regionId = region.id;
      button.style.left = `${(region.bbox.x / width) * 100}%`;
      button.style.top = `${(region.bbox.y / height) * 100}%`;
      button.style.width = `${(region.bbox.w / width) * 100}%`;
      button.style.height = `${(region.bbox.h / height) * 100}%`;
      button.setAttribute("aria-label", region.label);
      button.innerHTML = `<span class="region-label">${escapeHtml(region.label)}</span>`;
      button.addEventListener("click", () => {
        hideContextMenu();
        setActiveRegion(region.id);
      });
      button.addEventListener("contextmenu", (event) => {
        event.preventDefault();
        setActiveRegion(region.id);
        placeContextMenu(event, region.id);
      });
      regionsEl.appendChild(button);
    });
  }

  function escapeHtml(value) {
    return value
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;");
  }

  image.src = data.page.imageSrc;
  image.alt = data.page.title;
  renderRegions();
  renderDetail(null);
  setDisplayMode("both");

  labelsButton.addEventListener("click", () => {
    labelsButton.classList.toggle("is-active");
    regionsEl.classList.toggle("show-labels");
  });

  modeButtons.forEach((button) => {
    button.addEventListener("click", () => {
      setDisplayMode(button.dataset.mode);
      hideContextMenu();
    });
  });

  contextMenu.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      setDisplayMode(button.dataset.mode);
      hideContextMenu();
    });
  });

  document.addEventListener("click", (event) => {
    if (!contextMenu.contains(event.target)) {
      hideContextMenu();
    }
  });

  document.addEventListener("scroll", hideContextMenu, true);
})();
