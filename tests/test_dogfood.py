"""The acceptance gate: RepoProof must verify its own README quickstart end to end.

If this fails, RepoProof is shipping a README it cannot stand behind — which is the one
thing the whole product exists to prevent.
"""

from conftest import ROOT
from proof.scripts.models import GOOD_OUTCOMES
from proof.scripts.verify import verify_repo


def test_repoproof_verifies_its_own_readme():
    rep = verify_repo(ROOT, mode="subprocess", timeout_s=300)
    assert rep.outcome in GOOD_OUTCOMES, f"own README quickstart not trustworthy: {rep.notes}"
    assert rep.steps and rep.steps[-1].ok
