# Per-language quickstart conventions

How RepoProof recognizes and runs each ecosystem.

## Python
- Markers: `pyproject.toml`, `setup.py`, `requirements.txt`.
- Install verbs: `pip install`, `pip3 install`, `pipx install`, `uv pip install`, `poetry install`.
- Run: `python main.py`, `python -m <pkg>`, console-script entrypoints.
- Web markers: flask, django, fastapi, starlette, uvicorn.

## Node
- Markers: `package.json`.
- Install verbs: `npm install`, `npm ci`, `yarn add`, `pnpm install`.
- Run: `node index.js`, `npm start`, scripts in `package.json`.
- Web markers: express, next, vite, react-dom, vue, svelte; plus a `start`/`dev`/`serve` script.

## Rust
- Markers: `Cargo.toml`.
- Build/run: `cargo build`, `cargo run`.
- Web markers: actix-web, axum, rocket.
- Note: on Windows the MSVC linker must be available; a linker failure is an environment
  problem (`sandbox_unavailable`), not a code bug.

## Go
- Markers: `go.mod`.
- Build/run: `go build`, `go run main.go`, `go get`.
- Web markers: detected from imported frameworks where present.

## Ruby
- Markers: `Gemfile`, `*.gemspec`, `.rb` files.
- Install verbs: `gem install`, `bundle install`.
- Run: `ruby main.rb`, `ruby app.rb`.
- Web markers: rails, sinatra, hanami, rack.

## Placeholders
Any command containing `<...>`, `YOUR_...`, `path/to/...`, `example.com`, `{{...}}`, or `${ENV}`
is treated as needing user input and is not executed (outcome `needs_input`).
