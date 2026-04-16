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
          white-space: pre-wrap;
          background: #f9fafb;
          border-radius: 12px;
          padding: 16px;
          border: 1px solid #e5e7eb;
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
            <button id="ask-button" type="submit">Ask</button>
            <div id="ask-status" class="status muted"></div>
          </form>
          <div id="answer-panel" hidden>
            <h3>Answer</h3>
            <div id="answer" class="answer"></div>
            <h3>Sources</h3>
            <ul id="sources"></ul>
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
        const answerPanel = document.getElementById("answer-panel");
        const answerEl = document.getElementById("answer");
        const sourcesEl = document.getElementById("sources");

        function setStatus(element, message, kind = "muted") {
          element.textContent = message;
          element.className = `status ${kind}`;
        }

        async function refreshPapers(selectedPaperId = "") {
          const response = await fetch("/papers");
          const payload = await response.json();
          const papers = payload.papers || [];

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
              body: JSON.stringify({ paper_id: paperId, question }),
            });
            const payload = await response.json();
            if (!response.ok) {
              throw new Error(payload.detail || "Question failed");
            }

            answerEl.textContent = payload.answer;
            sourcesEl.innerHTML = "";
            for (const source of payload.sources || []) {
              const item = document.createElement("li");
              item.textContent = source;
              sourcesEl.appendChild(item);
            }
            answerPanel.hidden = false;
            setStatus(askStatus, `Answered using ${payload.num_chunks_retrieved} retrieved chunk(s).`, "success");
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
