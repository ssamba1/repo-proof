Run RepoProof to verify a repository's README quickstart actually runs, and report the result
faithfully. Never claim the quickstart works unless RepoProof itself exits 0, and never invent a
fix RepoProof did not produce.

Target repo path: `$ARGUMENTS` (default to the current directory if empty).

Run exactly this command and wait for it to finish:

```
python "@@PROOF_RUN@@" verify $ARGUMENTS
```

Then summarize:
- the outcome (verified / fixed / real_code_bug / needs_services / needs_input / extraction_failed),
- any proposed README edit (old -> new),
- the exit code (0 = pass or legitimately skipped; non-zero = a real problem).
