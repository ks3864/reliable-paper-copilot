# Deployment Notes

This project is still local-first. The safest default is to run the FastAPI app on the same machine where you upload papers and open the browser UI.

## Recommended local setup

Run everything on one host:

```bash
make install
make run-api
```

Then open `http://127.0.0.1:8000` in your browser.

This keeps three things together:

- uploaded PDFs
- persisted `data/` artifacts and indexes
- the browser session that drives demos

## Local Docker setup

If you want a cleaner demo environment, run the app with Docker Compose:

```bash
docker compose up --build
```

The compose file mounts `./data` into the container so ingestion outputs survive restarts.

## Split-host workflow for browser-assisted demos

A reasonable portfolio-demo pattern is:

- **host A**: the machine running this API and storing `data/`
- **host B**: the browser you use for screen sharing, remote control, or live walkthroughs

In that model, keep ingestion and retrieval on host A, and use host B only as a browser client.

### When split-host is useful

Use this when:

- the API runs on a stronger workstation or homelab box
- you want to demo from a lighter laptop
- a browser automation tool or remote browser session lives on another machine

### Guardrails

For this project, prefer these guardrails:

1. Keep a single writable `data/` directory on the API host.
2. Do not upload the same paper into separate unsynced deployments if you want reproducible demos.
3. Treat the browser host as stateless. It should call the API, not store canonical artifacts.
4. Bind the API to a trusted interface only, unless you intentionally place it behind a reverse proxy or tunnel.

### Minimal split-host run pattern

On the API host:

```bash
make run-api
```

If you need LAN access for another browser host, start uvicorn on all interfaces instead of the localhost-only default:

```bash
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

Then from the browser host, open:

```text
http://<api-host>:8000
```

### Reverse proxy or tunnel note

If you expose the app beyond your local machine, put a small reverse proxy or authenticated tunnel in front of it.
This repo does not yet include production auth, multi-user isolation, or hardened upload controls.

## Browser-assisted workflow note

The built-in UI is enough for most demos:

1. open the web UI
2. upload a paper
3. ask a question
4. inspect the evidence panel and retrieval scores

If you use a separate browser automation or remote-browser environment, point it at the same API base URL and keep the paper registry on the API host.
That preserves the main portfolio value: reproducible ingestion, grounded answers, and persistent metadata.

## Current recommendation

For interviews, walkthroughs, and portfolio sharing:

- use local single-host deployment whenever possible
- use split-host only for convenience or screen-sharing constraints
- avoid calling this production-ready internet-facing software without adding auth and deployment hardening first
