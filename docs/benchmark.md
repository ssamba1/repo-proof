# RepoProof benchmark

Measured against real, popular GitHub repositories. Regenerate with
`python tools/benchmark.py --run`.

## Tier 1 — extraction (the moat claim)

**13/20** repos: a runnable quickstart command was extracted from arbitrary
prose with zero config. **4/20** had an install step but no shell run
command (typical of libraries whose example is a code snippet, not a CLI invocation).

| Repo | Lang | Kind | Result | Extracted run command |
|------|------|------|--------|------------------------|
| httpie/httpie | python | cli | found_run | `https httpie.io/hello` |
| sherlock-project/sherlock | python | cli | found_run | `sherlock user123` |
| yt-dlp/yt-dlp | python | cli | found_run | `yt-dlp --print filename -o "test video.%(ext)s" BaW_jenozKc` |
| psf/requests | python | lib | install_only | — |
| pallets/click | python | lib | found_run | `python hello.py --count=3` |
| Textualize/rich | python | lib | found_run | `python -m rich.spinner` |
| tj/commander.js | node | lib | found_run | `node split.js -s - --fits a-b-c` |
| chalk/chalk | node | lib | install_only | — |
| sindresorhus/execa | node | lib | install_only | — |
| expressjs/express | node | lib | found_run | `express /tmp/foo` |
| BurntSushi/ripgrep | rust | cli | found_run | `rg -n -w '[A-Z]+_SUSPEND'` |
| sharkdp/bat | rust | cli | found_run | `bat README.md` |
| sharkdp/fd | rust | cli | found_run | `fd -e zip -x unzip` |
| spf13/cobra | go | lib | install_only | — |
| junegunn/fzf | go | cli | found_run | `eval "$(fzf --bash)"` |
| charmbracelet/glow | go | cli | found_run | `nix-shell -p glow --command glow` |
| rails/rails | ruby | lib | found_run | `rails new myapp` |
| fastlane/fastlane | ruby | cli | none | — |
| Homebrew/brew | ruby | cli | none | — |
| jekyll/jekyll | ruby | cli | none | — |

### Honest read

`found_run` means *a* command was extracted, not that it is guaranteed the intended one.
Manual review of this corpus: about **11/20** extracted the exact intended quickstart,
**4/20** were correctly identified as install-only (libraries whose example is a code
snippet, not a CLI invocation), and **3/20** were correctly reported as having *no*
in-repo quickstart at all — fastlane, Homebrew, and jekyll ship landing-page READMEs
whose actual getting-started lives off-site, so `none` is the honest answer, not a miss.
That is ~**18/20 handled correctly**, up from a ~6/16 baseline. Two soft spots remain:
fzf (extracts the shell-completion `eval` line) and glow (extracts a `nix-shell` wrapper)
— *a* runnable command, just not the cleanest demo of the tool itself.

ripgrep used to extract `cargo test --all` (its only fenced 'run' block); two-phase
ranking now demerits build/test commands and mines the `rg …` usage example from prose,
so it extracts the intended quickstart instead.

**Known limitation / roadmap:** READMEs that show usage only as an image/asciicast, and
picking the single *best* example when a tool documents many equally-valid invocations.

