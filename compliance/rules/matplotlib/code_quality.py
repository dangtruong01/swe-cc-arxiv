"""matplotlib: Code and quality -- 7 rules.

Layer C. Every rule is two layers (`docs/checker-authoring.md` §2): ``precondition``
selects on the rule's ANTECEDENT, ``pass_condition`` grades.

Four of the seven (C255--C258) are matplotlib's logging convention, and they are kept
apart deliberately (§7.5) so that one bad call cannot depress four rates:

* C255 asks whether the file reaches for ``print`` at all -- its target is the *file*.
* C256 asks how the module *logger* is created -- it fires only where a
  ``logging.getLogger`` assignment was added, so a module that never makes one is out of
  scope rather than failing.
* C257 asks how one logging call passes its *arguments*; C258 asks what *level* it uses.
  Both fire per call, and neither reads the other's property: a pre-formatted
  ``_log.debug`` violates C257 and satisfies C258, which is the correct pair of answers.

**C152 shares one tool report with two rules in `language_style.py` (§7.5).** ``ruff``
is both the PEP8 linter and the pre-commit hook runner, so a single new finding could
depress three rates at once. The report is partitioned instead, and each rule names the
others: C236 grades line length from the patch and owns ``E501``; C235 owns the remaining
pycodestyle findings (``E``/``W``); C152 owns everything else the hooks report -- the
import, bugbear and formatting checks -- plus the case a linter cannot be run over at all,
a submitted file that does not parse.

Two corpus mismatches, recorded rather than corrected in the workbook (§0/§5):

* **C152** is filed ``differential`` and is one, but the sentence names ``prek``/pre-commit
  rather than one Phase 5 source. It declares ``lint_run`` -- the nearest named missing
  input -- so the withholding is auditable and sunsets itself the day a linter is run over
  base and head.
* **C291** is filed ``differential``. Nothing differential decides it: what a hook did to
  a file, and whether the agent then re-staged it, are both recorded in the command log,
  so it declares ``("commands",)`` and follows the sentence (§5).
"""

from __future__ import annotations

import ast
import re

from compliance.core.models import (EvidenceBundle, Satisfied, Target, Undetermined,
                                    Violated)
from compliance.core.registry import rule
from compliance.extractors import imports as im
from compliance.rules.matplotlib._common import (TYPING_STUB, classes,
                                                 contribution_target,
                                                 introduces_deprecation, is_package_path,
                                                 modules, python_files, target,
                                                 unparseable)

CATEGORY = "Code and quality"

#: A logging call: a logger-shaped receiver and one of the level methods. Written as the
#: name the file uses, because `_log` is bound by assignment rather than imported and the
#: import table therefore cannot resolve it.
_LOG_CALL = re.compile(
    r"(?:^|\.)(?:_log|log|logger|_logger|logging|LOG|LOGGER|_LOG)\."
    r"(debug|info|warning|warn|error|exception|critical)$")
#: The one level the convention allows for an expected code path (C258).
_EXPECTED_LEVEL = "debug"
#: `_log = logging.getLogger(__name__)` -- the spelling C256 states verbatim.
_LOGGER_FACTORY = re.compile(r"\blogging\.getLogger\b|\bgetLogger\b")
_LOGGER_NAME = "_log"

#: A pycodestyle finding: ruff reports PEP8 under the `E` and `W` prefixes. Owned by
#: `language_style.C235` (and `E501` by C236), so C152 subtracts them (§7.5).
PEP8_CODE = re.compile(r"^[EW]\d")

#: A `prek`/pre-commit invocation, and what its output says when a hook rewrote a file.
_PRE_COMMIT_RUN = re.compile(r"\b(prek|pre-commit)\b(?!\s*(install|--version))")
_HOOK_MODIFIED = re.compile(r"files? (were|was) modified by this hook", re.I)
#: Putting a file back into the index and into a commit.
_RESTAGE = re.compile(r"\bgit\s+add\b|\bgit\s+commit\b[^\n]*\B-a\b|\bgit\s+stage\b")
_RECOMMIT = re.compile(r"\bgit\s+commit\b")


def _package_modules(bundle: EvidenceBundle):
    """(path, PyModule) for each library module the agent edited -- no tests, no stubs."""
    return [(path, module) for path, module in modules(bundle, tests=False)
            if is_package_path(path)]


def _logging_calls(module):
    """(CallSite, level) for every logging call in a parsed module."""
    out = []
    for call in module.calls:
        if match := _LOG_CALL.search(call.func):
            out.append((call, match.group(1)))
    return out


def _handler_spans(module) -> list[tuple[int, int]]:
    """Line spans of every ``except`` handler body -- the unexpected code paths."""
    if module.tree is None:
        return []
    return [(h.lineno, getattr(h, "end_lineno", h.lineno))
            for h in ast.walk(module.tree) if isinstance(h, ast.ExceptHandler)]


def _preformatted(node) -> str:
    """The kind of pre-formatting a logging message argument uses, '' when it uses none."""
    if isinstance(node, ast.JoinedStr):
        return "an f-string"
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
        return "eager %-formatting"
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return "string concatenation"
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "format"):
        return "str.format()"
    return ""


@rule(
    id="MATPLOTLIB-C152",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- a whole-contribution rule: the obligation is that
                          # the *change* passes, not that any one file does
    reads=("files", "lint_run"),  # spec §5: the hooks' own verdict over base and head
)
class PreCommitChecksPassBeforeOpeningThePullRequest:
    """Pre-condition: the contribution submits Python, which the ``prek`` hooks run over.
    Pass condition: the hooks report nothing new outside the pycodestyle findings that
    C235 and C236 own.

    Deliberately *not* "the agent ran ``prek``": the sentence asks for the checks to be
    **passing**, so a contribution that never installed the hooks is judged rather than
    excused (§7.1 -- the antecedent is having submitted code, not having run the tool).

    Graded **one-sidedly** where no report exists (§9). A submitted module that will not
    parse provably fails ruff and every other hook, and that is decidable from the patch;
    anything else needs the run, so the rule withholds rather than reading source text as
    a clean bill. Not heuristic: the report is the tool's own verdict (§6.2), and the
    withholding branch does not grade at all.

    The ``E``/``W`` findings are excluded here and graded by ``language_style.C235`` and
    ``C236``, so one badly formatted line is one violation rather than three (§7.5).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        submitted = python_files(b)
        if not submitted:
            return []
        return contribution_target(b, "prek",
                                   f"{len(submitted)} Python file(s) submitted")

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        if broken := unparseable(bundle):
            return Violated(f"the pre-commit checks cannot pass: {len(broken)} submitted "
                            f"file(s) are not valid Python -- {broken[0]}")
        report = bundle.lint.get("ruff")
        if report is None or not report.usable:
            note = report.note if report is not None else "no lint report for this run"
            return Undetermined("tool_missing",
                                f"the prek pre-commit checks were not evaluated: {note}")
        ours = [f for f in report.new_findings if not PEP8_CODE.match(f.code)]
        if not ours:
            return Satisfied(f"the pre-commit checks report nothing new outside "
                             f"pycodestyle ({report.n_findings_base} pre-existing "
                             f"finding(s) subtracted)")
        first = ours[0]
        return Violated(f"the pre-commit checks report {len(ours)} new finding(s), "
                        f"e.g. {first.path}: {first.code} {first.message}")


@rule(
    id="MATPLOTLIB-C242",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- "add or change" covers editing an existing public
                          # signature, so the wider selection is the right one
    reads=("files",),  # spec §5: both the API change and the stub are in the patch
    heuristic=True,
)
class MypyTypeHintsFollowAPublicApiChange:
    """Pre-condition: each library module where the agent added or changed a public
    function or class definition.
    Pass condition: the contribution also edits that module's ``.pyi`` type stub, or the
    shared ``typing`` module.

    Heuristic on **both** layers (§6.2, §6.3). The pre-condition approximates *add or
    change public API* by a public ``def``/``class`` header on a line the agent's edit
    reaches, so a change made purely inside a body -- a new keyword argument's default,
    say -- is not seen, and a private helper never is. The pass condition accepts any edit
    to the sibling stub rather than checking that the stub now matches the signature,
    which would need the type checker's own verdict.

    A file where the public-API change *is* a deprecation is excluded and left to
    ``specialized.C209``, which asks the same question of the same stub for that case;
    without the exclusion one deprecation would depress two rates (§7.5).

    Instances older than the stub files exist: matplotlib grew ``lib/matplotlib/*.pyi`` in
    3.8, and a checkout without them can only fail. That is a property of the benchmark
    rather than of the rule, and it is reported rather than papered over.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        deprecating = set(introduces_deprecation(b))  # §7.5: those files are C209's
        for path, module in _package_modules(b):
            if not path.endswith(".py") or path in deprecating:
                continue
            touched_lines = b.files[path].modified_lines
            names = [f.name for f in module.functions
                     if f.lineno in touched_lines and not f.name.startswith("_")]
            names += [n.name for n in classes(module)
                      if n.lineno in touched_lines and not n.name.startswith("_")]
            if names:
                out.append(target(f"mypy-stub:{path}", path, None, (path, names, b),
                                  f"{path} changes public API: {', '.join(names[:3])}"))
        return out

    def pass_condition(self, t: Target):
        path, names, bundle = t.payload
        stub = path[:-3] + ".pyi"
        if stub in bundle.files:
            return Satisfied(f"{path} changes {names[0]} and the change updates {stub}")
        if TYPING_STUB in bundle.files:
            return Satisfied(f"{path} changes {names[0]} and the change updates "
                             f"{TYPING_STUB}")
        return Violated(f"{path} adds or changes public API ({', '.join(names[:3])}) "
                        f"without touching {stub} or {TYPING_STUB}")


@rule(
    id="MATPLOTLIB-C255",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a property the code must have, no newness
                          # qualifier in the sentence
    reads=("files",),  # spec §5: the call is in the patch
    heuristic=True,
)
class LoggingRatherThanPrintForDebugOutput:
    """Pre-condition: each library module the agent edited, any of which could emit debug
    output.
    Pass condition: it adds no ``print`` call.

    Heuristic on **both** layers (§6.3, §6.2). *Emitting debug output* is not observable,
    so the pre-condition fires on the superset -- every library module the agent touched --
    and the pass condition treats any added ``print`` as debug output. A ``print`` that is
    genuinely the module's product would read as a violation here; the direction of that
    error is declared rather than removed. Gallery examples and tests are excluded, since
    printing is what much of that code is for.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"no-print:{path}", path, None, (path, module, b),
                       f"{path} edited")
                for path, module in _package_modules(b)]

    def pass_condition(self, t: Target):
        path, module, bundle = t.payload
        authored = bundle.files[path].authored_lines
        printed = [c for c in module.calls
                   if c.func == "print" and c.lineno in authored]
        if printed:
            return Violated(f"{path}:{printed[0].lineno} writes debug output with "
                            f"print() instead of the module logger")
        return Satisfied(f"{path} adds no print() call")


@rule(
    id="MATPLOTLIB-C256",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- "create the module logger" is a newness
                          # qualifier; the target is a logger the agent introduced
    reads=("files",),  # spec §5: the assignment and the imports are both in the patch
    heuristic=True,
)
class ModuleLoggerIsCreatedRightAfterTheImports:
    """Pre-condition: each library module where the agent added a module-level
    ``logging.getLogger`` assignment.
    Pass condition: it is bound to ``_log`` and is the first statement after the module's
    leading import block.

    §7.1: the antecedent is *creating a module logger*, not *creating one correctly* -- a
    module that makes no logger is out of scope, and a badly named or badly placed one is
    a recorded violation rather than an absent target.

    Heuristic on the **pass condition** (§6.6, the doubt named). The name and the call are
    exact, but "right after the imports" is graded as *the first statement following the
    leading import block*, with blank lines and comments skipped; a module that separates
    the two with a constant is failed on a reading the sentence does not spell out.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in _package_modules(b):
            if module.tree is None:
                continue
            authored = b.files[path].authored_lines
            for node in module.tree.body:
                if not isinstance(node, ast.Assign) or node.lineno not in authored:
                    continue
                text = _segment(module, node)
                if _LOGGER_FACTORY.search(text):
                    out.append(target(f"module-logger:{path}:{node.lineno}", path,
                                      (node.lineno, node.end_lineno or node.lineno),
                                      (path, module, node), text.strip()[:120]))
        return out

    def pass_condition(self, t: Target):
        path, module, node = t.payload
        names = [tgt.id for tgt in node.targets if isinstance(tgt, ast.Name)]
        if _LOGGER_NAME not in names:
            return Violated(f"{path}:{node.lineno} binds the module logger to "
                            f"{', '.join(names) or 'a non-name target'}, not {_LOGGER_NAME}")
        call = node.value
        if not (isinstance(call, ast.Call) and call.args
                and isinstance(call.args[0], ast.Name) and call.args[0].id == "__name__"):
            return Violated(f"{path}:{node.lineno} does not create the logger as "
                            f"logging.getLogger(__name__)")
        block = im.leading_block(im.import_lines(module=module, path=path))
        if not block:
            return Violated(f"{path}:{node.lineno} creates the module logger with no "
                            f"leading import block above it")
        last_import = max(line.end_lineno for line in block)
        between = _statements_between(module, last_import, node.lineno)
        if between:
            return Violated(f"{path}:{node.lineno} creates the module logger after "
                            f"{len(between)} other statement(s), not right after the "
                            f"imports (line {last_import})")
        return Satisfied(f"{path}:{node.lineno} creates _log = "
                         f"logging.getLogger(__name__) right after the imports")


def _segment(module, node) -> str:
    lines = module.source.split("\n")
    end = getattr(node, "end_lineno", node.lineno) or node.lineno
    return "\n".join(lines[node.lineno - 1:end])


def _statements_between(module, after: int, before: int) -> list:
    """Module-body statements strictly between two lines -- imports do not count."""
    if module.tree is None:
        return []
    return [n for n in module.tree.body
            if after < n.lineno < before
            and not isinstance(n, (ast.Import, ast.ImportFrom))]


@rule(
    id="MATPLOTLIB-C257",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the target is a logging call the agent wrote
    reads=("files",),  # spec §5: the call and its arguments are in the patch
)
class LoggingArgumentsArePercentStyleParameters:
    """Pre-condition: each logging call the agent added to a library module.
    Pass condition: its message argument is a plain string, with any values passed as
    further arguments rather than formatted into it.

    Not heuristic (§6.2): "pre-formatted" is checked as a closed list of syntactic forms
    -- an f-string, ``%`` applied at the call site, ``str.format()``, and string
    concatenation -- each of which is a node type rather than a text pattern, and the
    rule's own standard names the alternative it wants.

    §7.1: every logging call is selected, not only the pre-formatted ones, so a compliant
    call is recorded as a pass instead of vanishing from the denominator.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in _package_modules(b):
            authored = b.files[path].authored_lines
            for call, level in _logging_calls(module):
                if call.lineno not in authored:
                    continue
                out.append(target(f"log-args:{path}:{call.lineno}", path, call.span(),
                                  (path, call), f"{call.func}(...) at {path}:{call.lineno}"))
        return out

    def pass_condition(self, t: Target):
        path, call = t.payload
        if not call.args:
            return Satisfied(f"{path}:{call.lineno} logs a message with no interpolation")
        if kind := _preformatted(call.args[0]):
            return Violated(f"{path}:{call.lineno} passes a pre-formatted message to "
                            f"{call.func}() using {kind}, not %-style parameters")
        return Satisfied(f"{path}:{call.lineno} passes {call.func}() a plain message "
                         f"string")


@rule(
    id="MATPLOTLIB-C258",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the target is a logging call the agent wrote
    reads=("files",),  # spec §5: the call and the branch it sits in are in the patch
    heuristic=True,
)
class ExpectedCodePathsAreLoggedAtDebugLevel:
    """Pre-condition: each logging call the agent added to a library module outside an
    ``except`` handler -- the calls that report an expected code path.
    Pass condition: the call uses the ``debug`` level.

    Heuristic on the **pre-condition** (§6.3): *an expected code path* is a category the
    project does not enumerate, and it is approximated here by *not inside an exception
    handler*. A recoverable-but-unexpected condition detected by an ordinary ``if`` is
    therefore selected and, if logged at ``warning``, reads as a violation; a call inside
    a handler is excluded so the common legitimate ``warning`` is not failed.

    Deliberately separate from C257 (§7.5): that rule grades how the arguments are passed
    and this one grades the level, so one badly written call cannot depress two rates.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in _package_modules(b):
            authored = b.files[path].authored_lines
            handlers = _handler_spans(module)
            for call, level in _logging_calls(module):
                if call.lineno not in authored:
                    continue
                if any(lo <= call.lineno <= hi for lo, hi in handlers):
                    continue
                out.append(target(f"log-level:{path}:{call.lineno}", path, call.span(),
                                  (path, call, level),
                                  f"{call.func}(...) at {path}:{call.lineno}"))
        return out

    def pass_condition(self, t: Target):
        path, call, level = t.payload
        if level == _EXPECTED_LEVEL:
            return Satisfied(f"{path}:{call.lineno} logs an expected code path at debug "
                             f"level")
        return Violated(f"{path}:{call.lineno} logs an expected code path at {level} "
                        f"level, which the convention reserves for unexpected ones")


@rule(
    id="MATPLOTLIB-C291",
    category=CATEGORY,
    ownership="touched",  # spec §4 -- the target is a command the agent ran; no file
                          # ownership applies, and `touched` is the value that means so
    reads=("commands",),  # spec §5: the sentence, not CheckTier=differential -- both what
                          # the hook did and what the agent did next are in the log
    heuristic=True,
)
class FilesAPreCommitHookModifiedAreRestagedAndRecommitted:
    """Pre-condition: each ``prek``/pre-commit invocation whose output reports that a hook
    modified a file.
    Pass condition: a ``git add`` and a ``git commit`` follow it in the command log.

    §7.2 is the shape: the antecedent is the *hook having rewritten something*, never the
    re-staging itself, so a run that re-staged is recorded as a pass and one that walked
    away is a violation. A run whose hooks changed nothing finds no target, which is
    correct -- there is nothing to re-commit.

    Heuristic on the **pre-condition** (§6.3), which reads the command's own output text
    for "files were modified by this hook" rather than re-running the tool, and on the
    **pass condition**, which accepts any later ``git add`` plus ``git commit`` without
    checking that the re-staged paths are the ones the hook rewrote.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for command in b.commands:
            if not _PRE_COMMIT_RUN.search(command.command):
                continue
            if not _HOOK_MODIFIED.search(command.output or ""):
                continue
            out.append(target(f"restage:{command.index}", None, None, (command, b),
                              command.command.strip()[:120], source="trajectory"))
        return out

    def pass_condition(self, t: Target):
        command, bundle = t.payload
        after = [c for c in bundle.commands if c.index > command.index]
        staged = any(_RESTAGE.search(c.command) for c in after)
        committed = any(_RECOMMIT.search(c.command) for c in after)
        if staged and committed:
            return Satisfied(f"the files a hook rewrote at command {command.index} were "
                             f"re-staged and re-committed")
        missing = "re-staged" if not staged else "re-committed"
        return Violated(f"a pre-commit hook modified files at command {command.index} "
                        f"and they were never {missing}")
