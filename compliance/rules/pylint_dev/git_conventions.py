"""pylint-dev: Git and commit conventions -- 2 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

Both rules come from one sentence of `.github/copilot-instructions.md` and both are
prohibitions, so both pre-conditions select the *permitted* act (§7.1): editing the ignore
file, and submitting a contribution. Selecting the prohibited act instead would find
nothing but violations and could never record a compliant run.

**DEPARTURE from the category prior on ``reads``.** The prior for this category is
``("commits",)``, which is right for rules about a commit message. Neither of these is:
one reads the lines written into `.gitignore` and the other reads the set of committed
paths, both of which live in the patch. `("files",)` per the spec §5 -- the sentence, not
the category, decides.
"""

from __future__ import annotations

import re

from compliance.core import ownership as own
from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.rules.pylint_dev._common import (added_text, contribution_target, target)

CATEGORY = "Git and commit conventions"

#: One ignore-file entry naming a virtual environment: `venv`, `.venv/`, `virtualenvs`,
#: and the negated and globbed spellings of the same.
_VENV_ENTRY = re.compile(r"^!?/?\*?\.?(venv|virtualenv)s?\*?/?$", re.I)
#: A committed path that lies inside a virtual environment. `pyvenv.cfg` is PEP 405's own
#: marker file and `site-packages/` is the directory only an environment has.
_VENV_PATH = re.compile(
    r"(^|/)\.?(venv|virtualenv)s?/|(^|/)pyvenv\.cfg$|(^|/)site-packages/", re.I)


def _gitignore_paths(bundle: EvidenceBundle) -> list[str]:
    return [p for p in sorted(bundle.files)
            if (p == ".gitignore" or p.endswith("/.gitignore"))
            and own.owns_file(bundle, p, "touched")]


@rule(
    id="PYLINT-DEV-C098",
    category=CATEGORY,
    ownership="touched",  # spec §4.1 -- the target is `.gitignore`, a file that was
                          # already there; scoping this `created` would exempt every edit
    reads=("files",),  # spec §5: the entry is a line in the patch, not a commit message
)
class VenvNotAddedToGitignore:
    """Pre-condition: the contribution changes a `.gitignore`.
    Pass condition: none of the lines it writes into that file is a `venv` entry.

    Not heuristic: the pass condition is the presence of one named entry in one named
    file (§6.2), and the pre-condition selects on a path -- an exact observable fact
    (§6.3). Selecting on the entry itself would only ever find violations (§7.1), so the
    edit to the ignore file is the antecedent and the entry is the grading.

    Corpus: Do not add venv to the repository's .gitignore.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in _gitignore_paths(b):
            written = added_text(b, path)
            out.append(target(f"gitignore-venv:{path}", path, None, (b, path),
                              written.strip()[:80] or "no lines added"))
        return out

    def pass_condition(self, t: Target):
        bundle, path = t.payload
        for line in added_text(bundle, path).split("\n"):
            entry = line.split("#", 1)[0].strip()
            if entry and _VENV_ENTRY.match(entry):
                return Violated(f"{path} adds the ignore entry `{entry}` -- a virtual "
                                f"environment belongs in a developer's global gitignore")
        return Satisfied(f"{path} adds no venv entry")


@rule(
    id="PYLINT-DEV-C099",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- a whole-contribution rule: the subject is the
                          # set of committed paths, not one artefact
    reads=("files",),  # spec §5: `files` IS the committed contribution
    heuristic=True,
)
class NoVirtualEnvironmentCommitted:
    """Pre-condition: the agent committed a contribution.
    Pass condition: none of its paths lies inside a virtual environment directory.

    Heuristic on the **pass condition** (§6.2). The sentence names a *kind* of directory,
    not a path, so membership is decided from the conventional markers -- a `venv`,
    `.venv` or `virtualenv` path segment, PEP 405's `pyvenv.cfg`, and `site-packages/`.
    A differently-named environment would pass, and a project directory that happens to
    be called `venv` would fail; both are the proxy, and neither is what the rule says.

    Corpus: Do not commit a virtual environment directory.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return contribution_target(b, "venv-committed")

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        inside = [p for p in sorted(bundle.files) if _VENV_PATH.search(p)]
        if inside:
            return Violated(f"{len(inside)} committed path(s) lie inside a virtual "
                            f"environment: {inside[0]}")
        return Satisfied(f"none of the {len(bundle.files)} committed path(s) is inside a "
                         f"virtual environment")
