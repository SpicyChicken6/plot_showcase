import { figureCatalog, siteMeta } from "./figures.js";

const analysisFilters = [
  "All analyses",
  ...new Set(figureCatalog.map((figure) => figure.analysisType)),
];

const state = {
  searchTerm: "",
  analysisFilter: "All analyses",
  selectedId: figureCatalog[0]?.id ?? null,
};

let inspectorLoadId = 0;

const elements = {
  heroText: document.querySelector("#heroText"),
  heroStats: document.querySelector("#heroStats"),
  searchInput: document.querySelector("#searchInput"),
  analysisChips: document.querySelector("#analysisChips"),
  figureGrid: document.querySelector("#figureGrid"),
  inspector: document.querySelector("#inspector"),
  authoringGuide: document.querySelector("#authoringGuide"),
};

init();

function init() {
  renderHero();
  renderAnalysisChips();
  renderAuthoringGuide();
  attachEvents();
  renderPage();
}

function attachEvents() {
  elements.searchInput.addEventListener("input", (event) => {
    state.searchTerm = event.target.value.trim().toLowerCase();
    renderPage();
  });

  elements.analysisChips.addEventListener("click", (event) => {
    const chip = event.target.closest("[data-analysis-filter]");
    if (!chip) {
      return;
    }

    state.analysisFilter = chip.dataset.analysisFilter;
    renderPage();
  });

  elements.figureGrid.addEventListener("click", (event) => {
    const card = event.target.closest("[data-figure-id]");
    if (!card) {
      return;
    }

    state.selectedId = card.dataset.figureId;
    renderPage();
  });

  elements.figureGrid.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" && event.key !== " ") {
      return;
    }

    const card = event.target.closest("[data-figure-id]");
    if (!card) {
      return;
    }

    event.preventDefault();
    state.selectedId = card.dataset.figureId;
    renderPage();
  });
}

function renderPage() {
  const filteredFigures = getFilteredFigures();
  ensureSelection(filteredFigures);
  renderHeroStats(filteredFigures.length);
  renderAnalysisChips();
  renderFigureGrid(filteredFigures);
  renderInspector();
}

function renderHero() {
  elements.heroText.innerHTML = `
    <p class="section-kicker">Showcase Site</p>
    <h1>${escapeHtml(siteMeta.title)}</h1>
    <p class="hero-subtitle">${escapeHtml(siteMeta.subtitle)}</p>
    <p class="hero-intro">${escapeHtml(siteMeta.intro)}</p>
    <div class="callout-row">
      ${siteMeta.callouts
        .map((callout) => `<span class="callout-pill">${escapeHtml(callout)}</span>`)
        .join("")}
    </div>
  `;
}

function renderHeroStats(visibleCount) {
  const totalFigures = figureCatalog.length;
  const analysisCount = new Set(
    figureCatalog.map((figure) => figure.analysisType),
  ).size;
  const omicsCount = new Set(figureCatalog.map((figure) => figure.omicsDomain)).size;

  const statCards = [
    { label: "Total figures", value: String(totalFigures).padStart(2, "0") },
    { label: "Analysis groups", value: String(analysisCount).padStart(2, "0") },
    { label: "Omics domains", value: String(omicsCount).padStart(2, "0") },
    { label: "Visible now", value: String(visibleCount).padStart(2, "0") },
  ];

  elements.heroStats.innerHTML = statCards
    .map(
      (card) => `
        <article class="stat-card">
          <span class="stat-value">${card.value}</span>
          <span class="stat-label">${card.label}</span>
        </article>
      `,
    )
    .join("");
}

function renderAnalysisChips() {
  elements.analysisChips.innerHTML = analysisFilters
    .map((analysisType) => {
      const isActive = analysisType === state.analysisFilter;
      return `
        <button
          type="button"
          class="chip ${isActive ? "is-active" : ""}"
          data-analysis-filter="${escapeHtml(analysisType)}"
        >
          ${escapeHtml(analysisType)}
        </button>
      `;
    })
    .join("");
}

function renderFigureGrid(filteredFigures) {
  if (!filteredFigures.length) {
    elements.figureGrid.innerHTML = `
      <div class="empty-state">
        <h3>No figures match this filter.</h3>
        <p>Try a broader search term or switch back to a wider analysis category.</p>
      </div>
    `;
    return;
  }

  elements.figureGrid.innerHTML = filteredFigures
    .map((figure, index) => {
      const isSelected = figure.id === state.selectedId;
      return `
        <article
          class="figure-card ${isSelected ? "is-selected" : ""}"
          data-figure-id="${escapeHtml(figure.id)}"
          tabindex="0"
          style="--accent:${figure.accent}; --entry-delay:${index * 60}ms;"
        >
          <div class="card-topline">
            <span class="eyebrow">${escapeHtml(figure.analysisType)}</span>
            <span class="domain-pill">${escapeHtml(figure.omicsDomain)}</span>
          </div>
          <h3>${escapeHtml(figure.title)}</h3>
          <p>${escapeHtml(figure.summary)}</p>
          <div class="tag-row">
            ${figure.tags
              .map((tag) => `<span class="tag-pill">${escapeHtml(tag)}</span>`)
              .join("")}
          </div>
          <div class="card-footer">
            <span>${escapeHtml(figure.figureType)}</span>
            <span>${escapeHtml(figure.datasetLabel)}</span>
          </div>
        </article>
      `;
    })
    .join("");
}

function renderInspector() {
  const selectedFigure = figureCatalog.find((figure) => figure.id === state.selectedId);

  if (!selectedFigure) {
    elements.inspector.innerHTML = `
      <div class="status-surface">
        <h3>Select a figure</h3>
        <p>Choose a card on the left to render its plot, inspect the code, and preview the attached test dataset.</p>
      </div>
    `;
    return;
  }

  const datasetUrl = resolveAsset(selectedFigure.datasetPath);
  const codeUrl = resolveAsset(selectedFigure.codePath ?? selectedFigure.rendererPath);

  elements.inspector.innerHTML = `
    <article class="inspector-shell" style="--accent:${selectedFigure.accent};">
      <header class="inspector-header">
        <div class="inspector-topline">
          <span class="eyebrow">${escapeHtml(selectedFigure.analysisType)}</span>
          <span class="domain-pill">${escapeHtml(selectedFigure.omicsDomain)}</span>
        </div>
        <h3>${escapeHtml(selectedFigure.title)}</h3>
        <p class="inspector-summary">${escapeHtml(selectedFigure.narrative)}</p>
        <p class="inspector-caption">${escapeHtml(selectedFigure.caption)}</p>
        <div class="resource-row">
          <a class="resource-link" href="${datasetUrl}" download>Download dataset</a>
          <a class="resource-link" href="${codeUrl}" download>Download code</a>
        </div>
      </header>

      <section class="inspector-section">
        <div class="section-header">
          <h4>Live figure</h4>
          <span class="section-meta">${escapeHtml(selectedFigure.figureType)}</span>
        </div>
        <div id="plotMount" class="plot-stage">
          <div class="status-surface compact">
            <div class="loading-dot"></div>
            <p>Rendering figure from attached demo data...</p>
          </div>
        </div>
      </section>

      <section class="inspector-section">
        <div class="section-header">
          <h4>Figure notes</h4>
          <span class="section-meta">${escapeHtml(selectedFigure.datasetLabel)}</span>
        </div>
        <div class="note-grid">
          ${selectedFigure.notes
            .map((note) => `<div class="note-card">${escapeHtml(note)}</div>`)
            .join("")}
        </div>
      </section>

      <section class="inspector-section">
        <div class="section-header">
          <h4>Source code</h4>
          <span class="section-meta">${escapeHtml(selectedFigure.codeLanguage)}</span>
        </div>
        <pre class="code-block"><code id="codeViewer">Loading source...</code></pre>
      </section>

      <section class="inspector-section">
        <div class="section-header">
          <h4>Dataset preview</h4>
          <span class="section-meta">Attached demo input</span>
        </div>
        <div id="datasetPreview" class="dataset-preview">
          <div class="status-surface compact">
            <div class="loading-dot"></div>
            <p>Inspecting dataset structure...</p>
          </div>
        </div>
      </section>
    </article>
  `;

  hydrateInspector(selectedFigure);
}

async function hydrateInspector(figure) {
  const loadId = ++inspectorLoadId;
  const plotMount = elements.inspector.querySelector("#plotMount");
  const codeViewer = elements.inspector.querySelector("#codeViewer");
  const datasetPreview = elements.inspector.querySelector("#datasetPreview");

  try {
    const [dataset, rendererModule, codeText] = await Promise.all([
      loadDataset(figure.datasetPath),
      import(resolveAsset(figure.rendererPath)),
      fetchText(figure.codePath ?? figure.rendererPath),
    ]);

    if (loadId !== inspectorLoadId) {
      return;
    }

    if (!window.Plotly) {
      throw new Error("Plotly did not load.");
    }

    await rendererModule.renderFigure(plotMount, dataset, {
      Plotly: window.Plotly,
      figure,
    });

    if (loadId !== inspectorLoadId) {
      return;
    }

    codeViewer.textContent = codeText;
    datasetPreview.innerHTML = createDatasetPreview(dataset);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";

    plotMount.innerHTML = `
      <div class="status-surface error">
        <h4>Could not render this figure</h4>
        <p>${escapeHtml(message)}</p>
      </div>
    `;

    codeViewer.textContent = `Failed to load source code.\n\n${message}`;
    datasetPreview.innerHTML = `
      <div class="status-surface error">
        <h4>Dataset preview unavailable</h4>
        <p>${escapeHtml(message)}</p>
      </div>
    `;
  }
}

async function loadDataset(relativePath) {
  const response = await fetch(resolveAsset(relativePath));
  if (!response.ok) {
    throw new Error(`Failed to load dataset: ${response.status}`);
  }

  const extension = relativePath.split(".").pop()?.toLowerCase();

  if (extension === "json") {
    return response.json();
  }

  const rawText = await response.text();

  if (extension === "csv" || extension === "tsv") {
    if (!window.Papa) {
      throw new Error("PapaParse did not load.");
    }

    const parsed = window.Papa.parse(rawText, {
      delimiter: extension === "tsv" ? "\t" : ",",
      dynamicTyping: true,
      header: true,
      skipEmptyLines: true,
    });

    if (parsed.errors.length) {
      throw new Error(parsed.errors[0].message);
    }

    return parsed.data;
  }

  return rawText;
}

async function fetchText(relativePath) {
  const response = await fetch(resolveAsset(relativePath));
  if (!response.ok) {
    throw new Error(`Failed to load source code: ${response.status}`);
  }

  return response.text();
}

function resolveAsset(relativePath) {
  return new URL(relativePath, import.meta.url).href;
}

function createDatasetPreview(dataset) {
  if (Array.isArray(dataset) && dataset.length && typeof dataset[0] === "object") {
    return renderTabularPreview(dataset);
  }

  if (isMatrixDataset(dataset)) {
    return renderMatrixPreview(dataset);
  }

  return `
    <div class="status-surface compact">
      <p>This dataset format is valid, but the previewer does not have a tailored table for it yet.</p>
    </div>
  `;
}

function renderTabularPreview(rows) {
  const columns = Object.keys(rows[0] ?? {}).slice(0, 6);
  const visibleRows = rows.slice(0, 6);

  return `
    <div class="dataset-meta-row">
      <span class="dataset-pill">${rows.length} rows</span>
      <span class="dataset-pill">${columns.length} columns shown</span>
    </div>
    <div class="table-shell">
      <table>
        <thead>
          <tr>${columns.map((column) => `<th>${escapeHtml(column)}</th>`).join("")}</tr>
        </thead>
        <tbody>
          ${visibleRows
            .map(
              (row) => `
                <tr>
                  ${columns
                    .map((column) => `<td>${escapeHtml(formatCell(row[column]))}</td>`)
                    .join("")}
                </tr>
              `,
            )
            .join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderMatrixPreview(dataset) {
  const sampleSlice = dataset.samples.slice(0, 4);
  const featureSlice = dataset.features.slice(0, 4);

  return `
    <div class="dataset-meta-row">
      <span class="dataset-pill">${dataset.features.length} features</span>
      <span class="dataset-pill">${dataset.samples.length} samples</span>
      <span class="dataset-pill">${dataset.values.length} matrix rows</span>
    </div>
    <div class="table-shell">
      <table>
        <thead>
          <tr>
            <th>Feature</th>
            ${sampleSlice.map((sample) => `<th>${escapeHtml(sample)}</th>`).join("")}
          </tr>
        </thead>
        <tbody>
          ${featureSlice
            .map((feature, rowIndex) => {
              const cells = sampleSlice
                .map((sample, columnIndex) => {
                  const value = dataset.values[rowIndex]?.[columnIndex];
                  return `<td>${escapeHtml(formatCell(value))}</td>`;
                })
                .join("");
              return `<tr><th>${escapeHtml(feature)}</th>${cells}</tr>`;
            })
            .join("")}
        </tbody>
      </table>
    </div>
  `;
}

function isMatrixDataset(dataset) {
  return (
    Boolean(dataset) &&
    !Array.isArray(dataset) &&
    Array.isArray(dataset.features) &&
    Array.isArray(dataset.samples) &&
    Array.isArray(dataset.values)
  );
}

function renderAuthoringGuide() {
  const steps = [
    {
      title: "1. Add a small test dataset",
      detail:
        "Place a CSV, TSV, or JSON file in content/datasets so each figure can be regenerated quickly on GitHub Pages.",
      path: "content/datasets/",
    },
    {
      title: "2. Add a browser renderer",
      detail:
        "Create a module in content/renderers that exports renderFigure(container, dataset, context).",
      path: "content/renderers/",
    },
    {
      title: "3. Register the figure",
      detail:
        "Add one metadata object in assets/figures.js to link the card, live preview, dataset, and displayed source code.",
      path: "assets/figures.js",
    },
  ];

  elements.authoringGuide.innerHTML = steps
    .map(
      (step) => `
        <article class="authoring-card">
          <h3>${escapeHtml(step.title)}</h3>
          <p>${escapeHtml(step.detail)}</p>
          <code>${escapeHtml(step.path)}</code>
        </article>
      `,
    )
    .join("");
}

function getFilteredFigures() {
  return figureCatalog.filter((figure) => {
    const matchesAnalysis =
      state.analysisFilter === "All analyses" ||
      figure.analysisType === state.analysisFilter;

    const searchCorpus = [
      figure.title,
      figure.summary,
      figure.analysisType,
      figure.omicsDomain,
      figure.figureType,
      ...figure.tags,
    ]
      .join(" ")
      .toLowerCase();

    const matchesSearch =
      !state.searchTerm || searchCorpus.includes(state.searchTerm);

    return matchesAnalysis && matchesSearch;
  });
}

function ensureSelection(filteredFigures) {
  if (!filteredFigures.length) {
    state.selectedId = null;
    return;
  }

  const stillVisible = filteredFigures.some((figure) => figure.id === state.selectedId);
  if (!stillVisible) {
    state.selectedId = filteredFigures[0].id;
  }
}

function formatCell(value) {
  if (typeof value === "number") {
    return Number.isInteger(value) ? String(value) : value.toFixed(3);
  }

  if (value === null || value === undefined || value === "") {
    return "NA";
  }

  return String(value);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
