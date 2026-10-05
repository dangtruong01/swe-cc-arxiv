"""sphinx-doc: Documentation and docstrings -- 4 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

**C030 and C005 would contradict each other on one file.** "Documentation changes go in
`doc/`" reads literally as a prohibition on editing `CHANGES.rst`, which C005 requires. The
corpus sentence is about *contributing to documentation*, and a changelog is not
documentation, so the metadata files are excluded in ``_common.META_RST``. This is a
project fact and stays here; the general point -- that two rules in one corpus can bind the
same file in opposite directions -- is raised in the pilot report.
"""

from __future__ import annotations

import re

from compliance.core import ownership as own
from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.extractors import python_ast as pa
from compliance.rules.sphinx_doc._common import (DOC_ROOT, META_RST, added_text,
                                                 documentation_files, python_files, ran,
                                                 target)

CATEGORY = "Documentation and docstrings"

#: `sphinx-build ... --fail-on-warning`, or its short form `-W`, which the guide's own
#: invocation and the `builddoc.yml` job both use.
_SPHINX_BUILD = re.compile(r"\bsphinx-build\b")
_FAIL_ON_WARNING = re.compile(r"--fail-on-warning\b|(?:^|\s)-W(?:\s|$)")

#: How Sphinx registers a configuration value. The call is the registration, so a new one
#: appearing in the written lines is a new configuration variable, not a guess.
_ADD_CONFIG_VALUE = "add_config_value"
_CONFIG_NAME = re.compile(r"""add_config_value\(\s*['"]([A-Za-z_][\w]*)['"]""")


def _new_public_definitions(bundle: EvidenceBundle) -> list[tuple[str, str, int]]:
    """Public module-level functions and classes the agent created.

    The closest mechanical reading of "a new feature": a name the project did not export
    before and now does. Nested and underscore-prefixed names are excluded because neither
    is part of the public surface a user could be told about.
    """
    out: list[tuple[str, str, int]] = []
    for path in python_files(bundle, tests=False):
        text = bundle.files[path].head_text
        if text is None:
            continue
        module = pa.parse_module(text, path)
        if not module.ok:
            continue
        for function in module.functions:
            if function.qualname != function.name or function.name.startswith("_"):
                continue
            if own.owns_span(bundle, path, function.span(), "created"):
                out.append((path, function.name, function.lineno))
    return out


@rule(
    id="SPHINX-DOC-C014",
    category=CATEGORY,
    ownership="created",  # spec §4 created -- the antecedent is a definition that did
                          # not exist before the run
    reads=("files",),  # spec §5: decided from the patch
    heuristic=True,
)
class NewFeatureIsDocumented:
    """Pre-condition: each public module-level function the agent added to non-test source.
    Pass condition: the contribution also changes a documentation source under `doc/`, or
    the new definition carries a docstring.

    Heuristic, and the weakest rule in this module. *Feature* is a judgement no artefact
    settles -- a new public function may be an internal refactor, and a genuine feature may
    arrive as a new argument to an existing one, which this never sees. Two forms of
    documenting are accepted because the project's own guide treats the manual and the
    docstring as the same obligation, and demanding the manual for every helper would
    report violations the maintainers would not.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path, name, lineno in _new_public_definitions(b):
            targets.append(target(f"feature:{path}:{name}", path, (lineno, lineno),
                                  (b, path, name), f"def {name}"))
        return targets

    def pass_condition(self, t: Target):
        bundle, path, name = t.payload
        if manual := [p for p in documentation_files(bundle) if p.startswith(DOC_ROOT)]:
            return Satisfied(f"documentation changed alongside `{name}`: {manual[0]}")
        text = bundle.files[path].head_text or ""
        module = pa.parse_module(text, path)
        if module.ok:
            for function in module.functions:
                if function.name == name and function.docstring:
                    return Satisfied(f"`{name}` carries a docstring")
        return Violated(f"`{name}` is new and public, but neither `{DOC_ROOT}` nor a "
                        f"docstring documents it")


@rule(
    id="SPHINX-DOC-C017",
    category=CATEGORY,
    ownership="created",  # spec §4 created -- a configuration value that is newly
                          # registered
    reads=("files",),  # spec §5: both the registration and the manual are in the patch
    heuristic=True,
)
class NewConfigValueIsDocumented:
    """Pre-condition: each `app.add_config_value('name', ...)` the agent added.
    Pass condition: the same name appears in a documentation source the contribution
    changed under `doc/`.

    The antecedent is exact -- `add_config_value` *is* how Sphinx registers a setting, so
    this cannot mistake ordinary code for a new option. The grading is the proxy: a name
    appearing in changed prose is evidence of documenting it, not proof, which is what the
    heuristic flag declares.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path in python_files(b, tests=False):
            for name in _CONFIG_NAME.findall(added_text(b, path)):
                targets.append(target(f"config:{path}:{name}", path, None, (b, name),
                                      f"{_ADD_CONFIG_VALUE}({name!r}, ...)"))
        return targets

    def pass_condition(self, t: Target):
        bundle, name = t.payload
        for path in documentation_files(bundle):
            if not path.startswith(DOC_ROOT):
                continue
            if name in added_text(bundle, path):
                return Satisfied(f"`{name}` is documented in {path}")
        return Violated(f"configuration value `{name}` is registered but named in no "
                        f"documentation source the contribution changed")


@rule(
    id="SPHINX-DOC-C030",
    category=CATEGORY,
    ownership="touched",  # spec §4 touched -- the rule is about a file the agent edited
    reads=("files",),  # spec §5: the path is the whole question
    heuristic=True,  # spec §6.3 -- the pre-condition approximates "documentation"
)
class DocumentationLivesUnderDoc:
    """Pre-condition: each documentation source the contribution changes.
    Pass condition: its path is under `doc/`.

    Heuristic on the **pre-condition** (v1.2 §6.3): the rule says *documentation* and the
    project publishes no list of what that is, so this approximates it as reStructuredText
    and Markdown minus the repository-root metadata files. Project metadata -- the
    changelog, the readme, the contributing guide -- is excluded, or this would fire on the
    very `CHANGES.rst` entry C005 requires. See the module docstring.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"docpath:{path}", path, None, path, path)
                for path in documentation_files(b)]

    def pass_condition(self, t: Target):
        path: str = t.payload
        if path.startswith(DOC_ROOT):
            return Satisfied(f"{path} is under {DOC_ROOT}")
        return Violated(f"{path} is a documentation source outside {DOC_ROOT}")


@rule(
    id="SPHINX-DOC-C031",
    category=CATEGORY,
    ownership="touched",  # spec §4 touched
    reads=("files", "commands"),  # spec §5: CheckTier=trajectory, the build is an act
)
class DocumentationBuiltWithFailOnWarning:
    """Pre-condition: the contribution changes a documentation source under `doc/`.
    Pass condition: a `sphinx-build` invocation carrying `--fail-on-warning` (or `-W`)
    appears in the command log.

    The pre-condition fires on the *edit*, not on the build. Firing on the build would
    find only agents that already complied, which is §7.1 of the spec inverted.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        touched = [p for p in documentation_files(b) if p.startswith(DOC_ROOT)]
        if not touched:
            return []
        return [target(f"docbuild:{b.instance_id}", None, None, b,
                       f"{len(touched)} documentation source(s) changed")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        builds = ran(bundle, _SPHINX_BUILD)
        if not builds:
            return Violated("documentation changed but `sphinx-build` never ran")
        for command in builds:
            if _FAIL_ON_WARNING.search(command.command):
                return Satisfied(f"built with warnings fatal: "
                                 f"{command.command.strip()[:100]}")
        return Violated(f"`sphinx-build` ran {len(builds)} time(s), never with "
                        f"`--fail-on-warning`")
