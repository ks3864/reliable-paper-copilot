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
        input[type="file"], textarea, select {
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
              <div class="actions-row">
                <button id="copy-brief-button" class="button-secondary" type="button">Copy paper brief</button>
                <button id="download-brief-button" class="button-secondary" type="button">Download paper brief</button>
                <span id="brief-status" class="status muted"></span>
              </div>
              <pre id="brief-preview" class="brief-preview" hidden></pre>
            </div>
            <div>
              <label for="paper-id">Paper</label>
              <select id="paper-id" required>
                <option value="">Select an uploaded paper</option>
              </select>
            </div>
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
        const askForm = document.getElementById("ask-form");
        const askButton = document.getElementById("ask-button");
        const askStatus = document.getElementById("ask-status");
        const paperSelect = document.getElementById("paper-id");
        const paperDetails = document.getElementById("paper-details");
        const paperSummary = document.getElementById("paper-summary");
        const paperSignals = document.getElementById("paper-signals");
        const paperNotes = document.getElementById("paper-notes");
        const answerPanel = document.getElementById("answer-panel");
        const answerEl = document.getElementById("answer");
        const sourcesEl = document.getElementById("sources");
        const evidenceEl = document.getElementById("evidence");
        const retrievalMetaEl = document.getElementById("retrieval-meta");
        const retrievalScoresEl = document.getElementById("retrieval-scores");
        const copyBriefButton = document.getElementById("copy-brief-button");
        const downloadBriefButton = document.getElementById("download-brief-button");
        const briefStatus = document.getElementById("brief-status");
        const briefPreview = document.getElementById("brief-preview");
        let paperRecords = [];

        function setStatus(element, message, kind = "muted") {
          element.textContent = message;
          element.className = `status ${kind}`;
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

        function buildBriefMarkdown(brief) {
          const overview = brief.overview || {};
          const studySignals = brief.study_signals || {};
          const ingestion = brief.ingestion || {};
          const artifactValidation = ingestion.artifact_validation || {};
          const provenance = ingestion.provenance || {};

          const formatList = (items, fallback = "None") => {
            if (!items || !items.length) {
              return fallback;
            }
            return items.map((item) => `- ${item}`).join("\n");
          };

          const formatEntries = (entries) => {
            const rows = Object.entries(entries || {});
            if (!rows.length) {
              return "None";
            }
            return rows.map(([key, value]) => `- ${key}: ${value}`).join("\n");
          };

          return [
            `# ${brief.title || brief.paper_id}`,
            "",
            `- Paper ID: ${brief.paper_id}`,
            `- Status: ${brief.status || "unknown"}`,
            `- Original filename: ${brief.original_filename || "Unknown"}`,
            `- Created: ${brief.created_at || "Unknown"}`,
            "",
            "## Overview",
            `- Authors: ${(overview.authors || []).join(", ") || "Unknown"}`,
            `- Pages: ${overview.page_count || 0}`,
            `- Chunks: ${overview.num_chunks || 0}`,
            `- Sections: ${overview.section_count || 0}`,
            `- Tables: ${overview.tables_count || 0}`,
            `- Total word count: ${overview.total_word_count || 0}`,
            `- Section names: ${(overview.section_names || []).join(", ") || "None"}`,
            `- Abstract preview: ${overview.abstract_preview || "Not available"}`,
            "",
            "## Study signals",
            "### Datasets",
            formatList(studySignals.datasets),
            "",
            "### Sample sizes",
            formatList((studySignals.sample_sizes || []).map(String)),
            "",
            "### Limitations",
            formatList(studySignals.limitations),
            "",
            "### Inclusion criteria",
            formatList(studySignals.inclusion_criteria),
            "",
            "### Exclusion criteria",
            formatList(studySignals.exclusion_criteria),
            "",
            "### Extracted counts",
            formatEntries(studySignals.counts),
            "",
            "## Ingestion",
            `- Artifacts complete: ${artifactValidation.all_required_present ? "yes" : "no"}`,
            `- Missing required artifacts: ${(artifactValidation.missing_required || []).join(", ") || "None"}`,
            `- Source label: ${provenance.source_label || "Unknown"}`,
            `- Uploaded via: ${provenance.uploaded_via || "Unknown"}`,
            `- Source URL: ${provenance.source_url || "Unknown"}`,
            "",
            "### Automated ingestion notes",
            formatList(ingestion.ingestion_notes),
            "",
            "### Operator notes",
            formatList(ingestion.operator_ingestion_notes),
            "",
            "### Chunking strategies",
            formatEntries(overview.chunking_strategies),
          ].join("\n");
        }

        async function fetchPaperBrief(paperId) {
          const response = await fetch(`/papers/${paperId}/brief`);
          const payload = await response.json();
          if (!response.ok) {
            throw new Error(payload.detail || "Failed to load paper brief");
          }
          return payload;
        }

        async function handleBriefAction(action) {
          const paperId = paperSelect.value;
          if (!paperId) {
            setStatus(briefStatus, "Select a paper first.", "error");
            return;
          }

          copyBriefButton.disabled = true;
          downloadBriefButton.disabled = true;
          setStatus(briefStatus, "Preparing paper brief...", "muted");

          try {
            const brief = await fetchPaperBrief(paperId);
            const briefMarkdown = buildBriefMarkdown(brief);
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
            anchor.download = `${brief.paper_id}-paper-brief.md`;
            document.body.appendChild(anchor);
            anchor.click();
            anchor.remove();
            URL.revokeObjectURL(url);
            setStatus(briefStatus, `Downloaded ${anchor.download}.`, "success");
          } catch (error) {
            setStatus(briefStatus, error.message, "error");
          } finally {
            copyBriefButton.disabled = false;
            downloadBriefButton.disabled = false;
          }
        }

        function updatePaperDetails(paperId) {
          const paper = paperRecords.find((item) => item.paper_id === paperId);
          if (!paper) {
            paperDetails.hidden = true;
            paperSummary.innerHTML = "";
            paperSignals.innerHTML = "";
            paperNotes.innerHTML = "";
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

          paperDetails.hidden = false;
          resetBriefUi();
        }

        async function refreshPapers(selectedPaperId = "") {
          const response = await fetch("/papers");
          const payload = await response.json();
          const papers = payload.papers || [];
          paperRecords = papers;

          paperSelect.innerHTML = '<option value="">Select an uploaded paper</option>';
          for (const paper of papers) {
            const option = document.createElement("option");
            option.value = paper.paper_id;
            option.textContent = paper.title ? `${paper.title} (${paper.paper_id.slice(0, 8)})` : paper.paper_id;
            if (paper.paper_id === selectedPaperId) {
              option.selected = true;
            }
            paperSelect.appendChild(option);
          }

          updatePaperDetails(selectedPaperId || paperSelect.value);
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

        paperSelect.addEventListener("change", (event) => {
          updatePaperDetails(event.target.value);
        });

        copyBriefButton.addEventListener("click", async () => {
          await handleBriefAction("copy");
        });

        downloadBriefButton.addEventListener("click", async () => {
          await handleBriefAction("download");
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
            const response = await fetch("/upload", { method: "POST", body: formData });
            const payload = await response.json();
            if (!response.ok) {
              throw new Error(payload.detail || "Upload failed");
            }

            await refreshPapers(payload.paper_id);
            setStatus(uploadStatus, `Ready: ${payload.title || payload.paper_id} (${payload.num_chunks} chunks)`, "success");
            fileInput.value = "";
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
          const retrievalMode = document.getElementById("retrieval-mode").value;
          const topK = Number(document.getElementById("top-k").value || 5);
          const denseWeight = Number(document.getElementById("dense-weight").value || 1.0);
          const lexicalWeight = Number(document.getElementById("lexical-weight").value || 1.0);
          const rrfK = Number(document.getElementById("rrf-k").value || 60);

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

        checkHealth();
        refreshPapers();
      </script>
    </body>
    </html>
    """
).strip()
