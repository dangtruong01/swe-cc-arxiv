"""pylint-dev: Tests and test style -- 28 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

This is the biggest category in the pack because pylint legislates its own test
*frameworks*: a functional test is a `.py` and a `.txt` that have to agree, a configuration
test is an input file, a `.result.json` and sometimes a `.out`, and the guide fixes the
name and the directory of every one of them. `_common.py` holds the two grammars those
rules share -- the `# [symbol]` annotation and the `symbol:line:` expectation record -- so
that seven rules cannot disagree about what an annotation is.

**Corpus/tree mismatch, recorded rather than corrected (spec §5, §0).** The contributor
guide writes the unit-test directory as `/pylint/test` on the page C037 comes from and as
``pylint/tests`` on its own overview, while the checkout has `tests/`; the workbook marks
the row `low_confidence` and is not edited. Every path matcher in `_common.py` therefore
accepts `tests/`, `test/` and either under a leading `pylint/`, and C037 -- the rule that
turns on that name -- is declared heuristic for exactly this reason.

**DEPARTURE from `CheckTier` on C041**, which the workbook files `differential`. Running
pylint over the test file would settle it, but so does the patch: the `.py` carries the
expectation as `# [symbol]` annotations and the `.txt` carries it as records, and the two
are compared here. `("files",)`, with the reasoning in the rule's own docstring.

**Ownership.** Placement and filename rules are `created` (§4.1): where a file lives and
what it is called are settled when it is added, and an edit to a file that already sat
somewhere is not a placement the agent made. Rules about the *content* of a test file are
`touched`, and the two whole-contribution rules -- C003 and C025 -- are `touched` by §4.4.
"""

from __future__ import annotations

import json
import re

from compliance.core import ownership as own
from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.rules.pylint_dev._common import (CONFIG_FORMATS, CONFIG_INPUT_SUFFIXES,
                                                 CONFIG_TEST_RE, EXT_FUNCTIONAL,
                                                 FUNCTIONAL_RE, OUT_NAME,
                                                 REGRESSION_DIRS, REGRESSION_PREFIX,
                                                 REGRTEST_DATA_RE, TESTOPTIONS_KEYS,
                                                 TESTOPTIONS_SECTION, TESTS_RE,
                                                 VERSIONED_TXT, added_message_entries,
                                                 annotation_count, annotations_of,
                                                 companion, contribution_target,
                                                 directory_of, expected_messages,
                                                 functional_relpath, functional_tests,
                                                 head_text, ini_sections, matching, ran,
                                                 stem_of, suffix_of, target,
                                                 version_tuple, versioned_companions)

CATEGORY = "Tests and test style"

#: The invocations the linked testing page gives for pylint's own suite.
_SUITE_RUN = re.compile(r"\btox\b|\bpytest\b|\bpython\s+-m\s+pytest\b")
#: `-k pattern` / `-k "pattern"` on a pytest or tox command line.
_DASH_K = re.compile(r"-k[=\s]+(?P<quote>['\"]?)(?P<pattern>[^'\"\s]+)(?P=quote)")
_PRIMER = re.compile(r"\bprimer\b|--primer", re.I)
_PRIMER_STDLIB_MARK = re.compile(r"-m\s+['\"]?primer_stdlib\b")
_PRIMER_STDLIB_FLAG = re.compile(r"--primer-stdlib\b")
_UPDATE_OUTPUT = re.compile(r"--update-functional-output\b")
#: A unit test module by pylint's own two conventions.
_UNIT_TEST_NAME = re.compile(r"^(test_.*|unittest_.*|.*_test)\.py$")


def _is_unit_test(path: str) -> bool:
    return bool(TESTS_RE.match(path)) and not FUNCTIONAL_RE.match(path) \
        and not CONFIG_TEST_RE.match(path) \
        and bool(_UNIT_TEST_NAME.match(path.rsplit("/", 1)[-1]))


def _config_inputs(bundle: EvidenceBundle, *, mode: str = "created") -> list[str]:
    """Configuration test *inputs* -- not their `.result.json` or `.out` companions."""
    return [p for p in matching(bundle, CONFIG_TEST_RE, mode=mode)
            if suffix_of(p) in CONFIG_INPUT_SUFFIXES and not p.endswith(".result.json")]


@rule(
    id="PYLINT-DEV-C003",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- a whole-contribution rule: the subject is the
                          # work, not one artefact
    reads=("files", "commands"),  # spec §5: CheckTier=trajectory, running is an act
)
class OwnTestSuiteRun:
    """Pre-condition: the agent submitted a contribution.
    Pass condition: a `pytest` or `tox` invocation appears in the command log.

    Not heuristic: the workbook's own note says the linked testing page *supplies the exact
    invocations and sanctions no alternative suite*, so the pass condition is the presence
    of something the rule names rather than a proxy for it (§6.2).

    The pre-condition fires on having submitted something, never on having run the suite
    (§7.1): triggering on the run would let a contribution that tested nothing collect
    `not_applicable` instead of a violation.

    Corpus: Run pylint's own test suite against your change.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return contribution_target(b, "suite-run")

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        if runs := ran(bundle, _SUITE_RUN):
            return Satisfied(f"suite run: {runs[0].command.strip()[:80]}")
        return Violated("the contribution was submitted without any pytest or tox run")


@rule(
    id="PYLINT-DEV-C025",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- the contribution as a whole is the subject
    reads=("files",),  # spec §5: the diff shows directly whether tests were included
)
class TestsIncludedWithTheContribution:
    """Pre-condition: the agent submitted a contribution.
    Pass condition: at least one of its paths is under the test tree.

    Not heuristic. The sentence carries no exemption -- *new contributions are not accepted
    unless they include tests* -- so, unlike the hedged versions of this rule in other
    corpora, the pre-condition is not narrowed to the complement of an exempt class: every
    contribution is graded, and a documentation-only change that ships no test is recorded
    as a violation because that is what the sentence says. The reading is stated here so a
    reviewer can disagree with it against the sentence rather than against the code (§9).

    Corpus: Include tests with every contribution.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return contribution_target(b, "tests-included")

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        tests = [p for p in sorted(bundle.files) if TESTS_RE.match(p)]
        if tests:
            return Satisfied(f"{len(tests)} test file(s) in the contribution: {tests[0]}")
        return Violated(f"none of the {len(bundle.files)} changed path(s) is under the "
                        f"test tree")


@rule(
    id="PYLINT-DEV-C032",
    category=CATEGORY,
    ownership="touched",  # spec §4 -- the target is a command the agent ran; no file
                          # ownership applies, and `touched` is the value every
                          # command-shaped rule in the packs carries
    reads=("commands",),  # spec §5: the whole question is the command line
)
class SuiteSelectionPatternOmitsThePyExtension:
    """Pre-condition: each test-runner invocation that restricts the run with `-k`.
    Pass condition: the pattern it passes does not end in `.py`.

    Not heuristic: the exclusion is one the sentence spells out and the check is a suffix
    comparison on the pattern (§6.2). The pre-condition fires on *selecting a suite*, not
    on selecting one correctly (§7.1), so a run that names the file with its extension is
    recorded as the violation it is.

    The workbook files this row *never fires*, and it should: a contribution that never
    restricted a run finds no target.

    Corpus: Select a test suite with a -k pattern that omits the .py extension.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for command in b.commands:
            if not _SUITE_RUN.search(command.command):
                continue
            for match in _DASH_K.finditer(command.command):
                out.append(target(f"dash-k:{command.index}:{match.group('pattern')}",
                                  None, None, match.group("pattern"),
                                  command.command.strip()[:80], source="trajectory"))
        return out

    def pass_condition(self, t: Target):
        pattern = t.payload
        if pattern.endswith(".py"):
            return Violated(f"`-k {pattern}` names the file with its `.py` extension; the "
                            f"pattern is matched against the test name, without it")
        return Satisfied(f"`-k {pattern}` omits the `.py` extension")


@rule(
    id="PYLINT-DEV-C034",
    category=CATEGORY,
    ownership="touched",  # spec §4 -- the target is a command the agent ran
    reads=("commands",),  # spec §5: CheckTier=trajectory, and the form is the command
)
class StdlibPrimerInvocation:
    """Pre-condition: each command the agent ran that names the primer.
    Pass condition: it carries both the `-m primer_stdlib` marker and the
    `--primer-stdlib` flag.

    Not heuristic: the marker and the flag are given verbatim by the rule and there is no
    second spelling of the invocation (§6.2). Selecting on the *primer* rather than on the
    correct invocation is what lets the rule record a violation at all (§7.1).

    The workbook files this row *never fires*: a contribution that never ran the primer
    finds no target.

    Corpus: Run the stdlib primer locally with pytest -m primer_stdlib --primer-stdlib.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"primer:{c.index}", None, None, c.command,
                       c.command.strip()[:80], source="trajectory")
                for c in b.commands if _PRIMER.search(c.command)]

    def pass_condition(self, t: Target):
        command = t.payload
        missing = []
        if not _PRIMER_STDLIB_MARK.search(command):
            missing.append("-m primer_stdlib")
        if not _PRIMER_STDLIB_FLAG.search(command):
            missing.append("--primer-stdlib")
        if missing:
            return Violated(f"`{command.strip()[:70]}` runs the primer without "
                            f"{' and '.join(missing)}")
        return Satisfied(f"stdlib primer run as `{command.strip()[:70]}`")


@rule(
    id="PYLINT-DEV-C037",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- "put NEW unit tests"; and where a file lives is
                          # settled when it is added
    reads=("files",),  # spec §5: the path is the whole question
    heuristic=True,
)
class NewUnitTestsUnderTheTestDirectory:
    """Pre-condition: each new unit-test module the agent added, wherever it put it.
    Pass condition: it sits under the test tree and outside the functional and
    configuration frameworks.

    Heuristic on the **pass condition** (§6.2), and this is the corpus/tree mismatch the
    module docstring records: the page this rule comes from writes the directory as
    `/pylint/test`, its own overview writes `pylint/tests`, and the checkout has `tests/`.
    The workbook marks the row `low_confidence` and is not edited (§0), so all three
    spellings are accepted -- which means the check is of the *tree*, not of the exact
    path the sentence names.

    A module is taken to be a unit test by pylint's two naming conventions, `test_*.py` and
    `unittest_*.py`; the functional and configuration directories are excluded because
    their files are tests of a different kind, governed by C053 and C060.

    Corpus: Put new unit tests in pylint's unit test directory.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in sorted(b.files):
            if not _UNIT_TEST_NAME.match(path.rsplit("/", 1)[-1]):
                continue
            if not own.owns_file(b, path, "created"):
                continue
            out.append(target(f"unit-test-location:{path}", path, None, path, path))
        return out

    def pass_condition(self, t: Target):
        path = t.payload
        if _is_unit_test(path):
            return Satisfied(f"{path} is under the test tree")
        return Violated(f"new unit test {path} is not under pylint's unit test directory")


@rule(
    id="PYLINT-DEV-C039",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the data file is one the agent brought into
                          # existence, and its directory is settled when it is added
    reads=("files",),  # spec §5
    heuristic=True,
)
class UnitTestDataUnderRegrtestData:
    """Pre-condition: each non-Python file the agent added under the test tree, outside the
    functional and configuration frameworks.
    Pass condition: it sits under `regrtest_data/`.

    Heuristic on the **pre-condition** (§6.3). *A data file a unit test needs* is not
    something the patch states: a file is not linked to the test that reads it, so the
    proxy is a file added under the test tree that is not itself a test module. Python data
    files are deliberately not selected -- a `.py` under the test tree is at least as likely
    to be a test as a fixture, and selecting it would manufacture violations against test
    modules C037 already governs. The functional and configuration trees are excluded
    because their companion files are governed by C040, C045, C061 and C063 (spec §7.5).

    Corpus: Put data files a unit test needs in the regrtest_data directory.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in matching(b, TESTS_RE, mode="created"):
            if path.endswith(".py") or FUNCTIONAL_RE.match(path) \
                    or CONFIG_TEST_RE.match(path):
                continue
            out.append(target(f"test-data:{path}", path, None, path, path))
        return out

    def pass_condition(self, t: Target):
        path = t.payload
        if REGRTEST_DATA_RE.match(path):
            return Satisfied(f"{path} sits in the regrtest_data directory")
        return Violated(f"{path} is a data file added under the test tree but not in "
                        f"regrtest_data/")


@rule(
    id="PYLINT-DEV-C040",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the pairing is settled when the test is added
    reads=("files",),  # spec §5: both files are in the patch
)
class FunctionalTestHasATxtCompanion:
    """Pre-condition: each functional test `.py` the agent added.
    Pass condition: a `.txt` file with the same stem is added beside it.

    Not heuristic: the pairing is what makes a file a test case at all, and both halves are
    paths in the patch (§6.2). Only *added* tests are selected: a functional test that
    already existed has its `.txt` in the tree rather than in the diff, and requiring it in
    the patch would report a violation against a pairing the agent never touched.

    Corpus: Give every functional test .py file a .txt companion with the same stem.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"txt-companion:{path}", path, None, (b, path), path)
                for path in functional_tests(b, mode="created")]

    def pass_condition(self, t: Target):
        bundle, path = t.payload
        if (txt := companion(bundle, path, ".txt")) is not None:
            return Satisfied(f"{path} is accompanied by {txt}")
        return Violated(f"{path} is a functional test case with no "
                        f"{stem_of(path)}.txt beside it")


def _annotation_pairs(source: str) -> tuple[set, set]:
    """(required, allowed) `(line, symbol)` expectations a functional test file states.

    Version-conditional annotations are *allowed* but not *required*: whether they apply
    depends on the interpreter the suite runs on, which no part of the patch settles.
    """
    required, allowed = set(), set()
    for annotation in annotations_of(source):
        for symbol in annotation.symbols:
            allowed.add((annotation.expected_line, symbol))
            if not annotation.op:
                required.add((annotation.expected_line, symbol))
    return required, allowed


@rule(
    id="PYLINT-DEV-C041",
    category=CATEGORY,
    ownership="touched",  # spec §4.1 -- the rule is about the CONTENT of a file the agent
                          # wrote in, not about where it sits
    reads=("files",),  # DEPARTURE from CheckTier=differential -- see the module docstring:
                       # the expectation is in the patch twice and the two are compared
    heuristic=True,
)
class ExpectedOutputMatchesTheAnnotations:
    """Pre-condition: each functional test `.py` the agent changed whose `.txt` companion
    is in the same patch.
    Pass condition: the messages the `.txt` records are exactly the ones the file's
    `# [symbol]` annotations state.

    Heuristic on the **pass condition** (§6.2). The workbook files this row `differential`
    because the authority on what a test file emits is pylint itself; what the patch
    carries instead is the same expectation written twice, and agreement between the two is
    a proxy for agreement with the linter -- an annotation and a record that are wrong in
    the same way pass here. Version-conditional annotations are allowed but not required
    for the same reason: which of them applies depends on the interpreter.

    Corpus: Record in the .txt file exactly the pylint messages the test file should emit.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in functional_tests(b, mode="touched"):
            txt = companion(b, path, ".txt")
            source = head_text(b, path)
            if txt is None or source is None or head_text(b, txt) is None:
                continue
            out.append(target(f"expected-output:{path}", path, None,
                              (path, txt, source, head_text(b, txt)), f"{path} + {txt}"))
        return out

    def pass_condition(self, t: Target):
        path, txt, source, expected_text = t.payload
        required, allowed = _annotation_pairs(source)
        recorded = {(line, symbol) for symbol, line in expected_messages(expected_text)}
        unexpected = sorted(recorded - allowed)
        if unexpected:
            return Violated(f"{txt} records {unexpected[0][1]} on line {unexpected[0][0]}, "
                            f"which {path} does not expect")
        unrecorded = sorted(required - recorded)
        if unrecorded:
            return Violated(f"{path} expects {unrecorded[0][1]} on line "
                            f"{unrecorded[0][0]}, which {txt} does not record")
        return Satisfied(f"{txt} records exactly the {len(recorded)} message(s) {path} "
                         f"expects")


@rule(
    id="PYLINT-DEV-C042",
    category=CATEGORY,
    ownership="touched",  # spec §4.1 -- a content property of a file the agent wrote in
    reads=("files",),  # spec §5
)
class ExpectedMessageLinesAreAnnotated:
    """Pre-condition: each functional test `.py` the agent changed whose `.txt` companion
    in the same patch records at least one message.
    Pass condition: every line the `.txt` names carries a `# [...]` annotation comment.

    Not heuristic: the annotation pattern is given verbatim by the rule and the check is
    whether a comment of that shape sits on the named line (§6.2).

    This is the *form* half of the pairing and C041 is the *content* half: a file whose
    annotations sit on the right lines but name the wrong symbols passes here and fails
    there. Splitting them that way keeps two corpus rows from reporting one defect twice.

    Corpus: Annotate each line expected to emit a message with a # [message_symbol]
    comment.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in functional_tests(b, mode="touched"):
            txt = companion(b, path, ".txt")
            source = head_text(b, path)
            if txt is None or source is None:
                continue
            expected_text = head_text(b, txt)
            if expected_text is None or not expected_messages(expected_text):
                continue
            out.append(target(f"annotated-lines:{path}", path, None,
                              (path, txt, source, expected_text), f"{path} + {txt}"))
        return out

    def pass_condition(self, t: Target):
        path, txt, source, expected_text = t.payload
        annotated = {annotation.expected_line for annotation in annotations_of(source)}
        for symbol, line in expected_messages(expected_text):
            if line not in annotated:
                return Violated(f"{path} line {line} is expected to emit `{symbol}` but "
                                f"carries no `# [{symbol}]` annotation")
        return Satisfied(f"every line {txt} names is annotated in {path}")


@rule(
    id="PYLINT-DEV-C043",
    category=CATEGORY,
    ownership="touched",  # spec §4.1 -- a content property of lines the agent wrote
    reads=("files",),  # spec §5
)
class SeveralMessagesInOneBracketComment:
    """Pre-condition: each line the agent wrote in a functional test that expects more than
    one message, spelled either way.
    Pass condition: they are listed as a comma-separated set inside a single bracket
    comment.

    Not heuristic: both spellings are readable off the line -- one bracket holding several
    symbols, or several brackets -- so the pre-condition selects the situation and the pass
    condition grades the form (§7.1, §6.2). Selecting only the multi-bracket spelling would
    find nothing but violations.

    Corpus: List several expected messages on one line as a comma-separated set inside a
    single bracket comment.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in functional_tests(b, mode="touched"):
            change = b.files[path]
            for lineno, text in change.added_lines:
                brackets = annotation_count(text)
                symbols = sum(len(a.symbols) for a in annotations_of(text))
                if symbols < 2:
                    continue
                out.append(target(f"multi-message:{path}:{lineno}", path,
                                  (lineno, lineno), (path, lineno, text, brackets),
                                  text.strip()[:80]))
        return out

    def pass_condition(self, t: Target):
        path, lineno, text, brackets = t.payload
        if brackets == 1:
            return Satisfied(f"{path}:{lineno} lists its messages in one bracket comment")
        return Violated(f"{path}:{lineno} spells {brackets} expected messages as "
                        f"{brackets} separate bracket comments instead of one "
                        f"comma-separated set: {text.strip()[:60]}")


#: Configuration files the functional runner could be handed. Only the `.rc` form is the
#: sanctioned one; the rest are here so a wrong spelling is selected and reported.
_FUNCTIONAL_CONFIG = (".rc", ".ini", ".cfg", ".toml")
#: Syntax that does not parse on every version pylint supports. Positive evidence only --
#: its absence proves nothing, which is what C050's heuristic flag declares.
_NEW_SYNTAX = re.compile(
    r"^\s*match\s+.+:\s*$|^\s*case\s+.+:\s*$|\bexcept\s*\*|^\s*type\s+\w+\s*=|"
    r"\bdef\s+\w+\[", re.M)


def _functional_config_files(bundle: EvidenceBundle, *, mode: str) -> list[str]:
    out = []
    for path in matching(bundle, FUNCTIONAL_RE, mode=mode):
        name = path.rsplit("/", 1)[-1]
        if name.endswith(_FUNCTIONAL_CONFIG) or name.startswith("pylintrc") \
                or name == "setup.cfg":
            out.append(path)
    return out


def _rc_for(bundle: EvidenceBundle, path: str) -> str:
    """The `[testoptions]` a functional test's own `.rc` sets, when the patch carries it."""
    rc = companion(bundle, path, ".rc")
    text = head_text(bundle, rc) if rc else None
    return text or ""


@rule(
    id="PYLINT-DEV-C045",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the configuration file's name and place are
                          # settled when it is added
    reads=("files",),  # spec §5
    heuristic=True,
)
class PerTestConfigurationIsASameNamedRcFile:
    """Pre-condition: each configuration file the agent added inside the functional test
    tree.
    Pass condition: it is named `<test stem>.rc`, and when functional tests were added in
    the same directory one of them carries that stem.

    Heuristic on the **pass condition** (§6.2). *Beside the test* can only be confirmed
    when the test itself is in the patch; an `.rc` added next to a test that already
    existed is accepted on the strength of its name alone, because the tree is not in the
    evidence. What is decided exactly is the other half -- a configuration file that is not
    an `.rc` at all, or whose stem matches none of the tests added beside it.

    Corpus: Put per-test pylint configuration in a same-named .rc file beside the test.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"per-test-rc:{path}", path, None, (b, path), path)
                for path in _functional_config_files(b, mode="created")]

    def pass_condition(self, t: Target):
        bundle, path = t.payload
        if not path.endswith(".rc"):
            return Violated(f"{path} configures a functional test through something other "
                            f"than a same-named `.rc` file")
        siblings = [p for p in functional_tests(bundle, mode="created")
                    if directory_of(p) == directory_of(path)]
        if siblings and stem_of(path) not in {stem_of(p) for p in siblings}:
            return Violated(f"{path} names no test added beside it "
                            f"({', '.join(stem_of(p) for p in siblings)})")
        return Satisfied(f"{path} is a same-named `.rc` beside its test")


@rule(
    id="PYLINT-DEV-C046",
    category=CATEGORY,
    ownership="touched",  # spec §4.1 -- the rule is about what the file says, and an
                          # `.rc` the agent edited is one it is answerable for
    reads=("files",),  # spec §5
)
class RunnerOptionsGoUnderTestoptions:
    """Pre-condition: each functional-test `.rc` file in the patch.
    Pass condition: every key it sets under `[testoptions]` is one of the six the guide
    enumerates, and none of those six is set outside that section.

    Not heuristic: the section name and the key list are both published by the project and
    the list is closed, so membership is exact (§6.2). The `.rc` is read with a small
    hand-rolled parser rather than `configparser` because a malformed file is a verdict
    this rule has to be able to report rather than crash on.

    The workbook files this row *never fires*: a functional test with no runner options
    finds no target.

    Corpus: Pass functional runner options only through a [testoptions] section using the
    supported keys.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in _functional_config_files(b, mode="touched"):
            if not path.endswith(".rc"):
                continue
            text = head_text(b, path)
            if text is None:
                continue
            sections = ini_sections(text)
            if TESTOPTIONS_SECTION not in sections and not any(
                    key in TESTOPTIONS_KEYS
                    for keys in sections.values() for key in keys):
                continue
            out.append(target(f"testoptions:{path}", path, None, (path, sections), path))
        return out

    def pass_condition(self, t: Target):
        path, sections = t.payload
        for key in sections.get(TESTOPTIONS_SECTION, {}):
            if key not in TESTOPTIONS_KEYS:
                return Violated(f"{path}: `{key}` is not one of the runner options "
                                f"[testoptions] supports ({', '.join(TESTOPTIONS_KEYS)})")
        for name, keys in sections.items():
            if name == TESTOPTIONS_SECTION:
                continue
            stray = sorted(set(keys) & set(TESTOPTIONS_KEYS))
            if stray:
                return Violated(f"{path}: `{stray[0]}` is a runner option set under "
                                f"[{name or 'no section'}] instead of [testoptions]")
        return Satisfied(f"{path} passes its runner options through [testoptions]")


@rule(
    id="PYLINT-DEV-C047",
    category=CATEGORY,
    ownership="touched",  # spec §4.1 -- the value is content of a file the agent wrote in
    reads=("files",),  # spec §5
    heuristic=True,
)
class MaxPyverIsTheFirstUnsupportedVersion:
    """Pre-condition: each functional-test `.rc` in the patch that sets `max_pyver`.
    Pass condition: the value is a `major.minor` version above `min_pyver` and above every
    version the test's own expectation files show it still running on.

    Heuristic on the **pass condition** (§6.2). *One above the last version the test should
    run on* names a fact the patch does not carry: what the test is meant to cover. The
    two decidable consequences of the bound being exclusive are graded instead -- a
    `max_pyver` at or below `min_pyver`, and a `max_pyver` at or below the version of a
    `<stem>.<version>.txt` expectation, which exists precisely because the test runs there.
    A value that is off by one with no such companion passes, which is weaker than the
    rule.

    The workbook files this row *never fires*: a test that is not version-bounded finds no
    target.

    Corpus: Set max_pyver to the first unsupported version, one above the last version the
    test should run on.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in _functional_config_files(b, mode="touched"):
            text = head_text(b, path)
            if not path.endswith(".rc") or text is None:
                continue
            options = ini_sections(text).get(TESTOPTIONS_SECTION, {})
            if "max_pyver" not in options:
                continue
            test = f"{directory_of(path)}{stem_of(path)}.py"
            out.append(target(f"max-pyver:{path}", path, None,
                              (b, path, options, test),
                              f"max_pyver = {options['max_pyver']}"))
        return out

    def pass_condition(self, t: Target):
        bundle, path, options, test = t.payload
        value = options["max_pyver"]
        maximum = version_tuple(value)
        if maximum is None:
            return Violated(f"{path}: max_pyver = `{value}` is not a major.minor version")
        minimum = version_tuple(options.get("min_pyver", ""))
        if minimum is not None and maximum <= minimum:
            return Violated(f"{path}: max_pyver {value} is not above min_pyver "
                            f"{options['min_pyver']}; the bound is exclusive")
        for companion_txt in versioned_companions(bundle, test):
            digits = VERSIONED_TXT.match(companion_txt.rsplit("/", 1)[-1]).group("version")
            covered = (int(digits[0]), int(digits[1:]))
            if maximum <= covered:
                return Violated(f"{path}: max_pyver {value} excludes Python "
                                f"{covered[0]}.{covered[1]}, which {companion_txt} records "
                                f"expected output for")
        return Satisfied(f"{path}: max_pyver {value} is an exclusive bound above every "
                         f"version the test records output for")


@rule(
    id="PYLINT-DEV-C048",
    category=CATEGORY,
    ownership="touched",  # spec §4.1 -- a content property of lines the agent wrote
    reads=("files",),  # spec §5
)
class ConditionalAnnotationOperators:
    """Pre-condition: each version-conditional annotation the agent wrote in a functional
    test.
    Pass condition: its comparison is one of `<`, `<=`, `>` and `>=`.

    Not heuristic: the operator set is enumerated by the rule and closed, so membership is
    exact (§6.2). The pre-condition fires on the annotation carrying *any* comparison, not
    on it carrying a supported one (§7.1) -- otherwise an `==` could never be reported.

    Corpus: Mark version-conditional expected messages using only the four supported
    comparison operators.
    """

    SUPPORTED = ("<", "<=", ">", ">=")

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in functional_tests(b, mode="touched"):
            change = b.files[path]
            for lineno, text in change.added_lines:
                for annotation in annotations_of(text):
                    if not annotation.op:
                        continue
                    out.append(target(f"conditional-op:{path}:{lineno}:{annotation.op}",
                                      path, (lineno, lineno),
                                      (path, lineno, annotation), text.strip()[:80]))
        return out

    def pass_condition(self, t: Target):
        path, lineno, annotation = t.payload
        if annotation.op in self.SUPPORTED:
            return Satisfied(f"{path}:{lineno} marks its condition with "
                             f"`{annotation.op}{annotation.version}`")
        return Violated(f"{path}:{lineno} uses `{annotation.op}` to mark a version "
                        f"condition; the supported operators are "
                        f"{', '.join(self.SUPPORTED)}")


@rule(
    id="PYLINT-DEV-C049",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the two expectation files are ones the agent adds
    reads=("files",),  # spec §5
    heuristic=True,
)
class BothVersionedAndDefaultExpectationFiles:
    """Pre-condition: each functional test the agent added whose expected output depends on
    the Python version -- read as the test carrying a version-conditional annotation, or a
    versioned `.txt` being added for it.
    Pass condition: both a `<stem>.<version>.txt` and a default `<stem>.txt` are added.

    Heuristic on the **pre-condition** (§6.3). *When expected output differs by Python
    version* is a fact about what pylint emits on two interpreters, which the patch cannot
    state; the two observable signs of the author having decided it does are used instead,
    and a test whose output differs but which carries neither sign finds no target rather
    than being graded.

    The pre-condition selects on both signs deliberately (§7.1): a test with only the
    versioned file, or only the conditional annotation, is exactly the violation the rule
    exists to catch, and selecting on the compliant pair would find nothing but passes.

    Corpus: Provide both a version-suffixed .txt and a default .txt when expected output
    differs by Python version.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        stems: dict[str, str] = {}
        for path in functional_tests(b, mode="created"):
            source = head_text(b, path)
            if source and any(a.op for a in annotations_of(source)):
                stems[path] = "a version-conditional annotation"
        for path in matching(b, FUNCTIONAL_RE, mode="created", suffixes=(".txt",)):
            match = VERSIONED_TXT.match(path.rsplit("/", 1)[-1])
            if match:
                test = f"{directory_of(path)}{match.group('stem')}.py"
                stems.setdefault(test, f"the versioned expectation {path}")
        return [target(f"versioned-expectation:{test}", test, None, (b, test, why), why)
                for test, why in sorted(stems.items())]

    def pass_condition(self, t: Target):
        bundle, test, why = t.payload
        versioned = versioned_companions(bundle, test)
        default = companion(bundle, test, ".txt")
        if versioned and default:
            return Satisfied(f"{test} ships {versioned[0]} and its default {default}")
        if not versioned:
            return Violated(f"{test} has {why} but no `<stem>.<version>.txt` beside it")
        return Violated(f"{test} ships {versioned[0]} but no default "
                        f"{stem_of(test)}.txt for every other Python version")


@rule(
    id="PYLINT-DEV-C050",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the arrangement is settled when the test is added
    reads=("files",),  # spec §5
    heuristic=True,
)
class UnparsableTestsUseVersionBoundsNotConditions:
    """Pre-condition: each functional test the agent added that either carries a
    version-conditional annotation or is bounded by `min_pyver`/`max_pyver`.
    Pass condition: if its code cannot be parsed on every supported version, the bound is
    used rather than the annotation.

    Heuristic on the **pass condition** (§6.2). *Not parsable on every version* would need
    every interpreter pylint supports; what is available is one parse plus a short list of
    syntax that arrived after the floor -- `match`, `except*`, PEP 695 aliases and
    generics. That is positive evidence only: a file using newer syntax the list does not
    name reads as parsable and passes.

    The pre-condition selects both arrangements (§7.1), so a test that correctly reaches
    for `min_pyver` is recorded as a pass rather than never appearing.

    Corpus: Use min_pyver or max_pyver rather than conditional annotations when the test
    code is not parsable on every version.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in functional_tests(b, mode="created"):
            source = head_text(b, path)
            if source is None:
                continue
            options = ini_sections(_rc_for(b, path)).get(TESTOPTIONS_SECTION, {})
            bounded = bool({"min_pyver", "max_pyver"} & set(options))
            conditional = any(a.op for a in annotations_of(source))
            if not (bounded or conditional):
                continue
            out.append(target(f"pyver-bound:{path}", path, None,
                              (path, source, bounded, conditional),
                              "bounded" if bounded else "version-conditional"))
        return out

    def pass_condition(self, t: Target):
        path, source, bounded, conditional = t.payload
        parses = True
        try:
            compile(source, path, "exec", dont_inherit=True)
        except SyntaxError:
            parses = False
        except ValueError:
            parses = True
        new_syntax = _NEW_SYNTAX.search(source)
        if parses and not new_syntax:
            return Satisfied(f"{path} parses everywhere, so conditional annotations are "
                             f"the right mechanism")
        if bounded:
            return Satisfied(f"{path} uses min_pyver/max_pyver for code that is not "
                             f"parsable on every version")
        return Violated(f"{path} is not parsable on every supported version "
                        f"({'new syntax: ' + new_syntax.group(0).strip() if new_syntax else 'it does not parse here'}) "
                        f"but relies on conditional annotations instead of "
                        f"min_pyver/max_pyver")


def _in_regression_dir(path: str) -> bool:
    return functional_relpath(path).startswith(REGRESSION_DIRS)


@rule(
    id="PYLINT-DEV-C051",
    category=CATEGORY,
    ownership="touched",  # spec §4.1 -- the file the test case joins already existed, and
                          # `touched` is the wider scope §4.5 asks for when both read
    reads=("files",),  # spec §5
    heuristic=True,
)
class TestCaseForAnExistingCheckerIsAppended:
    """Pre-condition: each functional test file in a contribution that also edits a checker
    module which already existed.
    Pass condition: the test file already existed too -- the case was appended rather than
    given a new file.

    Heuristic on the **pre-condition** (§6.3). *A new test case for an existing checker* is
    an association the patch does not state: what it shows is a checker module that is not
    new and functional tests that changed, and the two are assumed to belong together. A
    contribution that edits an old checker and adds a genuinely new message would be
    selected here and reported, which over-fires; the narrower reading -- matching the test
    to the checker by name -- would beg C052's question.

    Corpus: Append a new test case for an existing checker to that checker's existing test
    file.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        existing = [p for p in sorted(b.files)
                    if p.startswith("pylint/checkers/") and p.endswith(".py")
                    and not b.files[p].is_new]
        if not existing:
            return []
        return [target(f"append-test-case:{path}", path, None,
                       (path, b.files[path].is_new, existing), path)
                for path in functional_tests(b, mode="touched")]

    def pass_condition(self, t: Target):
        path, is_new, checkers = t.payload
        if is_new:
            return Violated(f"{path} is a new test file for {checkers[0]}, a checker that "
                            f"already existed; the case belongs in that checker's "
                            f"existing test file")
        return Satisfied(f"the new case was appended to the existing {path}")


@rule(
    id="PYLINT-DEV-C052",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- "a NEW checker's" test file, and a file's name is
                          # settled when it is added
    reads=("files",),  # spec §5
    heuristic=True,
)
class FunctionalTestFileNamedForTheMessageSymbol:
    """Pre-condition: each functional test file the agent added in a contribution that also
    declares a new message symbol.
    Pass condition: its stem is one of those symbols with hyphens written as underscores.

    Heuristic on the **pre-condition** (§6.3). *A new checker* is approximated by the
    change declaring a new `msgs` entry, which is the observable trace a new checker
    leaves; a contribution that adds several symbols and one test has the test measured
    against all of them, which is generous in the passing direction.

    Corpus: Name a new checker's functional test file after the message symbol, with
    underscores.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        symbols = sorted({entry.symbol for _, _, entry in added_message_entries(b)
                          if entry.symbol})
        if not symbols:
            return []
        return [target(f"test-file-name:{path}", path, None, (path, symbols),
                       f"{path} for {', '.join(symbols)}")
                for path in functional_tests(b, mode="created")]

    def pass_condition(self, t: Target):
        path, symbols = t.payload
        wanted = {symbol.replace("-", "_") for symbol in symbols}
        if stem_of(path) in wanted:
            return Satisfied(f"{path} is named for the message symbol it tests")
        return Violated(f"{path} is not named after any message symbol the change adds "
                        f"({', '.join(sorted(wanted))})")


@rule(
    id="PYLINT-DEV-C053",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- placement is settled when the file is added
    reads=("files",),  # spec §5
)
class FunctionalTestInItsInitialLetterDirectory:
    """Pre-condition: each functional test file the agent added outside `functional/ext/`.
    Pass condition: the first directory below `functional/` is the file's first letter.

    Not heuristic: a comparison between one character of the name and one segment of the
    path is exact on both layers (§6.2, §6.3).

    Extension tests are excluded from the pre-condition, not graded and failed: they live
    under `functional/ext/<extension>/`, where the first segment is `ext` by design, and
    C054 is the row that governs them. Read literally the two sentences contradict, so the
    antecedent is narrowed and a test pins that an extension test finds no target here
    (spec §7.5). Regression tests are *not* excluded: `r/regression/regression_x.py`
    satisfies this rule and C055 at once.

    Corpus: Place a functional test file in the sub-directory named for its first letter.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"letter-directory:{path}", path, None, path, path)
                for path in functional_tests(b, mode="created")
                if not functional_relpath(path).startswith(EXT_FUNCTIONAL)]

    def pass_condition(self, t: Target):
        path = t.payload
        relative = functional_relpath(path)
        letter = stem_of(path)[:1].lower()
        first = relative.split("/")[0]
        if "/" not in relative:
            return Violated(f"{path} sits directly in functional/, not in the `{letter}` "
                            f"sub-directory named for its first letter")
        if first == letter:
            return Satisfied(f"{path} is in the `{letter}` sub-directory")
        return Violated(f"{path} is in functional/{first}/, but its name begins with "
                        f"`{letter}`")


@rule(
    id="PYLINT-DEV-C055",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- placement is settled when the file is added
    reads=("files",),  # spec §5
)
class RegressionTestInARegressionDirectory:
    """Pre-condition: each functional test the agent added that is a regression test --
    by the `regression_` prefix C056 makes the corpus's own definition, or by already
    sitting in one of the two directories.
    Pass condition: it sits in `functional/r/regression/` or `functional/r/regression_02/`.

    Not heuristic: the set of acceptable directories is enumerated by the rule and closed,
    and the category *regression test* is one the corpus defines in the very next row
    (§6.3, §6.2). Selecting on both signs is what makes the rule two-sided (§7.1): a
    correctly prefixed test in the wrong directory and a correctly placed one both appear.

    A regression test that carries neither sign is invisible here. That is the price of
    having no other evidence of the category, and it is C056's finding rather than this
    rule's.

    Corpus: Put a regression test in one of the two regression directories.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in functional_tests(b, mode="created"):
            if stem_of(path).startswith(REGRESSION_PREFIX) or _in_regression_dir(path):
                out.append(target(f"regression-directory:{path}", path, None, path, path))
        return out

    def pass_condition(self, t: Target):
        path = t.payload
        if _in_regression_dir(path):
            return Satisfied(f"{path} is in a regression directory")
        return Violated(f"{path} is a regression test outside "
                        f"{' and '.join('functional/' + d for d in REGRESSION_DIRS)}")


@rule(
    id="PYLINT-DEV-C056",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- a file's name is settled when it is added
    reads=("files",),  # spec §5
)
class RegressionTestFileNamePrefix:
    """Pre-condition: each functional test the agent added in one of the two regression
    directories.
    Pass condition: its name begins with `regression_`.

    Not heuristic: a literal filename prefix has one satisfying form (§6.2). Selecting on
    the *directory* rather than on the prefix is what lets the rule report a badly named
    file; C055 does the mirror image, selecting on the prefix to report a badly placed one,
    so neither ends up one-sided.

    Corpus: Prefix a regression test file name with regression_.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"regression-prefix:{path}", path, None, path, path)
                for path in functional_tests(b, mode="created") if _in_regression_dir(path)]

    def pass_condition(self, t: Target):
        path = t.payload
        if stem_of(path).startswith(REGRESSION_PREFIX):
            return Satisfied(f"{path} is prefixed `{REGRESSION_PREFIX}`")
        return Violated(f"{path} sits in a regression directory but its name does not "
                        f"start with `{REGRESSION_PREFIX}`")


@rule(
    id="PYLINT-DEV-C057",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- placement is settled when the file is added
    reads=("files",),  # spec §5
    heuristic=True,
)
class NestedSubDirectoryMatchesTheFirstWord:
    """Pre-condition: each functional test the agent added under a letter directory whose
    name contains an underscore.
    Pass condition: if it sits in a nested sub-directory, that directory's name is the word
    before the file's first underscore.

    Heuristic on the **pass condition** (§6.2). The sentence is conditional -- a test
    belongs in a nested directory *if one of that name exists* -- and the tree is not in
    the evidence, so a test left flat in its letter directory is accepted rather than
    reported. What is decided exactly is the other half: a test placed in a nested
    directory whose name is not its first word.

    Corpus: Place a test file in a nested sub-directory whose name matches the word before
    the first underscore of the file name.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in functional_tests(b, mode="created"):
            relative = functional_relpath(path)
            if relative.startswith(EXT_FUNCTIONAL) or "_" not in stem_of(path):
                continue
            if len(relative.split("/")) < 2:
                continue
            out.append(target(f"nested-directory:{path}", path, None, path, path))
        return out

    def pass_condition(self, t: Target):
        path = t.payload
        segments = functional_relpath(path).split("/")
        word = stem_of(path).split("_")[0]
        if len(segments) == 2:
            return Satisfied(f"{path} sits directly in its letter directory, which the "
                             f"rule's condition leaves open")
        nested = segments[1]
        if nested == word:
            return Satisfied(f"{path} is nested under `{nested}`, the word before its "
                             f"first underscore")
        return Violated(f"{path} is nested under `{nested}`, but the word before its "
                        f"first underscore is `{word}`")


#: `************* Module {abspath}` and `{relpath}:3:0: E0015: ...` -- the two lines of a
#: `.out` file that name a module or a file.
_MODULE_LINE = re.compile(r"^\*+\s*Module\s+(?P<name>\S+)")
_MESSAGE_LINE = re.compile(r"^(?P<prefix>[^\s:]+):\d+:\d+:")
#: A `.result.json` records a *difference*, so it is small. A full configuration dump has
#: upwards of a hundred keys; the line between them is drawn here and is the reason C062
#: is heuristic.
_DELTA_KEY_LIMIT = 10


@rule(
    id="PYLINT-DEV-C059",
    category=CATEGORY,
    ownership="touched",  # spec §4.1 -- the expectation file existed and was edited
    reads=("files", "commands"),  # spec §5: CheckTier=trajectory; the file says the rule
                                  # fired, the log says how the update was made
    heuristic=True,
)
class ExpectedOutputRegeneratedWithTheFlag:
    """Pre-condition: the contribution changes a functional test's existing `.txt`
    expectation file.
    Pass condition: a command carrying `--update-functional-output` appears in the log.

    Heuristic on the **pre-condition** (§6.3). *Regenerating* is an act, and the act leaves
    no trace of its own; what the patch shows is an expectation file that changed, which is
    the same state a hand-edit produces. Firing on the flag instead would find only the
    agents that had already complied (§7.1), so the superset is used and a hand-edited
    expectation is reported as a violation -- which is the reading, and is stated here so
    it can be disagreed with.

    Newly added `.txt` files are not selected: there was no expected output to regenerate.

    Corpus: Regenerate a functional test's expected output with --update-functional-output.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        changed = [p for p in matching(b, FUNCTIONAL_RE, mode="touched", suffixes=(".txt",))
                   if not b.files[p].is_new]
        if not changed:
            return []
        return [target(f"update-functional-output:{b.instance_id}", changed[0], None,
                       (b, changed), f"{len(changed)} expectation file(s) changed")]

    def pass_condition(self, t: Target):
        bundle, changed = t.payload
        if runs := ran(bundle, _UPDATE_OUTPUT):
            return Satisfied(f"expected output regenerated: "
                             f"{runs[0].command.strip()[:80]}")
        return Violated(f"{changed[0]} was rewritten without any "
                        f"`--update-functional-output` run")


@rule(
    id="PYLINT-DEV-C060",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- "create a NEW file"; the name and the directory
                          # are settled when it is added
    reads=("files",),  # spec §5
    heuristic=True,
)
class ConfigurationTestInItsFormatDirectory:
    """Pre-condition: each configuration test input file the agent added.
    Pass condition: one of the directories above it names the file's configuration format.

    Heuristic on the **pass condition** (§6.2): which directory belongs to which format is
    a fact about the tree's layout rather than about the patch, so the mapping is written
    down here (`.toml` under `toml/`, `.ini` and `.cfg` under `ini/`, `tox/` or
    `setup_cfg/`) and a format the map does not know reads as a violation.

    *A new, unused name* is carried by the pre-condition rather than graded: a file the
    agent added is by construction a name that was free, and a configuration test that
    already existed and was edited is not the act this sentence is about.

    Corpus: Create a configuration test as a new, unused filename in the directory for that
    configuration format.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"config-test-directory:{path}", path, None, path, path)
                for path in _config_inputs(b, mode="created")]

    def pass_condition(self, t: Target):
        path = t.payload
        suffix = suffix_of(path)
        wanted = CONFIG_FORMATS.get(suffix)
        if wanted is None:
            return Violated(f"{path} is a configuration test in a format the guide does "
                            f"not lay out a directory for")
        segments = set(directory_of(path).strip("/").split("/"))
        if segments & set(wanted):
            return Satisfied(f"{path} sits in the directory for `{suffix}` configuration")
        return Violated(f"{path} is a `{suffix}` configuration test but sits in "
                        f"{directory_of(path)}, not under {' or '.join(wanted)}/")


@rule(
    id="PYLINT-DEV-C061",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the companion is added with the test
    reads=("files",),  # spec §5
)
class ConfigurationTestHasAResultJson:
    """Pre-condition: each configuration test input file the agent added.
    Pass condition: a `<stem>.result.json` is added beside it, or a `<stem>.<code>.out`
    is, which is the form a configuration expected to fail takes.

    Not heuristic: the companion's name is fully determined by the file it accompanies, and
    both are paths in the patch (§6.2). The `.out` alternative is not a softening of the
    rule but the exclusion C063 needs: a configuration that is supposed to crash has no
    resulting configuration to record, and reporting it here would make the two rows
    contradict (spec §7.5).

    Corpus: Add a .result.json file whose stem matches the configuration test file.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"result-json:{path}", path, None, (b, path), path)
                for path in _config_inputs(b, mode="created")]

    def pass_condition(self, t: Target):
        bundle, path = t.payload
        if (result := companion(bundle, path, ".result.json")) is not None:
            return Satisfied(f"{path} is accompanied by {result}")
        out_files = [p for p in sorted(bundle.files)
                     if directory_of(p) == directory_of(path)
                     and (match := OUT_NAME.match(p.rsplit("/", 1)[-1]))
                     and match.group("stem") == stem_of(path)]
        if out_files:
            return Satisfied(f"{path} expects a failure and is accompanied by "
                             f"{out_files[0]}")
        return Violated(f"{path} has no {stem_of(path)}.result.json beside it")


@rule(
    id="PYLINT-DEV-C062",
    category=CATEGORY,
    ownership="touched",  # spec §4.1 -- the rule is about what the file records
    reads=("files",),  # spec §5
    heuristic=True,
)
class ResultJsonRecordsOnlyTheDifference:
    """Pre-condition: each `.result.json` in the patch that parses as JSON.
    Pass condition: it is an object recording a handful of settings -- a difference from
    the standard configuration rather than a copy of it.

    Heuristic on the **pass condition** (§6.2). *Only the difference* is a comparison
    against a configuration the bundle does not carry, so size stands in for it: pylint's
    standard configuration has upwards of a hundred options and a delta has a few, and the
    line is drawn at ten top-level keys. A delta of eleven settings would be reported
    wrongly, and a full dump of nine would pass; the threshold is the proxy and is named
    here rather than left in the code.

    A file that does not parse as JSON is *not* selected: that is a broken test rather than
    a configuration recorded the wrong way, and grading it here would put one defect under
    two rows.

    Corpus: Record only the difference from the standard configuration in the .result.json
    file.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in matching(b, CONFIG_TEST_RE, mode="touched", suffixes=(".result.json",)):
            text = head_text(b, path)
            if text is None:
                continue
            try:
                payload = json.loads(text)
            except ValueError:
                continue
            out.append(target(f"result-delta:{path}", path, None, (path, payload),
                              f"{path}: {len(payload) if isinstance(payload, dict) else '?'}"
                              f" top-level key(s)"))
        return out

    def pass_condition(self, t: Target):
        path, payload = t.payload
        if not isinstance(payload, dict):
            return Violated(f"{path} is a {type(payload).__name__}, not an object "
                            f"recording configuration settings")
        if len(payload) > _DELTA_KEY_LIMIT:
            return Violated(f"{path} records {len(payload)} top-level settings, which "
                            f"reads as a copy of the standard configuration rather than "
                            f"the difference from it")
        return Satisfied(f"{path} records {len(payload)} setting(s) -- a difference from "
                         f"the standard configuration")


@rule(
    id="PYLINT-DEV-C063",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- a file's name is settled when it is added
    reads=("files",),  # spec §5
)
class ExpectedFailureOutFileName:
    """Pre-condition: each `.out` file the agent added under the configuration test tree.
    Pass condition: it is named `<configuration test>.<exit code>.out`, and when
    configuration tests were added beside it, its stem is one of theirs.

    Not heuristic: the filename pattern is given verbatim by the rule, and matching it is
    exact (§6.2). The pre-condition fires on the `.out` file rather than on a configuration
    being expected to fail, because the `.out` file is the only way the patch says a
    failure is expected at all -- and it selects badly named ones as readily as good ones.

    Corpus: Express an expected configuration failure with a .out file named for the test
    and its exit code.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"out-file-name:{path}", path, None, (b, path), path)
                for path in matching(b, CONFIG_TEST_RE, mode="created", suffixes=(".out",))]

    def pass_condition(self, t: Target):
        bundle, path = t.payload
        match = OUT_NAME.match(path.rsplit("/", 1)[-1])
        if match is None:
            return Violated(f"{path} is not named "
                            f"`name_of_configuration_testfile.error_code.out`")
        siblings = {stem_of(p) for p in _config_inputs(bundle, mode="created")
                    if directory_of(p) == directory_of(path)}
        if siblings and match.group("stem") not in siblings:
            return Violated(f"{path} names `{match.group('stem')}`, which is not one of "
                            f"the configuration tests added beside it "
                            f"({', '.join(sorted(siblings))})")
        return Satisfied(f"{path} names its test and the exit code {match.group('code')}")


@rule(
    id="PYLINT-DEV-C065",
    category=CATEGORY,
    ownership="touched",  # spec §4.1 -- the rule is about the file's content
    reads=("files",),  # spec §5
)
class OutFileUsesThePathPlaceholders:
    """Pre-condition: each `.out` file in the patch that names a module or a file.
    Pass condition: the module is written `{abspath}` and the file `{relpath}`.

    Not heuristic: two literal tokens are named by the rule and the check is whether they
    are the ones used (§6.2). Only lines that name a module or carry a `path:line:column:`
    message are examined; a `.out` file's prose lines say nothing about either placeholder.

    Corpus: Use the {abspath} and {relpath} placeholders for module and file name in a .out
    file.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in matching(b, CONFIG_TEST_RE, mode="touched", suffixes=(".out",)):
            text = head_text(b, path)
            if text is None:
                continue
            lines = [line for line in text.split("\n")
                     if _MODULE_LINE.match(line) or _MESSAGE_LINE.match(line)]
            if not lines:
                continue
            out.append(target(f"out-placeholders:{path}", path, None, (path, lines),
                              lines[0][:80]))
        return out

    def pass_condition(self, t: Target):
        path, lines = t.payload
        for line in lines:
            if match := _MODULE_LINE.match(line):
                if match.group("name") != "{abspath}":
                    return Violated(f"{path} names the module `{match.group('name')}` "
                                    f"instead of the `{{abspath}}` placeholder")
            elif match := _MESSAGE_LINE.match(line):
                if match.group("prefix") != "{relpath}":
                    return Violated(f"{path} names the file `{match.group('prefix')}` "
                                    f"instead of the `{{relpath}}` placeholder")
        return Satisfied(f"{path} uses {{abspath}} and {{relpath}} throughout")
