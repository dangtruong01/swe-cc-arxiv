"""The paper's names for things the code calls something else.

The code keeps its internal identifiers: a corpus directory is named after the SWE-bench
instance prefix (``pallets`` for ``pallets__flask-*``) and the two policy-provision
settings are stored as ``naive`` and ``guided``. Everything a user reads -- CLI output,
the released results, the regenerated tables -- uses the paper's terms instead. This
module is the one place the two vocabularies meet.
"""

from __future__ import annotations

# SWE-bench instance prefix (corpus directory, policy-id prefix) -> project name in the paper.
PROJECTS: dict[str, str] = {
    "astropy": "astropy",
    "django": "django",
    "matplotlib": "matplotlib",
    "mwaskom": "seaborn",
    "pallets": "flask",
    "psf": "requests",
    "pydata": "xarray",
    "pylint-dev": "pylint",
    "pytest-dev": "pytest",
    "scikit-learn": "scikit-learn",
    "sphinx-doc": "sphinx",
    "sympy": "sympy",
}
PROJECT_SLUGS: dict[str, str] = {name: slug for slug, name in PROJECTS.items()}

# Stored condition -> policy-provision setting in the paper (Section 3.4).
SETTINGS: dict[str, str] = {"naive": "native", "guided": "consolidated"}
CONDITIONS: dict[str, str] = {setting: cond for cond, setting in SETTINGS.items()}

# Corpus `CheckTier` -> evidence type in the paper (Table 6).
EVIDENCE_TYPES: dict[str, str] = {"static": "output", "differential": "differential",
                                  "trajectory": "trajectory"}

# Row verdict/status -> outcome of one policy on one run (Section 3.5, Appendix C.4).
OUTCOMES = ("pass", "fail", "withheld", "not_triggered")


def project_slug(name: str) -> str:
    """Accept either a paper project name or an internal slug; return the slug."""
    if name in PROJECTS:
        return name
    if name in PROJECT_SLUGS:
        return PROJECT_SLUGS[name]
    raise ValueError(f"unknown project {name!r}; expected one of {sorted(PROJECT_SLUGS)}")


def condition(name: str | None) -> str | None:
    """Accept either a paper setting or a stored condition; return the stored condition."""
    if name is None:
        return None
    return CONDITIONS.get(name, name)


def outcome(row: dict) -> str:
    """Collapse a row's verdict and status to one of OUTCOMES, as `summarise` counts them."""
    if row["verdict"] in ("pass", "fail"):
        return row["verdict"]
    if row["status"] in ("tool_missing", "parse_error", "error"):
        return "withheld"
    return "not_triggered"
