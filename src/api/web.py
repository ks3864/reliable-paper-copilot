"""Lightweight web UI for the Reliable Scientific Paper Copilot."""

from textwrap import dedent

WEB_UI_HTML = dedent(
    """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>Reliable Scientific Paper Copilot</title>
      <style>
        :root {
          color-scheme: light;
          font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          background: #f3f4f6;
          color: #111827;
        }
        body {
          margin: 0;
          padding: 32px 16px;
          background: linear-gradient(180deg, #f9fafb 0%, #eef2ff 100%);
        }
        .container {
          max-width: 880px;
          margin: 0 auto;
        }
        .hero, .panel {
          background: rgba(255, 255, 255, 0.92);
          border: 1px solid #e5e7eb;
          border-radius: 16px;
          box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
        }
        .hero {
          padding: 28px;
          margin-bottom: 20px;
        }
        .panel {
          padding: 24px;
          margin-bottom: 16px;
        }
        h1, h2 {
          margin-top: 0;
        }
        p {
          line-height: 1.5;
        }
        form {
          display: grid;
          gap: 12px;
        }
        label {
          font-weight: 600;
        }
        input, textarea, select, button {
          font: inherit;
        }
        input[type="file"], input[type="text"], textarea, select {
          width: 100%;
          box-sizing: border-box;
          border: 1px solid #d1d5db;
          border-radius: 10px;
          padding: 12px;
          background: white;
        }
        textarea {
          min-height: 120px;
          resize: vertical;
        }
        button {
          width: fit-content;
          border: 0;
          border-radius: 999px;
          padding: 10px 16px;
          background: #4f46e5;
          color: white;
          font-weight: 600;
          cursor: pointer;
        }
        button:disabled {
          opacity: 0.6;
          cursor: wait;
        }
        .muted {
          color: #6b7280;
        }
        .status {
          min-height: 24px;
          font-weight: 600;
        }
        .error {
          color: #b91c1c;
        }
        .success {
          color: #047857;
        }
        .answer {
          background: #f9fafb;
          border-radius: 12px;
          padding: 16px;
          border: 1px solid #e5e7eb;
          line-height: 1.7;
        }
        .answer-line {
          margin-bottom: 12px;
        }
        .answer-line:last-child {
          margin-bottom: 0;
        }
        .citation-anchor {
          margin-left: 6px;
          border: 0;
          border-radius: 999px;
          padding: 2px 8px;
          background: #e0e7ff;
          color: #3730a3;
          cursor: pointer;
          font-size: 0.8rem;
          font-weight: 700;
        }
        .citation-anchor:hover {
          background: #c7d2fe;
        }
        .control-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
          gap: 12px;
        }
        input[type="number"] {
          width: 100%;
          box-sizing: border-box;
          border: 1px solid #d1d5db;
          border-radius: 10px;
          padding: 12px;
          background: white;
        }
        .score-table {
          width: 100%;
          border-collapse: collapse;
          margin-top: 12px;
          font-size: 0.95rem;
        }
        .score-table th,
        .score-table td {
          border-bottom: 1px solid #e5e7eb;
          padding: 10px 8px;
          text-align: left;
          vertical-align: top;
        }
        .score-table th {
          background: #f9fafb;
          font-weight: 600;
        }
        .score-table code {
          display: inline-block;
          margin-top: 4px;
        }
        .evidence-list {
          display: grid;
          gap: 12px;
          margin-top: 12px;
        }
        .evidence-card {
          background: #f9fafb;
          border: 1px solid #e5e7eb;
          border-radius: 12px;
          padding: 12px;
          scroll-margin-top: 20px;
          transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
        }
        .evidence-card.is-highlighted {
          border-color: #4f46e5;
          background: #eef2ff;
          box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.14);
        }
        .evidence-card-header {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          margin-bottom: 8px;
          align-items: center;
        }
        .evidence-snippet {
          white-space: pre-wrap;
          margin: 0;
          line-height: 1.5;
        }
        .paper-details {
          margin-top: 16px;
          padding: 16px;
          border-radius: 12px;
          border: 1px solid #e5e7eb;
          background: #f9fafb;
        }
        .detail-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
          gap: 12px;
          margin-bottom: 16px;
        }
        .detail-card {
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 10px;
          padding: 12px;
        }
        .detail-card h4 {
          margin: 0 0 8px 0;
          font-size: 0.95rem;
        }
        .detail-card p,
        .detail-card li {
          margin: 0;
          font-size: 0.95rem;
        }
        .actions-row {
          display: flex;
          flex-wrap: wrap;
          gap: 10px;
          margin: 16px 0 0;
        }
        .paper-picker {
          display: grid;
          gap: 10px;
        }
        .paper-picker-meta {
          font-size: 0.9rem;
          color: #6b7280;
        }
        .metadata-editor {
          margin-top: 16px;
          padding: 16px;
          border-radius: 12px;
          border: 1px solid #e5e7eb;
          background: white;
        }
        .metadata-editor textarea {
          min-height: 96px;
        }
        .button-secondary {
          background: #eef2ff;
          color: #3730a3;
          border: 1px solid #c7d2fe;
        }
        .button-secondary:hover {
          background: #e0e7ff;
        }
        .brief-preview {
          margin-top: 14px;
          padding: 12px;
          background: #111827;
          color: #f9fafb;
          border-radius: 10px;
          overflow-x: auto;
          font-size: 0.85rem;
          line-height: 1.45;
          white-space: pre-wrap;
        }
        .detail-list {
          margin: 8px 0 0 0;
          padding-left: 18px;
        }
        .history-list {
          display: grid;
          gap: 10px;
          margin-top: 8px;
        }
        .history-item {
          border: 1px solid #e5e7eb;
          border-radius: 10px;
          padding: 10px;
          background: #f9fafb;
        }
        .history-item p {
          margin: 0;
        }
        .history-item-meta {
          margin-top: 6px;
          font-size: 0.9rem;
          color: #6b7280;
        }
        .history-item-actions {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          margin-top: 8px;
        }
        .mini-button {
          padding: 6px 10px;
          font-size: 0.85rem;
        }
        .chips {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
        }
        .chip {
          display: inline-flex;
          align-items: center;
          border-radius: 999px;
          padding: 4px 10px;
          font-size: 0.85rem;
          background: #e0e7ff;
          color: #3730a3;
        }
        ul {
          padding-left: 20px;
        }
        code {
          background: #eef2ff;
          padding: 2px 6px;
          border-radius: 6px;
        }
      </style>
    </head>
    <body>
      <main class="container">
        <section class="hero">
          <h1>Reliable Scientific Paper Copilot</h1>
          <p>
            Upload a paper, then ask grounded questions against the processed chunks and retrieval index.
            This lightweight UI talks directly to the existing FastAPI endpoints.
          </p>
          <p class="muted">API status: <span id="health-status">Checking...</span></p>
        </section>

        <section class="panel">
          <h2>1. Upload a PDF</h2>
          <form id="upload-form">
            <div>
              <label for="paper-file">Paper PDF</label>
              <input id="paper-file" name="file" type="file" accept="application/pdf" required />
            </div>
            <div class="control-grid">
              <div>
                <label for="upload-source-label">Source label (optional)</label>
                <input id="upload-source-label" name="source_label" type="text" placeholder="arXiv PDF export" />
              </div>
              <div>
                <label for="upload-source-url">Source URL (optional)</label>
                <input id="upload-source-url" name="source_url" type="text" placeholder="https://arxiv.org/abs/..." />
              </div>
            </div>
            <div>
              <label for="upload-citation-hint">Citation hint (optional)</label>
              <input id="upload-citation-hint" name="citation_hint" type="text" placeholder="NeurIPS 2024 camera-ready PDF" />
            </div>
            <button id="upload-button" type="submit">Upload and process</button>
            <div id="upload-status" class="status muted"></div>
          </form>
        </section>

        <section class="panel">
          <h2>2. Ask a question</h2>
          <form id="ask-form">
            <div id="paper-details" class="paper-details" hidden>
              <h3>Selected paper details</h3>
              <div id="paper-summary" class="detail-grid"></div>
              <div id="paper-signals" class="detail-grid"></div>
              <div id="paper-notes" class="detail-grid"></div>
              <div id="paper-history" class="detail-grid"></div>
              <div id="paper-activity" class="detail-grid"></div>
              <section class="metadata-editor">
                <h3>Export activity transcript</h3>
                <p class="muted">Copy or download the five most recent paper questions as a shareable Markdown transcript, or clear saved question history to reset a live demo.</p>
                <div class="actions-row">
                  <button id="copy-activity-button" class="button-secondary" type="button">Copy activity transcript</button>
                  <button id="download-activity-button" class="button-secondary" type="button">Download activity transcript</button>
                  <button id="clear-activity-button" class="button-secondary" type="button">Clear question history</button>
                </div>
              </section>
              <section class="metadata-editor">
                <h3>Export demo recap</h3>
                <p class="muted">Copy or download one Markdown handoff that combines the paper brief with the recent activity recap.</p>
                <div class="actions-row">
                  <button id="copy-demo-recap-button" class="button-secondary" type="button">Copy demo recap</button>
                  <button id="download-demo-recap-button" class="button-secondary" type="button">Download demo recap</button>
                </div>
              </section>
              <div class="actions-row">
                <button id="copy-brief-button" class="button-secondary" type="button">Copy paper brief</button>
                <button id="download-brief-button" class="button-secondary" type="button">Download paper brief</button>
                <button id="delete-paper-button" class="button-secondary" type="button">Delete paper</button>
                <span id="brief-status" class="status muted"></span>
              </div>
              <pre id="brief-preview" class="brief-preview" hidden></pre>
              <section id="metadata-form" class="metadata-editor">
                <h3>Edit operator metadata</h3>
                <div class="control-grid">
                  <div>
                    <label for="source-label-input">Source label</label>
                    <input id="source-label-input" type="text" placeholder="Curated arXiv export" />
                  </div>
                  <div>
                    <label for="source-url-input">Source URL</label>
                    <input id="source-url-input" type="text" placeholder="https://example.com/paper" />
                  </div>
                </div>
                <div>
                  <label for="citation-hint-input">Citation hint</label>
                  <input id="citation-hint-input" type="text" placeholder="Nature 2024 supplementary appendix" />
                </div>
                <div>
                  <label for="operator-notes-input">Operator notes (one per line)</label>
                  <textarea id="operator-notes-input" placeholder="Add manual provenance checks, caveats, or follow-up tasks"></textarea>
                </div>
                <div class="actions-row">
                  <button id="save-metadata-button" type="button">Save metadata</button>
                  <span id="metadata-status" class="status muted"></span>
                </div>
              </section>
              <section class="metadata-editor">
                <h3>Export operator metadata history</h3>
                <p class="muted">Copy or download the recent saved operator metadata edits as Markdown for provenance review or demo handoff.</p>
                <div class="actions-row">
                  <button id="copy-metadata-history-button" class="button-secondary" type="button">Copy metadata history</button>
                  <button id="download-metadata-history-button" class="button-secondary" type="button">Download metadata history</button>
                </div>
              </section>
            </div>
            <div class="paper-picker">
              <label for="paper-id">Paper</label>
              <input id="paper-search" type="text" placeholder="Filter papers by title, file name, or id" autocomplete="off" />
              <select id="paper-id" required>
                <option value="">Select an uploaded paper</option>
              </select>
              <div id="paper-picker-meta" class="paper-picker-meta">No papers loaded yet.</div>
            </div>
            <section class="metadata-editor">
              <h3>Paper library snapshot</h3>
              <p class="muted">Copy or download the aggregate paper-library snapshot as Markdown for demo setup notes or handoff context.</p>
              <div class="actions-row">
                <button id="copy-library-summary-button" class="button-secondary" type="button">Copy library snapshot</button>
                <button id="download-library-summary-button" class="button-secondary" type="button">Download library snapshot</button>
                <span id="paper-library-export-status" class="status muted"></span>
              </div>
              <p id="paper-library-meta" class="muted">Loading library summary...</p>
              <div id="paper-library-summary" class="detail-grid">
                <section class="detail-card"><h4>Library summary</h4><p class="muted">Loading library summary...</p></section>
              </div>
            </section>
            <section class="metadata-editor">
              <h3>Demo question presets</h3>
              <p class="muted">Load a packaged sample question into the ask box for faster live demos.</p>
              <div class="control-grid">
                <div>
                  <label for="question-preset">Preset question</label>
                  <select id="question-preset">
                    <option value="">Select a packaged demo question</option>
                  </select>
                </div>
                <div style="display: flex; align-items: end;">
                  <button id="load-question-preset-button" class="button-secondary" type="button">Load preset question</button>
                </div>
              </div>
              <div id="question-preset-meta" class="paper-picker-meta">No demo presets loaded yet.</div>
            </section>
            <div>
              <label for="question">Question</label>
              <textarea id="question" placeholder="What dataset was used, and what limitations did the authors mention?" required></textarea>
            </div>
            <div class="control-grid">
              <div>
                <label for="retrieval-mode">Retrieval mode</label>
                <select id="retrieval-mode">
                  <option value="dense">Dense</option>
                  <option value="lexical">Lexical (BM25)</option>
                  <option value="hybrid">Hybrid fusion</option>
                </select>
              </div>
              <div>
                <label for="top-k">Top K chunks</label>
                <input id="top-k" type="number" min="1" max="10" value="5" />
              </div>
              <div>
                <label for="dense-weight">Dense weight</label>
                <input id="dense-weight" type="number" min="0" step="0.1" value="1.0" />
              </div>
              <div>
                <label for="lexical-weight">Lexical weight</label>
                <input id="lexical-weight" type="number" min="0" step="0.1" value="1.0" />
              </div>
              <div>
                <label for="rrf-k">RRF k</label>
                <input id="rrf-k" type="number" min="1" step="1" value="60" />
              </div>
            </div>
            <div class="actions-row">
              <button id="reset-retrieval-preset-button" class="button-secondary" type="button">Reset retrieval preset</button>
              <span id="retrieval-preset-status" class="status muted"></span>
            </div>
            <button id="ask-button" type="submit">Ask</button>
            <div id="ask-status" class="status muted"></div>
          </form>
          <div id="answer-panel" hidden>
            <h3>Answer</h3>
            <div id="answer" class="answer"></div>
            <h3>Sources</h3>
            <ul id="sources"></ul>
            <h3>Evidence</h3>
            <div id="evidence" class="evidence-list"></div>
            <h3>Retrieval score breakdown</h3>
            <div id="retrieval-meta" class="muted"></div>
            <table id="retrieval-scores-table" class="score-table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Section</th>
                  <th>Scores</th>
                </tr>
              </thead>
              <tbody id="retrieval-scores"></tbody>
            </table>
          </div>
        </section>
      </main>

      <script>
        const healthStatus = document.getElementById("health-status");
        const uploadForm = document.getElementById("upload-form");
        const uploadButton = document.getElementById("upload-button");
        const uploadStatus = document.getElementById("upload-status");
        const uploadSourceLabelInput = document.getElementById("upload-source-label");
        const uploadSourceUrlInput = document.getElementById("upload-source-url");
        const uploadCitationHintInput = document.getElementById("upload-citation-hint");
        const askForm = document.getElementById("ask-form");
        const askButton = document.getElementById("ask-button");
        const askStatus = document.getElementById("ask-status");
        const paperSelect = document.getElementById("paper-id");
        const paperSearchInput = document.getElementById("paper-search");
        const paperPickerMeta = document.getElementById("paper-picker-meta");
        const paperLibraryMeta = document.getElementById("paper-library-meta");
        const paperLibrarySummary = document.getElementById("paper-library-summary");
        const copyLibrarySummaryButton = document.getElementById("copy-library-summary-button");
        const downloadLibrarySummaryButton = document.getElementById("download-library-summary-button");
        const paperLibraryExportStatus = document.getElementById("paper-library-export-status");
        const questionPresetSelect = document.getElementById("question-preset");
        const loadQuestionPresetButton = document.getElementById("load-question-preset-button");
        const questionPresetMeta = document.getElementById("question-preset-meta");
        const paperDetails = document.getElementById("paper-details");
        const paperSummary = document.getElementById("paper-summary");
        const paperSignals = document.getElementById("paper-signals");
        const paperNotes = document.getElementById("paper-notes");
        const paperHistory = document.getElementById("paper-history");
        const paperActivity = document.getElementById("paper-activity");
        const answerPanel = document.getElementById("answer-panel");
        const answerEl = document.getElementById("answer");
        const sourcesEl = document.getElementById("sources");
        const evidenceEl = document.getElementById("evidence");
        const retrievalMetaEl = document.getElementById("retrieval-meta");
        const retrievalScoresEl = document.getElementById("retrieval-scores");
        const copyBriefButton = document.getElementById("copy-brief-button");
        const downloadBriefButton = document.getElementById("download-brief-button");
        const copyActivityButton = document.getElementById("copy-activity-button");
        const downloadActivityButton = document.getElementById("download-activity-button");
        const clearActivityButton = document.getElementById("clear-activity-button");
        const copyDemoRecapButton = document.getElementById("copy-demo-recap-button");
        const downloadDemoRecapButton = document.getElementById("download-demo-recap-button");
        const copyMetadataHistoryButton = document.getElementById("copy-metadata-history-button");
        const downloadMetadataHistoryButton = document.getElementById("download-metadata-history-button");
        const deletePaperButton = document.getElementById("delete-paper-button");
        const briefStatus = document.getElementById("brief-status");
        const briefPreview = document.getElementById("brief-preview");
        const metadataForm = document.getElementById("metadata-form");
        const sourceLabelInput = document.getElementById("source-label-input");
        const sourceUrlInput = document.getElementById("source-url-input");
        const citationHintInput = document.getElementById("citation-hint-input");
        const operatorNotesInput = document.getElementById("operator-notes-input");
        const saveMetadataButton = document.getElementById("save-metadata-button");
        const metadataStatus = document.getElementById("metadata-status");
        const questionInput = document.getElementById("question");
        const retrievalModeInput = document.getElementById("retrieval-mode");
        const topKInput = document.getElementById("top-k");
        const denseWeightInput = document.getElementById("dense-weight");
        const lexicalWeightInput = document.getElementById("lexical-weight");
        const rrfKInput = document.getElementById("rrf-k");
        const retrievalPresetStatus = document.getElementById("retrieval-preset-status");
        const resetRetrievalPresetButton = document.getElementById("reset-retrieval-preset-button");
        const DEFAULT_RETRIEVAL_UI_STATE = {
          retrievalMode: "dense",
          topK: 5,
          denseWeight: 1.0,
          lexicalWeight: 1.0,
          rrfK: 60,
        };
        const initialUiState = getInitialUiState();
        let paperRecords = [];
        let demoQuestionPresets = [];

        function setStatus(element, message, kind = "muted") {
          element.textContent = message;
          element.className = `status ${kind}`;
        }

        function parseIntegerParam(value, fallback) {
          const parsed = Number.parseInt(value || "", 10);
          return Number.isFinite(parsed) ? parsed : fallback;
        }

        function parseFloatParam(value, fallback) {
          const parsed = Number.parseFloat(value || "");
          return Number.isFinite(parsed) ? parsed : fallback;
        }

        function normalizeRetrievalUiState(rawState = {}) {
          const allowedRetrievalModes = new Set(["dense", "lexical", "hybrid"]);
          const issues = [];
          const retrievalMode = allowedRetrievalModes.has(rawState.retrievalMode) ? rawState.retrievalMode : DEFAULT_RETRIEVAL_UI_STATE.retrievalMode;
          if ((rawState.retrievalMode || "") && rawState.retrievalMode !== retrievalMode) {
            issues.push(`retrieval_mode=${rawState.retrievalMode} → dense`);
          }

          const rawTopK = parseIntegerParam(rawState.topK, DEFAULT_RETRIEVAL_UI_STATE.topK);
          const topK = Math.min(10, Math.max(1, rawTopK));
          if (rawTopK !== topK) {
            issues.push(`top_k=${rawState.topK} → ${topK}`);
          }

          const rawDenseWeight = parseFloatParam(rawState.denseWeight, DEFAULT_RETRIEVAL_UI_STATE.denseWeight);
          const denseWeight = rawDenseWeight >= 0 ? rawDenseWeight : DEFAULT_RETRIEVAL_UI_STATE.denseWeight;
          if (rawDenseWeight !== denseWeight) {
            issues.push(`dense_weight=${rawState.denseWeight} → 1.0`);
          }

          const rawLexicalWeight = parseFloatParam(rawState.lexicalWeight, DEFAULT_RETRIEVAL_UI_STATE.lexicalWeight);
          const lexicalWeight = rawLexicalWeight >= 0 ? rawLexicalWeight : DEFAULT_RETRIEVAL_UI_STATE.lexicalWeight;
          if (rawLexicalWeight !== lexicalWeight) {
            issues.push(`lexical_weight=${rawState.lexicalWeight} → 1.0`);
          }

          const rawRrfK = parseIntegerParam(rawState.rrfK, DEFAULT_RETRIEVAL_UI_STATE.rrfK);
          const rrfK = rawRrfK >= 1 ? rawRrfK : DEFAULT_RETRIEVAL_UI_STATE.rrfK;
          if (rawRrfK !== rrfK) {
            issues.push(`rrf_k=${rawState.rrfK} → ${rrfK}`);
          }

          return {
            paperId: rawState.paperId || "",
            questionPreset: rawState.questionPreset || "",
            retrievalMode,
            topK,
            denseWeight,
            lexicalWeight,
            rrfK,
            retrievalIssues: issues,
          };
        }

        function getInitialUiState() {
          const params = new URLSearchParams(window.location.search);
          return normalizeRetrievalUiState({
            paperId: params.get("paper_id") || "",
            questionPreset: params.get("question_preset") || "",
            retrievalMode: params.get("retrieval_mode") || DEFAULT_RETRIEVAL_UI_STATE.retrievalMode,
            topK: params.get("top_k"),
            denseWeight: params.get("dense_weight"),
            lexicalWeight: params.get("lexical_weight"),
            rrfK: params.get("rrf_k"),
          });
        }

        function syncUrlState({
          paperId = paperSelect.value,
          questionPreset = questionPresetSelect.value,
          retrievalMode = retrievalModeInput.value,
          topK = parseIntegerParam(topKInput.value, 5),
          denseWeight = parseFloatParam(denseWeightInput.value, 1.0),
          lexicalWeight = parseFloatParam(lexicalWeightInput.value, 1.0),
          rrfK = parseIntegerParam(rrfKInput.value, 60),
        } = {}) {
          const url = new URL(window.location.href);
          const normalizedState = normalizeRetrievalUiState({
            paperId,
            questionPreset,
            retrievalMode,
            topK,
            denseWeight,
            lexicalWeight,
            rrfK,
          });

          if (paperId) {
            url.searchParams.set("paper_id", paperId);
          } else {
            url.searchParams.delete("paper_id");
          }

          if (questionPreset) {
            url.searchParams.set("question_preset", questionPreset);
          } else {
            url.searchParams.delete("question_preset");
          }

          if (normalizedState.retrievalMode && normalizedState.retrievalMode !== "dense") {
            url.searchParams.set("retrieval_mode", normalizedState.retrievalMode);
          } else {
            url.searchParams.delete("retrieval_mode");
          }

          if (normalizedState.topK !== 5) {
            url.searchParams.set("top_k", String(normalizedState.topK));
          } else {
            url.searchParams.delete("top_k");
          }

          if (normalizedState.denseWeight !== 1.0) {
            url.searchParams.set("dense_weight", String(normalizedState.denseWeight));
          } else {
            url.searchParams.delete("dense_weight");
          }

          if (normalizedState.lexicalWeight !== 1.0) {
            url.searchParams.set("lexical_weight", String(normalizedState.lexicalWeight));
          } else {
            url.searchParams.delete("lexical_weight");
          }

          if (normalizedState.rrfK !== 60) {
            url.searchParams.set("rrf_k", String(normalizedState.rrfK));
          } else {
            url.searchParams.delete("rrf_k");
          }

          history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
        }

        function applyRetrievalUiState(state) {
          retrievalModeInput.value = state.retrievalMode || DEFAULT_RETRIEVAL_UI_STATE.retrievalMode;
          topKInput.value = String(state.topK || DEFAULT_RETRIEVAL_UI_STATE.topK);
          denseWeightInput.value = String(state.denseWeight || DEFAULT_RETRIEVAL_UI_STATE.denseWeight);
          lexicalWeightInput.value = String(state.lexicalWeight || DEFAULT_RETRIEVAL_UI_STATE.lexicalWeight);
          rrfKInput.value = String(state.rrfK || DEFAULT_RETRIEVAL_UI_STATE.rrfK);
        }

        function renderRetrievalPresetStatus(state) {
          const issues = state && state.retrievalIssues || [];
          if (!issues.length) {
            setStatus(retrievalPresetStatus, "", "muted");
            return;
          }
          setStatus(retrievalPresetStatus, `Adjusted invalid retrieval URL preset values: ${issues.join(", ")}.`, "error");
        }

        function formatFileSize(bytes) {
          if (!bytes) {
            return "Unknown";
          }
          if (bytes < 1024) {
            return `${bytes} B`;
          }
          if (bytes < 1024 * 1024) {
            return `${(bytes / 1024).toFixed(1)} KB`;
          }
          return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
        }

        function renderPaperLibrarySummary(summary) {
          const totalPapers = Number(summary && summary.total_papers || 0);
          if (!totalPapers) {
            paperLibraryMeta.textContent = "No papers uploaded yet.";
            paperLibrarySummary.innerHTML = renderDetailCard("Library summary", '<p class="muted">Upload a paper to populate the demo library snapshot.</p>');
            return;
          }

          const latestPaperLabel = summary.latest_paper_title || summary.latest_paper_id || "Unknown";
          paperLibraryMeta.textContent = `${totalPapers} paper${totalPapers === 1 ? "" : "s"} tracked across the local demo registry.`;
          paperLibrarySummary.innerHTML = [
            renderDetailCard("Coverage", `
              <p><strong>Ready papers:</strong> ${Number(summary.ready_papers || 0)} / ${totalPapers}</p>
              <p><strong>Papers with operator notes:</strong> ${Number(summary.papers_with_operator_notes || 0)}</p>
              <p><strong>Total pages:</strong> ${Number(summary.total_pages || 0)}</p>
            `),
            renderDetailCard("Artifacts", `
              <p><strong>Total chunks:</strong> ${Number(summary.total_chunks || 0)}</p>
              <p><strong>Total file size:</strong> ${formatFileSize(Number(summary.total_file_size_bytes || 0))}</p>
            `),
            renderDetailCard("Latest paper", `
              <p><strong>Paper:</strong> ${escapeHtml(latestPaperLabel)}</p>
              <p><strong>Created:</strong> ${escapeHtml(formatTimestamp(summary.latest_created_at || ""))}</p>
            `),
          ].join("");
        }

        function renderDetailCard(title, body) {
          return `<section class="detail-card"><h4>${title}</h4>${body}</section>`;
        }

        function renderList(items, emptyMessage = "None") {
          if (!items || !items.length) {
            return `<p class="muted">${emptyMessage}</p>`;
          }
          return `<ul class="detail-list">${items.map((item) => `<li>${item}</li>`).join("")}</ul>`;
        }

        function renderChips(items, emptyMessage = "None detected") {
          if (!items || !items.length) {
            return `<p class="muted">${emptyMessage}</p>`;
          }
          return `<div class="chips">${items.map((item) => `<span class="chip">${item}</span>`).join("")}</div>`;
        }

        function formatScore(value) {
          if (value === null || value === undefined) {
            return "n/a";
          }
          return Number(value).toFixed(4);
        }

        function escapeHtml(value) {
          return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#39;");
        }

        function highlightEvidenceCard(chunkId) {
          for (const card of evidenceEl.querySelectorAll(".evidence-card")) {
            card.classList.remove("is-highlighted");
          }

          if (chunkId === null || chunkId === undefined) {
            return;
          }

          const card = evidenceEl.querySelector(`[data-chunk-id="${chunkId}"]`);
          if (!card) {
            return;
          }

          card.classList.add("is-highlighted");
          card.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }

        function renderAnswer(payload) {
          const answerText = payload.answer || "";
          const citations = payload.answer_citations || [];

          if (!citations.length) {
            answerEl.textContent = answerText;
            return;
          }

          answerEl.innerHTML = citations.map((citation) => {
            const context = [citation.section || "unknown", citation.page_label || "page unknown"].filter(Boolean).join(" • ");
            return `
              <div class="answer-line">
                <span>${escapeHtml(citation.sentence_text || "")}</span>
                <button
                  type="button"
                  class="citation-anchor"
                  data-chunk-id="${citation.chunk_id ?? ""}"
                  title="Jump to evidence: ${escapeHtml(context)}"
                >${escapeHtml(citation.label || "[?]")}</button>
              </div>
            `;
          }).join("");

          for (const button of answerEl.querySelectorAll(".citation-anchor")) {
            button.addEventListener("click", () => {
              const rawChunkId = button.dataset.chunkId;
              highlightEvidenceCard(rawChunkId === "" ? null : Number(rawChunkId));
            });
          }
        }

        function renderEvidence(payload) {
          const evidence = payload.evidence || [];

          if (!evidence.length) {
            evidenceEl.innerHTML = '<p class="muted">No structured evidence returned.</p>';
            return;
          }

          evidenceEl.innerHTML = evidence.map((item) => {
            const location = item.page_label || (item.page_numbers && item.page_numbers.length ? `pages ${item.page_numbers.join(", ")}` : "page unknown");
            return `
              <article class="evidence-card" data-chunk-id="${item.chunk_id ?? ""}">
                <div class="evidence-card-header">
                  <strong>${item.section || "unknown"}</strong>
                  <span class="chip">${location}</span>
                  <code>chunk ${item.chunk_id ?? "?"}</code>
                  <span class="muted">score ${formatScore(item.retrieval_score)}</span>
                </div>
                <p class="evidence-snippet">${item.text || ""}</p>
              </article>
            `;
          }).join("");
        }

        function renderRetrievalScores(payload) {
          const retrievalScores = payload.retrieval_scores || [];
          retrievalMetaEl.textContent = `Mode: ${payload.retrieval_mode || "dense"}, chunks returned: ${payload.num_chunks_retrieved || 0}`;

          if (!retrievalScores.length) {
            retrievalScoresEl.innerHTML = '<tr><td colspan="3" class="muted">No retrieval score details available.</td></tr>';
            return;
          }

          retrievalScoresEl.innerHTML = retrievalScores.map((chunk) => {
            const scoreLines = [
              `retrieval=${formatScore(chunk.retrieval_score)}`,
              chunk.hybrid_score !== null && chunk.hybrid_score !== undefined ? `hybrid=${formatScore(chunk.hybrid_score)}` : null,
              chunk.dense_score !== null && chunk.dense_score !== undefined ? `dense=${formatScore(chunk.dense_score)}` : null,
              chunk.lexical_score !== null && chunk.lexical_score !== undefined ? `lexical=${formatScore(chunk.lexical_score)}` : null,
              chunk.dense_rank ? `dense rank=${chunk.dense_rank}` : null,
              chunk.lexical_rank ? `lexical rank=${chunk.lexical_rank}` : null,
            ].filter(Boolean);

            return `
              <tr>
                <td>${chunk.rank || "-"}</td>
                <td>${chunk.section || "unknown"}<br /><code>chunk ${chunk.chunk_id ?? "?"}</code></td>
                <td>${scoreLines.map((line) => `<div>${line}</div>`).join("")}</td>
              </tr>
            `;
          }).join("");
        }

        function resetBriefUi() {
          setStatus(briefStatus, "", "muted");
          briefPreview.hidden = true;
          briefPreview.textContent = "";
        }

        function parseOperatorNotes(value) {
          return String(value || "")
            .split("\n")
            .map((item) => item.trim())
            .filter(Boolean);
        }

        function populateMetadataEditor(paper) {
          const provenance = paper && paper.provenance || {};
          sourceLabelInput.value = provenance.source_label || "";
          sourceUrlInput.value = provenance.source_url || "";
          citationHintInput.value = provenance.citation_hint || "";
          operatorNotesInput.value = (paper && paper.operator_ingestion_notes || []).join("\n");
          setStatus(metadataStatus, "", "muted");
        }

        function formatActivityRetrievalConfig(item) {
          const parts = [
            `mode=${item.retrieval_mode || "dense"}`,
            item.top_k ? `top_k=${item.top_k}` : null,
            item.dense_weight !== null && item.dense_weight !== undefined ? `dense=${Number(item.dense_weight).toFixed(1)}` : null,
            item.lexical_weight !== null && item.lexical_weight !== undefined ? `lexical=${Number(item.lexical_weight).toFixed(1)}` : null,
            item.rrf_k !== null && item.rrf_k !== undefined ? `rrf_k=${item.rrf_k}` : null,
          ].filter(Boolean);
          return parts.join(" • ");
        }

        function summarizeActivityItems(items) {
          if (!items || !items.length) {
            return {
              questionCount: 0,
              averageLatencyMs: 0,
              totalTokens: 0,
              retrievalModesLabel: "None recorded",
              goodMatchRateLabel: "No match data",
            };
          }

          const totalLatencyMs = items.reduce((sum, item) => sum + Number(item.latency_ms || 0), 0);
          const totalTokens = items.reduce((sum, item) => sum + Number(item.token_usage && item.token_usage.total_tokens || 0), 0);
          const modeCounts = items.reduce((counts, item) => {
            const mode = item.retrieval_mode || "dense";
            counts[mode] = (counts[mode] || 0) + 1;
            return counts;
          }, {});
          const retrievalModesLabel = Object.entries(modeCounts)
            .sort((left, right) => left[0].localeCompare(right[0]))
            .map(([mode, count]) => `${mode} (${count})`)
            .join(", ") || "None recorded";
          const matchValues = items
            .map((item) => item.has_good_match)
            .filter((value) => value !== null && value !== undefined);
          const goodMatchCount = matchValues.filter(Boolean).length;
          const goodMatchRateLabel = matchValues.length
            ? `${goodMatchCount}/${matchValues.length} (${Math.round((goodMatchCount / matchValues.length) * 100)}%)`
            : "No match data";

          return {
            questionCount: items.length,
            averageLatencyMs: totalLatencyMs / items.length,
            totalTokens,
            retrievalModesLabel,
            goodMatchRateLabel,
          };
        }

        function renderActivitySummary(activity) {
          const summary = activity && activity.summary;
          const items = activity && activity.items || [];
          if (!summary && !items.length) {
            return '<p class="muted">No recent question activity was recorded for this paper.</p>';
          }

          const normalizedSummary = summary || summarizeActivityItems(items);
          const questionCount = Number(normalizedSummary.question_count ?? normalizedSummary.questionCount ?? 0);
          const averageLatencyMs = Number(normalizedSummary.average_latency_ms ?? normalizedSummary.averageLatencyMs ?? 0);
          const goodMatchRateLabel = normalizedSummary.good_match_rate_label || normalizedSummary.goodMatchRateLabel || "No match data";
          const retrievalModesLabel = normalizedSummary.retrieval_modes_label || normalizedSummary.retrievalModesLabel || "None recorded";
          const totalTokens = Number(normalizedSummary.total_tokens ?? normalizedSummary.totalTokens ?? 0);
          return `
            <p><strong>Questions included:</strong> ${questionCount}</p>
            <p><strong>Average latency:</strong> ${averageLatencyMs.toFixed(2)} ms</p>
            <p><strong>Good-match rate:</strong> ${escapeHtml(goodMatchRateLabel)}</p>
            <p><strong>Retrieval modes:</strong> ${escapeHtml(retrievalModesLabel)}</p>
            <p><strong>Total tokens:</strong> ${totalTokens}</p>
          `;
        }

        function renderActivityItems(items) {
          if (!items || !items.length) {
            return '<p class="muted">No question history yet.</p>';
          }

          return `<ul class="detail-list">${items.map((item) => {
            const status = item.has_good_match === null || item.has_good_match === undefined
              ? "match unknown"
              : item.has_good_match ? "good match" : "fallback or weak match";
            const promptTokens = item.token_usage && item.token_usage.total_tokens ? `${item.token_usage.total_tokens} tokens` : "token usage unavailable";
            const retrievalConfig = formatActivityRetrievalConfig(item);
            const escapedQuestion = escapeHtml(item.question || "");
            const answerPreview = item.answer_preview ? `<p style="margin: 6px 0 0;"><strong>Answer:</strong> ${escapeHtml(item.answer_preview)}</p>` : "";
            const evidenceCues = item.evidence_labels && item.evidence_labels.length
              ? `<p class="muted" style="margin: 6px 0 0;">Evidence cues: ${escapeHtml(item.evidence_labels.join(", "))}</p>`
              : "";
            const retrievalConfigLine = retrievalConfig
              ? `<p class="muted" style="margin: 6px 0 0;">Retrieval: ${escapeHtml(retrievalConfig)}</p>`
              : "";
            const actionButton = item.question
              ? `<div class="history-item-actions"><button type="button" class="button-secondary mini-button reuse-question-button" data-question="${escapedQuestion}">Reuse question</button></div>`
              : "";
            return `<li><strong>${escapeHtml(item.question || "Unknown question")}</strong><br /><span class="muted">${escapeHtml(formatTimestamp(item.timestamp || "Unknown time"))} • ${Number(item.latency_ms || 0).toFixed(2)} ms • ${item.num_chunks_retrieved || 0} chunk(s) • ${escapeHtml(status)} • ${escapeHtml(promptTokens)}</span>${retrievalConfigLine}${answerPreview}${evidenceCues}${actionButton}</li>`;
          }).join("")}</ul>`;
        }

        function reuseRecentQuestion(question) {
          if (!question) {
            setStatus(askStatus, "No saved question was available to reuse.", "error");
            return;
          }

          questionInput.value = question;
          questionInput.focus();
          setStatus(askStatus, "Loaded a recent question into the ask box.", "success");
        }

        function formatTimestamp(value) {
          if (!value) {
            return "Not yet recorded";
          }

          const parsed = new Date(value);
          if (Number.isNaN(parsed.getTime())) {
            return value;
          }

          return parsed.toLocaleString(undefined, {
            dateStyle: "medium",
            timeStyle: "short",
          });
        }

        function renderMetadataHistory(history, provenance) {
          const items = (history || []).slice().reverse();
          if (!items.length) {
            const updateCount = Number(provenance && provenance.operator_update_count || 0);
            return `<div class="history-list">
              <article class="history-item">
                <p><strong>${escapeHtml(updateCount ? `Saved ${updateCount} operator update${updateCount === 1 ? "" : "s"}` : "No saved operator edits yet")}</strong></p>
                <p class="history-item-meta">Save notes or provenance fields to start the history.</p>
              </article>
            </div>`;
          }

          return `<div class="history-list">${items.map((item) => {
            const noteCount = (item.operator_ingestion_notes || []).length;
            const details = [
              item.source_label ? `Source label: ${item.source_label}` : null,
              item.citation_hint ? `Citation hint: ${item.citation_hint}` : null,
              item.source_url ? `Source URL saved` : null,
              noteCount ? `${noteCount} operator note${noteCount === 1 ? "" : "s"}` : "No operator notes",
            ].filter(Boolean).join(" • ");

            return `
            <article class="history-item">
              <p><strong>Update ${Number(item.operator_update_count || 0) || "?"}</strong></p>
              <p class="history-item-meta">${escapeHtml(formatTimestamp(item.timestamp))} • ${escapeHtml(item.source || "source unknown")}</p>
              <p class="history-item-meta">${escapeHtml(details || "No metadata details recorded.")}</p>
            </article>
          `;
          }).join("")}</div>`;
        }

        function flattenDemoQuestions(questionSets) {
          return (questionSets || []).flatMap((questionSet) => {
            return (questionSet.questions || []).map((item) => ({
              package_id: questionSet.package_id,
              package_title: questionSet.title,
              package_description: questionSet.description,
              id: item.id,
              question: item.question,
              expected_focus: item.expected_focus,
              value: `${questionSet.package_id}::${item.id}`,
            }));
          });
        }

        function renderQuestionPresetOptions(selectedValue = "") {
          const presets = flattenDemoQuestions(demoQuestionPresets);
          questionPresetSelect.innerHTML = '<option value="">Select a packaged demo question</option>';

          for (const preset of presets) {
            const option = document.createElement("option");
            option.value = preset.value;
            option.textContent = `${preset.package_title || preset.package_id}: ${preset.id}`;
            if (preset.value === selectedValue) {
              option.selected = true;
            }
            questionPresetSelect.appendChild(option);
          }

          if (!presets.length) {
            questionPresetMeta.textContent = "No demo presets loaded yet.";
            return [];
          }

          questionPresetMeta.textContent = `${presets.length} demo preset${presets.length === 1 ? "" : "s"} available from packaged sample questions.`;
          return presets;
        }

        function updateQuestionPresetMeta() {
          const presets = flattenDemoQuestions(demoQuestionPresets);
          const selectedPreset = presets.find((item) => item.value === questionPresetSelect.value);
          if (!selectedPreset) {
            if (!presets.length) {
              questionPresetMeta.textContent = "No demo presets loaded yet.";
              return;
            }
            questionPresetMeta.textContent = `${presets.length} demo preset${presets.length === 1 ? "" : "s"} available from packaged sample questions.`;
            return;
          }

          const detailParts = [selectedPreset.package_title || selectedPreset.package_id];
          if (selectedPreset.expected_focus) {
            detailParts.push(`Focus: ${selectedPreset.expected_focus}`);
          }
          questionPresetMeta.textContent = detailParts.join(" • ");
        }

        function loadSelectedQuestionPreset() {
          const presets = flattenDemoQuestions(demoQuestionPresets);
          const selectedPreset = presets.find((item) => item.value === questionPresetSelect.value);
          if (!selectedPreset) {
            setStatus(askStatus, "Choose a demo preset to load.", "error");
            return;
          }

          questionInput.value = selectedPreset.question;
          setStatus(askStatus, `Loaded demo preset ${selectedPreset.id}.`, "success");
          updateQuestionPresetMeta();
        }

        function buildPaperSearchText(paper) {
          return [paper.title, paper.original_filename, paper.paper_id]
            .filter(Boolean)
            .join(" ")
            .toLowerCase();
        }

        function sortPapersByRecency(papers) {
          return [...papers].sort((left, right) => {
            const leftCreated = Date.parse(left.created_at || "") || 0;
            const rightCreated = Date.parse(right.created_at || "") || 0;
            if (leftCreated !== rightCreated) {
              return rightCreated - leftCreated;
            }
            return (left.title || left.paper_id || "").localeCompare(right.title || right.paper_id || "");
          });
        }

        function getVisiblePapers(query) {
          const normalizedQuery = (query || "").trim().toLowerCase();
          const sortedPapers = sortPapersByRecency(paperRecords);
          if (!normalizedQuery) {
            return sortedPapers;
          }
          return sortedPapers.filter((paper) => buildPaperSearchText(paper).includes(normalizedQuery));
        }

        function renderPaperOptions(selectedPaperId = "") {
          const visiblePapers = getVisiblePapers(paperSearchInput.value);
          paperSelect.innerHTML = '<option value="">Select an uploaded paper</option>';
          for (const paper of visiblePapers) {
            const option = document.createElement("option");
            option.value = paper.paper_id;
            option.textContent = paper.title ? `${paper.title} (${paper.paper_id.slice(0, 8)})` : paper.paper_id;
            if (paper.paper_id === selectedPaperId) {
              option.selected = true;
            }
            paperSelect.appendChild(option);
          }

          const totalCount = paperRecords.length;
          const visibleCount = visiblePapers.length;
          const suffix = totalCount === 1 ? "paper" : "papers";
          if (!totalCount) {
            paperPickerMeta.textContent = "No papers uploaded yet.";
          } else if ((paperSearchInput.value || "").trim()) {
            paperPickerMeta.textContent = `Showing ${visibleCount} of ${totalCount} ${suffix}, newest first.`;
          } else {
            paperPickerMeta.textContent = `${totalCount} ${suffix} available, newest first.`;
          }

          return visiblePapers;
        }

        async function fetchPaperBriefMarkdown(paperId) {
          const response = await fetch(`/papers/${paperId}/brief/export`);
          const payload = await response.text();
          if (!response.ok) {
            try {
              const parsed = JSON.parse(payload);
              throw new Error(parsed.detail || "Failed to load paper brief");
            } catch (error) {
              throw new Error(payload || "Failed to load paper brief");
            }
          }
          return payload;
        }

        async function fetchPaperLibrarySummary() {
          const response = await fetch("/papers/summary");
          const payload = await response.json();
          if (!response.ok) {
            throw new Error(payload.detail || "Failed to load paper library summary");
          }
          return payload;
        }

        async function fetchPaperLibrarySummaryMarkdown() {
          const response = await fetch("/papers/summary/export");
          const payload = await response.text();
          if (!response.ok) {
            try {
              const parsed = JSON.parse(payload);
              throw new Error(parsed.detail || "Failed to export paper library snapshot");
            } catch (error) {
              if (error instanceof SyntaxError) {
                throw new Error(payload || "Failed to export paper library snapshot");
              }
              throw error;
            }
          }
          return payload;
        }

        function setPaperActionState(disabled) {
          copyBriefButton.disabled = disabled;
          downloadBriefButton.disabled = disabled;
          copyActivityButton.disabled = disabled;
          downloadActivityButton.disabled = disabled;
          clearActivityButton.disabled = disabled;
          copyDemoRecapButton.disabled = disabled;
          downloadDemoRecapButton.disabled = disabled;
          copyMetadataHistoryButton.disabled = disabled;
          downloadMetadataHistoryButton.disabled = disabled;
          deletePaperButton.disabled = disabled;
        }

        async function handleLibrarySummaryAction(action) {
          copyLibrarySummaryButton.disabled = true;
          downloadLibrarySummaryButton.disabled = true;
          setStatus(paperLibraryExportStatus, "Preparing library snapshot...", "muted");

          try {
            const summaryMarkdown = await fetchPaperLibrarySummaryMarkdown();
            briefPreview.textContent = summaryMarkdown;
            briefPreview.hidden = false;

            if (action === "copy") {
              if (!navigator.clipboard || typeof navigator.clipboard.writeText !== "function") {
                setStatus(
                  paperLibraryExportStatus,
                  "Clipboard copy is unavailable in this browser. The library snapshot preview is open below, or you can use Download instead.",
                  "error"
                );
                return;
              }

              try {
                await navigator.clipboard.writeText(summaryMarkdown);
                setStatus(paperLibraryExportStatus, "Library snapshot copied to clipboard.", "success");
              } catch (error) {
                const detail = error instanceof Error && error.message ? ` ${error.message}` : "";
                setStatus(
                  paperLibraryExportStatus,
                  `Could not copy the library snapshot to the clipboard.${detail} The preview is open below, or you can use Download instead.`,
                  "error"
                );
              }
              return;
            }

            try {
              const blob = new Blob([summaryMarkdown], { type: "text/markdown;charset=utf-8" });
              const url = URL.createObjectURL(blob);
              const anchor = document.createElement("a");
              anchor.href = url;
              anchor.download = "paper-library-snapshot.md";
              document.body.appendChild(anchor);
              anchor.click();
              anchor.remove();
              URL.revokeObjectURL(url);
              setStatus(paperLibraryExportStatus, `Downloaded ${anchor.download}.`, "success");
            } catch (error) {
              const detail = error instanceof Error && error.message ? ` ${error.message}` : "";
              setStatus(
                paperLibraryExportStatus,
                `Could not download the library snapshot.${detail} The preview is open below, so you can still copy it manually.`,
                "error"
              );
            }
          } catch (error) {
            setStatus(paperLibraryExportStatus, error.message, "error");
          } finally {
            copyLibrarySummaryButton.disabled = false;
            downloadLibrarySummaryButton.disabled = false;
          }
        }

        async function handleBriefAction(action) {
          const paperId = paperSelect.value;
          if (!paperId) {
            setStatus(briefStatus, "Select a paper first.", "error");
            return;
          }

          setPaperActionState(true);
          setStatus(briefStatus, "Preparing paper brief...", "muted");

          try {
            const briefMarkdown = await fetchPaperBriefMarkdown(paperId);
            briefPreview.textContent = briefMarkdown;
            briefPreview.hidden = false;

            if (action === "copy") {
              await navigator.clipboard.writeText(briefMarkdown);
              setStatus(briefStatus, "Paper brief copied to clipboard.", "success");
              return;
            }

            const blob = new Blob([briefMarkdown], { type: "text/markdown;charset=utf-8" });
            const url = URL.createObjectURL(blob);
            const anchor = document.createElement("a");
            anchor.href = url;
            anchor.download = `${paperId}-paper-brief.md`;
            document.body.appendChild(anchor);
            anchor.click();
            anchor.remove();
            URL.revokeObjectURL(url);
            setStatus(briefStatus, `Downloaded ${anchor.download}.`, "success");
          } catch (error) {
            setStatus(briefStatus, error.message, "error");
          } finally {
            setPaperActionState(false);
          }
        }

        async function handleActivityTranscriptAction(action) {
          const paperId = paperSelect.value;
          if (!paperId) {
            setStatus(briefStatus, "Select a paper first.", "error");
            return;
          }

          setPaperActionState(true);
          setStatus(briefStatus, "Preparing activity transcript...", "muted");

          try {
            const transcriptMarkdown = await fetchPaperActivityTranscript(paperId);
            briefPreview.textContent = transcriptMarkdown;
            briefPreview.hidden = false;

            const paper = paperRecords.find((item) => item.paper_id === paperId) || {};
            const downloadName = `${paper.paper_id || paperId}-activity-transcript.md`;

            if (action === "copy") {
              await navigator.clipboard.writeText(transcriptMarkdown);
              setStatus(briefStatus, "Activity transcript copied to clipboard.", "success");
              return;
            }

            const blob = new Blob([transcriptMarkdown], { type: "text/markdown;charset=utf-8" });
            const url = URL.createObjectURL(blob);
            const anchor = document.createElement("a");
            anchor.href = url;
            anchor.download = downloadName;
            document.body.appendChild(anchor);
            anchor.click();
            anchor.remove();
            URL.revokeObjectURL(url);
            setStatus(briefStatus, `Downloaded ${anchor.download}.`, "success");
          } catch (error) {
            setStatus(briefStatus, error.message, "error");
          } finally {
            setPaperActionState(false);
          }
        }

        async function handleDemoRecapAction(action) {
          const paperId = paperSelect.value;
          if (!paperId) {
            setStatus(briefStatus, "Select a paper first.", "error");
            return;
          }

          setPaperActionState(true);
          setStatus(briefStatus, "Preparing demo recap...", "muted");

          try {
            const recapMarkdown = await fetchPaperDemoRecapMarkdown(paperId);
            briefPreview.textContent = recapMarkdown;
            briefPreview.hidden = false;

            const paper = paperRecords.find((item) => item.paper_id === paperId) || {};
            const downloadName = `${paper.paper_id || paperId}-demo-recap.md`;

            if (action === "copy") {
              await navigator.clipboard.writeText(recapMarkdown);
              setStatus(briefStatus, "Demo recap copied to clipboard.", "success");
              return;
            }

            const blob = new Blob([recapMarkdown], { type: "text/markdown;charset=utf-8" });
            const url = URL.createObjectURL(blob);
            const anchor = document.createElement("a");
            anchor.href = url;
            anchor.download = downloadName;
            document.body.appendChild(anchor);
            anchor.click();
            anchor.remove();
            URL.revokeObjectURL(url);
            setStatus(briefStatus, `Downloaded ${anchor.download}.`, "success");
          } catch (error) {
            setStatus(briefStatus, error.message, "error");
          } finally {
            setPaperActionState(false);
          }
        }

        async function handleMetadataHistoryAction(action) {
          const paperId = paperSelect.value;
          if (!paperId) {
            setStatus(briefStatus, "Select a paper first.", "error");
            return;
          }

          setPaperActionState(true);
          setStatus(briefStatus, "Preparing operator metadata history...", "muted");

          try {
            const metadataHistoryMarkdown = await fetchPaperMetadataHistoryMarkdown(paperId);
            briefPreview.textContent = metadataHistoryMarkdown;
            briefPreview.hidden = false;

            const paper = paperRecords.find((item) => item.paper_id === paperId) || {};
            const downloadName = `${paper.paper_id || paperId}-metadata-history.md`;

            if (action === "copy") {
              await navigator.clipboard.writeText(metadataHistoryMarkdown);
              setStatus(briefStatus, "Operator metadata history copied to clipboard.", "success");
              return;
            }

            const blob = new Blob([metadataHistoryMarkdown], { type: "text/markdown;charset=utf-8" });
            const url = URL.createObjectURL(blob);
            const anchor = document.createElement("a");
            anchor.href = url;
            anchor.download = downloadName;
            document.body.appendChild(anchor);
            anchor.click();
            anchor.remove();
            URL.revokeObjectURL(url);
            setStatus(briefStatus, `Downloaded ${anchor.download}.`, "success");
          } catch (error) {
            setStatus(briefStatus, error.message, "error");
          } finally {
            setPaperActionState(false);
          }
        }

        async function handleDeletePaper() {
          const paperId = paperSelect.value;
          if (!paperId) {
            setStatus(briefStatus, "Select a paper first.", "error");
            return;
          }

          const paper = paperRecords.find((item) => item.paper_id === paperId);
          const paperLabel = paper && (paper.title || paper.original_filename || paper.paper_id) || paperId;
          const confirmed = window.confirm(`Delete ${paperLabel}? This removes the paper and its saved artifacts.`);
          if (!confirmed) {
            return;
          }

          setPaperActionState(true);
          setStatus(briefStatus, "Deleting paper...", "muted");

          try {
            const response = await fetch(`/papers/${paperId}`, { method: "DELETE" });
            const payload = await response.json();
            if (!response.ok) {
              throw new Error(payload.detail || "Failed to delete paper");
            }

            answerPanel.hidden = true;
            sourcesEl.innerHTML = "";
            evidenceEl.innerHTML = "";
            retrievalScoresEl.innerHTML = "";
            retrievalMetaEl.textContent = "";
            await refreshPapers();
            const deletedArtifacts = (payload.deleted_artifacts || []).length;
            setStatus(briefStatus, `Deleted ${paperLabel}${deletedArtifacts ? ` and removed ${deletedArtifacts} artifact(s)` : ""}.`, "success");
          } catch (error) {
            setStatus(briefStatus, error.message, "error");
          } finally {
            setPaperActionState(false);
          }
        }

        async function handleClearPaperActivity() {
          const paperId = paperSelect.value;
          if (!paperId) {
            setStatus(briefStatus, "Select a paper first.", "error");
            return;
          }

          const paper = paperRecords.find((item) => item.paper_id === paperId);
          const paperLabel = paper && (paper.title || paper.original_filename || paper.paper_id) || paperId;
          const confirmed = window.confirm(`Clear saved question history for ${paperLabel}? This keeps the paper but removes recent activity for demo reset.`);
          if (!confirmed) {
            return;
          }

          setPaperActionState(true);
          setStatus(briefStatus, "Clearing question history...", "muted");

          try {
            const response = await fetch(`/papers/${paperId}/activity`, { method: "DELETE" });
            const payload = await response.json();
            if (!response.ok) {
              throw new Error(payload.detail || "Failed to clear paper activity");
            }

            await updatePaperDetails(paperId);
            const deletedEvents = Number(payload.deleted_events || 0);
            setStatus(briefStatus, `Cleared ${deletedEvents} saved question${deletedEvents === 1 ? "" : "s"} for ${paperLabel}.`, "success");
          } catch (error) {
            setStatus(briefStatus, error.message, "error");
          } finally {
            setPaperActionState(false);
          }
        }

        async function fetchPaperActivity(paperId) {
          const response = await fetch(`/papers/${paperId}/activity?limit=5`);
          const payload = await response.json();
          if (!response.ok) {
            throw new Error(payload.detail || "Failed to load paper activity");
          }
          return {
            summary: payload.summary || summarizeActivityItems(payload.items || []),
            items: payload.items || [],
          };
        }

        async function fetchPaperActivityTranscript(paperId) {
          const response = await fetch(`/papers/${paperId}/activity/export?limit=5`);
          const payload = await response.text();
          if (!response.ok) {
            try {
              const parsed = JSON.parse(payload);
              throw new Error(parsed.detail || "Failed to export paper activity transcript");
            } catch (error) {
              if (error instanceof SyntaxError) {
                throw new Error(payload || "Failed to export paper activity transcript");
              }
              throw error;
            }
          }
          return payload;
        }

        async function fetchPaperDemoRecapMarkdown(paperId) {
          const response = await fetch(`/papers/${paperId}/demo-recap/export?activity_limit=5`);
          const payload = await response.text();
          if (!response.ok) {
            try {
              const parsed = JSON.parse(payload);
              throw new Error(parsed.detail || "Failed to export paper demo recap");
            } catch (error) {
              if (error instanceof SyntaxError) {
                throw new Error(payload || "Failed to export paper demo recap");
              }
              throw error;
            }
          }
          return payload;
        }

        async function fetchPaperMetadataHistoryMarkdown(paperId) {
          const response = await fetch(`/papers/${paperId}/metadata/history/export?limit=10`);
          const payload = await response.text();
          if (!response.ok) {
            try {
              const parsed = JSON.parse(payload);
              throw new Error(parsed.detail || "Failed to export operator metadata history");
            } catch (error) {
              if (error instanceof SyntaxError) {
                throw new Error(payload || "Failed to export operator metadata history");
              }
              throw error;
            }
          }
          return payload;
        }

        async function savePaperMetadata(paperId, payload) {
          const response = await fetch(`/papers/${paperId}/metadata`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          });
          const responsePayload = await response.json();
          if (!response.ok) {
            throw new Error(responsePayload.detail || "Failed to update paper metadata");
          }
          return responsePayload;
        }

        async function updatePaperDetails(paperId) {
          const paper = paperRecords.find((item) => item.paper_id === paperId);
          if (!paper) {
            paperDetails.hidden = true;
            paperSummary.innerHTML = "";
            paperSignals.innerHTML = "";
            paperNotes.innerHTML = "";
            paperHistory.innerHTML = "";
            paperActivity.innerHTML = "";
            resetBriefUi();
            return;
          }

          const summary = paper.summary_metadata || {};
          const extracted = summary.extracted_summary || {};
          const artifactValidation = paper.artifact_validation || {};
          const provenance = paper.provenance || {};
          const missingArtifacts = artifactValidation.missing_required || [];
          const chunkingStrategies = Object.entries(summary.chunking_strategies || {}).map(([name, count]) => `${name}: ${count}`);

          paperSummary.innerHTML = [
            renderDetailCard("Paper summary", `
              <p><strong>Title:</strong> ${paper.title || "Unknown"}</p>
              <p><strong>Pages:</strong> ${paper.page_count || 0}</p>
              <p><strong>Chunks:</strong> ${paper.num_chunks || 0}</p>
              <p><strong>File size:</strong> ${formatFileSize(paper.file_size_bytes)}</p>
            `),
            renderDetailCard("Provenance", `
              <p><strong>Source label:</strong> ${provenance.source_label || paper.original_filename || "Unknown"}</p>
              <p><strong>Uploaded via:</strong> ${provenance.uploaded_via || "Unknown"}</p>
              <p><strong>Created:</strong> ${paper.created_at || "Unknown"}</p>
              <p><strong>Artifact status:</strong> ${artifactValidation.all_required_present ? "All required artifacts present" : `Missing ${missingArtifacts.join(", ") || "required artifacts"}`}</p>
            `),
            renderDetailCard("Abstract preview", summary.abstract_preview ? `<p>${summary.abstract_preview}</p>` : '<p class="muted">No abstract preview extracted.</p>'),
          ].join("");

          paperSignals.innerHTML = [
            renderDetailCard("Extracted datasets", renderChips(extracted.datasets, "No datasets detected")),
            renderDetailCard("Sample sizes", renderChips((extracted.sample_sizes || []).map(String), "No sample sizes detected")),
            renderDetailCard("Sections and chunking", `
              <p><strong>Sections:</strong> ${summary.section_count || 0}</p>
              ${renderChips(summary.section_names, "No sections detected")}
              <div style="margin-top: 10px;">${renderChips(chunkingStrategies, "No chunking metadata")}</div>
            `),
            renderDetailCard("Study signals", `
              <p><strong>Limitations</strong></p>
              ${renderList(extracted.limitations, "No limitations extracted")}
              <p style="margin-top: 10px;"><strong>Inclusion criteria</strong></p>
              ${renderList(extracted.inclusion_criteria, "No inclusion criteria extracted")}
              <p style="margin-top: 10px;"><strong>Exclusion criteria</strong></p>
              ${renderList(extracted.exclusion_criteria, "No exclusion criteria extracted")}
            `),
          ].join("");

          paperNotes.innerHTML = [
            renderDetailCard("Automated ingestion notes", renderList(paper.ingestion_notes, "No ingestion notes recorded")),
            renderDetailCard("Operator notes", renderList(paper.operator_ingestion_notes, "No operator notes added yet")),
          ].join("");

          paperHistory.innerHTML = renderDetailCard("Operator metadata history", renderMetadataHistory(paper.operator_metadata_history, provenance));
          paperActivity.innerHTML = [
            renderDetailCard("Recent activity summary", '<p class="muted">Loading recent activity...</p>'),
            renderDetailCard("Recent question history", '<p class="muted">Loading recent activity...</p>'),
          ].join("");
          paperDetails.hidden = false;
          resetBriefUi();
          populateMetadataEditor(paper);

          try {
            const activity = await fetchPaperActivity(paperId);
            paperActivity.innerHTML = [
              renderDetailCard("Recent activity summary", renderActivitySummary(activity)),
              renderDetailCard("Recent question history", renderActivityItems(activity.items)),
            ].join("");
          } catch (error) {
            paperActivity.innerHTML = [
              renderDetailCard("Recent activity summary", `<p class="muted">${escapeHtml(error.message)}</p>`),
              renderDetailCard("Recent question history", `<p class="muted">${escapeHtml(error.message)}</p>`),
            ].join("");
          }
        }

        async function refreshPapers(selectedPaperId = "") {
          const [papersResponse, librarySummary] = await Promise.all([
            fetch("/papers"),
            fetchPaperLibrarySummary(),
          ]);
          const payload = await papersResponse.json();
          const papers = payload.papers || [];
          paperRecords = papers;
          renderPaperLibrarySummary(librarySummary);

          const preferredPaperId = selectedPaperId || paperSelect.value || initialUiState.paperId || "";
          const visiblePapers = renderPaperOptions(preferredPaperId);
          const fallbackPaperId = visiblePapers[0] && visiblePapers[0].paper_id;
          const nextPaperId = preferredPaperId || fallbackPaperId || "";
          if (nextPaperId && !visiblePapers.some((paper) => paper.paper_id === nextPaperId)) {
            paperSelect.value = "";
            syncUrlState({ paperId: "" });
            await updatePaperDetails("");
            return;
          }

          if (nextPaperId) {
            paperSelect.value = nextPaperId;
          }
          syncUrlState({ paperId: nextPaperId || "" });
          await updatePaperDetails(nextPaperId || "");
        }

        async function refreshDemoQuestionPresets(selectedValue = "") {
          const response = await fetch("/demo/question-presets");
          const payload = await response.json();
          demoQuestionPresets = Array.isArray(payload) ? payload : [];
          const preferredQuestionPreset = selectedValue || questionPresetSelect.value || initialUiState.questionPreset || "";
          const presets = renderQuestionPresetOptions(preferredQuestionPreset);
          if (preferredQuestionPreset && !presets.some((item) => item.value === preferredQuestionPreset)) {
            questionPresetSelect.value = "";
            syncUrlState({ questionPreset: "" });
          } else if (preferredQuestionPreset) {
            questionPresetSelect.value = preferredQuestionPreset;
            syncUrlState({ questionPreset: preferredQuestionPreset });
          }
          updateQuestionPresetMeta();
        }

        async function checkHealth() {
          try {
            const response = await fetch("/health");
            const payload = await response.json();
            healthStatus.textContent = `${payload.status} (v${payload.version})`;
          } catch (error) {
            healthStatus.textContent = "unreachable";
          }
        }

        questionPresetSelect.addEventListener("change", () => {
          updateQuestionPresetMeta();
          syncUrlState({ questionPreset: questionPresetSelect.value });
        });

        retrievalModeInput.addEventListener("change", (event) => {
          syncUrlState({ retrievalMode: event.target.value });
        });

        for (const input of [topKInput, denseWeightInput, lexicalWeightInput, rrfKInput]) {
          input.addEventListener("change", () => {
            syncUrlState();
          });
        }

        loadQuestionPresetButton.addEventListener("click", () => {
          loadSelectedQuestionPreset();
        });

        resetRetrievalPresetButton.addEventListener("click", () => {
          applyRetrievalUiState(DEFAULT_RETRIEVAL_UI_STATE);
          setStatus(retrievalPresetStatus, "Reset retrieval controls to defaults and cleared shared URL preset values.", "success");
          syncUrlState({
            retrievalMode: DEFAULT_RETRIEVAL_UI_STATE.retrievalMode,
            topK: DEFAULT_RETRIEVAL_UI_STATE.topK,
            denseWeight: DEFAULT_RETRIEVAL_UI_STATE.denseWeight,
            lexicalWeight: DEFAULT_RETRIEVAL_UI_STATE.lexicalWeight,
            rrfK: DEFAULT_RETRIEVAL_UI_STATE.rrfK,
          });
        });

        paperSearchInput.addEventListener("input", async () => {
          const previouslySelectedPaperId = paperSelect.value;
          const visiblePapers = renderPaperOptions(previouslySelectedPaperId);
          const nextPaperId = visiblePapers.some((paper) => paper.paper_id === previouslySelectedPaperId)
            ? previouslySelectedPaperId
            : "";
          paperSelect.value = nextPaperId;
          syncUrlState({ paperId: nextPaperId });
          await updatePaperDetails(nextPaperId);
        });

        paperSelect.addEventListener("change", async (event) => {
          syncUrlState({ paperId: event.target.value });
          await updatePaperDetails(event.target.value);
        });

        paperActivity.addEventListener("click", (event) => {
          const button = event.target.closest(".reuse-question-button");
          if (!button) {
            return;
          }
          reuseRecentQuestion(button.dataset.question || "");
        });

        copyLibrarySummaryButton.addEventListener("click", async () => {
          await handleLibrarySummaryAction("copy");
        });

        downloadLibrarySummaryButton.addEventListener("click", async () => {
          await handleLibrarySummaryAction("download");
        });

        copyBriefButton.addEventListener("click", async () => {
          await handleBriefAction("copy");
        });

        downloadBriefButton.addEventListener("click", async () => {
          await handleBriefAction("download");
        });

        copyActivityButton.addEventListener("click", async () => {
          await handleActivityTranscriptAction("copy");
        });

        downloadActivityButton.addEventListener("click", async () => {
          await handleActivityTranscriptAction("download");
        });

        clearActivityButton.addEventListener("click", async () => {
          await handleClearPaperActivity();
        });

        copyDemoRecapButton.addEventListener("click", async () => {
          await handleDemoRecapAction("copy");
        });

        downloadDemoRecapButton.addEventListener("click", async () => {
          await handleDemoRecapAction("download");
        });

        copyMetadataHistoryButton.addEventListener("click", async () => {
          await handleMetadataHistoryAction("copy");
        });

        downloadMetadataHistoryButton.addEventListener("click", async () => {
          await handleMetadataHistoryAction("download");
        });

        deletePaperButton.addEventListener("click", async () => {
          await handleDeletePaper();
        });

        saveMetadataButton.addEventListener("click", async () => {
          const paperId = paperSelect.value;
          if (!paperId) {
            setStatus(metadataStatus, "Select a paper first.", "error");
            return;
          }

          saveMetadataButton.disabled = true;
          setStatus(metadataStatus, "Saving operator metadata...", "muted");

          try {
            const paper = paperRecords.find((item) => item.paper_id === paperId) || {};
            const provenance = paper.provenance || {};
            const operatorNotes = parseOperatorNotes(operatorNotesInput.value);
            const operatorUpdateCount = Number(provenance.operator_update_count || 0) + 1;

            await savePaperMetadata(paperId, {
              operator_ingestion_notes: operatorNotes,
              provenance: {
                source_label: sourceLabelInput.value.trim() || null,
                source_url: sourceUrlInput.value.trim() || null,
                citation_hint: citationHintInput.value.trim() || null,
                last_operator_update_at: new Date().toISOString(),
                last_operator_update_source: "web-ui",
                operator_update_count: operatorUpdateCount,
              },
            });

            await refreshPapers(paperId);
            setStatus(metadataStatus, "Metadata saved.", "success");
          } catch (error) {
            setStatus(metadataStatus, error.message, "error");
          } finally {
            saveMetadataButton.disabled = false;
          }
        });

        uploadForm.addEventListener("submit", async (event) => {
          event.preventDefault();
          const fileInput = document.getElementById("paper-file");
          const file = fileInput.files[0];
          if (!file) {
            setStatus(uploadStatus, "Choose a PDF before uploading.", "error");
            return;
          }

          uploadButton.disabled = true;
          setStatus(uploadStatus, "Uploading and processing paper...", "muted");

          try {
            const formData = new FormData();
            formData.append("file", file);
            if (uploadSourceLabelInput.value.trim()) {
              formData.append("source_label", uploadSourceLabelInput.value.trim());
            }
            if (uploadSourceUrlInput.value.trim()) {
              formData.append("source_url", uploadSourceUrlInput.value.trim());
            }
            if (uploadCitationHintInput.value.trim()) {
              formData.append("citation_hint", uploadCitationHintInput.value.trim());
            }
            const response = await fetch("/upload", { method: "POST", body: formData });
            const payload = await response.json();
            if (!response.ok) {
              throw new Error(payload.detail || "Upload failed");
            }

            await refreshPapers(payload.paper_id);
            setStatus(uploadStatus, `Ready: ${payload.title || payload.paper_id} (${payload.num_chunks} chunks)`, "success");
            fileInput.value = "";
            uploadSourceLabelInput.value = "";
            uploadSourceUrlInput.value = "";
            uploadCitationHintInput.value = "";
          } catch (error) {
            setStatus(uploadStatus, error.message, "error");
          } finally {
            uploadButton.disabled = false;
          }
        });

        askForm.addEventListener("submit", async (event) => {
          event.preventDefault();
          const paperId = paperSelect.value;
          const question = document.getElementById("question").value.trim();
          const retrievalMode = retrievalModeInput.value;
          const topK = Number(topKInput.value || 5);
          const denseWeight = Number(denseWeightInput.value || 1.0);
          const lexicalWeight = Number(lexicalWeightInput.value || 1.0);
          const rrfK = Number(rrfKInput.value || 60);

          if (!paperId || !question) {
            setStatus(askStatus, "Select a paper and enter a question.", "error");
            return;
          }

          askButton.disabled = true;
          answerPanel.hidden = true;
          setStatus(askStatus, "Retrieving evidence and generating answer...", "muted");

          try {
            const response = await fetch("/ask", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                paper_id: paperId,
                question,
                top_k: topK,
                retrieval_mode: retrievalMode,
                dense_weight: denseWeight,
                lexical_weight: lexicalWeight,
                rrf_k: rrfK,
              }),
            });
            const payload = await response.json();
            if (!response.ok) {
              throw new Error(payload.detail || "Question failed");
            }

            renderAnswer(payload);
            sourcesEl.innerHTML = "";
            renderEvidence(payload);
            renderRetrievalScores(payload);
            for (const source of payload.sources || []) {
              const item = document.createElement("li");
              item.textContent = source;
              sourcesEl.appendChild(item);
            }
            answerPanel.hidden = false;
            setStatus(askStatus, `Answered with ${payload.retrieval_mode || "dense"} retrieval using ${payload.num_chunks_retrieved} retrieved chunk(s).`, "success");
          } catch (error) {
            setStatus(askStatus, error.message, "error");
          } finally {
            askButton.disabled = false;
          }
        });

        applyRetrievalUiState(initialUiState);
        renderRetrievalPresetStatus(initialUiState);
        syncUrlState({
          retrievalMode: initialUiState.retrievalMode,
          topK: initialUiState.topK,
          denseWeight: initialUiState.denseWeight,
          lexicalWeight: initialUiState.lexicalWeight,
          rrfK: initialUiState.rrfK,
        });
        checkHealth();
        refreshPapers(initialUiState.paperId);
        refreshDemoQuestionPresets(initialUiState.questionPreset);
      </script>
    </body>
    </html>
    """
).strip()
