"""Every row in a run's `rows.jsonl` must belong to that run's own repository.

**WHY THIS TEST EXISTS.** `_REGISTRY` in `compliance/core/registry.py` is a module-level
dict and `registry.rule` refuses duplicate ids, so a scoring process can only ever
ACCUMULATE rule packs -- never swap one for another. A batch scorer that imports each
repository's rules as it reaches that repository, without calling `clear_registry()` in
between, therefore scores every run against its own pack plus every pack imported before
it. That is exactly what `tools/score_corpus.py` did until 16 Sep 2026.

The damage was large and completely silent. 1,401 of 4,000 OpenHands runs carried foreign
rows; 64% of all OpenHands rows belonged to another project. A seaborn run, whose rule base
is two rules, held 280 rows -- astropy's 111 and matplotlib's 167 on top of its own 2.
Foreign rules almost never fire, so they landed in the triggering DENOMINATOR as
`not_applicable` and pushed the rate down: OpenHands read 18-20% where it is 24-28%. On the
contaminated rows OpenHands appeared to comply LESS than mini-swe-agent, when it complies
more -- a reversed finding, from rows that raised no error and looked entirely plausible.

This test is the check that was missing. Nothing else caught the defect: the
cell-for-cell pin in the table script used astropy, which sorts first alphabetically and is therefore the one repository that can
never be contaminated. `tests/test_layers.py` forbids repository names in Layers A and B,
which is a different property entirely.

The property asserted here is the cheapest possible statement of correctness -- a row's
rule id must carry its own repository's prefix -- and it is the one that was missing.
"""
from __future__ import annotations

import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"

# rule-id prefix -> the `runs/<repo>` directory that prefix belongs to.
PREFIX_TO_REPO = {
    "ASTROPY": "astropy", "DJANGO": "django", "MATPLOTLIB": "matplotlib",
    "MWASKOM": "mwaskom", "PALLETS": "pallets", "PSF": "psf", "PYDATA": "pydata",
    "PYLINT": "pylint-dev", "PYTEST": "pytest-dev", "SCIKIT": "scikit-learn",
    "SKLEARN": "scikit-learn", "SPHINX": "sphinx-doc", "SYMPY": "sympy",
}


def scored_runs():
    if not RUNS.is_dir():
        return []
    return sorted(RUNS.glob("*/*/*/*/*/attempt*/rows.jsonl"))


@pytest.mark.skipif(not scored_runs(), reason="no scored runs in this checkout")
def test_no_run_carries_another_repositorys_rules():
    """No `rows.jsonl` may contain a rule id belonging to a different repository."""
    offenders: list[str] = []
    unmapped: set[str] = set()
    for rows_path in scored_runs():
        repo = rows_path.relative_to(RUNS).parts[0]
        foreign = set()
        for line in rows_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rule_id = json.loads(line).get("rule_id", "")
            prefix = rule_id.split("-")[0]
            owner = PREFIX_TO_REPO.get(prefix)
            if owner is None:
                unmapped.add(prefix)
            elif owner != repo:
                foreign.add(prefix)
        if foreign:
            offenders.append(f"{rows_path.relative_to(RUNS).parent}: {sorted(foreign)}")

    # An unmapped prefix is a gap in this test, not proof of cleanliness -- fail loudly
    # rather than quietly passing every row whose owner we could not determine.
    assert not unmapped, (
        f"rule-id prefixes not in PREFIX_TO_REPO: {sorted(unmapped)}. "
        "Add them; until then this test cannot vouch for those rows."
    )
    assert not offenders, (
        f"{len(offenders)} run(s) scored against another repository's rules. "
        "The batch scorer must call registry.clear_registry() between repositories. "
        f"First few: {offenders[:5]}"
    )


def test_score_corpus_clears_the_registry_between_repositories():
    """The source-level guarantee, so a fresh corpus cannot reintroduce the defect.

    The test above only sees runs that are already on disk. This one pins the line in the
    batch scorer that prevents them being written wrong in the first place.
    """
    src = (ROOT / "tools" / "score_corpus.py").read_text(encoding="utf-8")
    assert "clear_registry()" in src, (
        "tools/score_corpus.py must call registry.clear_registry() before loading a "
        "repository's rule modules; without it the registry accumulates packs across "
        "repositories and every run after the first is scored against foreign rules."
    )
    clear_at = src.index("clear_registry()")
    load_at = src.index("load_rule_modules(repo)")
    assert clear_at < load_at, (
        "clear_registry() must come BEFORE load_rule_modules(repo); clearing afterwards "
        "discards the pack that was just loaded."
    )
