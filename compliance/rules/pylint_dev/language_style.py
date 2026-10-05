"""pylint-dev: Language and framework style -- 12 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

Eleven of the twelve are pylint's contract for a *checker class*: what a checker must
declare, how its messages are numbered, how its visitor methods are named. The shared
reading of that contract -- what counts as a checker class, what its `msgs` dictionary
says -- lives in `_common.py` so that eleven rules cannot disagree about it.

**DEPARTURE from the category prior on ``ownership``.** The prior is `touched`, 41/41, and
every one of those 41 is a property of code as it stands. Five rules here are not: C016,
C066, C069, C070 and C100 all say *a new checker*, which §4.3 sends to `created`. They are
scoped with ``owns_span(..., "created")`` rather than ``owns_file``, because a checker class
added to a module that already existed is still one the agent brought into existence, and
``owns_file`` would see only the file and miss it.

C072 is this pack's one `enclosing` rule (§4.1): what decides its verdict is the set of
message ids on the surrounding checker class, most of which the agent did not write.
"""

from __future__ import annotations

import ast
import re

from compliance.core import ownership as own
from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.extractors import python_ast as pa
from compliance.rules.pylint_dev._common import (CHECKERS_ROOT, EXTENSIONS_ROOT,
                                                 MESSAGE_ID, added_message_entries,
                                                 checker_classes, class_attribute,
                                                 class_methods, message_entries, modules,
                                                 python_files, target)

CATEGORY = "Language and framework style"

_HANDLER = re.compile(r"^(visit|leave)_(?P<node>.*)$")
#: A lowered astroid class name is one lowercase token -- `classdef`, `assignname`.
_LOWERED_NODE = re.compile(r"^[a-z][a-z0-9]*$")
#: The two proxy families AGENTS.md names, and the base they share.
_PROXY_BASE = re.compile(r"(^|\.)(Proxy|Instance|BaseInstance)$")
_HASATTR = re.compile(r"\bhasattr\s*\(")


def _checker_classes(bundle: EvidenceBundle, mode: str) -> list[tuple]:
    """(path, module, class) for each checker class the agent owns under ``mode``."""
    out = []
    for path, module in modules(bundle, tests=False):
        for classdef in checker_classes(module):
            if own.owns_span(bundle, path, pa.span_of(classdef), mode):
                out.append((path, module, classdef))
    return out


def _declared_everywhere(bundle: EvidenceBundle) -> list[tuple[str, str, str, str]]:
    """(path, class name, msgid, symbol) for every message the changed modules declare."""
    out = []
    for path, module in modules(bundle, tests=False):
        for classdef in checker_classes(module):
            for entry in message_entries(classdef):
                out.append((path, classdef.name, entry.msgid, entry.symbol))
    return out


def _base_message_ids(bundle: EvidenceBundle, path: str) -> set[str]:
    """Message ids the file already declared at the base commit."""
    change = bundle.files.get(path)
    if change is None or change.base_text is None:
        return set()
    module = pa.parse_module(change.base_text, path)
    if not module.ok:
        return set()
    return {entry.msgid for classdef in checker_classes(module)
            for entry in message_entries(classdef)}


@rule(
    id="PYLINT-DEV-C016",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- "a NEW checker"; scoped by span, see the module
                          # docstring
    reads=("files",),  # spec §5: the declarations are in the patch
    heuristic=True,
)
class MessageIdNotAlreadyUsed:
    """Pre-condition: each `msgs` entry the agent wrote in a checker class.
    Pass condition: its message id is declared by no other checker in the contribution and
    was not already declared in the file it was added to.

    Heuristic on the **pass condition** (§6.2): *no existing checker* means every checker
    in the tree, and the bundle carries only the files the patch touched. A collision with
    an untouched checker is invisible here, so a pass is weaker than the rule -- which is
    also why the guide offers `get_unused_message_id_category.py` rather than expecting the
    check by eye. What is decidable, and is graded, is a collision inside the change itself
    and a collision with what the edited file already declared.

    Corpus: Give a new checker a message id that no existing checker already uses.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"message-id-unique:{path}:{entry.msgid}", path, entry.span(),
                       (b, path, classdef.name, entry),
                       f"{entry.msgid} ({entry.symbol})")
                for path, classdef, entry in added_message_entries(b)]

    def pass_condition(self, t: Target):
        bundle, path, class_name, entry = t.payload
        clashes = [(p, c) for p, c, msgid, _ in _declared_everywhere(bundle)
                   if msgid == entry.msgid and (p, c) != (path, class_name)]
        if clashes:
            return Violated(f"message id {entry.msgid} is also declared by "
                            f"{clashes[0][1]} in {clashes[0][0]}")
        if entry.msgid in _base_message_ids(bundle, path):
            return Violated(f"message id {entry.msgid} was already declared in {path} "
                            f"before the change")
        return Satisfied(f"message id {entry.msgid} clashes with nothing the change can "
                         f"see")


@rule(
    id="PYLINT-DEV-C066",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- "a new checker class"
    reads=("files",),  # spec §5
)
class CheckerClassDeclaresName:
    """Pre-condition: each checker class the agent added.
    Pass condition: its body assigns a `name` attribute.

    Not heuristic: the pass condition is the presence of an attribute the rule names
    exactly, read off the class body (§6.2), and the pre-condition selects on an exact
    observable fact -- a class whose bases name a checker and whose lines the agent wrote
    (§6.3).

    Corpus: Give a new checker class a name attribute.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"checker-name:{path}:{classdef.name}", path,
                       pa.span_of(classdef), (path, classdef), f"class {classdef.name}")
                for path, _, classdef in _checker_classes(b, "created")]

    def pass_condition(self, t: Target):
        path, classdef = t.payload
        if class_attribute(classdef, "name") is not None:
            return Satisfied(f"{classdef.name} declares a `name` attribute")
        return Violated(f"{path}: checker class {classdef.name} declares no `name` "
                        f"attribute")


@rule(
    id="PYLINT-DEV-C067",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a property every checker must have, no newness
    reads=("files",),  # spec §5
    heuristic=True,
)
class EmittedMessagesAreDeclared:
    """Pre-condition: each `self.add_message("<symbol>", ...)` call, written with a literal
    name, inside a checker class the agent edited whose module declares messages.
    Pass condition: that name is one of the ids or symbols the class's `msgs` dictionary
    declares.

    Heuristic on the **pass condition** (§6.2). A checker may emit a message its *base*
    class declares, and the base can live in a module the patch never touched, so a name
    absent from this class is not proof it is undeclared. The pre-condition is exact -- a
    literal argument at a call site -- and calls that pass a variable are simply not
    selected rather than guessed at.

    Corpus: Declare every message a checker emits in its msgs dictionary.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module, classdef in _checker_classes(b, "touched"):
            if not message_entries(classdef):
                continue
            for call in module.calls_within(pa.span_of(classdef)):
                if call.short != "add_message" or not call.args:
                    continue
                first = call.args[0]
                if not (isinstance(first, ast.Constant) and isinstance(first.value, str)):
                    continue
                out.append(target(f"declared-message:{path}:{call.lineno}", path,
                                  call.span(), (path, classdef, first.value),
                                  f'add_message("{first.value}")'))
        return out

    def pass_condition(self, t: Target):
        path, classdef, name = t.payload
        known = set()
        for entry in message_entries(classdef):
            known.update({entry.msgid, entry.symbol})
        if name in known:
            return Satisfied(f"`{name}` is declared in {classdef.name}.msgs")
        return Violated(f"{path}: {classdef.name} emits `{name}`, which its `msgs` "
                        f"dictionary does not declare")


@rule(
    id="PYLINT-DEV-C068",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a naming property of the handlers, no newness
    reads=("files",),  # spec §5
    heuristic=True,
)
class NodeHandlerNaming:
    """Pre-condition: each `visit_`/`leave_` method the agent wrote on a checker class.
    Pass condition: what follows the prefix is a single lowercase token, the form a lowered
    astroid class name takes.

    Heuristic on the **pass condition** (§6.2). Whether the token names a real astroid node
    class depends on astroid's class list, which is not in the evidence; what is decidable
    is the *form* the lowering produces -- `visit_classdef`, never `visit_class_def` or
    `visit_ClassDef`. A mis-spelled but well-formed handler therefore passes, and what this
    catches is the failure that makes dispatch silently never fire.

    Corpus: Name a checker's node handlers visit_ or leave_ followed by the lowered astroid
    class name.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _, classdef in _checker_classes(b, "touched"):
            for method in class_methods(classdef):
                if not _HANDLER.match(method.name):
                    continue
                if not own.owns_span(b, path, pa.span_of(method), "touched"):
                    continue
                out.append(target(f"handler-name:{path}:{method.name}", path,
                                  pa.span_of(method), (path, method.name),
                                  f"def {method.name}"))
        return out

    def pass_condition(self, t: Target):
        path, name = t.payload
        node = _HANDLER.match(name).group("node")
        if _LOWERED_NODE.match(node):
            return Satisfied(f"`{name}` names its node as a lowered class name")
        return Violated(f"{path}: `{name}` -- `{node}` is not a lowered astroid class "
                        f"name, so the visitor will never dispatch to it")


@rule(
    id="PYLINT-DEV-C069",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- the antecedent is a checker class newly written
    reads=("files",),  # spec §5
)
class ModuleLevelRegisterFunction:
    """Pre-condition: each module in which the agent added a checker class.
    Pass condition: the module defines a top-level `register` function that calls
    `register_checker`.

    Not heuristic: both halves are named exactly by the rule -- a function of that name at
    module level, and the registration it performs -- so this is presence-checking, not
    approximation (§6.2). `qualname == name` is what makes the function module-level: a
    nested one carries its scope in the qualified name.

    Corpus: Add a module-level register function that registers the checker with the
    linter.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out, seen = [], set()
        for path, module, classdef in _checker_classes(b, "created"):
            if path in seen:
                continue
            seen.add(path)
            out.append(target(f"register:{path}", path, None, (path, module),
                              f"{classdef.name} added in {path}"))
        return out

    def pass_condition(self, t: Target):
        path, module = t.payload
        top_level = [f for f in module.functions
                     if f.name == "register" and f.qualname == f.name]
        if not top_level:
            return Violated(f"{path} adds a checker class but defines no module-level "
                            f"`register` function")
        for function in top_level:
            if any(call.short == "register_checker"
                   for call in module.calls_within(function.span())):
                return Satisfied(f"{path} registers its checker in `register` at line "
                                 f"{function.lineno}")
        return Violated(f"{path}: `register` never calls `register_checker`")


@rule(
    id="PYLINT-DEV-C070",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- the id is one the agent wrote
    reads=("files",),  # spec §5
)
class MessageIdFormat:
    """Pre-condition: each `msgs` entry the agent wrote in a checker class.
    Pass condition: its key is one of `C`, `W`, `E`, `F`, `R` followed by exactly four
    digits.

    Not heuristic: a closed five-letter set and a fixed digit count are a format, and a
    format has one satisfying shape (§6.2).

    Corpus: Form a message id as one of the five category letters followed by four digits.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"message-id-format:{path}:{entry.msgid}", path, entry.span(),
                       (path, entry), f"{entry.msgid} ({entry.symbol})")
                for path, _, entry in added_message_entries(b)]

    def pass_condition(self, t: Target):
        path, entry = t.payload
        if MESSAGE_ID.match(entry.msgid):
            return Satisfied(f"{entry.msgid} is a category letter and four digits")
        return Violated(f"{path}: `{entry.msgid}` is not one of C/W/E/F/R followed by "
                        f"four digits")


@rule(
    id="PYLINT-DEV-C072",
    category=CATEGORY,
    ownership="enclosing",  # spec §4.1 -- what decides the verdict is the surrounding
                            # checker class, whose other ids the agent did not write
    reads=("files",),  # spec §5
)
class ConsistentMessageIdPrefix:
    """Pre-condition: each checker class the agent edited that declares more than one
    well-formed, non-shared message id.
    Pass condition: all of those ids begin with the same two digits.

    Not heuristic: the comparison is between digits, and the one exception -- shared
    messages -- is written into the rule's own sentence and read off the entry's `shared`
    option (§6.2). An id that is not `C0000`-shaped is skipped rather than compared,
    because its shape is C070's finding and reporting it twice would depress both rates.

    Corpus: Keep the first two digits of a checker's message ids the same across that
    checker.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _, classdef in _checker_classes(b, "enclosing"):
            ids = [e for e in message_entries(classdef)
                   if MESSAGE_ID.match(e.msgid) and not e.shared]
            if len(ids) < 2:
                continue
            out.append(target(f"id-prefix:{path}:{classdef.name}", path,
                              pa.span_of(classdef), (path, classdef.name, ids),
                              f"{classdef.name}: {', '.join(e.msgid for e in ids)}"))
        return out

    def pass_condition(self, t: Target):
        path, class_name, ids = t.payload
        prefixes = {entry.msgid[1:3] for entry in ids}
        if len(prefixes) == 1:
            return Satisfied(f"{class_name} numbers every message {prefixes.pop()}xx")
        listing = ", ".join(f"{e.msgid} ({e.symbol})" for e in ids)
        return Violated(f"{path}: {class_name} mixes message id prefixes "
                        f"{sorted(prefixes)} -- {listing}")


@rule(
    id="PYLINT-DEV-C073",
    category=CATEGORY,
    ownership="touched",  # spec §4.1 -- the entry existed before the run and was edited
    reads=("files",),  # spec §5: base and head of the file are both in the patch
)
class SymbolChangesWithTheMessageId:
    """Pre-condition: each `msgs` entry whose message id the change removed from the file
    that declared it -- the observable form of *changing* an id.
    Pass condition: the symbol that id carried is no longer declared in the file either.

    Not heuristic: both halves are set comparisons between the base and head versions of
    the same file, which the patch carries (§6.2). The pre-condition selects every id that
    went away, not only the ones whose symbol survived (§7.1): selecting the latter would
    find nothing but violations and could never record a compliant rename.

    Corpus: Change the message symbol whenever you change its message id.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in python_files(b, tests=False):
            change = b.files[path]
            if change.base_text is None or change.head_text is None:
                continue
            base, head = (pa.parse_module(change.base_text, path),
                          pa.parse_module(change.head_text, path))
            if not (base.ok and head.ok):
                continue
            head_ids, head_symbols = set(), set()
            for classdef in checker_classes(head):
                for entry in message_entries(classdef):
                    head_ids.add(entry.msgid)
                    head_symbols.add(entry.symbol)
            for classdef in checker_classes(base):
                for entry in message_entries(classdef):
                    if entry.msgid in head_ids or not entry.symbol:
                        continue
                    out.append(target(f"symbol-with-id:{path}:{entry.msgid}", path, None,
                                      (path, entry, head_symbols),
                                      f"{entry.msgid} ({entry.symbol}) is gone"))
        return out

    def pass_condition(self, t: Target):
        path, entry, head_symbols = t.payload
        if entry.symbol in head_symbols:
            return Violated(f"{path}: message id {entry.msgid} changed but its symbol "
                            f"`{entry.symbol}` is still declared -- the symbol/msgid "
                            f"association has to stay unique")
        return Satisfied(f"{path}: {entry.msgid} and its symbol `{entry.symbol}` changed "
                         f"together")


@rule(
    id="PYLINT-DEV-C075",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a property the declaration must have
    reads=("files",),  # spec §5
)
class SharedMessageDeclaresShared:
    """Pre-condition: each message id the contribution declares on more than one checker
    class.
    Pass condition: every one of those declarations sets `"shared": True`.

    Not heuristic: sharing is observable as the same id declared on two classes, and the
    option is one value the rule names exactly (§6.2). The workbook files this row *never
    fires*, and it should: a change that shares no message between checkers finds no
    target, which is the correct verdict and is not a pass.

    Corpus: Set the shared option to True on a message used by more than one checker.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        by_id: dict = {}
        for path, _, classdef in _checker_classes(b, "touched"):
            for entry in message_entries(classdef):
                by_id.setdefault(entry.msgid, []).append((path, classdef.name, entry))
        out = []
        for msgid, declarations in sorted(by_id.items()):
            classes = {(p, c) for p, c, _ in declarations}
            if len(classes) < 2:
                continue
            out.append(target(f"shared-message:{msgid}", declarations[0][0], None,
                              (msgid, declarations),
                              f"{msgid} declared by {len(classes)} checkers"))
        return out

    def pass_condition(self, t: Target):
        msgid, declarations = t.payload
        unflagged = [f"{c} in {p}" for p, c, entry in declarations if not entry.shared]
        if unflagged:
            return Violated(f"message {msgid} is used by more than one checker but "
                            f"{unflagged[0]} does not set `shared` to True")
        return Satisfied(f"every declaration of {msgid} sets `shared` to True")


@rule(
    id="PYLINT-DEV-C076",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a property of the checker as it stands
    reads=("files",),  # spec §5
)
class MapReduceMethodsComeAsAPair:
    """Pre-condition: each checker class the agent edited that defines either
    `get_map_data` or `reduce_map_data`.
    Pass condition: both are defined, and `get_map_data` returns something other than
    `None`.

    Not heuristic: the two method names and the non-`None` return are all named by the
    rule and each is read directly off the class body (§6.2). Selecting on *either* method
    is what makes the rule two-sided (§7.1); selecting on both would find only the
    compliant pair.

    Corpus: Implement get_map_data and reduce_map_data as a matching pair on a checker that
    reduces data.
    """

    PAIR = ("get_map_data", "reduce_map_data")

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _, classdef in _checker_classes(b, "touched"):
            methods = {m.name: m for m in class_methods(classdef)}
            present = sorted(set(self.PAIR) & set(methods))
            if not present:
                continue
            out.append(target(f"map-reduce:{path}:{classdef.name}", path,
                              pa.span_of(classdef), (path, classdef.name, methods),
                              f"{classdef.name} defines {', '.join(present)}"))
        return out

    def pass_condition(self, t: Target):
        path, class_name, methods = t.payload
        missing = [name for name in self.PAIR if name not in methods]
        if missing:
            return Violated(f"{path}: {class_name} defines "
                            f"{', '.join(n for n in self.PAIR if n in methods)} without "
                            f"{', '.join(missing)} -- the two are a matched pair")
        returns = [node for node in ast.walk(methods["get_map_data"])
                   if isinstance(node, ast.Return)]
        useful = [r for r in returns
                  if r.value is not None
                  and not (isinstance(r.value, ast.Constant) and r.value.value is None)]
        if not useful:
            return Violated(f"{path}: {class_name}.get_map_data returns nothing but None, "
                            f"so reduce_map_data is never given data to reduce")
        return Satisfied(f"{class_name} defines both methods and get_map_data returns data")


@rule(
    id="PYLINT-DEV-C080",
    category=CATEGORY,
    ownership="touched",  # spec §4.1 -- the guard existed before the run and was edited
    reads=("files",),  # spec §5
    heuristic=True,
)
class ProxyBaseInTheIsinstanceTuple:
    """Pre-condition: each `isinstance` call the agent wrote in a file whose change also
    removed a `hasattr` guard.
    Pass condition: its type tuple names one of the astroid proxy bases -- `Proxy`,
    `Instance` or `BaseInstance`.

    Heuristic on the **pre-condition** (§6.3). *Replacing a hasattr guard* is not something
    the patch states; what it shows is a file that lost a `hasattr` line and gained an
    `isinstance` one, and those two need not be the same guard. The pre-condition fires on
    that superset, which over-reports on a file that happened to do both; matching the
    removed and added lines to each other would be a guess about the diff's intent rather
    than a reading of it.

    Corpus: Include the astroid proxy base in the isinstance tuple when replacing a hasattr
    guard.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in modules(b, tests=False):
            change = b.files[path]
            if not any(_HASATTR.search(line) for line in change.removed_lines):
                continue
            for call in module.calls:
                if call.short != "isinstance" or len(call.args) < 2:
                    continue
                if call.lineno not in change.authored_lines:
                    continue
                out.append(target(f"proxy-base:{path}:{call.lineno}", path, call.span(),
                                  (path, call), f"isinstance at line {call.lineno}"))
        return out

    def pass_condition(self, t: Target):
        path, call = t.payload
        second = call.args[1]
        elements = second.elts if isinstance(second, (ast.Tuple, ast.List)) else [second]
        names = [name for name in (pa.dotted_name(e) for e in elements) if name]
        proxy = next((name for name in names if _PROXY_BASE.search(name)), None)
        if proxy is not None:
            return Satisfied(f"the isinstance tuple includes the proxy base `{proxy}`")
        return Violated(f"{path}:{call.lineno}: the isinstance tuple "
                        f"({', '.join(names) or 'unreadable'}) omits the astroid proxy "
                        f"base, so cases the hasattr guard caught are silently dropped")


@rule(
    id="PYLINT-DEV-C100",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- "a NEW checker class"
    reads=("files",),  # spec §5
)
class NewCheckerClassLivesUnderCheckers:
    """Pre-condition: each checker class the agent added outside `pylint/extensions/`.
    Pass condition: the module that holds it is under `pylint/checkers/`.

    Not heuristic: a path prefix is an exact criterion on both layers (§6.2, §6.3).

    Extensions are excluded from the pre-condition rather than graded and passed: a checker
    that ships as an extension lives under `pylint/extensions/` by the same guide that puts
    core checkers under `pylint/checkers/`, and C054 is the row that governs extension
    checkers. Reading this sentence to cover them would make the two rules contradict
    (spec §7.5), so the antecedent is narrowed and a test pins that an extension checker
    finds no target here.

    Corpus: Put a new checker class in the appropriate file under pylint/checkers/.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"checker-location:{path}:{classdef.name}", path,
                       pa.span_of(classdef), (path, classdef.name),
                       f"class {classdef.name}")
                for path, _, classdef in _checker_classes(b, "created")
                if not path.startswith(EXTENSIONS_ROOT)]

    def pass_condition(self, t: Target):
        path, class_name = t.payload
        if path.startswith(CHECKERS_ROOT):
            return Satisfied(f"{class_name} is defined in {path}, under {CHECKERS_ROOT}")
        return Violated(f"checker class {class_name} is defined in {path}, outside "
                        f"{CHECKERS_ROOT}")
