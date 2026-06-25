# web-demo fixture

A self-contained static page used to produce a **real** web-demo screenshot for RepoProof's
`proof demo --web` path (Success Criterion 3: a `.png` for a web fixture).

It has no external assets, so it renders fully offline under `file://` or any static server.

## Quickstart

```bash
python -m http.server 8000
```

Then capture it:

```bash
python proof/run.py demo --web http://localhost:8000
```

The committed artifact lives at `docs/web-demo.png` and is embedded in the project README.
