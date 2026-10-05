"""matplotlib: Tests and test style -- 16 rules.

Layer C. Every rule is two layers (`docs/checker-authoring.md` §2): ``precondition``
selects on the rule's ANTECEDENT, ``pass_condition`` grades.

Four groups. Two rules are about *acts* and are graded off the command log (C083, C166);
five are about where a test lives and what it is called (C167--C170, C271); two about
randomness (C176, C177); five about image comparison (C181--C184, C187, C188).

**Three §7.5 narrowings, each pinned by a no-target test.**

* **C167 and C168** both reach a badly placed test module. C167 grades the *directory and
  the mirroring* -- a file under the tests tree whose stem, once any ``test_`` prefix is
  stripped, names a library module the same contribution changed. C168 grades the
  ``test_`` *prefix* and nothing else. So ``lib/matplotlib/tests/axis.py`` satisfies C167
  and violates C168, and one defect never depresses two rates.
* **C176 and C177** both reach a seeded test. C176 asks whether a test that draws random
  numbers fixes a seed *at all*; C177 asks what *value* is used where numpy's generator is
  seeded, and finds no target in a test that seeds nothing. A test seeded with ``42``
  passes C176 and violates C177, which is the pair of answers the two sentences give.
* **C257/C258's** counterpart here is C181 and C183: C181 asks whether the decorator names
  its baselines at all, C183 asks whether those names carry a file extension, and C183
  finds no target when there are no names to inspect.

**Two corpus mismatches, recorded rather than corrected in the workbook (§0/§5).**

* **C182** is filed ``differential``. Whether the baseline image was committed is a fact
  about the patch -- the file is in the diff or it is not -- so it declares ``("files",)``.
* **C271** is filed ``differential`` and is decidable from the patch for the reading its
  sentence supports: "test new and changed code" asks for a test to accompany the change,
  which is what ``("files",)`` answers. Whether that test fails before and passes after is
  a different sentence, and this corpus does not contain it.
"""

from __future__ import annotations

import ast
import re

from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.rules.matplotlib._common import (BASELINE_DIR, CHECK_FIGURES_EQUAL,
                                                 IMAGE_COMPARISON, TEST_CLASS_PREFIX,
                                                 TEST_PREFIX, TEST_ROOT, baseline_images,
                                                 call_nodes_in, calls_in, classes,
                                                 contribution_target, decorator_argument,
                                                 is_test_path, literal_of, modules,
                                                 owned_functions, parameter_names, ran,
                                                 source_files, target, test_functions)

CATEGORY = "Tests and test style"

#: The seed the project fixes across its tests and gallery examples (C177).
PROJECT_SEED = 19680801
#: The style a new image-comparison test must pin (C184).
MPL20_STYLE = "mpl20"
#: The two figure parameters `check_figures_equal` injects (C187).
FIGURE_PARAMETERS = ("fig_test", "fig_ref")
#: The formats `image_comparison` compares when `extensions` is not given.
DEFAULT_EXTENSIONS = ("png", "pdf", "svg")
_IMAGE_SUFFIXES = (".png", ".pdf", ".svg", ".eps", ".jpg", ".jpeg", ".ps")

#: Drawing random numbers. Both the legacy module-level routines and a Generator's
#: methods count; the seeding calls below are a subset and are excluded where it matters.
_RANDOM_CALL = re.compile(r"^(?:np|numpy)\.random\.\w+$|^random\.\w+$"
                          r"|\.(?:standard_normal|normal|uniform|randint|random_sample"
                          r"|rand|randn|choice|permutation|shuffle)$")
#: Fixing a seed, by any of the spellings the project uses.
_SEED_CALL = re.compile(r"^(?:np|numpy)\.random\.(?:seed|default_rng|RandomState)$"
                        r"|^random\.seed$|^(?:default_rng|RandomState)$")
#: Seeding *numpy's* generator, which is what C177 fixes the value of.
_NUMPY_SEED_CALL = re.compile(r"^(?:np|numpy)\.random\.(?:seed|default_rng|RandomState)$"
                              r"|^default_rng$")

#: Making a figure or Axes the way the project asks for.
_PYPLOT_CONSTRUCTOR = re.compile(
    r"^(?:plt|pyplot|matplotlib\.pyplot|mpl\.pyplot)\."
    r"(?:figure|subplots|subplot|subplot_mosaic|figaspect|axes)$")
#: Making one by instantiating the class instead.
_DIRECT_CONSTRUCTOR = re.compile(
    r"(?:^|\.)(?:Figure|SubFigure|Axes|Subplot|AxesSubplot)$")

#: Running the suite. `pytest`, `python -m pytest`, and a `cd` in front of either.
_TEST_RUN = re.compile(r"\bpytest\b")
_BARE_PYTEST = re.compile(r"^\s*pytest\b")
_VIA_PYTHON = re.compile(r"\bpython3?\s+-m\s+pytest\b")
_LEADING_CD = re.compile(r"^\s*cd\s+(?P<where>\S+)")
#: Executing a reproducer: a script, or an inline program.
_REPRODUCER = re.compile(r"\bpython3?\s+(?:-m\s+)?(?!-m\b)(?:-c\b|\S+\.py\b)")
_TRACEBACK = re.compile(r"Traceback \(most recent call last\)|^\w*Error:", re.M)


# --- shared selection -------------------------------------------------------------------


def _image_tests(bundle: EvidenceBundle, *, mode: str = "touched"):
    """(path, module, function, decorator) for each `image_comparison` test."""
    out = []
    for path, module, function in owned_functions(bundle, mode=mode, tests=True):
        dec = function.decorator(IMAGE_COMPARISON)
        if dec is not None:
            out.append((path, module, function, dec))
    return out


def _looks_like_a_test(function) -> bool:
    """A function that asserts, or that carries one of the image-comparison decorators.

    The proxy the naming rules need: pytest decides by name, so a rule *about* the name
    cannot use the name to select what it grades (§7.1).
    """
    if function.has_decorator(IMAGE_COMPARISON, CHECK_FIGURES_EQUAL):
        return True
    if function.has_decorator("fixture", "pytest.fixture", "contextmanager"):
        return False
    node = function.node
    if node is None:
        return False
    return any(isinstance(child, ast.Assert) for child in ast.walk(node))


def _module_stems(bundle: EvidenceBundle) -> set[str]:
    """Library modules the contribution changed, as the stem a test file would mirror."""
    stems = set()
    for path in source_files(bundle):
        stems.add(path.rsplit("/", 1)[-1][:-3].lstrip("_"))
        parent = path.rsplit("/", 2)[-2] if "/" in path else ""
        if parent and not parent.startswith("lib"):
            stems.add(parent.lstrip("_"))
    return stems


def _mirrored_stem(path: str) -> str:
    stem = path.rsplit("/", 1)[-1]
    stem = stem[:-3] if stem.endswith(".py") else stem
    if stem.startswith(TEST_PREFIX):
        stem = stem[len(TEST_PREFIX):]
    return stem.lstrip("_")


def _baseline_dir(test_path: str) -> str:
    folder, _, name = test_path.rpartition("/")
    return f"{folder}/{BASELINE_DIR}/{name[:-3]}/"


# --- acts -------------------------------------------------------------------------------


@rule(
    id="MATPLOTLIB-C083",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- a whole-contribution rule about an act; the
                          # contribution is code the agent edited
    reads=("files", "commands"),  # spec §5: the fix is in the patch, running the
                                  # reproducer is an act and is recorded in the log
    heuristic=True,
)
class TheIssueReproducerIsRunAgainstTheBranch:
    """Pre-condition: a contribution that changes library code, so there is a fix whose
    effect on the reported problem could be confirmed.
    Pass condition: the last reproducer the agent executed ran to completion without a
    traceback.

    §7.2's shape: the antecedent is *having made the change*, never *having run the
    script* -- firing on the invocation would find only agents that already complied and
    could never record a run that skipped the check.

    Heuristic on **both** layers (§6.2, §6.3). "The issue's reproducer" is approximated by
    any ``python script.py`` or ``python -c`` execution, so a reproducer run through
    ``pytest`` or a REPL is not seen; and "gives the desired result" is approximated by
    the absence of a traceback and of a non-zero exit in the recorded output, which is not
    the same as the behaviour the issue asked for.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        changed = source_files(b)
        if not changed:
            return []
        return contribution_target(b, "reproducer",
                                   f"{len(changed)} library file(s) changed")

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        runs = ran(bundle, _REPRODUCER)
        if not runs:
            return Violated("library code changed but no reproducer was ever executed "
                            "against the branch")
        last = runs[-1]
        if last.returncode not in (None, 0):
            return Violated(f"the last reproducer run exited {last.returncode}: "
                            f"{last.command.strip()[:80]}")
        if _TRACEBACK.search(last.output or ""):
            return Violated(f"the last reproducer run still raises: "
                            f"{last.command.strip()[:80]}")
        return Satisfied(f"the reproducer runs clean against the branch: "
                         f"{last.command.strip()[:80]}")


@rule(
    id="MATPLOTLIB-C166",
    category=CATEGORY,
    ownership="touched",  # spec §4 -- the target is a command the agent ran; no file
                          # ownership applies, and `touched` is the value that says so
    reads=("commands",),  # spec §5: CheckTier=trajectory, and the form of the invocation
                          # is the whole question
    heuristic=True,
)
class TheSuiteIsRunWithABarePytestFromTheRepositoryRoot:
    """Pre-condition: each invocation in the command log that runs the test suite.
    Pass condition: it is a bare ``pytest``, issued from the repository root.

    §7.1: the antecedent is *running the tests*, not *running them the sanctioned way* --
    selecting only bare invocations would record nothing but passes. A run that never ran
    the suite at all finds no target here; that omission is C271's and C083's territory,
    not a violation of a rule about how to spell the command.

    Heuristic on the **pass condition** (§6.2): the working directory is not recorded, so
    "from the repository root" is read off a ``cd`` in front of the command, and an
    invocation issued from elsewhere in an earlier shell is not seen.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"pytest-run:{c.index}", None, None, c,
                       c.command.strip()[:120], source="trajectory")
                for c in b.commands if _TEST_RUN.search(c.command)]

    def pass_condition(self, t: Target):
        command = t.payload
        text = command.command.strip()
        if match := _LEADING_CD.match(text):
            where = match.group("where")
            if where not in (".", "./") and not where.startswith("$"):
                return Violated(f"the suite is run from {where}, not the repository "
                                f"root: {text[:80]}")
            text = text.split("&&", 1)[-1].strip()
        if _VIA_PYTHON.search(text):
            return Violated(f"the suite is run through `python -m pytest`, not a bare "
                            f"pytest: {text[:80]}")
        if not _BARE_PYTEST.match(text):
            return Violated(f"the suite is not run with a bare pytest: {text[:80]}")
        return Satisfied(f"the suite is run with a bare pytest: {text[:80]}")


@rule(
    id="MATPLOTLIB-C271",
    category=CATEGORY,
    ownership="touched",  # spec §4.2 -- the antecedent is the code change, which is code
                          # that already existed; the test it demands is the artefact
    reads=("files",),  # spec §5: the sentence, not CheckTier=differential -- both the
                       # changed code and the test that accompanies it are in the patch
    heuristic=True,
)
class NewAndChangedCodeIsTested:
    """Pre-condition: a contribution that changes library code outside the tests.
    Pass condition: it also adds or edits a test function.

    Fires on the *change*, not on the test (§7.1), so a contribution that ships no test is
    a recorded violation rather than an absent row -- the whole point of the sentence.

    Heuristic on the **pre-condition** (§6.3): "new and changed code" is approximated by
    library Python appearing in the patch, a superset that also catches a comment fix
    nobody would ask for a test about.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        changed = source_files(b)
        if not changed:
            return []
        return [target(f"tested:{b.instance_id}", None, None, b,
                       f"{len(changed)} library file(s) changed")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        written = test_functions(bundle)
        if written:
            path, _module, function = written[0]
            return Satisfied(f"{len(written)} test(s) accompany the change, e.g. "
                             f"{path}::{function.name}")
        return Violated("library code changed and the contribution adds or edits no test "
                        "function")


# --- where a test lives and what it is called ---------------------------------------------


@rule(
    id="MATPLOTLIB-C167",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- "put a test in the file" is about a test being
                          # placed, i.e. one the agent added
    reads=("files",),  # spec §5: the path and the module it mirrors are both in the patch
    heuristic=True,
)
class ATestGoesInTheFileMirroringTheModuleItTests:
    """Pre-condition: each test function the agent added, in a contribution that also
    changes at least one library module.
    Pass condition: it sits under the tests tree, in a file whose stem names one of those
    modules.

    Grades the **directory and the mirroring only**; the ``test_`` prefix is C168's and is
    stripped before the stems are compared, so a file called ``tests/axis.py`` satisfies
    this rule and violates that one (§7.5).

    Heuristic on **both** layers (§6.3, §6.2). *The module it tests* is not recorded
    anywhere, so it is approximated by the library modules the same contribution changed;
    and the mirroring accepts the module's own stem or its package directory's name, since
    ``axes/_axes.py`` is tested in ``test_axes.py``.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        stems = _module_stems(b)
        if not stems:
            return []
        return [target(f"mirrors:{path}:{function.name}", path, function.span(),
                       (path, function, stems), f"{path}::{function.name}")
                for path, _module, function in test_functions(b, mode="created")]

    def pass_condition(self, t: Target):
        path, function, stems = t.payload
        if not (path.startswith(TEST_ROOT) or is_test_path(path)):
            return Violated(f"{path}::{function.name} is not under {TEST_ROOT}")
        stem = _mirrored_stem(path)
        if stem in stems:
            return Satisfied(f"{path} mirrors the changed module {stem}")
        return Violated(f"{path}::{function.name} is filed under a stem ({stem!r}) that "
                        f"mirrors none of the modules this change touches: "
                        f"{', '.join(sorted(stems)[:3])}")


@rule(
    id="MATPLOTLIB-C168",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- naming a module is naming one the agent added
    reads=("files",),  # spec §5: the file name is in the patch
    heuristic=True,
)
class ATestModuleIsNamedWithATestPrefix:
    """Pre-condition: each file the agent added under a tests tree that defines something
    pytest would collect.
    Pass condition: its name begins with ``test_``.

    §7.1: the antecedent cannot be "a module named ``test_*``" -- that selects only the
    compliant ones -- so it is *a module of tests*, recognised by its content.

    Heuristic on the **pre-condition** (§6.3), which recognises a test module by a
    function that asserts or carries an image-comparison decorator; a module of nothing
    but fixtures is deliberately not selected, and ``conftest.py`` and ``__init__.py`` are
    excluded because pytest gives them their own names.

    Grades the prefix and nothing else: where the file sits and what it mirrors are
    C167's, so a misfiled but correctly prefixed module passes here (§7.5).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in modules(b, mode="created", tests=True):
            name = path.rsplit("/", 1)[-1]
            if name in ("conftest.py", "__init__.py"):
                continue
            if not any(_looks_like_a_test(f) for f in module.functions):
                continue
            out.append(target(f"test-module:{path}", path, None, (path, name), path))
        return out

    def pass_condition(self, t: Target):
        path, name = t.payload
        if name.startswith(TEST_PREFIX):
            return Satisfied(f"{path} is named with the test_ prefix")
        return Violated(f"{path} defines tests but is not named with a test_ prefix, so "
                        f"pytest never collects it")


@rule(
    id="MATPLOTLIB-C169",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- naming a test is naming one the agent added
    reads=("files",),  # spec §5: the definition is in the patch
    heuristic=True,
)
class ATestFunctionIsNamedWithATestPrefix:
    """Pre-condition: each function the agent added to a test module that asserts
    something or carries an image-comparison decorator.
    Pass condition: its name begins with ``test_``.

    §7.1 again: selecting functions already called ``test_*`` would make the rule
    unfailable, so the antecedent is *a function that behaves like a test*.

    Heuristic on the **pre-condition** (§6.3): "behaves like a test" is approximated by
    containing an ``assert`` or wearing ``@image_comparison`` /
    ``@check_figures_equal``, with fixtures and context managers excluded. A test whose
    only check is a ``pytest.raises`` block is not seen, and a helper full of assertions
    is wrongly selected.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, function in owned_functions(b, mode="created", tests=True):
            if not _looks_like_a_test(function):
                continue
            out.append(target(f"test-name:{path}:{function.name}", path, function.span(),
                              (path, function), f"{path}::{function.name}"))
        return out

    def pass_condition(self, t: Target):
        path, function = t.payload
        if function.name.startswith(TEST_PREFIX):
            return Satisfied(f"{path}::{function.name} carries the test_ prefix")
        return Violated(f"{path}::{function.name} asserts like a test but has no test_ "
                        f"prefix, so pytest never collects it")


@rule(
    id="MATPLOTLIB-C170",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- naming a class is naming one the agent added
    reads=("files",),  # spec §5: the definition is in the patch
    heuristic=True,
)
class ATestClassIsNamedWithATestPrefix:
    """Pre-condition: each class the agent added to a test module whose body holds a
    method that behaves like a test.
    Pass condition: its name begins with ``Test``.

    Heuristic on the **pre-condition** (§6.3), for the same reason as C169: a class is
    recognised as a grouping of tests by what its methods do, since selecting on the name
    would make the rule unfailable (§7.1).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in modules(b, tests=True):
            authored = b.files[path].authored_lines
            for node in classes(module):
                if node.lineno not in authored:
                    continue
                methods = [f for f in module.functions
                           if node.lineno < f.lineno <= (node.end_lineno or node.lineno)]
                if not any(_looks_like_a_test(f) for f in methods):
                    continue
                out.append(target(f"test-class:{path}:{node.name}", path,
                                  (node.lineno, node.end_lineno or node.lineno),
                                  (path, node), f"{path}::{node.name}"))
        return out

    def pass_condition(self, t: Target):
        path, node = t.payload
        if node.name.startswith(TEST_CLASS_PREFIX):
            return Satisfied(f"{path}::{node.name} carries the Test prefix")
        return Violated(f"{path}::{node.name} groups tests but has no Test prefix, so "
                        f"pytest never collects it")


# --- randomness -----------------------------------------------------------------------


@rule(
    id="MATPLOTLIB-C176",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a property "any test" must have, with no newness
                          # qualifier in the sentence
    reads=("files",),  # spec §5: the calls are in the patch
    heuristic=True,
)
class ATestUsingRandomNumbersFixesTheSeed:
    """Pre-condition: each test the agent wrote or edited that draws random numbers.
    Pass condition: it fixes a seed -- by seeding the global routine, or by constructing
    a generator with one.

    Asks only whether *a* seed is fixed. Which value it must be is C177's question and is
    deliberately not asked twice, so a test seeded with ``42`` passes here and fails there
    (§7.5).

    Heuristic on the **pre-condition** (§6.3): randomness is recognised from the call
    names in the test body, so a helper that draws numbers on the test's behalf is not
    seen; and a fixture supplying a seeded generator reads as a violation.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, function in test_functions(b):
            called = calls_in(function.node)
            if not any(_RANDOM_CALL.search(c) for c in called):
                continue
            out.append(target(f"seeded:{path}:{function.name}", path, function.span(),
                              (path, function, called), f"{path}::{function.name}"))
        return out

    def pass_condition(self, t: Target):
        path, function, called = t.payload
        seeds = [c for c in called if _SEED_CALL.match(c)]
        if seeds:
            return Satisfied(f"{path}::{function.name} fixes its seed with {seeds[0]}()")
        return Violated(f"{path}::{function.name} draws random numbers without fixing a "
                        f"seed, so its result is not reproducible")


@rule(
    id="MATPLOTLIB-C177",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the target is a seeding call the agent wrote
    reads=("files",),  # spec §5: the argument is in the patch
)
class NumpysGeneratorIsSeededWithTheProjectSeed:
    """Pre-condition: each call the agent wrote that seeds numpy's random generator.
    Pass condition: the seed is ``19680801``.

    Not heuristic (§6.2): the pass condition compares against a number the project
    publishes, and the pre-condition selects on an observable call. Both the legacy
    ``np.random.seed`` and ``np.random.default_rng``/``RandomState`` spellings are
    accepted as "numpy's default random generator", because the project's own examples use
    the first and its newer tests the second.

    Selecting the *seeding call* rather than the test keeps this apart from C176 (§7.5): a
    test that seeds nothing is that rule's finding and finds no target here.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in modules(b):
            if module.tree is None:
                continue
            authored = b.files[path].authored_lines
            for name, node in call_nodes_in(module.tree):
                if not _NUMPY_SEED_CALL.match(name) or node.lineno not in authored:
                    continue
                out.append(target(f"seed-value:{path}:{node.lineno}", path,
                                  (node.lineno, node.end_lineno or node.lineno),
                                  (path, name, node), f"{name}(...) at {path}:{node.lineno}"))
        return out

    def pass_condition(self, t: Target):
        path, name, node = t.payload
        value = literal_of(node.args[0]) if node.args else None
        if value == PROJECT_SEED:
            return Satisfied(f"{path}:{node.lineno} seeds {name} with {PROJECT_SEED}")
        if value is None:
            return Violated(f"{path}:{node.lineno} calls {name} with no literal seed, so "
                            f"the run is not reproducible")
        return Violated(f"{path}:{node.lineno} seeds {name} with {value!r}, not the "
                        f"project's {PROJECT_SEED}")


@rule(
    id="MATPLOTLIB-C178",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a property the sentence states of test figures
                          # generally, with no newness qualifier
    reads=("files",),  # spec §5: the construction is in the patch
    heuristic=True,
)
class TestFiguresAreMadeThroughPyplot:
    """Pre-condition: each test the agent wrote or edited that creates a Figure or an
    Axes, by whatever means.
    Pass condition: it creates them through a pyplot constructor rather than by
    instantiating the class.

    §7.1: the antecedent is *making a figure*, so a test that makes one properly is
    recorded as a pass; selecting direct instantiations would only ever find violations.

    Heuristic on the **pre-condition** (§6.3), which recognises figure creation from the
    call names in the test body: a figure produced by a fixture or by a helper the test
    calls is not seen.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, function in test_functions(b):
            called = calls_in(function.node)
            if not any(_PYPLOT_CONSTRUCTOR.match(c) or _DIRECT_CONSTRUCTOR.search(c)
                       for c in called):
                continue
            out.append(target(f"pyplot-figure:{path}:{function.name}", path,
                              function.span(), (path, function, called),
                              f"{path}::{function.name}"))
        return out

    def pass_condition(self, t: Target):
        path, function, called = t.payload
        direct = [c for c in called if _DIRECT_CONSTRUCTOR.search(c)
                  and not _PYPLOT_CONSTRUCTOR.match(c)]
        if direct:
            return Violated(f"{path}::{function.name} builds its figure with "
                            f"{direct[0]}() instead of a pyplot constructor")
        made = [c for c in called if _PYPLOT_CONSTRUCTOR.match(c)]
        return Satisfied(f"{path}::{function.name} builds its figure with {made[0]}()")


# --- image comparison ------------------------------------------------------------------


@rule(
    id="MATPLOTLIB-C181",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a property of the decorator, no newness qualifier
    reads=("files",),  # spec §5: the decorator is in the patch
)
class TheImageComparisonDecoratorNamesItsBaselines:
    """Pre-condition: each test the agent wrote or edited that carries
    ``@image_comparison``.
    Pass condition: the decorator supplies a non-empty list of baseline image names.

    Not heuristic (§6.2): the decorator's first argument either is a list of names or it
    is not, which is a presence check against something the rule names exactly.

    Asks only whether the names are *there*. Whether they carry a file extension is
    C183's question, and that rule finds no target when there is nothing to inspect
    (§7.5).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"baselines-named:{path}:{function.name}", path, function.span(),
                       (path, function, dec), f"{path}::{function.name}")
                for path, _module, function, dec in _image_tests(b)]

    def pass_condition(self, t: Target):
        path, function, dec = t.payload
        names = baseline_images(dec)
        if names:
            return Satisfied(f"{path}::{function.name} names {len(names)} baseline "
                             f"image(s), e.g. {names[0]}")
        return Violated(f"{path}::{function.name} carries @{IMAGE_COMPARISON} without "
                        f"naming the expected baseline images")


@rule(
    id="MATPLOTLIB-C182",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- "the new baseline image" is a newness qualifier
    reads=("files",),  # spec §5: the sentence, not CheckTier=differential -- the image is
                       # a file, so it is in the diff or it is not
    heuristic=True,
)
class TheNewBaselineImageIsCommittedBesideItsTest:
    """Pre-condition: each baseline image name declared by an ``@image_comparison`` test
    the agent added.
    Pass condition: a file of that name is committed under the test module's
    ``baseline_images`` subdirectory.

    §4.2 is why this is scoped to tests the agent *added*: a pre-existing test's baseline
    is already in the tree and demanding it again in this patch would fail every run that
    edited one.

    Heuristic on the **pass condition** (§6.2): a baseline name is written without its
    extension, so the check accepts any committed file whose stem matches, in any of the
    image formats the decorator compares.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, function, dec in _image_tests(b, mode="created"):
            for name in baseline_images(dec) or []:
                out.append(target(f"baseline-file:{path}:{name}", path, function.span(),
                                  (path, function, str(name), b),
                                  f"{path}::{function.name} expects {name}"))
        return out

    def pass_condition(self, t: Target):
        path, function, name, bundle = t.payload
        folder = _baseline_dir(path)
        stem = name
        for suffix in _IMAGE_SUFFIXES:
            if stem.endswith(suffix):
                stem = stem[:-len(suffix)]
                break
        committed = [p for p in bundle.files
                     if p.startswith(folder)
                     and p[len(folder):].rsplit(".", 1)[0] == stem]
        if committed:
            return Satisfied(f"{committed[0]} is committed for "
                             f"{path}::{function.name}")
        return Violated(f"{path}::{function.name} expects baseline {name!r} but no "
                        f"matching image is committed under {folder}")


@rule(
    id="MATPLOTLIB-C183",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a property of the names, no newness qualifier
    reads=("files",),  # spec §5: the decorator is in the patch
)
class BaselineNamesOmitTheExtensionWhenSeveralFormatsAreCompared:
    """Pre-condition: each baseline name declared by an ``@image_comparison`` test whose
    decorator compares more than one format.
    Pass condition: the name carries no file extension.

    "Several formats" is decided from the decorator's ``extensions`` argument, and from
    its documented default of ``png``, ``pdf`` and ``svg`` when the argument is absent, so
    a test pinned to a single format is out of scope rather than failed.

    Not heuristic (§6.2): the extension is either present in the string or it is not, and
    the alternative the rule wants is stated. Finds no target when the decorator names no
    baselines at all -- that omission is C181's (§7.5).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, function, dec in _image_tests(b):
            extensions = literal_of(decorator_argument(dec, None, "extensions"))
            if extensions is None:
                extensions = list(DEFAULT_EXTENSIONS)
            if len(extensions) < 2:
                continue
            for name in baseline_images(dec) or []:
                out.append(target(f"baseline-ext:{path}:{name}", path, function.span(),
                                  (path, function, str(name), tuple(extensions)),
                                  f"{path}::{function.name} expects {name}"))
        return out

    def pass_condition(self, t: Target):
        path, function, name, extensions = t.payload
        if name.lower().endswith(_IMAGE_SUFFIXES):
            return Violated(f"{path}::{function.name} names its baseline {name!r} with a "
                            f"file extension while comparing "
                            f"{len(extensions)} formats")
        return Satisfied(f"{path}::{function.name} names its baseline {name!r} without an "
                         f"extension")


@rule(
    id="MATPLOTLIB-C184",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- "a new image-comparison test" is a newness
                          # qualifier, stated in the sentence
    reads=("files",),  # spec §5: the decorator is in the patch
)
class ANewImageComparisonTestPinsTheMpl20Style:
    """Pre-condition: each ``@image_comparison`` test the agent added.
    Pass condition: its decorator sets ``style='mpl20'``.

    Not heuristic (§6.2): the value is a string the sentence names, so the check is an
    equality against a stated criterion. Scoped to tests the agent *added* because the
    sentence says "a new image-comparison test"; an existing test edited in place keeps
    whatever style its baselines were generated under, and failing it would grade the
    agent on someone else's choice (§4.3).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"mpl20:{path}:{function.name}", path, function.span(),
                       (path, function, dec), f"{path}::{function.name}")
                for path, _module, function, dec in _image_tests(b, mode="created")]

    def pass_condition(self, t: Target):
        path, function, dec = t.payload
        style = literal_of(decorator_argument(dec, None, "style"))
        if style == MPL20_STYLE:
            return Satisfied(f"{path}::{function.name} pins style={MPL20_STYLE!r}")
        if style is None:
            return Violated(f"{path}::{function.name} is a new image-comparison test "
                            f"that sets no style, so it inherits whatever the suite left "
                            f"in place")
        return Violated(f"{path}::{function.name} sets style={style!r}, not "
                        f"{MPL20_STYLE!r}")


@rule(
    id="MATPLOTLIB-C187",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a property of the signature, no newness qualifier
    reads=("files",),  # spec §5: the signature is in the patch
    heuristic=True,
)
class ACheckFiguresEqualTestTakesTwoFigureParameters:
    """Pre-condition: each test the agent wrote or edited that carries
    ``@check_figures_equal``.
    Pass condition: it takes exactly the two figure parameters the decorator injects,
    ``fig_test`` and ``fig_ref``.

    Heuristic on the **pass condition** (§6.2): the two parameters are checked by the
    names the decorator supplies, but *which* of them is drawn by the tested method and
    which by the baseline method is a fact about the body that no signature records, so
    the second half of the sentence is approximated by the pair being present and
    distinct. Other parameters -- fixtures, ``pytest.mark.parametrize`` arguments -- are
    permitted, since the sentence constrains the Figure parameters only.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, function in owned_functions(b, tests=True):
            if not function.has_decorator(CHECK_FIGURES_EQUAL):
                continue
            out.append(target(f"figures-equal:{path}:{function.name}", path,
                              function.span(), (path, function),
                              f"{path}::{function.name}"))
        return out

    def pass_condition(self, t: Target):
        path, function = t.payload
        names = parameter_names(function)
        present = [p for p in FIGURE_PARAMETERS if p in names]
        if len(present) == 2:
            return Satisfied(f"{path}::{function.name} takes {', '.join(present)}")
        missing = [p for p in FIGURE_PARAMETERS if p not in names]
        return Violated(f"{path}::{function.name} uses @{CHECK_FIGURES_EQUAL} without "
                        f"both figure parameters -- {', '.join(missing)} missing")


@rule(
    id="MATPLOTLIB-C188",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a property of how a tolerance is set, no newness
                          # qualifier
    reads=("files",),  # spec §5: the decorator and the body are both in the patch
    heuristic=True,
)
class AnImageComparisonToleranceIsSetWithTheTolArgument:
    """Pre-condition: each ``@image_comparison`` test the agent wrote or edited in which a
    comparison tolerance is set at all, by any means.
    Pass condition: it is set with the decorator's ``tol`` argument and nowhere else.

    §7.1's shape for a "do it this way rather than any other" sentence: a test that needs
    no tolerance finds no target, one that sets it in the decorator passes, and one that
    reaches for ``compare_images`` in its body to pass a tolerance is a violation.

    Heuristic on the **pre-condition** (§6.3): "setting a tolerance" is recognised from
    two forms -- the decorator's ``tol`` keyword and a tolerance argument to a
    ``compare_images`` call -- so a tolerance smuggled in through a fixture or an rcParam
    is not seen.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, function, dec in _image_tests(b):
            tol = decorator_argument(dec, None, "tol")
            others = [node for name, node in call_nodes_in(function.node)
                      if name.split(".")[-1] == "compare_images"
                      and (len(node.args) > 2 or any(k.arg == "tol" for k in node.keywords))]
            if tol is None and not others:
                continue
            out.append(target(f"tolerance:{path}:{function.name}", path, function.span(),
                              (path, function, tol, others),
                              f"{path}::{function.name}"))
        return out

    def pass_condition(self, t: Target):
        path, function, tol, others = t.payload
        if others:
            return Violated(f"{path}::{function.name} sets its comparison tolerance in a "
                            f"compare_images() call at line {others[0].lineno} rather "
                            f"than with the decorator's tol argument")
        return Satisfied(f"{path}::{function.name} sets its tolerance with the "
                         f"decorator's tol argument")
