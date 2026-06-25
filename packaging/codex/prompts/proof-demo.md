Run RepoProof to capture a real demo of a repository. The artifact it writes is a genuine
capture of the program running — not a mockup. Report exactly where the artifact was written.

Target repo path: `$ARGUMENTS` (default to the current directory if empty).

Run exactly this command and wait for it to finish:

```
python "@@PROOF_RUN@@" demo $ARGUMENTS
```

Then report the artifact path and the capture tool used (vhs / text-fallback / playwright). If the
project is a web app, tell the user to re-run with `--web <url>` against a running instance.
