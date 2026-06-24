import pytest

from conftest import FIXTURES
from proof.scripts.detect import detect_kind, detect_lang
from proof.scripts.models import Lang, ProjectKind


@pytest.mark.parametrize(
    ("fixture", "lang"),
    [
        ("py-working", Lang.PYTHON),
        ("py-broken", Lang.PYTHON),
        ("node-working", Lang.NODE),
        ("node-broken", Lang.NODE),
        ("rust-working", Lang.RUST),
        ("rust-broken", Lang.RUST),
        ("go-working", Lang.GO),
        ("go-broken", Lang.GO),
        ("ruby-working", Lang.RUBY),
        ("ruby-broken", Lang.RUBY),
    ],
)
def test_detect_lang(fixture, lang):
    assert detect_lang(FIXTURES / fixture) == lang


@pytest.mark.parametrize(
    "fixture",
    ["py-working", "node-working", "rust-working", "go-working", "ruby-working"],
)
def test_detect_kind_is_cli(fixture):
    repo = FIXTURES / fixture
    assert detect_kind(repo, detect_lang(repo)) == ProjectKind.CLI


def test_unknown_lang_for_empty_dir(tmp_path):
    assert detect_lang(tmp_path) == Lang.UNKNOWN
