"""matplotlib: Specialized changes -- 30 rules.

Layer C. Every rule is two layers (`docs/checker-authoring.md` §2): ``precondition``
selects on the rule's ANTECEDENT, ``pass_condition`` grades.

Six groups: adding an rcParam (C192--C194), the pyplot wrapper contract (C195, C196),
colormaps and styles (C197, C198), the deprecation lifecycle (C202--C217), packaging and
vendored code (C244, C249--C251), and licensing plus minimum versions (C262--C265, C284,
C286, C287).

**The deprecation group is where §7.5 bites hardest.** Five rules reach the same ``.pyi``
stub, so the antecedents are partitioned by the helper that was used:

* **C209** takes deprecations made with ``deprecated``, ``warn_deprecated`` and
  ``deprecate_privatize_attribute``, and asks only whether the stub was touched;
* **C210** takes ``rename_parameter`` and ``make_keyword_only``, and asks whether the
  parameter's name reaches the stub;
* **C211** takes ``delete_parameter``, and asks whether the stub gives it a default;
* **C214** takes *expiry* -- a helper removed -- and asks whether the stub lost the item;
* ``code_quality.C242`` is narrowed to exclude every file that introduces a deprecation,
  because that case is C209's.

Two more pairs are narrowed the same way. **C249 and C250** both reach an edit under
:file:`extern/`: C250 asks whether the edit is a style fix, and C249 fires only on edits
that are *not* style fixes, so a cosmetic edit is one violation rather than two. **C262
and C263** split by tree: vendored code arrives under :file:`extern/`, and a licence
problem in the main code base is C263's.

**Corpus mismatches, recorded rather than corrected in the workbook (§0/§5).** Nine rows
here are filed ``differential``. Five are decidable from the patch and declare
``("files",)``: C196 (the regenerated wrappers are a file in the diff), C197, C203, C206,
C209, C213, C249. Two genuinely need the deprecated API exercised and declare
``deprecated_api_run``: C202 and C213's behavioural half is not asked. C208 needs the
project version at the base commit to know what "the next point release" is; it declares
``repo_version``, the registered Phase 5 source for exactly that, and withholds.
"""

from __future__ import annotations

import ast
import re

from compliance.core.models import (EvidenceBundle, Satisfied, Target, Undetermined,
                                    Violated)
from compliance.core.registry import rule
from compliance.rules.matplotlib._common import (EXTERN_ROOT, LICENSE_ROOT, MATPLOTLIBRC,
                                                 MIN_NUMPY_FILES, MIN_PYTHON_FILES,
                                                 PYPLOT, RCSETUP, TYPING_STUB,
                                                 added_lines, added_text, deprecation_sites,
                                                 expires_deprecation, is_c_source,
                                                 is_package_path, modules, python_files,
                                                 raises_min_numpy, raises_min_python,
                                                 ran, removed_text, satisfies_min_file,
                                                 target)

CATEGORY = "Specialized changes"

# --- rcParams ----------------------------------------------------------------------------

_RC_KEY = re.compile(r"""["']([a-z0-9_]+(?:\.[a-z0-9_]+)+)["']""")
_RC_COMMENTED = re.compile(r"^\s*#\s*([a-z0-9_]+(?:\.[a-z0-9_]+)+)\s*:")
_PARAM_ENTRY = re.compile(r"\b_Param\s*\(")

# --- pyplot wrappers -----------------------------------------------------------------------

#: The two modules whose Axes methods `tools/boilerplate.py` wraps into pyplot.
PYPLOT_WRAPPED = ("lib/matplotlib/axes/_axes.py", "lib/matplotlib/axes/_base.py",
                  "lib/matplotlib/figure.py")
_PYPLOT_UP_TO_DATE = re.compile(r"test_pyplot_up_to_date")

# --- colormaps, colour sequences and styles ------------------------------------------------

COLORMAP_FILES = ("lib/matplotlib/_cm.py", "lib/matplotlib/_cm_listed.py",
                  "lib/matplotlib/_cm_multivar.py", "lib/matplotlib/_cm_bivar.py")
STYLE_ROOT = "lib/matplotlib/mpl-data/stylelib/"
_COLOR_SEQUENCES = re.compile(r"_color_sequences\s*=|\bColorSequenceRegistry\b")
#: Licences matplotlib names as compatible, plus the public-domain dedications its
#: colormaps actually ship under.
BSD_COMPATIBLE = re.compile(
    r"\bBSD\b|\bMIT\b|\bPSF\b|\bPython Software Foundation\b|\bApache\b|\bISC\b"
    r"|\bCC0\b|\bpublic domain\b|\bunlicen[cs]e\b|\bzlib\b", re.I)
COPYLEFT = re.compile(r"\bL?GPL\b|\bGNU (?:Lesser )?General Public License\b"
                      r"|\bAGPL\b|\bAffero\b", re.I)

# --- deprecation lifecycle -------------------------------------------------------------------

PARAMETER_HELPERS = ("rename_parameter", "delete_parameter", "make_keyword_only")
PLAIN_HELPERS = ("deprecated", "warn_deprecated", "deprecate_privatize_attribute")
_HELPER_CALL = re.compile(r"\b(?:_api\.)?(?P<name>deprecated|warn_deprecated"
                          r"|deprecate_privatize_attribute|rename_parameter"
                          r"|delete_parameter|make_keyword_only)\s*\(")
_HAND_ROLLED = re.compile(r"warnings\.warn\s*\(")
_DEPRECATION_CATEGORY = re.compile(r"\b(?:Pending)?DeprecationWarning\b")
_MPL_DEPRECATION = re.compile(r"\bMatplotlibDeprecationWarning\b")
_VERSION = re.compile(r"^(\d+)\.(\d+)")
#: A body that no longer does anything, which is how "still functional" fails visibly.
_GUTTED = re.compile(r"raise\s+NotImplementedError|raise\s+RuntimeError")
MESO_GAP = 2

# --- packaging, vendored code, licences ----------------------------------------------------

MESON = "meson.build"
_MESON_ROOTS = ("lib/", "src/", "extern/")
_NOLINT = re.compile(r"//\s*NOLINT(?P<form>NEXTLINE|BEGIN|END)?(?P<scope>\([^)]*\))?"
                     r"(?P<rest>.*)$")
_THIRD_PARTY = re.compile(r"copyright\s*(?:\(c\)|©)?\s*\d{4}|\bAll rights reserved\b"
                          r"|\bderived from\b|\badapted from\b|\bvendored\b", re.I)
TOOLKIT_ROOT = "lib/mpl_toolkits/"
MAIN_CODE_ROOTS = ("lib/", "src/")
_REQUIRES_PYTHON = re.compile(r"^\s*requires-python\s*=\s*[\"'][^0-9]*"
                              r"(?P<major>\d+)\.(?P<minor>\d+)")
_PY_CLASSIFIER = re.compile(r"Programming Language :: Python :: (?P<major>\d+)\.(?P<minor>\d+)")
_ENV_PYTHON = re.compile(r"^\s*-\s*python\s*[>=~]*\s*(?P<major>\d+)\.(?P<minor>\d+)", re.M)
PYPROJECT = "pyproject.toml"
ENVIRONMENT = "environment.yml"


def _helper_calls(bundle: EvidenceBundle, *, added: bool = True):
    """(path, module, name, ast.Call) for each `_api` deprecation helper in the patch."""
    out = []
    for path, module in modules(bundle, tests=False):
        if not is_package_path(path) or module.tree is None:
            continue
        lines = (bundle.files[path].authored_lines if added
                 else bundle.files[path].modified_lines)
        for node in ast.walk(module.tree):
            if not isinstance(node, ast.Call):
                continue
            name = _dotted(node.func).split(".")[-1]
            if name in PARAMETER_HELPERS + PLAIN_HELPERS and node.lineno in lines:
                out.append((path, module, name, node))
    return out


def _dotted(node) -> str:
    from compliance.extractors.python_ast import dotted_name

    return dotted_name(node)


def _argument(node: ast.Call, index, name: str):
    for keyword in node.keywords:
        if keyword.arg == name:
            return keyword.value
    if index is not None and len(node.args) > index:
        return node.args[index]
    return None


def _literal(node):
    if node is None:
        return None
    try:
        return ast.literal_eval(node)
    except (ValueError, SyntaxError, TypeError):
        return None


def _owner(module, node):
    """The function a helper call applies to: the one it decorates, or the one it sits in.

    A decorator's line is *above* the ``def``, so ``enclosing_function`` cannot find it;
    the decorator list is the only link between the two.
    """
    for function in module.functions:
        if any(d.lineno == node.lineno for d in function.decorators):
            return function
    return module.enclosing_function(node.lineno)


#: Where each parameter helper names the parameter it is about. `rename_parameter` takes
#: ``(since, old, new)`` and the rule is about the *new* name; the other two take
#: ``(since, name)``.
PARAMETER_ARGUMENT = {"rename_parameter": (2, "new"),
                      "delete_parameter": (1, "name"),
                      "make_keyword_only": (1, "name")}


def _named_parameter(name: str, node: ast.Call):
    index, keyword = PARAMETER_ARGUMENT[name]
    return _literal(_argument(node, index, keyword))


def _stub_of(path: str) -> str:
    return path[:-3] + ".pyi" if path.endswith(".py") else path


def _version(text) -> tuple[int, int] | None:
    if not isinstance(text, str):
        return None
    match = _VERSION.match(text.strip())
    return (int(match.group(1)), int(match.group(2))) if match else None


def _extern_files(bundle: EvidenceBundle) -> list[str]:
    return [p for p in sorted(bundle.files)
            if p.startswith(EXTERN_ROOT) and not bundle.files[p].is_new]


def _is_style_fix(bundle: EvidenceBundle, path: str) -> bool:
    """Whether an edit changes nothing but whitespace, formatting or comments."""
    change = bundle.files[path]

    def squeeze(lines):
        return sorted("".join(line.split()).lstrip("/*#") for line in lines if line.strip())

    return squeeze(text for _, text in change.added_lines) == squeeze(change.removed_lines)


# --- adding an rcParam ------------------------------------------------------------------------


def _rcparam_keys(bundle: EvidenceBundle) -> dict[str, set[str]]:
    """Each rcParam key this contribution introduces, with where it was seen.

    The antecedent the three rcParam rules share. It is deliberately read from *all three*
    places a key can appear, so that a key registered in only one of them is still
    selected and graded by the other two rules (§7.1).
    """
    keys: dict[str, set[str]] = {}
    for _, text in added_lines(bundle, RCSETUP):
        for key in _RC_KEY.findall(text):
            keys.setdefault(key, set()).add("rcsetup")
    for _, text in added_lines(bundle, MATPLOTLIBRC):
        if match := _RC_COMMENTED.match(text):
            keys.setdefault(match.group(1), set()).add("matplotlibrc")
    for _, text in added_lines(bundle, TYPING_STUB):
        for key in _RC_KEY.findall(text):
            keys.setdefault(key, set()).add("typing")
    return keys


def _rcparam_targets(bundle: EvidenceBundle, prefix: str) -> list[Target]:
    return [target(f"{prefix}:{key}", None, None, (key, seen, bundle),
                   f"new rcParam {key}")
            for key, seen in sorted(_rcparam_keys(bundle).items())]


@rule(
    id="MATPLOTLIB-C192",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- "a new rcParam" is a newness qualifier
    reads=("files",),  # spec §5: the registration is in the patch
    heuristic=True,
)
class ANewRcParamIsRegisteredWithAValidator:
    """Pre-condition: each rcParam key the contribution introduces, wherever it first
    appears.
    Pass condition: :file:`rcsetup.py` gains a validator entry for it.

    §7.1: the antecedent is *introducing a key*, read from all three places one can
    appear, so a key added only to :file:`matplotlibrc` is selected here and recorded as a
    violation rather than vanishing. C193 and C194 ask the same question of the other two
    files, and no rule reads another's artefact (§7.5).

    Heuristic on the **pre-condition** (§6.3): a new key is recognised from a dotted
    lower-case string on an added line of one of the three files, so a key introduced some
    other way is not seen.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _rcparam_targets(b, "rcparam-validator")

    def pass_condition(self, t: Target):
        key, seen, bundle = t.payload
        if "rcsetup" not in seen:
            return Violated(f"{key} is introduced without a validator entry in {RCSETUP}")
        if not _PARAM_ENTRY.search(added_text(bundle, RCSETUP)):
            return Violated(f"{key} is registered in {RCSETUP} with no _Param entry")
        return Satisfied(f"{key} is registered in {RCSETUP} with a validator and a "
                         f"_Param entry")


@rule(
    id="MATPLOTLIB-C193",
    category=CATEGORY,
    ownership="created",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class ANewRcParamGetsACommentedMatplotlibrcEntry:
    """Pre-condition: each rcParam key the contribution introduces.
    Pass condition: :file:`matplotlibrc` gains a commented-out entry for it.

    Heuristic on the **pre-condition** for the reason C192 gives; the pass condition is
    exact -- a ``#key: value`` line is either on an added line of the template or it is
    not.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _rcparam_targets(b, "rcparam-template")

    def pass_condition(self, t: Target):
        key, seen, _bundle = t.payload
        if "matplotlibrc" in seen:
            return Satisfied(f"{key} has a commented-out entry in {MATPLOTLIBRC}")
        return Violated(f"{key} is introduced with no commented-out entry in "
                        f"{MATPLOTLIBRC}")


@rule(
    id="MATPLOTLIB-C194",
    category=CATEGORY,
    ownership="created",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class ANewRcParamKeyReachesTheRcKeyTypeLiteral:
    """Pre-condition: each rcParam key the contribution introduces.
    Pass condition: it appears in :file:`lib/matplotlib/typing.py`, where the
    ``RcKeyType`` literal lists them.

    Heuristic on the **pre-condition** for the reason C192 gives, and on the **pass
    condition** (§6.2), which accepts the key appearing anywhere in the stub's added lines
    rather than parsing the ``Literal`` itself -- the literal is a very long expression and
    a key added to it is what a diff shows.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _rcparam_targets(b, "rcparam-typing")

    def pass_condition(self, t: Target):
        key, seen, _bundle = t.payload
        if "typing" in seen:
            return Satisfied(f"{key} is listed in {TYPING_STUB}")
        return Violated(f"{key} is introduced without reaching the RcKeyType literal in "
                        f"{TYPING_STUB}")


# --- the pyplot wrapper contract ---------------------------------------------------------------


def _pyplot_signature_change(bundle: EvidenceBundle) -> list[tuple[str, str]]:
    """(path, name) for each wrapped method whose signature line the agent edited."""
    out = []
    for path, module in modules(bundle, tests=False):
        if path not in PYPLOT_WRAPPED:
            continue
        touched = bundle.files[path].modified_lines
        for function in module.functions:
            if function.lineno in touched and not function.name.startswith("_"):
                out.append((path, function.name))
    return out


@rule(
    id="MATPLOTLIB-C195",
    category=CATEGORY,
    ownership="touched",  # spec §4.2 -- the antecedent is the signature change, made to
                          # code that already existed
    reads=("files", "commands"),  # spec §5: the change is in the patch, running the test
                                  # is an act and is recorded in the log
    heuristic=True,
)
class TestPyplotUpToDateIsRunAfterASignatureChange:
    """Pre-condition: the agent changed the signature of a public method in one of the
    modules ``tools/boilerplate.py`` wraps into pyplot.
    Pass condition: a ``test_pyplot_up_to_date`` invocation appears in the command log.

    §7.2's shape exactly: the pre-condition fires on the *edit*, never on the test run,
    because firing on the invocation would find only agents that already complied.

    Heuristic on the **pre-condition** (§6.3): *changing a signature* is approximated by
    the ``def`` line of a public method falling inside the agent's edit, so a default
    changed on a continuation line is not seen.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        changed = _pyplot_signature_change(b)
        if not changed:
            return []
        path, name = changed[0]
        return [target(f"pyplot-test:{b.instance_id}", path, None, (changed, b),
                       f"{len(changed)} wrapped signature(s) changed, e.g. {name}")]

    def pass_condition(self, t: Target):
        changed, bundle = t.payload
        if runs := ran(bundle, _PYPLOT_UP_TO_DATE):
            return Satisfied(f"test_pyplot_up_to_date was run: "
                             f"{runs[0].command.strip()[:80]}")
        return Violated(f"{changed[0][1]}'s signature changed without running "
                        f"test_pyplot_up_to_date")


@rule(
    id="MATPLOTLIB-C196",
    category=CATEGORY,
    ownership="touched",  # spec §4.2 -- the antecedent is the signature change
    reads=("files",),  # spec §5: the sentence, not CheckTier=differential -- regenerated
                       # wrappers are a file, so they are in the diff or they are not
    heuristic=True,
)
class ThePyplotWrappersAreRegeneratedAndCommitted:
    """Pre-condition: the agent changed the signature of a public method that pyplot
    wraps.
    Pass condition: the regenerated :file:`lib/matplotlib/pyplot.py` is in the
    contribution.

    Asks a different question from C195, which is whether the guard test was run; this one
    is whether the generated file was committed, and the two never grade the same artefact
    (§7.5).

    Heuristic on the **pre-condition** for the reason C195 gives, and on the **pass
    condition** (§6.2), which accepts any edit to :file:`pyplot.py` rather than checking
    that it is byte-for-byte what ``tools/boilerplate.py`` would emit -- that would need
    the generator to be run.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        changed = _pyplot_signature_change(b)
        if not changed:
            return []
        path, name = changed[0]
        return [target(f"pyplot-regen:{b.instance_id}", path, None, (changed, b),
                       f"{len(changed)} wrapped signature(s) changed, e.g. {name}")]

    def pass_condition(self, t: Target):
        changed, bundle = t.payload
        if PYPLOT in bundle.files:
            return Satisfied(f"{PYPLOT} is regenerated and committed alongside "
                             f"{changed[0][1]}")
        return Violated(f"{changed[0][1]}'s signature changed without committing the "
                        f"regenerated {PYPLOT}")


# --- colormaps, colour sequences and styles ------------------------------------------------------


def _palette_files(bundle: EvidenceBundle) -> list[str]:
    out = []
    for path in sorted(bundle.files):
        if path in COLORMAP_FILES or path.startswith(STYLE_ROOT):
            out.append(path)
        elif path.endswith(".py") and _COLOR_SEQUENCES.search(added_text(bundle, path)):
            out.append(path)
    return out


@rule(
    id="MATPLOTLIB-C197",
    category=CATEGORY,
    ownership="touched",  # spec §4.1 -- the target is a definition that already existed
    reads=("files",),  # spec §5: the sentence, not CheckTier=differential -- a modified
                       # entry shows on the minus side of the patch
    heuristic=True,
)
class ExistingColormapsAndStylesAreNotModified:
    """Pre-condition: each file the agent edited that defines colormaps, colour sequences
    or styles.
    Pass condition: it only gains entries -- nothing already there was changed or removed.

    §7.1: a prohibition, so the pre-condition selects *touching the palette files at all*
    and the pass condition asks whether an existing entry was disturbed. Selecting the
    modifications themselves could never record a compliant addition.

    Heuristic on the **pass condition** (§6.2): "modifying an existing colormap" is
    approximated by the edit having a minus side, so re-indenting a definition reads as a
    modification while a new entry inserted with no deletions reads as an addition.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"palette:{path}", path, None, (path, b), f"{path} edited")
                for path in _palette_files(b) if not b.files[path].is_new]

    def pass_condition(self, t: Target):
        path, bundle = t.payload
        removed = bundle.files[path].removed_lines
        if removed:
            return Violated(f"{path} changes {len(removed)} line(s) of an existing "
                            f"colormap, colour sequence or style, e.g. "
                            f"{removed[0].strip()[:60]}")
        return Satisfied(f"{path} only adds to the palette definitions")


@rule(
    id="MATPLOTLIB-C198",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- "any new colormap ... or style" is a newness
                          # qualifier
    reads=("files",),  # spec §5: the licence statement is in the patch
    heuristic=True,
)
class ANewColormapOrStyleCarriesABsdCompatibleLicence:
    """Pre-condition: each new colormap, colour sequence or style the contribution adds.
    Pass condition: the contribution states a BSD-compatible licence for it, and no
    copyleft one.

    Heuristic on **both** layers (§6.2, §6.3). *A new colormap* is approximated by a new
    style file or by added lines in the colormap tables; and the licence is read off text
    -- a recognised permissive name anywhere in the file, the licence directory, or the
    project's own licence tree -- rather than from any authoritative record.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in _palette_files(b):
            change = b.files[path]
            if change.is_new or change.added_lines:
                out.append(target(f"palette-licence:{path}", path, None, (path, b),
                                  f"{path} adds a colormap, colour sequence or style"))
        return out

    def pass_condition(self, t: Target):
        path, bundle = t.payload
        text = added_text(bundle, path)
        if COPYLEFT.search(text):
            return Violated(f"{path} adds a palette under a copyleft licence")
        if BSD_COMPATIBLE.search(text):
            return Satisfied(f"{path} states a BSD-compatible licence for the new palette")
        licences = [p for p in bundle.files if p.startswith(LICENSE_ROOT)]
        if licences:
            return Satisfied(f"{path} adds a palette and the change files {licences[0]}")
        return Violated(f"{path} adds a colormap, colour sequence or style with no "
                        f"BSD-compatible licence stated anywhere in the contribution")


# --- the deprecation lifecycle ---------------------------------------------------------------------


@rule(
    id="MATPLOTLIB-C202",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- the target is a deprecation the agent introduced
    reads=("files", "deprecated_api_run"),  # spec §5: whether the API still works is a
                                            # tool run over the deprecated API
    heuristic=True,
)
class DeprecatedApiStaysFunctional:
    """Pre-condition: each deprecation the agent introduced.
    Pass condition: the deprecated callable still does what it did.

    Graded **one-sidedly** (§9): a deprecated body that has been replaced by a bare
    ``raise`` provably breaks the contract and is decidable from the patch, and everything
    else needs the API exercised, which is what ``deprecated_api_run`` names. The rule withholds
    rather than reading an unchanged body as proof of unchanged behaviour, so its three
    cases are violated, withheld and no target.

    Heuristic on the **pre-condition** (§6.3): *introducing a deprecation* is approximated
    by one of the six ``_api`` helpers appearing on a line the agent wrote.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module, name, node in _helper_calls(b):
            function = _owner(module, node)
            out.append(target(f"still-works:{path}:{node.lineno}", path,
                              (node.lineno, node.end_lineno or node.lineno),
                              (path, name, function, module), f"{name}() at {path}"))
        return out

    def pass_condition(self, t: Target):
        path, name, function, module = t.payload
        if function is not None:
            from compliance.rules.matplotlib._common import function_source

            if _GUTTED.search(function_source(module, function)):
                return Violated(f"{path}::{function.name} is deprecated with {name}() and "
                                f"its body now raises instead of working")
        return Undetermined("tool_missing",
                            f"the API deprecated by {name}() at {path} was never "
                            f"exercised, so it cannot be shown to still work")


@rule(
    id="MATPLOTLIB-C203",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- the target is a deprecation the agent introduced
    reads=("files",),  # spec §5: the sentence, not CheckTier=differential -- what the
                       # deprecation points at is an argument in the patch
    heuristic=True,
)
class ADeprecationNamesItsReplacement:
    """Pre-condition: each deprecation the agent introduced.
    Pass condition: the helper names an alternative for callers to move to.

    Heuristic on the **pass condition** (§6.2): "ship the replacement" is approximated by
    the deprecation *naming* one, since whether the named alternative exists is a fact
    about the whole checkout rather than about the patch. A deprecation whose replacement
    ships in the same change but goes unnamed reads as a violation.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"replacement:{path}:{node.lineno}", path,
                       (node.lineno, node.end_lineno or node.lineno), (path, name, node),
                       f"{name}() at {path}:{node.lineno}")
                for path, _module, name, node in _helper_calls(b)]

    def pass_condition(self, t: Target):
        path, name, node = t.payload
        alternative = _literal(_argument(node, None, "alternative"))
        if isinstance(alternative, str) and alternative.strip():
            return Satisfied(f"{path}:{node.lineno} points callers at "
                             f"{alternative.strip()!r}")
        return Violated(f"{path}:{node.lineno} calls {name}() with no alternative, so "
                        f"callers are given no replacement to move to")


@rule(
    id="MATPLOTLIB-C206",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- the target is a deprecation the agent introduced
    reads=("files",),  # spec §5: the sentence, not CheckTier=differential -- which class
                       # is raised follows from which helper was used, and both are in the
                       # patch
    heuristic=True,
)
class DeprecatedApiRaisesMatplotlibDeprecationWarning:
    """Pre-condition: each deprecation the agent introduced, by an ``_api`` helper or by
    hand.
    Pass condition: it goes through an ``_api`` helper, which is what raises
    ``MatplotlibDeprecationWarning``.

    §7.1: the antecedent is *deprecating something*, whichever way, so a hand-rolled
    ``warnings.warn(..., DeprecationWarning)`` is a recorded violation and a helper call is
    a recorded pass; selecting only the hand-rolled ones could never record compliance.

    Heuristic on the **pass condition** (§6.2): the warning class is inferred from the
    helper rather than observed being raised, so a hand-rolled ``warnings.warn`` that names
    ``MatplotlibDeprecationWarning`` itself is accepted as an alternative form.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = [target(f"mpl-warning:{path}:{node.lineno}", path,
                      (node.lineno, node.end_lineno or node.lineno),
                      (path, name, "", ""), f"{name}() at {path}:{node.lineno}")
               for path, _module, name, node in _helper_calls(b)]
        for path in python_files(b, tests=False):
            if not is_package_path(path):
                continue
            for number, text in added_lines(b, path):
                if _HAND_ROLLED.search(text) and _DEPRECATION_CATEGORY.search(text):
                    out.append(target(f"mpl-warning:{path}:{number}", path,
                                      (number, number), (path, "warnings.warn", text, ""),
                                      text.strip()[:120]))
        return out

    def pass_condition(self, t: Target):
        path, name, text, _ = t.payload
        if name != "warnings.warn":
            return Satisfied(f"{path} deprecates through {name}(), which raises "
                             f"MatplotlibDeprecationWarning")
        if _MPL_DEPRECATION.search(text):
            return Satisfied(f"{path} raises MatplotlibDeprecationWarning directly")
        return Violated(f"{path} deprecates with a hand-rolled warnings.warn() that "
                        f"raises a plain DeprecationWarning: {text.strip()[:60]}")


@rule(
    id="MATPLOTLIB-C207",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the target is a helper call the agent wrote
    reads=("files",),  # spec §5: the helper and what it decorates are in the patch
    heuristic=True,
)
class TheDeprecationHelperMatchesTheKindOfApi:
    """Pre-condition: each ``_api`` deprecation helper call the agent wrote.
    Pass condition: it is the helper for the kind of API it is applied to -- a parameter
    helper naming a parameter the function actually has, and a whole-object helper applied
    to a definition.

    Heuristic on the **pass condition** (§6.2): "the matching helper" is checked by the
    one property each helper's own contract fixes -- that ``rename_parameter``,
    ``delete_parameter`` and ``make_keyword_only`` name a parameter in the signature, and
    that ``deprecated`` decorates a definition rather than an assignment. A privatised
    attribute deprecated with ``deprecated`` instead of ``deprecate_privatize_attribute``
    is not distinguished.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module, name, node in _helper_calls(b):
            out.append(target(f"helper-kind:{path}:{node.lineno}", path,
                              (node.lineno, node.end_lineno or node.lineno),
                              (path, name, node, _owner(module, node)),
                              f"{name}() at {path}:{node.lineno}"))
        return out

    def pass_condition(self, t: Target):
        from compliance.rules.matplotlib._common import parameter_names

        path, name, node, function = t.payload
        if name in PARAMETER_HELPERS:
            if function is None:
                return Violated(f"{path}:{node.lineno} uses {name}() where there is no "
                                f"function signature to change")
            wanted = _named_parameter(name, node)
            names = parameter_names(function)
            if wanted is None:
                return Violated(f"{path}:{node.lineno} uses {name}() without naming the "
                                f"parameter it applies to")
            if wanted not in names:
                return Violated(f"{path}:{node.lineno} uses {name}() for {wanted!r}, "
                                f"which is not a parameter of {function.name}")
            return Satisfied(f"{path}:{node.lineno} uses {name}() for the parameter "
                             f"{wanted!r} of {function.name}")
        if name == "deprecated" and function is None:
            return Violated(f"{path}:{node.lineno} applies deprecated() where no "
                            f"definition is being deprecated")
        return Satisfied(f"{path}:{node.lineno} uses {name}() for the kind of API it "
                         f"deprecates")


@rule(
    id="MATPLOTLIB-C208",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the target is a helper call the agent wrote
    reads=("files", "repo_version"),  # spec §5: "the next point release" is a fact about
                                      # the checked-out tree; `repo_version` is the
                                      # registered source for it and is carried by nothing
)
class TheDeprecationSinceIsTheNextPointRelease:
    """Pre-condition: each ``_api`` deprecation helper call the agent wrote.
    Pass condition: its ``since`` names the next point release.

    Graded **one-sidedly** (§9): a helper called with no ``since`` at all provably cannot
    name the next release, and that is decidable from the patch. Comparing a version that
    *is* given against the next point release needs the project's version at the base
    commit, which no run records; the rule declares ``repo_version`` and withholds, so the
    exemption sunsets itself the day that evidence is collected (§5).

    Not heuristic: neither branch approximates anything -- one is the absence of a named
    argument, the other declines to grade.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"since:{path}:{node.lineno}", path,
                       (node.lineno, node.end_lineno or node.lineno), (path, name, node),
                       f"{name}() at {path}:{node.lineno}")
                for path, _module, name, node in _helper_calls(b)]

    def pass_condition(self, t: Target):
        path, name, node = t.payload
        since = _literal(_argument(node, 0, "since"))
        if since is None:
            return Violated(f"{path}:{node.lineno} calls {name}() without a since "
                            f"version, so no deprecation period is stated")
        return Undetermined("tool_missing",
                            f"{path}:{node.lineno} sets since={since!r}; the project "
                            f"version at the base commit is not recorded, so the next "
                            f"point release is unknown")


def _stub_targets(bundle: EvidenceBundle, prefix: str, helpers: tuple[str, ...]):
    out = []
    for path, module, name, node in _helper_calls(bundle):
        if name not in helpers:
            continue
        out.append(target(f"{prefix}:{path}:{node.lineno}", path,
                          (node.lineno, node.end_lineno or node.lineno),
                          (path, name, node, _owner(module, node), bundle),
                          f"{name}() at {path}:{node.lineno}"))
    return out


@rule(
    id="MATPLOTLIB-C209",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- the target is a deprecation the agent introduced
    reads=("files",),  # spec §5: the sentence, not CheckTier=differential -- the stub is
                       # a file in the patch
    heuristic=True,
)
class TheStubIsUpdatedAfterADeprecation:
    """Pre-condition: each whole-object deprecation the agent introduced -- ``deprecated``,
    ``warn_deprecated`` or ``deprecate_privatize_attribute``.
    Pass condition: the module's ``.pyi`` stub is edited too.

    The three *parameter* helpers are deliberately excluded: ``rename_parameter`` and
    ``make_keyword_only`` are C210's, ``delete_parameter`` is C211's, and
    ``code_quality.C242`` excludes every deprecating file so that one deprecation cannot
    depress three rates (§7.5).

    Heuristic on the **pass condition** (§6.2): any edit to the sibling stub counts, since
    checking that the stub now *matches* runtime behaviour would need the type checker's
    verdict.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _stub_targets(b, "stub-deprecation", PLAIN_HELPERS)

    def pass_condition(self, t: Target):
        path, name, node, _function, bundle = t.payload
        stub = _stub_of(path)
        if stub in bundle.files:
            return Satisfied(f"{stub} is updated alongside the {name}() at "
                             f"{path}:{node.lineno}")
        return Violated(f"{path}:{node.lineno} deprecates with {name}() and leaves "
                        f"{stub} untouched")


@rule(
    id="MATPLOTLIB-C210",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- "at introduction" is a newness qualifier
    reads=("files",),  # spec §5: the helper and the stub are both in the patch
    heuristic=True,
)
class RenameAndKeywordOnlyDeprecationsUpdateTheStubSignature:
    """Pre-condition: each ``rename_parameter`` or ``make_keyword_only`` deprecation the
    agent introduced.
    Pass condition: the module's ``.pyi`` stub gains a line naming the parameter the
    helper is about.

    Narrowed to those two helpers so that C209 (whole-object deprecations) and C211
    (``delete_parameter``) never grade the same call (§7.5).

    Heuristic on the **pass condition** (§6.2): "the stub signature is updated" is
    approximated by the parameter name appearing on an added stub line, rather than by
    re-deriving the signature the stub should now carry.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _stub_targets(b, "stub-signature",
                             ("rename_parameter", "make_keyword_only"))

    def pass_condition(self, t: Target):
        path, name, node, function, bundle = t.payload
        stub = _stub_of(path)
        wanted = _named_parameter(name, node)
        if stub not in bundle.files:
            return Violated(f"{path}:{node.lineno} uses {name}() and leaves {stub} "
                            f"untouched")
        if wanted and re.search(rf"\b{re.escape(str(wanted))}\b", added_text(bundle, stub)):
            return Satisfied(f"{stub} names {wanted!r} after the {name}() at "
                             f"{path}:{node.lineno}")
        return Violated(f"{stub} is edited but never names {wanted!r}, so the stub "
                        f"signature does not follow the {name}() at {path}:{node.lineno}")


@rule(
    id="MATPLOTLIB-C211",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- the target is a deprecation the agent introduced
    reads=("files",),  # spec §5: the helper and the stub are both in the patch
    heuristic=True,
)
class DeleteParameterDeprecationsGiveTheStubADefault:
    """Pre-condition: each ``delete_parameter`` deprecation the agent introduced.
    Pass condition: the module's ``.pyi`` stub gains a line giving that parameter a
    default value.

    Narrowed to ``delete_parameter`` alone, so that C209 and C210 never reach the same
    call (§7.5).

    Heuristic on the **pass condition** (§6.2): "a default value hint" is recognised as the
    parameter name followed by ``=`` on an added stub line, which accepts ``= ...`` and any
    other default the author writes.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _stub_targets(b, "stub-default", ("delete_parameter",))

    def pass_condition(self, t: Target):
        path, name, node, function, bundle = t.payload
        stub = _stub_of(path)
        wanted = _named_parameter(name, node)
        if stub not in bundle.files:
            return Violated(f"{path}:{node.lineno} uses delete_parameter() and leaves "
                            f"{stub} untouched")
        if wanted and re.search(rf"\b{re.escape(str(wanted))}\b\s*(?::[^,=)]+)?=",
                                added_text(bundle, stub)):
            return Satisfied(f"{stub} gives {wanted!r} a default after the "
                             f"delete_parameter() at {path}:{node.lineno}")
        return Violated(f"{stub} never gives {wanted!r} a default value hint, which is "
                        f"what a delete_parameter deprecation needs")


@rule(
    id="MATPLOTLIB-C213",
    category=CATEGORY,
    ownership="touched",  # spec §4.1 -- expiring a deprecation edits, and deletes from,
                          # code that was already there
    reads=("files",),  # spec §5: the sentence, not CheckTier=differential -- what the
                       # patch removed is on its minus side
    heuristic=True,
)
class ExpiryRemovesTheWarningWithTheApi:
    """Pre-condition: each library file where the agent removed a deprecation helper --
    which is what expiring a deprecation looks like in a diff.
    Pass condition: the deprecated definition went with it.

    Heuristic on **both** layers (§6.3, §6.2). Expiry is approximated by the helper call
    disappearing, which is also what moving it elsewhere looks like; and "the API went
    too" is approximated by a ``def``, ``class`` or attribute assignment on the same minus
    side, so an API removed in a separate file of the same change reads as a violation.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"expiry:{path}", path, None, (path, b),
                       f"{path} removes a deprecation helper")
                for path in expires_deprecation(b)]

    def pass_condition(self, t: Target):
        path, bundle = t.payload
        removed = removed_text(bundle, path)
        if re.search(r"^\s*(?:async\s+)?(?:def|class)\s+\w+|^\s*\w+\s*=", removed, re.M):
            return Satisfied(f"{path} removes the deprecated API together with its "
                             f"warning")
        return Violated(f"{path} removes the deprecation warning "
                        f"({', '.join(sorted(set(deprecation_sites(removed))))}) but "
                        f"leaves the deprecated API in place")


@rule(
    id="MATPLOTLIB-C214",
    category=CATEGORY,
    ownership="touched",  # spec §4.1 -- the stub existed before the run
    reads=("files",),  # spec §5: the stub's minus side is in the patch
    heuristic=True,
)
class ExpiryRemovesTheItemFromTheStub:
    """Pre-condition: each library file where the agent removed a deprecation helper.
    Pass condition: the module's ``.pyi`` stub loses lines too.

    The expiry counterpart of C209's introduction rule, and kept apart from C213 (§7.5):
    that rule asks whether the *implementation* went, this one asks about the *stub*, and
    neither reads the other's file.

    Heuristic on the **pass condition** (§6.2): any removal from the sibling stub counts,
    since matching the removed names against the removed stub entries would need the
    signature the stub carried before the change.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"stub-expiry:{path}", path, None, (path, b),
                       f"{path} removes a deprecation helper")
                for path in expires_deprecation(b)]

    def pass_condition(self, t: Target):
        path, bundle = t.payload
        stub = _stub_of(path)
        if stub not in bundle.files:
            return Violated(f"{path} expires a deprecation and leaves {stub} untouched")
        if bundle.files[stub].removed_lines:
            return Satisfied(f"{stub} loses the expired entries alongside {path}")
        return Violated(f"{stub} is edited but nothing is removed from it, so the "
                        f"expired item is still declared")


@rule(
    id="MATPLOTLIB-C216",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the target is a helper call the agent wrote
    reads=("files",),  # spec §5: both arguments are in the patch
    heuristic=True,
)
class APendingDeprecationCarriesNoRemovalVersion:
    """Pre-condition: each deprecation the agent introduced with ``pending=True``.
    Pass condition: it names no removal version.

    Heuristic on the **pre-condition** (§6.3), and the doubt is worth naming: nothing else
    in the patch distinguishes a deprecation that *ought* to be pending from one that
    ought not, so the antecedent is *having marked it pending*. What is graded is the
    second half of the sentence, which is exact -- a ``removal`` argument is present or it
    is not.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, name, node in _helper_calls(b):
            if _literal(_argument(node, None, "pending")) is not True:
                continue
            out.append(target(f"pending:{path}:{node.lineno}", path,
                              (node.lineno, node.end_lineno or node.lineno),
                              (path, name, node), f"{name}(pending=True) at {path}"))
        return out

    def pass_condition(self, t: Target):
        path, name, node = t.payload
        removal = _argument(node, None, "removal")
        if removal is None:
            return Satisfied(f"{path}:{node.lineno} marks a pending deprecation with no "
                             f"removal version")
        return Violated(f"{path}:{node.lineno} marks a pending deprecation and still "
                        f"names removal={_literal(removal)!r}")


@rule(
    id="MATPLOTLIB-C217",
    category=CATEGORY,
    ownership="touched",  # spec §4.1 -- converting edits a deprecation that already
                          # existed; the `pending=True` is on the minus side
    reads=("files",),  # spec §5: both versions are in the patch
    heuristic=True,
)
class ConvertingAPendingDeprecationSetsTheVersions:
    """Pre-condition: each library file where the agent removed a ``pending=True`` from a
    deprecation while keeping the helper -- which is what converting one looks like.
    Pass condition: the converted call is no longer pending, names a ``since``, and sets
    ``removal`` at least two meso releases later.

    Heuristic on **both** layers (§6.3, §6.6). Conversion is recognised from
    ``pending=True`` disappearing from the file's minus side, so a conversion split across
    two files is not seen. And of the sentence's three clauses only two are graded: the gap
    between ``since`` and ``removal`` is arithmetic on the patch, but *"since is the next
    meso release"* would need the project's version at the base commit, which no run
    records -- so a converted deprecation whose ``since`` is a stale version is accepted
    here. The rate is an upper bound, and the doubt is named rather than hidden.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in python_files(b, tests=False):
            if not is_package_path(path):
                continue
            if "pending" not in removed_text(b, path):
                continue
            if not re.search(r"pending\s*=\s*True", removed_text(b, path)):
                continue
            calls = [(name, node) for p, _m, name, node in _helper_calls(b) if p == path]
            if not calls:
                continue
            name, node = calls[0]
            out.append(target(f"convert-pending:{path}:{node.lineno}", path,
                              (node.lineno, node.end_lineno or node.lineno),
                              (path, name, node), f"{name}() converted at {path}"))
        return out

    def pass_condition(self, t: Target):
        path, name, node = t.payload
        if _literal(_argument(node, None, "pending")) is True:
            return Violated(f"{path}:{node.lineno} still carries pending=True after the "
                            f"conversion")
        since = _version(_literal(_argument(node, 0, "since")))
        removal = _version(_literal(_argument(node, None, "removal")))
        if since is None:
            return Violated(f"{path}:{node.lineno} converts a pending deprecation without "
                            f"naming a since version")
        if removal is None:
            return Violated(f"{path}:{node.lineno} converts a pending deprecation without "
                            f"naming a removal version")
        gap = (removal[0] - since[0]) * 1000 + (removal[1] - since[1])
        if gap < MESO_GAP:
            return Violated(f"{path}:{node.lineno} removes at {removal[0]}.{removal[1]} "
                            f"only {gap} meso release(s) after since "
                            f"{since[0]}.{since[1]}; the rule asks for {MESO_GAP}")
        return Satisfied(f"{path}:{node.lineno} converts to since {since[0]}.{since[1]} "
                         f"with removal at {removal[0]}.{removal[1]}")


# --- packaging and vendored code -------------------------------------------------------------------


@rule(
    id="MATPLOTLIB-C244",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- "new files and directories" is a newness qualifier
    reads=("files",),  # spec §5: the file and the build definition are both in the patch
    heuristic=True,
)
class NewFilesAreListedInTheirMesonBuild:
    """Pre-condition: each source file the agent added under a tree meson builds.
    Pass condition: the :file:`meson.build` in its own directory is edited and names it.

    Heuristic on the **pre-condition** (§6.3): *a directory meson builds* is approximated
    by the three trees that carry :file:`meson.build` files, since the build definitions
    outside the patch are not visible. A new file in a directory whose build list is
    generated by a glob reads as a violation.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in sorted(b.files):
            change = b.files[path]
            name = path.rsplit("/", 1)[-1]
            if not change.is_new or name == MESON:
                continue
            if not path.startswith(_MESON_ROOTS):
                continue
            if not (path.endswith(".py") or path.endswith(".pyi") or is_c_source(path)):
                continue
            out.append(target(f"meson:{path}", path, None, (path, name, b),
                              f"{path} is new"))
        return out

    def pass_condition(self, t: Target):
        path, name, bundle = t.payload
        folder = path.rsplit("/", 1)[0]
        build = f"{folder}/{MESON}"
        if build not in bundle.files:
            return Violated(f"{path} is added without editing {build}")
        if name in added_text(bundle, build):
            return Satisfied(f"{build} lists {name}")
        return Violated(f"{build} is edited but never names {name}")


@rule(
    id="MATPLOTLIB-C249",
    category=CATEGORY,
    ownership="touched",  # spec §4.1 -- vendored code existed before the run
    reads=("files",),  # spec §5: the sentence, not CheckTier=differential -- where the
                       # change was made is the patch's own shape
    heuristic=True,
)
class VendoredCodeIsModifiedOnlyAsALastResort:
    """Pre-condition: each substantive edit the agent made to a file under
    :file:`extern/`.
    Pass condition: the same contribution also changes the project's own source, so the
    vendored edit is the part that could not be made there.

    A purely cosmetic edit to vendored code is excluded and left to C250, so a style fix
    under :file:`extern/` is one violation rather than two (§7.5).

    Heuristic on the **pass condition** (§6.2): *"the change cannot be made elsewhere"* is
    not observable, and it is approximated by whether the contribution attempted anything
    elsewhere at all. A change that genuinely belongs only in vendored code, and touches
    nothing else, reads as a violation; the direction of that error is declared rather
    than removed.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"extern-necessity:{path}", path, None, (path, b),
                       f"{path} edited")
                for path in _extern_files(b) if not _is_style_fix(b, path)]

    def pass_condition(self, t: Target):
        path, bundle = t.payload
        elsewhere = [p for p in sorted(bundle.files)
                     if p.startswith(MAIN_CODE_ROOTS) and not p.startswith(EXTERN_ROOT)]
        if elsewhere:
            return Satisfied(f"{path} is edited alongside the project's own "
                             f"{elsewhere[0]}, so the vendored change is the residue")
        return Violated(f"{path} is vendored code and the contribution changes nothing in "
                        f"the project's own tree, so the change was not attempted "
                        f"elsewhere first")


@rule(
    id="MATPLOTLIB-C250",
    category=CATEGORY,
    ownership="touched",  # spec §4.1 -- vendored code existed before the run
    reads=("files",),  # spec §5: both sides of the edit are in the patch
    heuristic=True,
)
class VendoredCodeGetsNoStyleFixes:
    """Pre-condition: each file under :file:`extern/` the agent edited.
    Pass condition: the edit changes something other than formatting.

    §7.1: a prohibition, so the pre-condition is *editing vendored code at all* and the
    graded question is whether the edit was a style fix. Selecting style fixes would only
    ever find violations.

    Heuristic on the **pass condition** (§6.2): "a style fix" is approximated by every
    removed line reappearing on the plus side once whitespace and comment markers are
    squeezed out, so a reflow that also renames a variable is not seen as a style fix.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"extern-style:{path}", path, None, (path, b), f"{path} edited")
                for path in _extern_files(b)]

    def pass_condition(self, t: Target):
        path, bundle = t.payload
        if _is_style_fix(bundle, path):
            return Violated(f"{path} is vendored code and the edit changes only "
                            f"formatting")
        return Satisfied(f"{path} is edited substantively, not restyled")


@rule(
    id="MATPLOTLIB-C251",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the target is a comment the agent wrote
    reads=("files",),  # spec §5: the comment is in the patch
    heuristic=True,
)
class ANolintCommentIsNarrowAndGivesTheReason:
    """Pre-condition: each ``NOLINT`` comment the agent added to C or C++ code.
    Pass condition: it names the check it suppresses (or applies to a single line) and
    carries a reason.

    Heuristic on the **pass condition** (§6.2): "gives the reason" is matched by prose
    after the directive, so a reason written on the line above is not seen, and a trailing
    fragment that explains nothing is accepted.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in sorted(b.files):
            if not is_c_source(path):
                continue
            for number, text in added_lines(b, path):
                if match := _NOLINT.search(text):
                    out.append(target(f"nolint:{path}:{number}", path, (number, number),
                                      (path, number, match), text.strip()[:120]))
        return out

    def pass_condition(self, t: Target):
        path, number, match = t.payload
        form = (match.group("form") or "").upper()
        scope = match.group("scope") or ""
        reason = (match.group("rest") or "").strip(" :-")
        if form == "BEGIN":
            return Violated(f"{path}:{number} opens a NOLINTBEGIN block, which suppresses "
                            f"clang-tidy over a whole region rather than narrowly")
        if not scope:
            return Violated(f"{path}:{number} suppresses every clang-tidy check rather "
                            f"than naming the false positive")
        if len(reason) < 3:
            return Violated(f"{path}:{number} suppresses {scope} without giving a reason")
        return Satisfied(f"{path}:{number} suppresses {scope} narrowly, with a reason: "
                         f"{reason[:60]}")


# --- licensing --------------------------------------------------------------------------------------


@rule(
    id="MATPLOTLIB-C262",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- the target is code brought in during the run
    reads=("files",),  # spec §5: the licence header is in the patch
    heuristic=True,
)
class CodeBroughtInCarriesACompatibleLicence:
    """Pre-condition: each file the agent added under :file:`extern/` -- how code from
    another project arrives in this tree.
    Pass condition: it names a PSF, BSD, MIT or otherwise compatible licence.

    Split from C263 by tree (§7.5): imported code is vendored under :file:`extern/`, and a
    licence problem in the main code base is that rule's, so no file is graded twice.

    Heuristic on **both** layers (§6.2, §6.3). *Code brought in from another project* is
    approximated by the vendoring directory, so a snippet pasted into a library module is
    not seen; and the licence is read off text rather than from any authoritative record.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in sorted(b.files):
            change = b.files[path]
            if not change.is_new or not path.startswith(EXTERN_ROOT):
                continue
            out.append(target(f"imported-licence:{path}", path, None, (path, b),
                              f"{path} is vendored in"))
        return out

    def pass_condition(self, t: Target):
        path, bundle = t.payload
        text = added_text(bundle, path)
        if COPYLEFT.search(text):
            return Violated(f"{path} is vendored in under a copyleft licence")
        if BSD_COMPATIBLE.search(text):
            return Satisfied(f"{path} names a compatible licence")
        licences = [p for p in bundle.files if p.startswith(LICENSE_ROOT)]
        if licences:
            return Satisfied(f"{path} is vendored in and the change files {licences[0]}")
        return Violated(f"{path} is brought in from another project with no licence "
                        f"stated anywhere in the contribution")


@rule(
    id="MATPLOTLIB-C263",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- the target is a file the agent added
    reads=("files",),  # spec §5: the licence text is in the patch
    heuristic=True,
)
class NoCopyleftCodeInTheMainCodeBase:
    """Pre-condition: each source file the agent added to the main code base --
    :file:`lib/` or :file:`src/`, excluding the vendoring tree.
    Pass condition: it declares no GPL or LGPL licence.

    §7.1: a prohibition, so the pre-condition selects *adding a file*, the permitted act,
    and the pass condition asks whether it was copyleft. Files under :file:`extern/` are
    C262's (§7.5).

    Heuristic on the **pre-condition** (§6.3): the sentence is about code brought in from
    elsewhere, and the antecedent fires on every added source file, which is the superset
    that can be observed. The pass condition is exact -- the licence family is named in
    the rule and matched by name.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in sorted(b.files):
            change = b.files[path]
            if not change.is_new or path.startswith(EXTERN_ROOT):
                continue
            if not path.startswith(MAIN_CODE_ROOTS):
                continue
            if not (path.endswith(".py") or is_c_source(path)):
                continue
            out.append(target(f"copyleft:{path}", path, None, (path, b), f"{path} is new"))
        return out

    def pass_condition(self, t: Target):
        path, bundle = t.payload
        text = added_text(bundle, path)
        if COPYLEFT.search(text):
            return Violated(f"{path} is added to the main code base carrying a "
                            f"GPL/LGPL licence")
        return Satisfied(f"{path} carries no copyleft licence")


@rule(
    id="MATPLOTLIB-C264",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- the target is a dependency vendored during the run
    reads=("files",),  # spec §5: both the dependency and the licence copy are files
    heuristic=True,
)
class AVendoredDependencyBringsItsLicence:
    """Pre-condition: the contribution vendors a dependency -- it adds files under
    :file:`extern/`.
    Pass condition: it also adds a licence copy under the licence directory.

    Heuristic on the **pass condition** (§6.2), and the doubt is named: the sentence's
    qualifier -- *"where its license requires distribution"* -- is not checked, because
    deciding it means reading the dependency's own licence terms. Almost every permissive
    licence does require it, so the rule asks for the copy unconditionally, and a
    dependency under a licence that does not would read as a violation.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        vendored = [p for p in sorted(b.files)
                    if p.startswith(EXTERN_ROOT) and b.files[p].is_new]
        if not vendored:
            return []
        return [target(f"vendored-licence:{b.instance_id}", vendored[0], None,
                       (vendored, b), f"{len(vendored)} file(s) vendored in")]

    def pass_condition(self, t: Target):
        vendored, bundle = t.payload
        copies = [p for p in sorted(bundle.files)
                  if p.startswith(LICENSE_ROOT) and bundle.files[p].is_new]
        if copies:
            return Satisfied(f"{copies[0]} accompanies the {len(vendored)} vendored "
                             f"file(s)")
        return Violated(f"{vendored[0]} vendors a dependency with no licence copy added "
                        f"under {LICENSE_ROOT}")


@rule(
    id="MATPLOTLIB-C265",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- the target is toolkit code added during the run
    reads=("files",),  # spec §5: the attribution and the licence are both in the patch
    heuristic=True,
)
class ToolkitCodeFromElsewhereStatesItsLicence:
    """Pre-condition: each file the agent added under :file:`lib/mpl_toolkits/` that
    carries a third-party attribution -- a foreign copyright line, or an "adapted from"
    note.
    Pass condition: it names the licence that code is under.

    Heuristic on **both** layers (§6.2, §6.3). *Non-BSD-compatible code* is not observable
    before the licence is read, so the antecedent is the weaker and observable *code from
    somewhere else*; and "states the license clearly" is matched by a recognised licence
    name in the file.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in sorted(b.files):
            change = b.files[path]
            if not change.is_new or not path.startswith(TOOLKIT_ROOT):
                continue
            text = added_text(b, path)
            if not _THIRD_PARTY.search(text):
                continue
            out.append(target(f"toolkit-licence:{path}", path, None, (path, text),
                              f"{path} carries a third-party attribution"))
        return out

    def pass_condition(self, t: Target):
        path, text = t.payload
        if BSD_COMPATIBLE.search(text) or COPYLEFT.search(text):
            return Satisfied(f"{path} states the licence of the code it borrows")
        return Violated(f"{path} borrows code from elsewhere without stating its licence")


# --- minimum supported versions ------------------------------------------------------------------------


@rule(
    id="MATPLOTLIB-C284",
    category=CATEGORY,
    ownership="touched",  # spec §4.1 -- pyproject.toml existed before the run
    reads=("files",),  # spec §5: both the field and the version it must agree with are in
                       # the patch
    heuristic=True,
)
class RequiresPythonMatchesTheMinimumSupportedVersion:
    """Pre-condition: the agent set ``requires-python`` in a :file:`pyproject.toml` that
    also declares which Python versions the project supports.
    Pass condition: the floor it sets is the lowest of those.

    Asks whether the *value* is right; whether the other five files moved with it is
    C286's, and neither rule reads the other's artefact (§7.5).

    Heuristic on the **pre-condition** (§6.3): "the minimum supported Python version" is
    not stated anywhere the patch can see, so it is approximated by the lowest
    ``Programming Language :: Python`` classifier in the same file, or by
    :file:`environment.yml`'s pin. A file that declares neither finds no target rather than
    being graded against a guess.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        if PYPROJECT not in b.files:
            return []
        declared = None
        for _, text in added_lines(b, PYPROJECT):
            if match := _REQUIRES_PYTHON.match(text):
                declared = (int(match.group("major")), int(match.group("minor")))
        if declared is None:
            return []
        head = b.files[PYPROJECT].head_text or ""
        supported = [(int(m.group("major")), int(m.group("minor")))
                     for m in _PY_CLASSIFIER.finditer(head)]
        if not supported and ENVIRONMENT in b.files:
            env = b.files[ENVIRONMENT].head_text or ""
            supported = [(int(m.group("major")), int(m.group("minor")))
                         for m in _ENV_PYTHON.finditer(env)]
        if not supported:
            return []
        return [target(f"requires-python:{b.instance_id}", PYPROJECT, None,
                       (declared, min(supported)),
                       f"requires-python >= {declared[0]}.{declared[1]}")]

    def pass_condition(self, t: Target):
        declared, lowest = t.payload
        if declared == lowest:
            return Satisfied(f"requires-python is {declared[0]}.{declared[1]}, the lowest "
                             f"Python the project declares support for")
        return Violated(f"requires-python is {declared[0]}.{declared[1]} while the "
                        f"project still declares support for "
                        f"{lowest[0]}.{lowest[1]}")


def _min_version_target(bundle: EvidenceBundle, prefix: str, what: str) -> list[Target]:
    return [target(f"{prefix}:{bundle.instance_id}", None, None, bundle,
                   f"the contribution raises the minimum {what} version")]


@rule(
    id="MATPLOTLIB-C286",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- the six files existed before the run, and the
                          # subject is the contribution as a whole
    reads=("files",),  # spec §5: all six are files in the patch
    heuristic=True,
)
class RaisingTheMinimumPythonUpdatesAllSixFiles:
    """Pre-condition: a contribution that raises the minimum supported Python version.
    Pass condition: all six files the policy names are in it.

    Heuristic on the **pre-condition** (§6.3): *raising the minimum* is approximated by
    the version fields the policy page names appearing on added lines of the files that
    carry them, so a bump written some other way is not seen. The pass condition is exact
    -- the six names are published, and the CI entry is a named group of paths.

    Asks only whether the six moved together. Whether ``requires-python`` was set to the
    *right* value is C284's (§7.5).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        if not raises_min_python(b):
            return []
        return _min_version_target(b, "min-python", "Python")

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        missing = [entry for entry in MIN_PYTHON_FILES
                   if not satisfies_min_file(bundle, entry)]
        if missing:
            return Violated(f"the minimum Python version is raised without updating "
                            f"{len(missing)} of the six named files: "
                            f"{', '.join(missing)}")
        return Satisfied("all six files named by the minimum-version policy are updated "
                         "together")


@rule(
    id="MATPLOTLIB-C287",
    category=CATEGORY,
    ownership="touched",  # spec §4.4
    reads=("files",),  # spec §5
    heuristic=True,
)
class RaisingTheMinimumNumpyUpdatesAllSixFiles:
    """Pre-condition: a contribution that raises the minimum supported NumPy version.
    Pass condition: all six files the policy names are in it.

    A different list from C286's: :file:`requirements/testing/minver.txt` and
    :file:`lib/matplotlib/__init__.py` appear here and nowhere else, which is why the two
    rules cannot share one predicate.

    Heuristic on the **pre-condition** for the reason C286 gives.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        if not raises_min_numpy(b):
            return []
        return _min_version_target(b, "min-numpy", "NumPy")

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        missing = [entry for entry in MIN_NUMPY_FILES
                   if not satisfies_min_file(bundle, entry)]
        if missing:
            return Violated(f"the minimum NumPy version is raised without updating "
                            f"{len(missing)} of the six named files: "
                            f"{', '.join(missing)}")
        return Satisfied("all six files named by the minimum-version policy are updated "
                         "together")
