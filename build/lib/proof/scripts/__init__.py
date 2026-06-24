"""RepoProof deterministic runtime core.

The skill layer (SKILL.md files) routes user intent; this package does the real,
testable work: extract a quickstart from a README, run it in a sandbox, classify
failures (doc error vs real code bug — never mask a real bug), propose doc-level
fixes, and capture real demos.
"""

__all__ = ["__version__"]
__version__ = "0.1.0"
