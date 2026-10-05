"""scikit-learn: Language and framework style -- 72 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects
on the rule's ANTECEDENT, ``pass_condition`` grades.

The largest module in the pack, and it is the estimator contract: what an ``__init__``
may do, what ``fit`` must return, which mixin each kind of estimator inherits, how a
deprecation is staged, how randomness is threaded, how a ``Display`` is shaped, and what
a callback must implement. Seven groups, in that order, each behind a banner comment.

**Why nearly everything here is `heuristic=True`.** The corpus says *estimator*,
*transformer*, *classifier*, *callback*, *Display*; scikit-learn marks none of them in the
source. Each is recognised from what a class inherits and which methods it defines --
``_common.is_estimator`` and the ``is_*`` predicates below -- which is a proxy for a
category the project defines socially (§6.3). Where a rule's own criterion is exact and
its antecedent names an observable construct (a method by name, an import statement, a
decorator's position), the flag is False and the docstring says why.

**Departures from `CheckTier`**, recorded here rather than corrected in the workbook
(spec §5, §8). C144, C162, C165, C167 and C168 are filed ``differential``, and no
before/after run collected by this instrument could answer them either: they are
behavioural contracts about array shapes and label order, and nothing here executes an
estimator. Each is graded from the structure of the code the agent wrote -- the helper it
calls, the attribute it consults -- and each says in its own docstring what that
structure does and does not establish.

**Pairs that partition an overlapping antecedent** (§7.5), so one defect is not counted
twice: C151 grades learned attributes the docstring exposes and C152 the ones it does
not; C169 asks whether a clustering class inherits its mixin and C171 whether it sets
``labels_``; C223 fires only on estimators outside ``sklearn/`` and C224 only on those
inside it.
"""

from __future__ import annotations

import ast
import re

from compliance.core import ownership as own
from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.extractors import docstrings as ds
from compliance.rules.scikit_learn._common import (API_REFERENCE_FILE, PACKAGE,
                                                   added_lines, base_module, calls_in,
                                                   classes, decorator_names,
                                                   deprecated_names, file_text,
                                                   has_deprecated_directive,
                                                   is_estimator, keyword_defaults,
                                                   modules, owned_classes,
                                                   parameter_entries, parameters,
                                                   raises_future_warning, returns_self,
                                                   self_assignments, target)

CATEGORY = "Language and framework style"

# --- vocabulary ----------------------------------------------------------------------

#: Argument names that carry training data. `__init__` may take none of them (C136).
TRAINING_DATA_ARGS = ("X", "y", "X_train", "y_train", "data", "targets", "Xt")

#: The helpers that validate array input and set the `*_in_` attributes.
VALIDATION_HELPERS = ("check_array", "check_X_y", "validate_data", "_validate_data",
                      "check_consistent_length")

#: Building an independent generator, which the randomness rules ask for.
RNG_BUILDERS = ("check_random_state", "RandomState", "default_rng")

#: Module-level RNG routines the utilities page forbids (C191).
_GLOBAL_RNG = re.compile(
    r"^(np|numpy)\.random\.(?!RandomState|Generator|default_rng|SeedSequence)\w+$"
    r"|^random\.\w+$")

#: The four hooks the FitCallback protocol publishes (C225).
FIT_CALLBACK_PROTOCOL = ("setup", "on_fit_task_begin", "on_fit_task_end", "teardown")
HOOKS = ("on_fit_task_begin", "on_fit_task_end")

#: A version number as the deprecation messages write it (C123, C124).
_VERSION = re.compile(r"\b(\d+)\.(\d+)(?:\.(\d+))?(?P<dev>[-.]?dev\d*)?\b")

_CAMEL_CASE = re.compile(r"[a-z0-9][A-Z]")
_MULTI_STATEMENT = re.compile(r";\s*\S")
_INLINE_BODY = re.compile(r"^\s*(if|for|while|else|elif)\b[^:]*:\s*\S")

_SENTINEL_DEFAULTS = ("warn", "deprecated")
_MUTATORS = ("append", "extend", "update", "sort", "insert", "pop", "add", "clear")
_COPIERS = ("copy", "deepcopy", "list", "dict", "set", "array", "asarray")


# --- selection helpers ---------------------------------------------------------------


def _source(node) -> str:
    try:
        return ast.unparse(node)
    except Exception:  # noqa: BLE001 -- an unparseable node is missing evidence
        return ""


def estimators(bundle: EvidenceBundle):
    """(path, module, class) for each estimator-shaped class the agent wrote or edited."""
    return [(p, m, c) for p, m, c in owned_classes(bundle, tests=False)
            if is_estimator(c) and p.startswith(PACKAGE)]


def is_transformer(info) -> bool:
    return info.inherits("TransformerMixin") or "transform" in info.methods


def is_classifier(info) -> bool:
    return (info.inherits("ClassifierMixin") or info.name.endswith("Classifier")
            or "predict_proba" in info.methods)


def is_regressor(info) -> bool:
    return (info.inherits("RegressorMixin")
            or info.name.endswith(("Regressor", "Regression")))


def is_clusterer(info) -> bool:
    sets_labels = any("labels_" in self_assignments(node)
                      for name, node in info.methods.items() if name != "__init__")
    return info.inherits("ClusterMixin") or sets_labels


def is_display(info) -> bool:
    return info.name.endswith("Display") or "plot" in info.methods


def is_callback(info) -> bool:
    return (info.name.endswith("Callback")
            or info.inherits("FitCallback", "AutoPropagatedCallback")
            or any(hook in info.methods for hook in HOOKS))


def has_callback_support(info) -> bool:
    if info.inherits("CallbackSupportMixin"):
        return True
    fit = info.method("fit")
    if fit is None:
        return False
    called = {c.split(".")[-1] for c in calls_in(fit)}
    return ("_init_callback_context" in called
            or any("with_callbacks" in d for d in decorator_names(fit)))


def learned_attributes(info) -> dict[str, str]:
    """Attributes a class assigns outside `__init__` -> the method that assigns them."""
    out: dict[str, str] = {}
    for name, node in info.methods.items():
        if name == "__init__":
            continue
        for attribute in self_assignments(node):
            out.setdefault(attribute, name)
    return out


def documented_attributes(info) -> set[str]:
    if not info.docstring:
        return set()
    parsed = ds.parse([(n, line) for n, line
                       in enumerate(info.docstring.split("\n"), info.lineno)])
    section = parsed.section("Attributes")
    if section is None:
        return set()
    return {name.strip() for entry in parameter_entries(section)
            for name in entry.names.split(",")}


def class_target(path: str, info, prefix: str, payload=None, snippet: str = "") -> Target:
    return target(f"{prefix}:{path}:{info.name}", path, info.span(),
                  payload if payload is not None else (path, info),
                  snippet or f"class {info.name}")


def method_target(path: str, info, name: str, node, prefix: str, payload=None) -> Target:
    return target(f"{prefix}:{path}:{info.name}.{name}", path,
                  (node.lineno, getattr(node, "end_lineno", node.lineno)),
                  payload if payload is not None else (path, info, name, node),
                  f"{info.name}.{name}")


def deprecation_messages(bundle: EvidenceBundle):
    """(path, lineno, message) for each deprecation message the agent wrote."""
    out = []
    for path, module in modules(bundle, tests=False):
        for function in module.functions:
            decorator = function.decorator("deprecated")
            if decorator is not None and isinstance(decorator.node, ast.Call):
                for argument in decorator.node.args:
                    if isinstance(argument, ast.Constant) and isinstance(argument.value,
                                                                        str):
                        out.append((path, decorator.lineno, argument.value))
        for call in module.calls:
            if call.short != "warn":
                continue
            everything = list(call.args) + [k.value for k in call.keywords]
            if not any("FutureWarning" in _source(a) or "DeprecationWarning" in _source(a)
                       for a in everything):
                continue
            for argument in call.args:
                if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
                    out.append((path, call.lineno, argument.value))
                    break
                text = _source(argument)
                if "'" in text or '"' in text:
                    out.append((path, call.lineno, text))
                    break
    return [(p, n, m) for p, n, m in out
            if own.owns_span(bundle, p, (n, n), "touched")]


def renamed_public_names(bundle: EvidenceBundle):
    """(path, name, still_defined, decorated) for public names the run renamed or retired.

    The observable trace of "a publicly accessible name was renamed": a public definition
    that existed at the base commit and, at head, is either gone or newly carrying the
    `@deprecated` decorator. A proxy -- a name deleted outright looks the same as one
    renamed -- and both C116 and C117 declare ``heuristic=True`` because of it.
    """
    out = []
    for path, module in modules(bundle, tests=False):
        base = base_module(bundle, path)
        if base is None:
            continue
        head_functions = {f.qualname: f for f in module.functions}
        head_classes = {c.name: c for c in classes(module)}
        for function in base.functions:
            if function.name.startswith("_") or "." in function.qualname:
                continue
            current = head_functions.get(function.qualname)
            if current is None:
                out.append((path, function.name, False, False))
            elif (current.has_decorator("deprecated")
                  and not function.has_decorator("deprecated")):
                out.append((path, function.name, True, True))
        for info in classes(base):
            if info.name.startswith("_"):
                continue
            current = head_classes.get(info.name)
            was = any(d.split(".")[-1] == "deprecated" for d in info.decorators)
            if current is None:
                out.append((path, info.name, False, False))
            elif not was and any(d.split(".")[-1] == "deprecated"
                                 for d in current.decorators):
                out.append((path, info.name, True, True))
    return out


# --- A. deprecation mechanics --------------------------------------------------------


@rule(
    id="SCIKIT-LEARN-C116",
    category=CATEGORY,
    ownership="touched",  # spec §4.2 -- the antecedent is the public name the agent
                          # renamed, which existed before the run
    reads=("files",),  # spec §5: the comparison is between base and head text
    heuristic=True,
)
class RenamedPublicNamesKeepWorkingAndWarn:
    """Pre-condition: each public name the contribution renames or retires.
    Pass condition: the old name is still defined and warns when it is used.

    Heuristic on the **pre-condition** (§6.3): a rename leaves the same trace as a
    deletion -- a public definition that was there at the base commit and is gone or newly
    deprecated at head -- so the two cannot be told apart and both are selected. The
    two-release window itself is not graded: a run sees one commit, not two releases, and
    this docstring says so rather than letting the flag imply it.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"rename:{path}:{name}", path, None,
                       (path, name, still, decorated), f"{path}::{name}")
                for path, name, still, decorated in renamed_public_names(b)]

    def pass_condition(self, t: Target):
        path, name, still_defined, decorated = t.payload
        if still_defined and decorated:
            return Satisfied(f"{path}::{name} survives the rename and warns through "
                             f"@deprecated")
        return Violated(f"{path}::{name} was a public name and is gone, so code calling "
                        f"it breaks immediately instead of being warned for two releases")


@rule(
    id="SCIKIT-LEARN-C117",
    category=CATEGORY,
    ownership="touched",  # spec §4.2
    reads=("files",),  # spec §5
    heuristic=True,
)
class RenamedFunctionsDelegateThroughDeprecated:
    """Pre-condition: each public name the contribution renames or retires.
    Pass condition: the old name carries `utils.deprecated` and its body calls the new one.

    Shares C116's antecedent and grades a different thing (§7.5): C116 asks whether the
    old name still works and warns, this asks whether the recipe's *mechanism* was used --
    the decorator plus delegation. Heuristic on **both layers** (§6.3, §6.2): the rename
    proxy again, and "delegates to the new name" is read as the old function calling some
    other function, since which name is the new one is recorded nowhere.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"delegate:{path}:{name}", path, None,
                       (path, name, still, decorated, b), f"{path}::{name}")
                for path, name, still, decorated in renamed_public_names(b)]

    def pass_condition(self, t: Target):
        path, name, still_defined, decorated, bundle = t.payload
        if not still_defined:
            return Violated(f"{path}::{name} was removed rather than decorated with "
                            f"`utils.deprecated` and left delegating to its new name")
        for candidate, module in modules(bundle, tests=False):
            if candidate != path:
                continue
            for function in module.functions:
                if function.name != name or not function.has_decorator("deprecated"):
                    continue
                called = [c for c in calls_in(function.node) if c and c != name]
                if called:
                    return Satisfied(f"{path}::{name} is @deprecated and delegates to "
                                     f"`{called[0]}`")
                return Violated(f"{path}::{name} is @deprecated but calls nothing, so it "
                                f"delegates to no new name")
        return Violated(f"{path}::{name} carries no `utils.deprecated` decorator")


@rule(
    id="SCIKIT-LEARN-C118",
    category=CATEGORY,
    ownership="touched",  # spec §4.2 -- the antecedent is the deprecation; the reference
                          # file it demands already existed
    reads=("files",),  # spec §5: both the deprecation and `doc/api_reference.py` are in
                       # the patch
    heuristic=True,
)
class DeprecatedApiReferenceIsUpdated:
    """Pre-condition: a contribution that deprecates a public name with `@deprecated`.
    Pass condition: `doc/api_reference.py` gains a `DEPRECATED_API_REFERENCE` entry.

    Heuristic on **both layers** (§6.3, §6.2): the deprecation is recognised by the
    decorator, and the update is recognised by the constant's name appearing among the
    written lines -- moving the *right* name into it is not checked, because the mapping
    from a decorated function to its reference-file entry is not in the patch.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        deprecated = deprecated_names(b)
        if not deprecated:
            return []
        return [target(f"api-reference:{b.instance_id}", API_REFERENCE_FILE, None,
                       (b, deprecated),
                       f"deprecates {', '.join(sorted(deprecated))[:70]}")]

    def pass_condition(self, t: Target):
        bundle, deprecated = t.payload
        written = "\n".join(text for _, text in added_lines(bundle, API_REFERENCE_FILE))
        if "DEPRECATED_API_REFERENCE" in written:
            return Satisfied(f"{API_REFERENCE_FILE} moves the deprecated name into "
                             f"DEPRECATED_API_REFERENCE")
        if API_REFERENCE_FILE in bundle.files:
            return Violated(f"{API_REFERENCE_FILE} was changed but nothing was moved "
                            f"into DEPRECATED_API_REFERENCE")
        return Violated(f"{', '.join(sorted(deprecated))[:60]} is deprecated but "
                        f"{API_REFERENCE_FILE} was not updated")


@rule(
    id="SCIKIT-LEARN-C119",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- states how an attribute or method is deprecated
    reads=("files",),  # spec §5
    heuristic=True,
)
class DeprecatedMembersUseTheDecorator:
    """Pre-condition: each method or property the agent wrote or edited whose docstring
    announces a deprecation.
    Pass condition: it carries the `utils.deprecated` decorator.

    Fires on the announcement, not on the decorator (§7.1) -- selecting decorated members
    would find only compliant ones. Heuristic on the **pre-condition** (§6.3): "is to be
    deprecated" is an intention, approximated by the `.. deprecated::` note the project's
    own C126 requires alongside it.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in owned_classes(b, tests=False):
            for name, node in info.methods.items():
                if not has_deprecated_directive(ast.get_docstring(node) or ""):
                    continue
                out.append(method_target(path, info, name, node, "deprecated-member"))
        return out

    def pass_condition(self, t: Target):
        path, info, name, node = t.payload
        if any(d.split(".")[-1] == "deprecated" for d in decorator_names(node)):
            return Satisfied(f"{path}::{info.name}.{name} is decorated `deprecated`")
        return Violated(f"{path}::{info.name}.{name} documents a deprecation without the "
                        f"`utils.deprecated` decorator")


@rule(
    id="SCIKIT-LEARN-C120",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
)
class DeprecatedComesAboveProperty:
    """Pre-condition: each member the agent wrote or edited carrying both `@deprecated`
    and `@property`.
    Pass condition: `@deprecated` is written above `@property`.

    Not heuristic: two decorators, one order, and the consequence of getting it wrong is
    stated in the same sentence of the guide. The decorator list is in source order, so
    its first element is the one written on top.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in owned_classes(b, tests=False):
            for name, node in info.methods.items():
                decorators = [d.split(".")[-1] for d in decorator_names(node)]
                if "deprecated" in decorators and "property" in decorators:
                    out.append(method_target(path, info, name, node, "decorator-order",
                                             (path, info, name, decorators)))
        return out

    def pass_condition(self, t: Target):
        path, info, name, decorators = t.payload
        if decorators.index("deprecated") < decorators.index("property"):
            return Satisfied(f"{path}::{info.name}.{name} writes @deprecated above "
                             f"@property")
        return Violated(f"{path}::{info.name}.{name} writes @property above @deprecated, "
                        f"so its docstring will not render properly")


@rule(
    id="SCIKIT-LEARN-C121",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class DeprecatedParametersRaiseAFutureWarning:
    """Pre-condition: each function the agent wrote or edited that documents one of its
    parameters as deprecated.
    Pass condition: a `FutureWarning` is raised in the function, or in the `fit` of the
    class it belongs to.

    Heuristic on the **pre-condition** (§6.3): a deprecated parameter is recognised from
    its own docstring entry saying so, which is the only trace a parameter deprecation
    leaves in the source. The class's `fit` is accepted as the place the warning is raised
    because C122 is the rule about *where*, and asking that twice would report one defect
    in two rows (§7.5).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in modules(b, tests=False):
            for doc in module.docstrings:
                if doc.kind != "function":
                    continue
                if not own.owns_span(b, path, doc.span(), "touched"):
                    continue
                section = ds.parse(doc.lines()).section("Parameters")
                if section is None:
                    continue
                deprecated = [e for e in parameter_entries(section)
                              if "deprecated" in e.description_text().lower()
                              or "deprecated" in e.type_text.lower()]
                function = next((f for f in module.functions if f.qualname == doc.owner),
                                None)
                if not deprecated or function is None:
                    continue
                out.append(target(f"param-warning:{path}:{doc.owner}", path,
                                  function.span(),
                                  (path, module, function, deprecated[0].names),
                                  f"{doc.owner} deprecates {deprecated[0].names}"))
        return out

    def pass_condition(self, t: Target):
        path, module, function, parameter = t.payload
        if raises_future_warning(function.node):
            return Satisfied(f"{path}::{function.qualname} raises a FutureWarning for "
                             f"`{parameter}`")
        owner = function.qualname.split(".")[0]
        for info in classes(module):
            if info.name != owner:
                continue
            fit = info.method("fit")
            if fit is not None and raises_future_warning(fit):
                return Satisfied(f"{path}::{owner}.fit raises the FutureWarning for "
                                 f"`{parameter}`")
        return Violated(f"{path}::{function.qualname} documents `{parameter}` as "
                        f"deprecated but raises no FutureWarning when it is passed")


@rule(
    id="SCIKIT-LEARN-C122",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class DeprecatedParametersAreValidatedInFit:
    """Pre-condition: each estimator class the agent wrote or edited that raises a
    `FutureWarning` somewhere.
    Pass condition: none of those warnings is raised in `__init__`.

    Fires on the class having a parameter deprecation at all, and grades *where* it is
    handled (§7.1); selecting only warnings already in `fit` would record compliance and
    never its absence. Heuristic on the **pre-condition** (§6.3): "estimator" is the
    inherited proxy, and a `FutureWarning` raised for some other reason is selected too.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in estimators(b):
            warning_methods = [name for name, node in info.methods.items()
                               if raises_future_warning(node)]
            if not warning_methods:
                continue
            out.append(class_target(path, info, "warn-in-fit",
                                    (path, info, warning_methods),
                                    f"{info.name} warns in {', '.join(warning_methods)}"))
        return out

    def pass_condition(self, t: Target):
        path, info, warning_methods = t.payload
        if "__init__" in warning_methods:
            return Violated(f"{path}::{info.name} validates a deprecated parameter and "
                            f"raises its warning in __init__ rather than in fit")
        return Satisfied(f"{path}::{info.name} raises its deprecation warning in "
                         f"{', '.join(warning_methods)}, not in __init__")


@rule(
    id="SCIKIT-LEARN-C123",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a property of the message, no newness qualifier
    reads=("files",),  # spec §5
    heuristic=True,
)
class DeprecationMessagesNameBothVersions:
    """Pre-condition: each deprecation message the agent wrote -- a `@deprecated` reason
    or a `FutureWarning` text.
    Pass condition: it names two version numbers.

    Heuristic on the **pass condition** (§6.2): "the version in which the deprecation
    happened and the version in which the old behaviour will be removed" is graded as two
    distinct version-shaped tokens, so a message naming one version twice, or naming a
    version and a date, is read differently from how a maintainer would read it.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"two-versions:{path}:{lineno}", path, (lineno, lineno),
                       (path, lineno, message), message[:80])
                for path, lineno, message in deprecation_messages(b)]

    def pass_condition(self, t: Target):
        path, lineno, message = t.payload
        versions = {m.group(0) for m in _VERSION.finditer(message)}
        if len(versions) >= 2:
            return Satisfied(f"{path}:{lineno} names {' and '.join(sorted(versions))}")
        return Violated(f"{path}:{lineno} names {len(versions)} version(s); the message "
                        f"must give both the deprecation and the removal version")


@rule(
    id="SCIKIT-LEARN-C124",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class DeprecationMessagesQuoteReleaseVersionsTwoApart:
    """Pre-condition: each deprecation message the agent wrote that names two versions.
    Pass condition: neither is a dev version, and the removal is two minor releases after
    the deprecation.

    Narrowed to messages that already name two versions, because a message naming fewer is
    C123's finding (§7.5). Heuristic on the **pass condition** (§6.2): which of the two
    numbers is the deprecation and which the removal is inferred from their order, and a
    message mentioning a third version is graded on the first two.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, lineno, message in deprecation_messages(b):
            found = list(_VERSION.finditer(message))
            if len({m.group(0) for m in found}) < 2:
                continue
            out.append(target(f"version-window:{path}:{lineno}", path, (lineno, lineno),
                              (path, lineno, message, found), message[:80]))
        return out

    def pass_condition(self, t: Target):
        path, lineno, message, found = t.payload
        if dev := [m.group(0) for m in found if m.group("dev")]:
            return Violated(f"{path}:{lineno} quotes the dev version `{dev[0]}`; the "
                            f"message should name the release it happened in")
        first, second = found[0], found[1]
        major_gap = int(second.group(1)) - int(first.group(1))
        minor_gap = int(second.group(2)) - int(first.group(2))
        two_apart = (major_gap == 0 and minor_gap == 2) or (major_gap == 1
                                                            and int(second.group(2)) == 1)
        if two_apart:
            return Satisfied(f"{path}:{lineno} sets removal two releases after "
                             f"{first.group(0)}")
        return Violated(f"{path}:{lineno} deprecates in {first.group(0)} and removes in "
                        f"{second.group(0)}, which is not two releases later")


@rule(
    id="SCIKIT-LEARN-C130",
    category=CATEGORY,
    ownership="touched",  # spec §4.2 -- the antecedent is the default the agent changed
    reads=("files",),  # spec §5: base and head text of the same file
    heuristic=True,
)
class ChangingDefaultsGoThroughASentinel:
    """Pre-condition: each function whose keyword default the contribution changes.
    Pass condition: the new default is a sentinel value and a `FutureWarning` is raised.

    Heuristic on the **pass condition** (§6.2): the guide gives `"warn"` as the example
    sentinel and this accepts `"warn"` or `"deprecated"`, so a project-specific sentinel
    object would read as a violation. The pre-condition is exact where the base text was
    reconstructed and selects nothing where it was not -- a gap in the evidence, not an
    approximation.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in modules(b, tests=False):
            base = base_module(b, path)
            if base is None:
                continue
            before = {f.qualname: f for f in base.functions}
            for function in module.functions:
                previous = before.get(function.qualname)
                if previous is None:
                    continue
                old = {n: _source(v) for n, v in keyword_defaults(previous.node).items()}
                new = {n: _source(v) for n, v in keyword_defaults(function.node).items()}
                changed = [n for n in old if n in new and old[n] != new[n]]
                if not changed:
                    continue
                out.append(target(f"sentinel:{path}:{function.qualname}", path,
                                  function.span(), (path, module, function, changed, new),
                                  f"{function.qualname} changes {', '.join(changed)}"))
        return out

    def pass_condition(self, t: Target):
        path, module, function, changed, new = t.payload
        name = changed[0]
        value = new[name].strip("'\"")
        if value not in _SENTINEL_DEFAULTS:
            return Violated(f"{path}::{function.qualname} changes `{name}`'s default to "
                            f"{new[name]} outright, with no sentinel to warn on")
        if raises_future_warning(function.node):
            return Satisfied(f"{path}::{function.qualname} replaces `{name}`'s default "
                             f"with the sentinel {new[name]} and warns on it")
        owner = function.qualname.split(".")[0]
        for info in classes(module):
            fit = info.method("fit") if info.name == owner else None
            if fit is not None and raises_future_warning(fit):
                return Satisfied(f"{path}::{owner}.fit warns when `{name}` is left at "
                                 f"the sentinel {new[name]}")
        return Violated(f"{path}::{function.qualname} uses the sentinel {new[name]} for "
                        f"`{name}` but raises no FutureWarning when it is left in place")


# --- B. instantiation and the fit contract -------------------------------------------


def _estimator_init_targets(bundle: EvidenceBundle, prefix: str) -> list[Target]:
    """Each estimator `__init__` the agent wrote or edited -- group B's antecedent."""
    out = []
    for path, _module, info in estimators(bundle):
        initialiser = info.method("__init__")
        if initialiser is None:
            continue
        out.append(method_target(path, info, "__init__", initialiser, prefix))
    return out


@rule(
    id="SCIKIT-LEARN-C136",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a property every estimator's __init__ must have
    reads=("files",),  # spec §5
    heuristic=True,
)
class InitDoesNotTakeTrainingData:
    """Pre-condition: each estimator `__init__` the agent wrote or edited.
    Pass condition: none of its parameters is training data.

    A prohibition, so the antecedent is *having an `__init__`* and the graded question is
    what it accepts (§7.1). Heuristic on **both layers** (§6.3, §6.2): "estimator" is the
    inherited proxy, and training data is recognised by the argument names the guide's own
    worked counter-example uses -- `X`, `y`, `data` and their variants -- so a training set
    passed under another name is not caught.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _estimator_init_targets(b, "init-data")

    def pass_condition(self, t: Target):
        path, info, name, node = t.payload
        offending = [p for p in parameters(node) if p in TRAINING_DATA_ARGS]
        if offending:
            return Violated(f"{path}::{info.name}.__init__ takes `{offending[0]}`, which "
                            f"is training data and belongs to fit()")
        return Satisfied(f"{path}::{info.name}.__init__ takes no training data")


@rule(
    id="SCIKIT-LEARN-C139",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class EveryInitKeywordBecomesAnAttribute:
    """Pre-condition: each estimator `__init__` the agent wrote or edited that takes
    parameters.
    Pass condition: each parameter is assigned to an instance attribute of the same name.

    Heuristic on the **pre-condition** (§6.3) only: "estimator" is the inherited proxy.
    The grading is exact -- `self.<name> = ...` for each keyword is what `get_params` and
    model selection rely on, and the assignment is either in the constructor or it is not.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for t in _estimator_init_targets(b, "init-attributes"):
            _path, _info, _name, node = t.payload
            if [p for p in parameters(node) if p != "self"]:
                out.append(t)
        return out

    def pass_condition(self, t: Target):
        path, info, name, node = t.payload
        expected = [p for p in parameters(node) if p != "self"]
        assigned = self_assignments(node)
        missing = [p for p in expected if p not in assigned]
        if missing:
            return Violated(f"{path}::{info.name}.__init__ accepts `{missing[0]}` but "
                            f"sets no attribute of that name")
        return Satisfied(f"{path}::{info.name}.__init__ mirrors all {len(expected)} "
                         f"keyword(s) onto the instance")


@rule(
    id="SCIKIT-LEARN-C141",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class InitCarriesNoLogic:
    """Pre-condition: each estimator `__init__` the agent wrote or edited.
    Pass condition: its body is assignments and nothing else -- no branch, no loop, no
    raise, no call.

    Heuristic on the **pass condition** (§6.2): "no logic, not even input validation" is
    graded as the absence of every statement kind other than assignment, plus the absence
    of calls on the right-hand side. That is stricter than the sentence in one place --
    `super().__init__(...)` is a call and would be reported -- and the reading is recorded
    here rather than left to be discovered.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _estimator_init_targets(b, "init-logic")

    def pass_condition(self, t: Target):
        path, info, name, node = t.payload
        for statement in node.body:
            if isinstance(statement, (ast.Assign, ast.AnnAssign, ast.Pass)):
                continue
            if isinstance(statement, ast.Expr) and isinstance(statement.value,
                                                              ast.Constant):
                continue  # the docstring
            return Violated(f"{path}::{info.name}.__init__ carries "
                            f"{type(statement).__name__} logic on line "
                            f"{statement.lineno}; validation belongs in fit")
        for statement in node.body:
            for child in ast.walk(statement):
                if isinstance(child, ast.Call):
                    return Violated(f"{path}::{info.name}.__init__ calls "
                                    f"`{_source(child.func)}` on line {child.lineno}; "
                                    f"the constructor should only store its arguments")
        return Satisfied(f"{path}::{info.name}.__init__ only stores its arguments")


@rule(
    id="SCIKIT-LEARN-C143",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class InitSetsNoTrailingUnderscoreAttributes:
    """Pre-condition: each estimator `__init__` the agent wrote or edited.
    Pass condition: it assigns no attribute whose name ends in an underscore.

    A prohibition selected on the permitted act -- writing a constructor -- rather than on
    the assignment it forbids (§7.1). Heuristic on the **pre-condition** (§6.3) only: the
    trailing underscore is the project's own marker for a fitted attribute, so the grading
    itself is exact.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _estimator_init_targets(b, "init-underscore")

    def pass_condition(self, t: Target):
        path, info, name, node = t.payload
        fitted = [a for a in self_assignments(node)
                  if a.endswith("_") and not a.startswith("_")]
        if fitted:
            return Violated(f"{path}::{info.name}.__init__ sets `{fitted[0]}`, and a "
                            f"trailing underscore is reserved for what fit learns")
        return Satisfied(f"{path}::{info.name}.__init__ sets no fitted attribute")


@rule(
    id="SCIKIT-LEARN-C142",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class MutableConstructorArgumentsAreCopiedBeforeUse:
    """Pre-condition: each estimator method other than `__init__` that mutates a stored
    constructor argument in place.
    Pass condition: the method copies it first.

    Heuristic on **both layers** (§6.3, §6.2): mutation is recognised by the in-place
    methods a list, dict or set exposes -- `append`, `update`, `sort` and their siblings
    -- and a copy by the constructors and helpers that make one, so a mutation through
    slice assignment is not seen and a copy taken in a helper is not credited. The
    sentence's second half -- *where the parameters are used, typically in fit* -- is
    satisfied by construction, since `__init__` is excluded from the selection.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in estimators(b):
            stored = set(self_assignments(info.method("__init__"))
                         if info.method("__init__") is not None else {})
            for name, node in info.methods.items():
                if name == "__init__":
                    continue
                mutated = []
                for child in ast.walk(node):
                    if not isinstance(child, ast.Call):
                        continue
                    if not isinstance(child.func, ast.Attribute):
                        continue
                    if child.func.attr not in _MUTATORS:
                        continue
                    written = _source(child.func.value)
                    attribute = written.split(".")[-1]
                    if written.startswith("self.") and attribute in stored:
                        mutated.append(attribute)
                if mutated:
                    out.append(method_target(path, info, name, node, "copy-before-mutate",
                                             (path, info, name, node, mutated)))
        return out

    def pass_condition(self, t: Target):
        path, info, name, node, mutated = t.payload
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                called = _source(child.func).split(".")[-1]
                if called in _COPIERS:
                    return Satisfied(f"{path}::{info.name}.{name} copies "
                                     f"`{mutated[0]}` with `{called}` before modifying it")
        return Violated(f"{path}::{info.name}.{name} modifies the constructor argument "
                        f"`{mutated[0]}` in place without copying it first")


@rule(
    id="SCIKIT-LEARN-C144",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5: DEPARTURE from CheckTier=differential -- no run this
                       # instrument collects executes an estimator, so the check is what
                       # the submitted `fit` does about the requirement
    heuristic=True,
)
class FitChecksThatXAndYAgreeOnSamples:
    """Pre-condition: each estimator `fit` the agent wrote or edited that takes both `X`
    and `y`.
    Pass condition: it validates their lengths -- through `check_X_y`, `validate_data` or
    `check_consistent_length`, or by raising `ValueError` itself.

    Heuristic on the **pass condition** (§6.2): the requirement is behavioural -- a
    `ValueError` when the sample counts differ -- and nothing here runs the estimator, so
    the check is that the fit calls one of the helpers the project offers for exactly this,
    or raises the named exception itself. A `fit` that validates by some other route reads
    as a violation, and that is the cost of grading a differential rule statically.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in estimators(b):
            fit = info.method("fit")
            if fit is None:
                continue
            names = parameters(fit)
            if "X" not in names or "y" not in names:
                continue
            out.append(method_target(path, info, "fit", fit, "xy-consistency"))
        return out

    def pass_condition(self, t: Target):
        path, info, name, node = t.payload
        called = {c.split(".")[-1] for c in calls_in(node)}
        if helper := called & set(VALIDATION_HELPERS):
            return Satisfied(f"{path}::{info.name}.fit validates X against y with "
                             f"`{sorted(helper)[0]}`")
        for child in ast.walk(node):
            if isinstance(child, ast.Raise) and "ValueError" in _source(child):
                return Satisfied(f"{path}::{info.name}.fit raises ValueError itself when "
                                 f"the shapes disagree")
        return Violated(f"{path}::{info.name}.fit accepts X and y without checking that "
                        f"they hold the same number of samples")


@rule(
    id="SCIKIT-LEARN-C145",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class UnsupervisedFitAcceptsAnIgnoredY:
    """Pre-condition: each `fit` on an estimator the agent wrote or edited that is neither
    a classifier nor a regressor.
    Pass condition: its second parameter is `y`, defaulting to `None`.

    Heuristic on the **pre-condition** (§6.3): "unsupervised" is approximated by the class
    inheriting neither supervised mixin and having no supervised name, so a supervised
    estimator that declares neither would be asked for the wrong signature. The pass
    condition is exact -- a position and a default, both stated.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in estimators(b):
            fit = info.method("fit")
            if fit is None or is_classifier(info) or is_regressor(info):
                continue
            out.append(method_target(path, info, "fit", fit, "unsupervised-y"))
        return out

    def pass_condition(self, t: Target):
        path, info, name, node = t.payload
        names = [p for p in parameters(node) if p != "self"]
        if len(names) < 2 or names[1] != "y":
            return Violated(f"{path}::{info.name}.fit does not take `y` in second "
                            f"position, so it cannot sit in a mixed pipeline")
        default = keyword_defaults(node).get("y")
        if default is None or _source(default) != "None":
            return Violated(f"{path}::{info.name}.fit takes `y` but not as `y=None`, so "
                            f"an unsupervised call has to supply it")
        return Satisfied(f"{path}::{info.name}.fit accepts an ignored `y=None` in second "
                         f"position")


@rule(
    id="SCIKIT-LEARN-C146",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
)
class CompositeMethodsTakeYInSecondPlace:
    """Pre-condition: each `fit_predict`, `fit_transform`, `score` or `partial_fit` the
    agent wrote or edited.
    Pass condition: its second parameter is `y`.

    Not heuristic: the sentence gives a closed list of four method names, conditioned on
    them being implemented, and a parameter position is exact. The class need not be
    recognised as an estimator for this one, which is why it does not carry the proxy
    every neighbouring rule does.
    """

    COMPOSITE = ("fit_predict", "fit_transform", "score", "partial_fit")

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in owned_classes(b, tests=False):
            for name in self.COMPOSITE:
                node = info.method(name)
                if node is not None:
                    out.append(method_target(path, info, name, node, "y-second"))
        return out

    def pass_condition(self, t: Target):
        path, info, name, node = t.payload
        names = [p for p in parameters(node) if p != "self"]
        if len(names) >= 2 and names[1] == "y":
            return Satisfied(f"{path}::{info.name}.{name} takes `y` in second place")
        return Violated(f"{path}::{info.name}.{name} takes ({', '.join(names) or 'nothing'})"
                        f"; `y` must be the second argument")


@rule(
    id="SCIKIT-LEARN-C147",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- states a property of every fit
    reads=("files",),  # spec §5
)
class FitReturnsSelf:
    """Pre-condition: each `fit` method the agent wrote or edited.
    Pass condition: it returns `self`.

    Not heuristic: `fit` is named exactly, and `return self` is one statement whose
    presence the AST answers outright. The class is not required to look like an estimator
    -- anything that defines `fit` is bound by the chaining contract the guide's worked
    one-liner depends on.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in owned_classes(b, tests=False):
            fit = info.method("fit")
            if fit is not None:
                out.append(method_target(path, info, "fit", fit, "returns-self"))
        return out

    def pass_condition(self, t: Target):
        path, info, name, node = t.payload
        if returns_self(node):
            return Satisfied(f"{path}::{info.name}.fit returns self")
        return Violated(f"{path}::{info.name}.fit never returns self, so "
                        f"`Estimator().fit(X, y).predict(X)` breaks")


@rule(
    id="SCIKIT-LEARN-C148",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class DataIndependentParametersBelongToInit:
    """Pre-condition: each estimator `fit` the agent wrote or edited that takes a
    parameter beyond the data.
    Pass condition: none of those parameters carries a value that could have been set
    before the data arrived.

    Heuristic on the **pass condition** (§6.2): "can have a value assigned prior to having
    access to the data" is approximated by *the parameter has a literal default* -- a
    hyper-parameter, by the complementary sentence the guide states next, since a
    data-dependent argument has nothing to default to. `sample_weight`, `groups` and
    routed `**fit_params` are exempt, being data-dependent by the project's own glossary.
    """

    DATA_ARGS = ("self", "X", "y", "Xt", "sample_weight", "groups", "classes")

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in estimators(b):
            fit = info.method("fit")
            if fit is None:
                continue
            extra = [p for p in parameters(fit) if p not in self.DATA_ARGS]
            if extra:
                out.append(method_target(path, info, "fit", fit, "fit-params",
                                         (path, info, fit, extra)))
        return out

    def pass_condition(self, t: Target):
        path, info, node, extra = t.payload
        defaults = keyword_defaults(node)
        settable = [p for p in extra
                    if p in defaults and isinstance(defaults[p], ast.Constant)
                    and defaults[p].value is not None]
        if settable:
            return Violated(f"{path}::{info.name}.fit takes `{settable[0]}="
                            f"{_source(defaults[settable[0]])}`, which could have been an "
                            f"__init__ keyword")
        return Satisfied(f"{path}::{info.name}.fit's extra parameter(s) "
                         f"({', '.join(extra)}) are data dependent")


@rule(
    id="SCIKIT-LEARN-C151",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class PublicLearnedAttributesEndInAnUnderscore:
    """Pre-condition: each learned attribute the agent's class exposes in its docstring's
    Attributes section.
    Pass condition: its name ends in a trailing underscore.

    Partitioned against C152 so one defect is not counted twice (§7.5): this rule takes
    the attributes the docstring *exposes* as public, C152 takes the ones it does not.
    Heuristic on the **pre-condition** (§6.3): "attributes you'd want to expose as public"
    is approximated by their being documented, which is the only record of that intent.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in owned_classes(b, tests=False):
            documented = documented_attributes(info)
            for attribute, method in learned_attributes(info).items():
                if attribute not in documented or attribute.startswith("_"):
                    continue
                out.append(target(f"learned-public:{path}:{info.name}.{attribute}", path,
                                  info.span(), (path, info, attribute, method),
                                  f"{info.name}.{attribute} set in {method}"))
        return out

    def pass_condition(self, t: Target):
        path, info, attribute, method = t.payload
        if attribute.endswith("_"):
            return Satisfied(f"{path}::{info.name}.{attribute} carries the trailing "
                             f"underscore `check_is_fitted` keys off")
        return Violated(f"{path}::{info.name}.{attribute} is learned in {method} and "
                        f"documented as public, so it must be named `{attribute}_`")


@rule(
    id="SCIKIT-LEARN-C152",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class NonPublicLearnedAttributesLeadWithAnUnderscore:
    """Pre-condition: each learned attribute the agent's class does not document.
    Pass condition: its name begins with a leading underscore.

    The complement of C151, and the partition is deliberate (§7.5): an undocumented
    learned attribute is one the class does not expose, so the guide's leading-underscore
    rule is the one that binds it. Heuristic on the **pre-condition** (§6.3): "you'd like
    to store yet not expose" is an intention, approximated by the attribute's absence from
    the Attributes section.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in owned_classes(b, tests=False):
            if not info.docstring:
                continue
            documented = documented_attributes(info)
            for attribute, method in learned_attributes(info).items():
                if attribute in documented:
                    continue
                out.append(target(f"learned-private:{path}:{info.name}.{attribute}", path,
                                  info.span(), (path, info, attribute, method),
                                  f"{info.name}.{attribute} set in {method}"))
        return out

    def pass_condition(self, t: Target):
        path, info, attribute, method = t.payload
        if attribute.startswith("_"):
            return Satisfied(f"{path}::{info.name}.{attribute} is marked non-public with "
                             f"a leading underscore")
        return Violated(f"{path}::{info.name}.{attribute} is learned in {method} and "
                        f"documented nowhere, so it should be named `_{attribute}`")


@rule(
    id="SCIKIT-LEARN-C155",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class FitSetsNFeaturesIn:
    """Pre-condition: each estimator `fit` the agent wrote or edited that takes `X`.
    Pass condition: it sets `n_features_in_`, or calls the validation helper that sets it.

    Heuristic on **both layers** (§6.3, §6.2): "expects tabular input" is approximated by
    `fit` taking `X`, which is a superset that also selects estimators over graphs or
    text; and `validate_data` is credited because the guide states that it sets the
    attribute for you, so the check accepts the indirect route as well as the direct one.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in estimators(b):
            fit = info.method("fit")
            if fit is None or "X" not in parameters(fit):
                continue
            out.append(method_target(path, info, "fit", fit, "n-features-in"))
        return out

    def pass_condition(self, t: Target):
        path, info, name, node = t.payload
        if "n_features_in_" in self_assignments(node):
            return Satisfied(f"{path}::{info.name}.fit sets n_features_in_")
        called = {c.split(".")[-1] for c in calls_in(node)}
        if helper := called & {"validate_data", "_validate_data"}:
            return Satisfied(f"{path}::{info.name}.fit sets n_features_in_ through "
                             f"`{sorted(helper)[0]}`")
        return Violated(f"{path}::{info.name}.fit never sets n_features_in_, so predict "
                        f"cannot check the feature count it was fitted on")


@rule(
    id="SCIKIT-LEARN-C156",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class FitSetsFeatureNamesIn:
    """Pre-condition: each estimator `fit` the agent wrote or edited that takes `X`.
    Pass condition: it sets `feature_names_in_`, or calls the validation helper that sets
    it.

    The same shape and the same two approximations as C155, and stated separately because
    the corpus states them separately: an estimator can set the count and not the names.
    Heuristic on **both layers** (§6.3, §6.2).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in estimators(b):
            fit = info.method("fit")
            if fit is None or "X" not in parameters(fit):
                continue
            out.append(method_target(path, info, "fit", fit, "feature-names-in"))
        return out

    def pass_condition(self, t: Target):
        path, info, name, node = t.payload
        if "feature_names_in_" in self_assignments(node):
            return Satisfied(f"{path}::{info.name}.fit sets feature_names_in_")
        called = {c.split(".")[-1] for c in calls_in(node)}
        if helper := called & {"validate_data", "_validate_data"}:
            return Satisfied(f"{path}::{info.name}.fit sets feature_names_in_ through "
                             f"`{sorted(helper)[0]}`")
        return Violated(f"{path}::{info.name}.fit never sets feature_names_in_, so a "
                        f"dataframe's column names are lost")


# --- C. estimator types and their mixins ---------------------------------------------


@rule(
    id="SCIKIT-LEARN-C158",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- the sentence says "a NEW estimator"; an existing
                          # class the agent merely edited is not its doing
    reads=("files",),  # spec §5
    heuristic=True,
)
class NewEstimatorsInheritBaseEstimator:
    """Pre-condition: each estimator class the agent adds.
    Pass condition: `BaseEstimator` is among its bases.

    Heuristic on the **pre-condition** (§6.3): "estimator" is recognised by the class
    defining `fit`, which is what the guide itself points at -- and deliberately not by
    it inheriting `BaseEstimator`, since selecting on the artefact the rule demands could
    only ever record compliance (§7.1).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [class_target(path, info, "base-estimator")
                for path, _module, info in owned_classes(b, mode="created", tests=False)
                if is_estimator(info)]

    def pass_condition(self, t: Target):
        path, info = t.payload
        if info.inherits("BaseEstimator"):
            return Satisfied(f"{path}::{info.name} inherits BaseEstimator")
        return Violated(f"{path}::{info.name} defines fit but does not inherit "
                        f"BaseEstimator, so get_params and set_params are missing")


@rule(
    id="SCIKIT-LEARN-C159",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- "a new estimator's bases"
    reads=("files",),  # spec §5
    heuristic=True,
)
class MixinsComeBeforeBaseEstimator:
    """Pre-condition: each estimator class the agent adds that inherits both a mixin and
    `BaseEstimator`.
    Pass condition: every mixin appears before `BaseEstimator` in the base list.

    Heuristic on the **pre-condition** (§6.3): a mixin is recognised by the `Mixin`
    suffix the project uses without exception. The ordering itself is exact, and its
    consequence -- the method resolution order -- is stated in the same sentence.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in owned_classes(b, mode="created", tests=False):
            bases = [base.split(".")[-1] for base in info.bases]
            if "BaseEstimator" not in bases:
                continue
            if not any(base.endswith("Mixin") for base in bases):
                continue
            out.append(class_target(path, info, "mro-order", (path, info, bases),
                                    f"{info.name}({', '.join(bases)})"))
        return out

    def pass_condition(self, t: Target):
        path, info, bases = t.payload
        position = bases.index("BaseEstimator")
        late = [base for base in bases[position:] if base.endswith("Mixin")]
        if late:
            return Violated(f"{path}::{info.name} lists `{late[0]}` after BaseEstimator; "
                            f"mixins go on the left for a correct MRO")
        return Satisfied(f"{path}::{info.name} lists its mixin(s) before BaseEstimator")


@rule(
    id="SCIKIT-LEARN-C160",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a property of the method wherever it is defined
    reads=("files",),  # spec §5
    heuristic=True,
)
class SklearnCloneReturnsAnInstance:
    """Pre-condition: each `__sklearn_clone__` the agent wrote or edited.
    Pass condition: it returns a value.

    Heuristic on the **pass condition** (§6.2): "must return an instance of the estimator"
    is graded as *it returns something*, because what a returned expression evaluates to is
    not decidable from the source. A method that falls off the end -- returning `None` --
    is the failure the rule exists to catch, and that is caught exactly.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in owned_classes(b, tests=False):
            node = info.method("__sklearn_clone__")
            if node is not None:
                out.append(method_target(path, info, "__sklearn_clone__", node,
                                         "clone-returns"))
        return out

    def pass_condition(self, t: Target):
        path, info, name, node = t.payload
        for child in ast.walk(node):
            if isinstance(child, ast.Return) and child.value is not None:
                return Satisfied(f"{path}::{info.name}.__sklearn_clone__ returns "
                                 f"`{_source(child.value)[:40]}`")
        return Violated(f"{path}::{info.name}.__sklearn_clone__ returns nothing, so "
                        f"base.clone() would produce None")


@rule(
    id="SCIKIT-LEARN-C161",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class TransformersInheritTheMixinAndImplementTransform:
    """Pre-condition: each class the agent wrote or edited that is a transformer.
    Pass condition: it inherits `TransformerMixin` and defines `transform`.

    Heuristic on the **pre-condition** (§6.3): a transformer is recognised by *either*
    mark -- the mixin or a `transform` method -- so that a class with one and not the other
    is selected and fails, which is the whole content of the rule. Selecting on both would
    find only the compliant ones (§7.1).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [class_target(path, info, "transformer")
                for path, _module, info in owned_classes(b, tests=False)
                if is_transformer(info)]

    def pass_condition(self, t: Target):
        path, info = t.payload
        if not info.inherits("TransformerMixin"):
            return Violated(f"{path}::{info.name} implements transform but does not "
                            f"inherit TransformerMixin")
        if "transform" not in info.methods:
            return Violated(f"{path}::{info.name} inherits TransformerMixin but "
                            f"implements no transform method")
        return Satisfied(f"{path}::{info.name} inherits TransformerMixin and implements "
                         f"transform")


@rule(
    id="SCIKIT-LEARN-C162",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5: DEPARTURE from CheckTier=differential -- nothing here
                       # executes a transformer, so the check is what the code does
    heuristic=True,
)
class TransformKeepsItsSamplesAlignedAndInOrder:
    """Pre-condition: each `transform` method the agent wrote or edited.
    Pass condition: its body contains no construct that drops or reorders rows.

    Graded from the code rather than from a run, and heuristic on the **pass condition**
    (§6.2) because of it: boolean-mask indexing, `np.delete(..., axis=0)`, `dropna` and
    `sort` are the shapes that change the sample count or its order, and a transformer
    that reorders through some other route passes. Sharpens the rule to what a patch can
    show, which is the honest reading of a behavioural contract nothing runs.
    """

    ROW_CHANGING = re.compile(r"\bnp\.delete\s*\(|\.dropna\s*\(|\.drop\s*\(|"
                              r"\.sort_values\s*\(|\bnp\.sort\s*\(|\.reset_index\s*\(")

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in owned_classes(b, tests=False):
            node = info.method("transform")
            if node is not None:
                out.append(method_target(path, info, "transform", node, "row-alignment"))
        return out

    def pass_condition(self, t: Target):
        path, info, name, node = t.payload
        body = _source(node)
        if match := self.ROW_CHANGING.search(body):
            return Violated(f"{path}::{info.name}.transform uses "
                            f"`{match.group(0).strip()}`, which can drop or reorder "
                            f"samples relative to its input")
        return Satisfied(f"{path}::{info.name}.transform carries no construct that drops "
                         f"or reorders rows")


@rule(
    id="SCIKIT-LEARN-C163",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class RegressorsInheritTheMixinAndImplementPredict:
    """Pre-condition: each class the agent wrote or edited that is a regressor.
    Pass condition: it inherits `RegressorMixin` and defines `predict`.

    Heuristic on the **pre-condition** (§6.3): a regressor is recognised by the mixin or
    by a `Regressor`/`Regression` name, both marks the project uses. The sentence's third
    clause -- *they should accept numerical `y`* -- is a behavioural claim about values
    passed at run time and is deliberately not graded; saying so here is the point of the
    docstring being load-bearing (§7.3).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [class_target(path, info, "regressor")
                for path, _module, info in owned_classes(b, tests=False)
                if is_regressor(info)]

    def pass_condition(self, t: Target):
        path, info = t.payload
        if not info.inherits("RegressorMixin"):
            return Violated(f"{path}::{info.name} is a regressor but does not inherit "
                            f"RegressorMixin, so it has no r2 score method")
        if "predict" not in info.methods:
            return Violated(f"{path}::{info.name} inherits RegressorMixin but implements "
                            f"no predict method")
        return Satisfied(f"{path}::{info.name} inherits RegressorMixin and implements "
                         f"predict")


@rule(
    id="SCIKIT-LEARN-C164",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class ClassifiersInheritClassifierMixin:
    """Pre-condition: each class the agent wrote or edited that is a classifier.
    Pass condition: it inherits `ClassifierMixin`.

    Heuristic on the **pre-condition** (§6.3): a classifier is recognised by the mixin, a
    `Classifier` name, or a `predict_proba` method -- the marks the project uses -- so a
    classifier declaring none of them is not selected.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [class_target(path, info, "classifier")
                for path, _module, info in owned_classes(b, tests=False)
                if is_classifier(info)]

    def pass_condition(self, t: Target):
        path, info = t.payload
        if info.inherits("ClassifierMixin"):
            return Satisfied(f"{path}::{info.name} inherits ClassifierMixin")
        return Violated(f"{path}::{info.name} is a classifier but does not inherit "
                        f"ClassifierMixin")


@rule(
    id="SCIKIT-LEARN-C165",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5: DEPARTURE from CheckTier=differential -- see the module
                       # docstring; nothing here fits a classifier on string labels
    heuristic=True,
)
class ClassifiersAcceptStringOrIntegerLabels:
    """Pre-condition: each `fit` on a classifier the agent wrote or edited.
    Pass condition: it encodes the labels it is given rather than assuming their type.

    Heuristic on the **pass condition** (§6.2): accepting "sequences of either strings or
    integers" is a run-time property, and the observable proxy is that `fit` passes `y`
    through one of the helpers that handles both -- `np.unique`, `LabelEncoder`,
    `check_classification_targets`, `column_or_1d`. A classifier that handles strings by
    hand reads as a violation, which is the cost of grading this from the patch.
    """

    ENCODERS = ("unique", "LabelEncoder", "check_classification_targets", "column_or_1d",
                "type_of_target")

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in owned_classes(b, tests=False):
            fit = info.method("fit")
            if fit is None or not is_classifier(info):
                continue
            out.append(method_target(path, info, "fit", fit, "label-types"))
        return out

    def pass_condition(self, t: Target):
        path, info, name, node = t.payload
        called = {c.split(".")[-1] for c in calls_in(node)}
        if used := called & set(self.ENCODERS):
            return Satisfied(f"{path}::{info.name}.fit encodes its labels with "
                             f"`{sorted(used)[0]}`, which accepts strings and integers")
        return Violated(f"{path}::{info.name}.fit uses y without encoding it, so a "
                        f"sequence of string labels is not accepted")


@rule(
    id="SCIKIT-LEARN-C166",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class ClassifiersStoreTheObservedLabels:
    """Pre-condition: each `fit` on a classifier the agent wrote or edited.
    Pass condition: it sets `classes_`.

    Heuristic on the **pre-condition** (§6.3) only: the classifier proxy. The grading is
    exact -- the guide names the attribute, and storing it is precisely what "should not
    assume the class labels are a contiguous range of integers" comes down to.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in owned_classes(b, tests=False):
            fit = info.method("fit")
            if fit is None or not is_classifier(info):
                continue
            out.append(method_target(path, info, "fit", fit, "classes-attribute"))
        return out

    def pass_condition(self, t: Target):
        path, info, name, node = t.payload
        if "classes_" in self_assignments(node):
            return Satisfied(f"{path}::{info.name}.fit stores the observed labels in "
                             f"classes_")
        return Violated(f"{path}::{info.name}.fit never sets classes_, so it assumes the "
                        f"labels are a contiguous integer range")


@rule(
    id="SCIKIT-LEARN-C167",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5: DEPARTURE from CheckTier=differential -- see the module
                       # docstring
    heuristic=True,
)
class ClassesAreOrderedLikeTheProbabilityColumns:
    """Pre-condition: each classifier the agent wrote or edited that both sets `classes_`
    and returns per-class scores.
    Pass condition: `classes_` is built by `np.unique`, whose sorted output is what fixes
    the column order.

    Heuristic on the **pass condition** (§6.2): the requirement is that two orderings
    agree, which only a run could establish. The proxy is the recipe the guide itself
    gives -- `self.classes_, y = np.unique(y, return_inverse=True)` -- so a classifier that
    guarantees the order another way reads as a violation. Recorded here because grading a
    differential rule from the patch is a narrowing, not a measurement.
    """

    SCORING = ("predict_proba", "predict_log_proba", "decision_function")

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in owned_classes(b, tests=False):
            fit = info.method("fit")
            if fit is None or "classes_" not in self_assignments(fit):
                continue
            if not any(name in info.methods for name in self.SCORING):
                continue
            out.append(method_target(path, info, "fit", fit, "classes-order"))
        return out

    def pass_condition(self, t: Target):
        path, info, name, node = t.payload
        assigned = self_assignments(node)
        written = _source(assigned.get("classes_"))
        if "unique" in written or "unique" in {c.split(".")[-1] for c in calls_in(node)}:
            return Satisfied(f"{path}::{info.name}.fit builds classes_ with np.unique, "
                             f"whose sorted order fixes the score columns")
        return Violated(f"{path}::{info.name}.fit sets classes_ from "
                        f"`{written[:40]}`, so nothing guarantees it matches the column "
                        f"order of {', '.join(self.SCORING)}")


@rule(
    id="SCIKIT-LEARN-C168",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5: DEPARTURE from CheckTier=differential -- see the module
                       # docstring
    heuristic=True,
)
class PredictReturnsLabelsFromClasses:
    """Pre-condition: each `predict` on a classifier the agent wrote or edited.
    Pass condition: its body reads `classes_`.

    Heuristic on the **pass condition** (§6.2): "returns arrays containing class labels
    from `classes_`" is a run-time property, and consulting the attribute is the observable
    trace of it -- the guide's own recipe, `return self.classes_[np.argmax(D, axis=1)]`,
    is exactly this shape. A predict that returns stored labels through a helper reads as
    a violation.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in owned_classes(b, tests=False):
            node = info.method("predict")
            if node is None or not is_classifier(info):
                continue
            out.append(method_target(path, info, "predict", node, "predict-labels"))
        return out

    def pass_condition(self, t: Target):
        path, info, name, node = t.payload
        if "classes_" in _source(node):
            return Satisfied(f"{path}::{info.name}.predict draws its labels from "
                             f"classes_")
        return Violated(f"{path}::{info.name}.predict never consults classes_, so what "
                        f"it returns need not be a label the estimator was fitted on")


@rule(
    id="SCIKIT-LEARN-C169",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class ClusteringAlgorithmsInheritClusterMixin:
    """Pre-condition: each class the agent wrote or edited that is a clustering algorithm.
    Pass condition: it inherits `ClusterMixin`.

    Partitioned against C171 (§7.5): a clustering algorithm is recognised by *either* mark
    -- the mixin or a `labels_` attribute -- and this rule grades the mixin while C171
    grades the attribute, so a class carrying one and not the other fails exactly one of
    them. Heuristic on the **pre-condition** (§6.3), which is that recognition.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [class_target(path, info, "cluster-mixin")
                for path, _module, info in owned_classes(b, tests=False)
                if is_clusterer(info)]

    def pass_condition(self, t: Target):
        path, info = t.payload
        if info.inherits("ClusterMixin"):
            return Satisfied(f"{path}::{info.name} inherits ClusterMixin")
        return Violated(f"{path}::{info.name} assigns cluster labels but does not "
                        f"inherit ClusterMixin")


@rule(
    id="SCIKIT-LEARN-C171",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class ClusteringAlgorithmsSetLabels:
    """Pre-condition: each class the agent wrote or edited that is a clustering algorithm.
    Pass condition: it sets a `labels_` attribute outside `__init__`.

    The complement of C169 over the same antecedent (§7.5). Heuristic on the
    **pre-condition** (§6.3): the clusterer proxy. The grading is exact -- the guide names
    the attribute, and `predict` is explicitly optional where `labels_` is not.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [class_target(path, info, "labels-attribute")
                for path, _module, info in owned_classes(b, tests=False)
                if is_clusterer(info)]

    def pass_condition(self, t: Target):
        path, info = t.payload
        if "labels_" in learned_attributes(info):
            return Satisfied(f"{path}::{info.name} sets labels_ with the per-sample "
                             f"cluster assignment")
        return Violated(f"{path}::{info.name} inherits ClusterMixin but never sets "
                        f"labels_")


# --- D. tags and the developer API ---------------------------------------------------


@rule(
    id="SCIKIT-LEARN-C173",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a property of every attribute added to a Tags
                          # subclass, with no newness qualifier on the class itself
    reads=("files",),  # spec §5
    heuristic=True,
)
class TagsSubclassAttributesCarryDefaults:
    """Pre-condition: each attribute declared on a class the agent wrote or edited that
    subclasses `Tags`.
    Pass condition: it carries a default value.

    Heuristic on the **pre-condition** (§6.3): a Tags subclass is recognised by a base
    named `Tags`, which is how the guide's worked `@dataclass class MyTags(Tags)` is
    written. The grading is exact: an annotated field either has a value or it does not,
    and the dataclass machinery is what makes that mandatory.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in owned_classes(b, tests=False):
            if not info.inherits("Tags"):
                continue
            for statement in info.node.body:
                if isinstance(statement, ast.AnnAssign):
                    name = _source(statement.target)
                    out.append(target(f"tag-default:{path}:{info.name}.{name}", path,
                                      (statement.lineno, statement.lineno),
                                      (path, info, name, statement),
                                      f"{info.name}.{name}"))
        return out

    def pass_condition(self, t: Target):
        path, info, name, statement = t.payload
        if statement.value is not None:
            return Satisfied(f"{path}::{info.name}.{name} defaults to "
                             f"`{_source(statement.value)[:30]}`")
        return Violated(f"{path}::{info.name}.{name} is added to a Tags subclass with no "
                        f"default value")


@rule(
    id="SCIKIT-LEARN-C175",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
)
class InitSubclassDoesNotDependOnAutoWrapOutputKeys:
    """Pre-condition: each `__init_subclass__` the agent wrote or edited.
    Pass condition: it never mentions `auto_wrap_output_keys`.

    A prohibition selected on the permitted act -- defining the hook -- rather than on the
    dependency it forbids (§7.1). Not heuristic: the method and the keyword are both named
    exactly, and `TransformerMixin` consumes the keyword before a super class sees it, so
    a mention is the defect.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in owned_classes(b, tests=False):
            node = info.method("__init_subclass__")
            if node is not None:
                out.append(method_target(path, info, "__init_subclass__", node,
                                         "auto-wrap"))
        return out

    def pass_condition(self, t: Target):
        path, info, name, node = t.payload
        if "auto_wrap_output_keys" in _source(node):
            return Violated(f"{path}::{info.name}.__init_subclass__ depends on "
                            f"auto_wrap_output_keys, which TransformerMixin consumes "
                            f"before the super class sees it")
        return Satisfied(f"{path}::{info.name}.__init_subclass__ does not depend on "
                         f"auto_wrap_output_keys")


@rule(
    id="SCIKIT-LEARN-C176",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class SklearnIsFittedTakesNothingAndReturnsABoolean:
    """Pre-condition: each `__sklearn_is_fitted__` the agent wrote or edited.
    Pass condition: it takes only `self` and returns a boolean-shaped expression.

    Heuristic on the **pass condition** (§6.2): the parameter half is exact, and "returns
    a boolean" is approximated by the returned expression being a literal, a comparison, a
    `bool(...)`/`hasattr(...)` call or a `not` -- a method returning a boolean computed
    some other way reads as a violation.
    """

    BOOLEAN_CALLS = ("bool", "hasattr", "isinstance", "all", "any", "callable")

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in owned_classes(b, tests=False):
            node = info.method("__sklearn_is_fitted__")
            if node is not None:
                out.append(method_target(path, info, "__sklearn_is_fitted__", node,
                                         "is-fitted"))
        return out

    def pass_condition(self, t: Target):
        path, info, name, node = t.payload
        extra = [p for p in parameters(node) if p != "self"]
        if extra:
            return Violated(f"{path}::{info.name}.__sklearn_is_fitted__ takes "
                            f"`{extra[0]}`; the method takes no input")
        for child in ast.walk(node):
            if not isinstance(child, ast.Return) or child.value is None:
                continue
            value = child.value
            boolean = (isinstance(value, (ast.Compare, ast.BoolOp))
                       or (isinstance(value, ast.UnaryOp)
                           and isinstance(value.op, ast.Not))
                       or (isinstance(value, ast.Constant)
                           and isinstance(value.value, bool))
                       or (isinstance(value, ast.Call)
                           and _source(value.func).split(".")[-1] in self.BOOLEAN_CALLS))
            if boolean:
                return Satisfied(f"{path}::{info.name}.__sklearn_is_fitted__ returns "
                                 f"`{_source(value)[:40]}`")
            return Violated(f"{path}::{info.name}.__sklearn_is_fitted__ returns "
                            f"`{_source(value)[:40]}`, which is not a boolean")
        return Violated(f"{path}::{info.name}.__sklearn_is_fitted__ returns nothing, so "
                        f"check_is_fitted would read None")


def _class_attribute(info, name: str):
    """The class-level assignment of ``name``, or None."""
    for statement in info.node.body:
        if isinstance(statement, ast.AnnAssign) and _source(statement.target) == name:
            return statement.value
        if isinstance(statement, ast.Assign):
            for element in statement.targets:
                if _source(element) == name:
                    return statement.value
    return None


@rule(
    id="SCIKIT-LEARN-C177",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class DocLinkCustomisationOverridesBothAttributes:
    """Pre-condition: each class the agent wrote or edited that overrides either
    `_doc_link_module` or `_doc_link_template`.
    Pass condition: it overrides both.

    Fires on *customising the documentation link at all* -- the situation the sentence
    addresses -- rather than on the pair already being present (§7.1). Heuristic on the
    **pre-condition** (§6.3): overriding one of the two is the observable sign of the
    intention the sentence is about, and a class that customises the link some third way
    is not selected.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in owned_classes(b, tests=False):
            has_module = _class_attribute(info, "_doc_link_module") is not None
            has_template = _class_attribute(info, "_doc_link_template") is not None
            if has_module or has_template:
                out.append(class_target(path, info, "doc-link",
                                        (path, info, has_module, has_template)))
        return out

    def pass_condition(self, t: Target):
        path, info, has_module, has_template = t.payload
        if has_module and has_template:
            return Satisfied(f"{path}::{info.name} overrides both _doc_link_module and "
                             f"_doc_link_template")
        missing = "_doc_link_template" if has_module else "_doc_link_module"
        return Violated(f"{path}::{info.name} customises its documentation link but does "
                        f"not override {missing}")


@rule(
    id="SCIKIT-LEARN-C178",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class DocLinkModuleNamesTheTopLevelPackage:
    """Pre-condition: each class the agent wrote or edited that sets `_doc_link_module`.
    Pass condition: its value is the top-level package of the file that defines it.

    Heuristic on the **pass condition** (§6.2): "the (top level) module that contains your
    estimator" is derived from the file's own path, which is right for a package laid out
    as this one is and would be wrong for a class re-exported from elsewhere. The
    consequence of getting it wrong is stated in the guide: no link is rendered.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in owned_classes(b, tests=False):
            value = _class_attribute(info, "_doc_link_module")
            if value is not None:
                out.append(class_target(path, info, "doc-link-module",
                                        (path, info, value)))
        return out

    def pass_condition(self, t: Target):
        path, info, value = t.payload
        written = _source(value).strip("'\"")
        expected = path.split("/")[0]
        if written == expected:
            return Satisfied(f"{path}::{info.name} sets _doc_link_module to "
                             f"'{expected}'")
        return Violated(f"{path}::{info.name} sets _doc_link_module to '{written}' while "
                        f"the estimator lives in the '{expected}' top-level module, so "
                        f"no documentation link is rendered")


@rule(
    id="SCIKIT-LEARN-C179",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class DocLinkParamGeneratorReturnsADict:
    """Pre-condition: each `_doc_link_url_param_generator` the agent wrote or edited.
    Pass condition: it returns a dictionary.

    Heuristic on the **pass condition** (§6.2): a returned dict literal or `dict(...)`
    call is recognised exactly, and a dict built into a local variable and then returned is
    recognised by that variable having been assigned one -- beyond that, what an expression
    evaluates to is not decidable from the source.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in owned_classes(b, tests=False):
            node = info.method("_doc_link_url_param_generator")
            if node is not None:
                out.append(method_target(path, info, "_doc_link_url_param_generator",
                                         node, "doc-link-params"))
        return out

    def pass_condition(self, t: Target):
        path, info, name, node = t.payload
        dict_names = {_source(element)
                      for statement in ast.walk(node)
                      if isinstance(statement, ast.Assign)
                      and (isinstance(statement.value, ast.Dict)
                           or _source(statement.value).startswith("dict("))
                      for element in statement.targets}
        for child in ast.walk(node):
            if not isinstance(child, ast.Return) or child.value is None:
                continue
            written = _source(child.value)
            if isinstance(child.value, ast.Dict) or written.startswith("dict("):
                return Satisfied(f"{path}::{info.name}.{name} returns a dictionary of "
                                 f"template variables")
            if written in dict_names:
                return Satisfied(f"{path}::{info.name}.{name} returns `{written}`, which "
                                 f"it built as a dictionary")
            return Violated(f"{path}::{info.name}.{name} returns `{written[:40]}`, which "
                            f"is not a dictionary of template variables")
        return Violated(f"{path}::{info.name}.{name} returns nothing, so no template "
                        f"variables reach the documentation link")


# --- E. general coding style ---------------------------------------------------------


def _package_modules(bundle: EvidenceBundle):
    return [(p, m) for p, m in modules(bundle, tests=False) if p.startswith(PACKAGE)]


def _owned_package_functions(bundle: EvidenceBundle):
    out = []
    for path, module in _package_modules(bundle):
        for function in module.functions:
            if own.owns_span(bundle, path, function.span(), "touched"):
                out.append((path, module, function))
    return out


@rule(
    id="SCIKIT-LEARN-C181",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- a name the agent did not choose is not its doing;
                          # only definitions it added are judged
    reads=("files",),  # spec §5
    heuristic=True,
)
class NonClassNamesSeparateWordsWithUnderscores:
    """Pre-condition: each function the agent adds to package code.
    Pass condition: its name separates words with underscores rather than capitals.

    Heuristic on the **pass condition** (§6.2): the guide's worked pair is `n_samples`
    rather than `nsamples`, and a run-together name of that kind is indistinguishable from
    a single word, so what is graded is the other failure -- camel case in a non-class
    name -- which is detectable. Stated here because the check is narrower than the rule.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in _package_modules(b):
            for function in module.functions:
                if not own.owns_span(b, path, function.span(), "created"):
                    continue
                out.append(target(f"naming:{path}:{function.qualname}", path,
                                  function.span(), (path, function),
                                  f"{path}::{function.qualname}"))
        return out

    def pass_condition(self, t: Target):
        path, function = t.payload
        if _CAMEL_CASE.search(function.name):
            return Violated(f"{path}::{function.qualname} runs words together in camel "
                            f"case; non-class names separate words with underscores")
        return Satisfied(f"{path}::{function.qualname} is named in lower case with "
                         f"underscores")


@rule(
    id="SCIKIT-LEARN-C182",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- lines the agent wrote inside existing files
    reads=("files",),  # spec §5
    heuristic=True,
)
class OneStatementPerLine:
    """Pre-condition: each Python file in the package the agent wrote lines into.
    Pass condition: none of those lines holds two statements or a control-flow header with
    its body attached.

    Heuristic on the **pass condition** (§6.2): a semicolon or an inline body after
    `if`/`for` is read textually, so a semicolon inside a string literal would be
    reported. That is the same trade ruff's own E-rules make, and it is the shape the
    sentence names.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module in _package_modules(b):
            written = added_lines(b, path)
            if written:
                out.append(target(f"one-statement:{path}", path, None, (path, written),
                                  f"{len(written)} written line(s)"))
        return out

    def pass_condition(self, t: Target):
        path, written = t.payload
        for lineno, text in written:
            if _MULTI_STATEMENT.search(text):
                return Violated(f"{path}:{lineno} puts more than one statement on a "
                                f"line: {text.strip()[:60]}")
            if _INLINE_BODY.match(text):
                return Violated(f"{path}:{lineno} attaches its body to the control-flow "
                                f"statement: {text.strip()[:60]}")
        return Satisfied(f"{len(written)} written line(s) in {path} hold one statement "
                         f"each")


@rule(
    id="SCIKIT-LEARN-C183",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- an import the agent wrote in an existing file
    reads=("files",),  # spec §5
)
class ImportsAreAbsolute:
    """Pre-condition: each import statement the agent wrote in package code.
    Pass condition: it is absolute.

    Not heuristic: a relative import is a syntactic fact -- `ImportFrom.level` is non-zero
    -- and the project's own ruff configuration bans the form. Selecting every import
    rather than only the relative ones is what lets a compliant import be recorded (§7.1).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in _package_modules(b):
            for node in ast.walk(module.tree):
                if not isinstance(node, (ast.Import, ast.ImportFrom)):
                    continue
                if not own.owns_span(b, path, (node.lineno, node.lineno), "touched"):
                    continue
                level = getattr(node, "level", 0) or 0
                out.append(target(f"absolute-import:{path}:{node.lineno}", path,
                                  (node.lineno, node.lineno),
                                  (path, node.lineno, level, _source(node)),
                                  _source(node)[:80]))
        return out

    def pass_condition(self, t: Target):
        path, lineno, level, written = t.payload
        if level:
            return Violated(f"{path}:{lineno} is a relative import "
                            f"({'.' * level}): {written[:60]}")
        return Satisfied(f"{path}:{lineno} imports absolutely: {written[:60]}")


@rule(
    id="SCIKIT-LEARN-C185",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
)
class NoStarImports:
    """Pre-condition: each import statement the agent wrote in package code.
    Pass condition: it is not a star import.

    A prohibition with the antecedent on the permitted act (§7.1). Not heuristic: `import
    *` is a syntactic form, and the guide's "in any case" overrides the section's own
    exception clause, so there is nothing left to approximate.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in _package_modules(b):
            for node in ast.walk(module.tree):
                if not isinstance(node, (ast.Import, ast.ImportFrom)):
                    continue
                if not own.owns_span(b, path, (node.lineno, node.lineno), "touched"):
                    continue
                star = isinstance(node, ast.ImportFrom) and any(
                    alias.name == "*" for alias in node.names)
                out.append(target(f"star-import:{path}:{node.lineno}", path,
                                  (node.lineno, node.lineno),
                                  (path, node.lineno, star, _source(node)),
                                  _source(node)[:80]))
        return out

    def pass_condition(self, t: Target):
        path, lineno, star, written = t.payload
        if star:
            return Violated(f"{path}:{lineno} uses a star import: {written[:60]}")
        return Satisfied(f"{path}:{lineno} imports names explicitly: {written[:60]}")


@rule(
    id="SCIKIT-LEARN-C189",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class InputValidationAvoidsAsanyarrayAndAtleast2d:
    """Pre-condition: each function in package code the agent wrote or edited that
    converts an array-like argument.
    Pass condition: it uses neither `np.asanyarray` nor `np.atleast_2d`.

    A prohibition with the antecedent on the permitted act -- converting input at all --
    so a compliant `np.asarray` can be recorded (§7.1). Heuristic on the **pre-condition**
    (§6.3): "for input validation" is approximated by the conversion helpers appearing in
    the function, and a call made for some other purpose is selected too.
    """

    CONVERTERS = ("asarray", "asanyarray", "atleast_2d", "check_array", "array")
    FORBIDDEN = ("asanyarray", "atleast_2d")

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, function in _owned_package_functions(b):
            called = [c.split(".")[-1] for c in calls_in(function.node)]
            if not set(called) & set(self.CONVERTERS):
                continue
            out.append(target(f"asanyarray:{path}:{function.qualname}", path,
                              function.span(), (path, function, called),
                              f"{path}::{function.qualname}"))
        return out

    def pass_condition(self, t: Target):
        path, function, called = t.payload
        forbidden = [c for c in called if c in self.FORBIDDEN]
        if forbidden:
            return Violated(f"{path}::{function.qualname} validates input with "
                            f"`np.{forbidden[0]}`, which lets np.matrix through")
        return Satisfied(f"{path}::{function.qualname} converts input without "
                         f"asanyarray or atleast_2d")


@rule(
    id="SCIKIT-LEARN-C190",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class PublicApiFunctionsCallCheckArray:
    """Pre-condition: each public module-level function in package code the agent wrote or
    edited that takes an array-like argument.
    Pass condition: it calls `check_array`, or one of the helpers that wraps it.

    Heuristic on the **pre-condition** (§6.3): "an array-like argument passed to a
    scikit-learn API function" is approximated by a public function taking a parameter
    named `X`, `y` or `array`, which is the project's own naming, so an array arriving
    under a different name is not selected.
    """

    ARRAY_ARGS = ("X", "y", "array", "Xt", "data")

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, function in _owned_package_functions(b):
            if function.name.startswith("_") or "." in function.qualname:
                continue
            if not set(parameters(function.node)) & set(self.ARRAY_ARGS):
                continue
            out.append(target(f"check-array:{path}:{function.qualname}", path,
                              function.span(), (path, function),
                              f"{path}::{function.qualname}"))
        return out

    def pass_condition(self, t: Target):
        path, function = t.payload
        called = {c.split(".")[-1] for c in calls_in(function.node)}
        if used := called & set(VALIDATION_HELPERS):
            return Satisfied(f"{path}::{function.qualname} validates its input with "
                             f"`{sorted(used)[0]}`")
        return Violated(f"{path}::{function.qualname} is public API taking an array-like "
                        f"argument and never calls check_array")


@rule(
    id="SCIKIT-LEARN-C191",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class PackageCodeAvoidsTheGlobalRng:
    """Pre-condition: each function in package code the agent wrote or edited that draws
    random numbers.
    Pass condition: it does so through an explicit generator, not a module-level routine.

    The same prohibition C232 states for tests, and kept separate because the corpus states
    it separately: this one selects package code (`tests=False`) and C232 selects tests, so
    a violation is reported once (§7.5). Heuristic on the **pre-condition** (§6.3):
    randomness is recognised from call names in the body.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, function in _owned_package_functions(b):
            called = calls_in(function.node)
            if not any(_GLOBAL_RNG.match(c) or c.split(".")[-1] in RNG_BUILDERS
                       for c in called):
                continue
            out.append(target(f"global-rng:{path}:{function.qualname}", path,
                              function.span(), (path, function, called),
                              f"{path}::{function.qualname}"))
        return out

    def pass_condition(self, t: Target):
        path, function, called = t.payload
        offending = [c for c in called if _GLOBAL_RNG.match(c)]
        if offending:
            return Violated(f"{path}::{function.qualname} calls `{offending[0]}`, a "
                            f"module-level RNG routine, so results are not repeatable")
        builder = [c for c in called if c.split(".")[-1] in RNG_BUILDERS]
        return Satisfied(f"{path}::{function.qualname} draws from an explicit generator "
                         f"built with `{builder[0]}`")


@rule(
    id="SCIKIT-LEARN-C192",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class RandomRoutinesTakeARandomStateKeyword:
    """Pre-condition: each module-level function in package code the agent wrote or edited
    that draws random numbers.
    Pass condition: it takes a `random_state` keyword and builds a generator from it.

    Heuristic on the **pre-condition** (§6.3): "your code depends on a random number
    generator" is approximated by the RNG call names appearing in the function body. The
    pass condition names both halves the guide states -- the keyword and the construction
    -- and `check_random_state` counts as the construction, since the guide points at it.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, function in _owned_package_functions(b):
            if "." in function.qualname:
                continue
            called = calls_in(function.node)
            if not any(_GLOBAL_RNG.match(c) or c.split(".")[-1] in RNG_BUILDERS
                       for c in called):
                continue
            out.append(target(f"random-state-kw:{path}:{function.name}", path,
                              function.span(), (path, function, called),
                              f"{path}::{function.name}"))
        return out

    def pass_condition(self, t: Target):
        path, function, called = t.payload
        if "random_state" not in parameters(function.node):
            return Violated(f"{path}::{function.name} draws random numbers without "
                            f"accepting a `random_state` keyword")
        builder = [c for c in called if c.split(".")[-1] in RNG_BUILDERS]
        if not builder:
            return Violated(f"{path}::{function.name} takes `random_state` but never "
                            f"builds a RandomState from it")
        return Satisfied(f"{path}::{function.name} takes `random_state` and builds its "
                         f"generator with `{builder[0]}`")


@rule(
    id="SCIKIT-LEARN-C193",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class RandomEstimatorsTakeRandomStateDefaultingToNone:
    """Pre-condition: each estimator the agent wrote or edited that uses randomness.
    Pass condition: its `__init__` takes `random_state`, defaulting to `None`.

    Heuristic on the **pre-condition** (§6.3): "uses randomness in an estimator" is
    approximated by an RNG call anywhere in the class, or by the keyword already being
    there -- the second is included so that an estimator which takes the keyword and gets
    the default wrong can still be selected and graded (§7.1).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in estimators(b):
            initialiser = info.method("__init__")
            if initialiser is None:
                continue
            uses_rng = any(_GLOBAL_RNG.match(c) or c.split(".")[-1] in RNG_BUILDERS
                           for node in info.methods.values() for c in calls_in(node))
            if not uses_rng and "random_state" not in parameters(initialiser):
                continue
            out.append(method_target(path, info, "__init__", initialiser,
                                     "random-state-init"))
        return out

    def pass_condition(self, t: Target):
        path, info, name, node = t.payload
        if "random_state" not in parameters(node):
            return Violated(f"{path}::{info.name}.__init__ takes no `random_state` "
                            f"argument although the estimator uses randomness")
        default = keyword_defaults(node).get("random_state")
        if default is None or _source(default) != "None":
            return Violated(f"{path}::{info.name}.__init__ takes `random_state` without "
                            f"the required default of None")
        return Satisfied(f"{path}::{info.name}.__init__ takes `random_state=None`")


@rule(
    id="SCIKIT-LEARN-C194",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class RandomStateIsStoredUnmodified:
    """Pre-condition: each estimator `__init__` the agent wrote or edited that takes
    `random_state`.
    Pass condition: it assigns `self.random_state = random_state`, unchanged.

    Heuristic on the **pre-condition** (§6.3) only: the estimator proxy. The grading is
    exact -- the attribute's name and the assigned expression are both read from the AST,
    and anything other than the bare parameter is a modification.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in estimators(b):
            initialiser = info.method("__init__")
            if initialiser is None or "random_state" not in parameters(initialiser):
                continue
            out.append(method_target(path, info, "__init__", initialiser,
                                     "random-state-attribute"))
        return out

    def pass_condition(self, t: Target):
        path, info, name, node = t.payload
        assigned = self_assignments(node)
        if "random_state" not in assigned:
            return Violated(f"{path}::{info.name}.__init__ takes `random_state` but "
                            f"stores no attribute of that name")
        written = _source(assigned["random_state"])
        if written != "random_state":
            return Violated(f"{path}::{info.name}.__init__ stores "
                            f"`self.random_state = {written[:40]}` rather than the "
                            f"argument unmodified")
        return Satisfied(f"{path}::{info.name}.__init__ stores random_state unmodified")


@rule(
    id="SCIKIT-LEARN-C196",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class PostFitGeneratorsLiveInRandomStateUnderscore:
    """Pre-condition: each estimator `fit` the agent wrote or edited that builds a
    generator.
    Pass condition: the generator is stored as `random_state_`.

    Heuristic on the **pre-condition** (§6.3): "randomness is needed after fit" is
    approximated by `fit` constructing a generator at all, which is a superset -- a fit
    that builds one and uses it only locally does not need to store it. The wider scope is
    the right direction of error (§4.5), and the attribute name is exact.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in estimators(b):
            fit = info.method("fit")
            if fit is None:
                continue
            if not any(c.split(".")[-1] in RNG_BUILDERS for c in calls_in(fit)):
                continue
            out.append(method_target(path, info, "fit", fit, "random-state-fitted"))
        return out

    def pass_condition(self, t: Target):
        path, info, name, node = t.payload
        if "random_state_" in self_assignments(node):
            return Satisfied(f"{path}::{info.name}.fit stores its generator in "
                             f"random_state_")
        return Violated(f"{path}::{info.name}.fit builds a generator but does not store "
                        f"it in random_state_, so it is unavailable after fit")


# --- F. Display classes and plotting -------------------------------------------------


def _displays(bundle: EvidenceBundle):
    return [(p, m, c) for p, m, c in owned_classes(bundle, tests=False) if is_display(c)]


@rule(
    id="SCIKIT-LEARN-C199",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a property every Display class must have
    reads=("files",),  # spec §5
    heuristic=True,
)
class DisplaysDefineAConstructorClassMethod:
    """Pre-condition: each `Display` class the agent wrote or edited.
    Pass condition: it defines `from_estimator`, `from_predictions`, or both.

    Heuristic on the **pre-condition** (§6.3): a Display is recognised by the `Display`
    suffix the project uses, or by defining a `plot` method, since nothing marks the type.
    The pass condition is exact -- two named class methods, one of which must exist.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [class_target(path, info, "display-constructors")
                for path, _module, info in _displays(b)]

    def pass_condition(self, t: Target):
        path, info = t.payload
        defined = [n for n in ("from_estimator", "from_predictions") if n in info.methods]
        if defined:
            return Satisfied(f"{path}::{info.name} defines {', '.join(defined)}")
        return Violated(f"{path}::{info.name} is a Display class but defines neither "
                        f"from_estimator nor from_predictions")


@rule(
    id="SCIKIT-LEARN-C200",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class DisplayInitTakesOnlyComputedData:
    """Pre-condition: each `Display` class `__init__` the agent wrote or edited.
    Pass condition: it takes no estimator or raw data, and computes nothing.

    Heuristic on **both layers** (§6.3, §6.2): the Display proxy, and "only the data
    needed to create the visualization" is graded as *no estimator or `X`/`y` parameter,
    and no call in the body* -- the same shape the estimator rule C141 uses, because the
    guide states the same separation of computation from construction.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in _displays(b):
            initialiser = info.method("__init__")
            if initialiser is not None:
                out.append(method_target(path, info, "__init__", initialiser,
                                         "display-init"))
        return out

    def pass_condition(self, t: Target):
        path, info, name, node = t.payload
        offending = [p for p in parameters(node)
                     if p in TRAINING_DATA_ARGS or p == "estimator"]
        if offending:
            return Violated(f"{path}::{info.name}.__init__ takes `{offending[0]}`; a "
                            f"Display's constructor takes only the computed data")
        for statement in node.body:
            for child in ast.walk(statement):
                if isinstance(child, ast.Call):
                    return Violated(f"{path}::{info.name}.__init__ computes "
                                    f"`{_source(child.func)}` on line {child.lineno}; "
                                    f"the calculation belongs to the class method")
        return Satisfied(f"{path}::{info.name}.__init__ stores the computed data and "
                         f"nothing else")


@rule(
    id="SCIKIT-LEARN-C201",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class DisplayPlotTakesOnlyVisualisationParameters:
    """Pre-condition: each `Display.plot` the agent wrote or edited.
    Pass condition: none of its parameters is an estimator or raw data.

    Heuristic on **both layers** (§6.3, §6.2): the Display proxy, and "only have to do
    with visualization" is graded as the complement of the computation arguments -- an
    estimator, `X`, `y` -- since the space of legitimate styling parameters is open and
    cannot be enumerated.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in _displays(b):
            node = info.method("plot")
            if node is not None:
                out.append(method_target(path, info, "plot", node, "display-plot-params"))
        return out

    def pass_condition(self, t: Target):
        path, info, name, node = t.payload
        offending = [p for p in parameters(node)
                     if p in TRAINING_DATA_ARGS or p == "estimator"]
        if offending:
            return Violated(f"{path}::{info.name}.plot takes `{offending[0]}`, which is "
                            f"a computation argument rather than a visualization one")
        return Satisfied(f"{path}::{info.name}.plot takes only visualization parameters")


@rule(
    id="SCIKIT-LEARN-C202",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class DisplayPlotStoresItsArtists:
    """Pre-condition: each `Display.plot` the agent wrote or edited.
    Pass condition: it stores at least one artist as a trailing-underscore attribute.

    Heuristic on the **pass condition** (§6.2): "the matplotlib artists" are recognised by
    the project's own convention for them -- an attribute whose name ends in an underscore,
    as `self.ax_`, `self.figure_` and `self.line_` do in the worked `RocCurveDisplay` --
    so a plot storing its artists under other names reads as a violation.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in _displays(b):
            node = info.method("plot")
            if node is not None:
                out.append(method_target(path, info, "plot", node, "display-artists"))
        return out

    def pass_condition(self, t: Target):
        path, info, name, node = t.payload
        stored = [a for a in self_assignments(node) if a.endswith("_")]
        if stored:
            return Satisfied(f"{path}::{info.name}.plot stores its artists as "
                             f"{', '.join(sorted(stored)[:3])}")
        return Violated(f"{path}::{info.name}.plot stores no artist on the display, so "
                        f"its style cannot be adjusted afterwards")


@rule(
    id="SCIKIT-LEARN-C203",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class DisplayClassMethodsReturnThePlot:
    """Pre-condition: each `from_estimator` or `from_predictions` the agent wrote or
    edited on a `Display` class.
    Pass condition: it returns the result of calling `plot`.

    Heuristic on the **pre-condition** (§6.3) only: the Display proxy. The grading follows
    the guide's worked ending -- `return viz.plot()` -- and reads the returned expression
    for a `.plot(` call, which is exact for that shape.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in _displays(b):
            for name in ("from_estimator", "from_predictions"):
                node = info.method(name)
                if node is not None:
                    out.append(method_target(path, info, name, node, "display-returns"))
        return out

    def pass_condition(self, t: Target):
        path, info, name, node = t.payload
        for child in ast.walk(node):
            if not isinstance(child, ast.Return) or child.value is None:
                continue
            written = _source(child.value)
            if ".plot(" in written:
                return Satisfied(f"{path}::{info.name}.{name} returns `{written[:40]}`")
            return Violated(f"{path}::{info.name}.{name} returns `{written[:40]}` rather "
                            f"than the result of the display's plot method")
        return Violated(f"{path}::{info.name}.{name} returns nothing, so the caller gets "
                        f"no display back")


@rule(
    id="SCIKIT-LEARN-C204",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class DisplayPlotValidatesTheNumberOfAxes:
    """Pre-condition: each `Display.plot` the agent wrote or edited that takes an `ax`
    parameter.
    Pass condition: it checks how many axes it was given before drawing.

    Heuristic on the **pass condition** (§6.2): "check if the number of axes is consistent
    with the number it expects" is recognised by the body measuring `ax` -- a `len(...)`,
    a `.size`, or an `isinstance` test against a list -- so a check written another way
    reads as a violation. The pre-condition is exact: a parameter named `ax`.
    """

    AXES_CHECK = re.compile(r"len\s*\(\s*ax|isinstance\s*\(\s*ax|np\.size\s*\(\s*ax|"
                            r"ax\.(size|shape|ravel|flatten)\b")

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in _displays(b):
            node = info.method("plot")
            if node is None or "ax" not in parameters(node):
                continue
            out.append(method_target(path, info, "plot", node, "display-axes"))
        return out

    def pass_condition(self, t: Target):
        path, info, name, node = t.payload
        if self.AXES_CHECK.search(_source(node)):
            return Satisfied(f"{path}::{info.name}.plot checks how many axes it was "
                             f"given")
        return Violated(f"{path}::{info.name}.plot accepts `ax` without checking that the "
                        f"number of axes matches what it draws")


@rule(
    id="SCIKIT-LEARN-C206",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a property of package modules that use matplotlib
    reads=("files",),  # spec §5
)
class MatplotlibIsImportedInsideThePlottingFunction:
    """Pre-condition: each package module the agent edited that imports matplotlib.
    Pass condition: no matplotlib import sits at module level.

    Not heuristic: an import's nesting is a syntactic fact, and matplotlib is named
    exactly. Fires on the module importing matplotlib at all, so a module doing it
    correctly -- inside the plotting function -- is recorded as a pass rather than skipped
    (§7.1).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in _package_modules(b):
            imports = [node for node in ast.walk(module.tree)
                       if isinstance(node, (ast.Import, ast.ImportFrom))
                       and "matplotlib" in (_source(node) or "")]
            if not imports:
                continue
            top_level = [node for node in module.tree.body
                         if isinstance(node, (ast.Import, ast.ImportFrom))
                         and "matplotlib" in (_source(node) or "")]
            out.append(target(f"mpl-import:{path}", path, None,
                              (path, imports, top_level),
                              f"{len(imports)} matplotlib import(s)"))
        return out

    def pass_condition(self, t: Target):
        path, imports, top_level = t.payload
        if top_level:
            return Violated(f"{path}:{top_level[0].lineno} imports matplotlib at module "
                            f"level, which makes it a hard dependency of the package")
        return Satisfied(f"{path} imports matplotlib only inside its plotting "
                         f"function(s)")


@rule(
    id="SCIKIT-LEARN-C207",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
)
class CheckMatplotlibSupportComesFirst:
    """Pre-condition: each function the agent wrote or edited that imports matplotlib
    inside itself.
    Pass condition: a `check_matplotlib_support` call appears above that import.

    Not heuristic: both the call and the import are statements with line numbers, and the
    guide's "before importing it" is exactly their order. The antecedent is the local
    import, which is the situation the sentence addresses.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, function in _owned_package_functions(b):
            imports = [node for node in ast.walk(function.node)
                       if isinstance(node, (ast.Import, ast.ImportFrom))
                       and "matplotlib" in (_source(node) or "")]
            if not imports:
                continue
            out.append(target(f"mpl-support:{path}:{function.qualname}", path,
                              function.span(), (path, function, imports),
                              f"{path}::{function.qualname}"))
        return out

    def pass_condition(self, t: Target):
        path, function, imports = t.payload
        first_import = min(node.lineno for node in imports)
        checks = [call for call in ast.walk(function.node)
                  if isinstance(call, ast.Call)
                  and _source(call.func).split(".")[-1] == "check_matplotlib_support"]
        if any(call.lineno < first_import for call in checks):
            return Satisfied(f"{path}::{function.qualname} calls check_matplotlib_support "
                             f"before importing matplotlib")
        if checks:
            return Violated(f"{path}::{function.qualname} calls check_matplotlib_support "
                            f"at line {checks[0].lineno}, after the import at line "
                            f"{first_import}")
        return Violated(f"{path}::{function.qualname} imports matplotlib at line "
                        f"{first_import} without calling check_matplotlib_support first")


# --- G. callbacks --------------------------------------------------------------------


def _callbacks(bundle: EvidenceBundle):
    return [(p, m, c) for p, m, c in owned_classes(bundle, tests=False) if is_callback(c)]


def _hook_methods(bundle: EvidenceBundle):
    for path, _module, info in _callbacks(bundle):
        for name in HOOKS:
            node = info.method(name)
            if node is not None:
                yield path, info, name, node


@rule(
    id="SCIKIT-LEARN-C221",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class CallbackSupportComesFromTheMixin:
    """Pre-condition: each estimator the agent wrote or edited that uses the callback
    machinery.
    Pass condition: it inherits `CallbackSupportMixin`.

    Heuristic on the **pre-condition** (§6.3): "supports callbacks" is recognised by any
    of the three marks the page describes -- the mixin, a `_init_callback_context` call in
    `fit`, or a `with_callbacks` decorator -- so a class calling into the machinery without
    the mixin is selected and fails, which is the rule's content (§7.1).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [class_target(path, info, "callback-mixin")
                for path, _module, info in estimators(b) if has_callback_support(info)]

    def pass_condition(self, t: Target):
        path, info = t.payload
        if info.inherits("CallbackSupportMixin"):
            return Satisfied(f"{path}::{info.name} inherits CallbackSupportMixin")
        return Violated(f"{path}::{info.name} uses the callback machinery without "
                        f"inheriting CallbackSupportMixin")


@rule(
    id="SCIKIT-LEARN-C222",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class FitCreatesTheRootCallbackContext:
    """Pre-condition: each callback-supporting estimator's `fit` the agent wrote or edited.
    Pass condition: it calls `_init_callback_context`.

    Heuristic on the **pre-condition** (§6.3): the callback-support proxy. The sentence
    also says *at the beginning of fit*, and position is deliberately not graded -- a call
    placed after input validation is idiomatic in this codebase, and reporting it would
    manufacture violations. Stated here rather than left implicit.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in estimators(b):
            fit = info.method("fit")
            if fit is None or not (has_callback_support(info)
                                   or info.inherits("CallbackSupportMixin")):
                continue
            out.append(method_target(path, info, "fit", fit, "callback-context"))
        return out

    def pass_condition(self, t: Target):
        path, info, name, node = t.payload
        if "_init_callback_context" in {c.split(".")[-1] for c in calls_in(node)}:
            return Satisfied(f"{path}::{info.name}.fit creates the root callback context")
        return Violated(f"{path}::{info.name}.fit never calls _init_callback_context, so "
                        f"no root context exists for the registered callbacks")


@rule(
    id="SCIKIT-LEARN-C223",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class ThirdPartyFitCarriesWithCallbacks:
    """Pre-condition: each callback-supporting estimator the agent wrote or edited
    **outside** the `sklearn/` package.
    Pass condition: its `fit` is decorated `with_callbacks`.

    Partitioned against C224 by location (§7.5): the guide gives one instruction for
    third-party estimators and the opposite one for built-in ones, so this rule selects
    only classes outside the package and C224 only those inside it. Heuristic on the
    **pre-condition** (§6.3): "third-party" is approximated by the file's path, which is
    the only signal a patch carries.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in owned_classes(b, tests=False):
            if path.startswith(PACKAGE) or not is_estimator(info):
                continue
            if not has_callback_support(info):
                continue
            fit = info.method("fit")
            if fit is None:
                continue
            out.append(method_target(path, info, "fit", fit, "with-callbacks"))
        return out

    def pass_condition(self, t: Target):
        path, info, name, node = t.payload
        if any("with_callbacks" in d for d in decorator_names(node)):
            return Satisfied(f"{path}::{info.name}.fit is decorated with_callbacks")
        return Violated(f"{path}::{info.name} is a third-party callback-supporting "
                        f"estimator whose fit is not decorated with_callbacks, so "
                        f"callbacks are not torn down on error")


@rule(
    id="SCIKIT-LEARN-C224",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class BuiltInEstimatorsDoNotUseWithCallbacks:
    """Pre-condition: each callback-supporting estimator the agent wrote or edited
    **inside** the `sklearn/` package.
    Pass condition: its `fit` is not decorated `with_callbacks`.

    The complement of C223, partitioned by the same path test (§7.5). A prohibition with
    its antecedent on the permitted act -- writing a built-in estimator with callback
    support -- so a compliant one is recorded rather than skipped (§7.1). Heuristic on the
    **pre-condition** (§6.3): the callback-support proxy.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in estimators(b):
            if not has_callback_support(info):
                continue
            fit = info.method("fit")
            if fit is None:
                continue
            out.append(method_target(path, info, "fit", fit, "no-with-callbacks"))
        return out

    def pass_condition(self, t: Target):
        path, info, name, node = t.payload
        if any("with_callbacks" in d for d in decorator_names(node)):
            return Violated(f"{path}::{info.name}.fit uses with_callbacks, but "
                            f"_fit_context already tears callbacks down for built-in "
                            f"estimators")
        return Satisfied(f"{path}::{info.name}.fit leaves the teardown to _fit_context")


@rule(
    id="SCIKIT-LEARN-C225",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class CallbacksImplementTheWholeProtocol:
    """Pre-condition: each callback class the agent wrote or edited.
    Pass condition: it defines `setup`, `on_fit_task_begin`, `on_fit_task_end` and
    `teardown`.

    Heuristic on the **pre-condition** (§6.3): a callback is recognised by the `Callback`
    suffix, the protocol as a base, or one of the hooks being defined -- so a class with
    two of the four is selected and fails, which is the rule's content. The protocol
    itself is given in full by the page, so the pass condition is a closed list.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [class_target(path, info, "fit-callback")
                for path, _module, info in _callbacks(b)]

    def pass_condition(self, t: Target):
        path, info = t.payload
        missing = [name for name in FIT_CALLBACK_PROTOCOL if name not in info.methods]
        if missing:
            return Violated(f"{path}::{info.name} implements the FitCallback protocol "
                            f"without {', '.join(missing)}")
        return Satisfied(f"{path}::{info.name} implements all four FitCallback hooks")


@rule(
    id="SCIKIT-LEARN-C226",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class HooksDeclareOnlyTheArgumentsTheyUse:
    """Pre-condition: each callback hook the agent wrote or edited that declares optional
    keyword arguments.
    Pass condition: every one of them is referenced in the hook's body.

    Heuristic on the **pass condition** (§6.2): "actually used by the hook" is graded as
    the name appearing in the body, so an argument passed straight through to `**kwargs`
    or consumed by a helper is credited as used -- the wider reading, which errs towards
    not manufacturing violations (§4.5).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, info, name, node in _hook_methods(b):
            optional = [a.arg for a in node.args.kwonlyargs]
            optional += [p for p in parameters(node)
                         if p in keyword_defaults(node) and p != "self"]
            if optional:
                out.append(method_target(path, info, name, node, "hook-arguments",
                                         (path, info, name, node, sorted(set(optional)))))
        return out

    def pass_condition(self, t: Target):
        path, info, name, node, optional = t.payload
        body = "\n".join(_source(statement) for statement in node.body)
        unused = [a for a in optional if not re.search(rf"\b{re.escape(a)}\b", body)]
        if unused:
            return Violated(f"{path}::{info.name}.{name} declares `{unused[0]}` and never "
                            f"uses it, so the framework computes a value nobody reads")
        return Satisfied(f"{path}::{info.name}.{name} uses all {len(optional)} optional "
                         f"argument(s) it declares")


@rule(
    id="SCIKIT-LEARN-C227",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class HookOptionalArgumentsAreKeywordOnly:
    """Pre-condition: each callback hook the agent wrote or edited that declares an
    argument with a default.
    Pass condition: every such argument is keyword-only.

    Heuristic on the **pre-condition** (§6.3): a hook is recognised by its name, one of
    the two the protocol publishes. The grading is exact -- the AST distinguishes
    `kwonlyargs` from ordinary parameters -- and the failure mode is stated in the guide's
    own warning: the values are silently not provided.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, info, name, node in _hook_methods(b):
            defaulted = [p for p in parameters(node) if p in keyword_defaults(node)]
            if defaulted or node.args.kwonlyargs:
                out.append(method_target(path, info, name, node, "keyword-only",
                                         (path, info, name, node, defaulted)))
        return out

    def pass_condition(self, t: Target):
        path, info, name, node, defaulted = t.payload
        if defaulted:
            return Violated(f"{path}::{info.name}.{name} declares `{defaulted[0]}` as a "
                            f"positional argument with a default; hook arguments must be "
                            f"keyword only or their values are not provided")
        return Satisfied(f"{path}::{info.name}.{name} declares its "
                         f"{len(node.args.kwonlyargs)} optional argument(s) keyword only")


@rule(
    id="SCIKIT-LEARN-C229",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class HooksDoNotPredictOnTheEstimatorTheyReceive:
    """Pre-condition: each callback hook the agent wrote or edited that receives an
    `estimator`.
    Pass condition: it calls neither `predict` nor `transform` on it.

    A prohibition with its antecedent on the permitted act -- receiving the estimator --
    so a hook that uses it correctly is recorded (§7.1). Heuristic on the **pass
    condition** (§6.2): the call is matched on the receiver's name, so an estimator bound
    to a local variable first is not tracked.
    """

    FORBIDDEN = re.compile(r"\bestimator\s*\.\s*(predict|transform|predict_proba|"
                           r"decision_function|score)\s*\(")

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, info, name, node in _hook_methods(b):
            names = parameters(node) + [a.arg for a in node.args.kwonlyargs]
            if "estimator" not in names:
                continue
            out.append(method_target(path, info, name, node, "hook-estimator"))
        return out

    def pass_condition(self, t: Target):
        path, info, name, node = t.payload
        if match := self.FORBIDDEN.search(_source(node)):
            return Violated(f"{path}::{info.name}.{name} calls "
                            f"`{match.group(0).strip()}` on the estimator it receives, "
                            f"which is not fully fitted; use fitted_estimator")
        return Satisfied(f"{path}::{info.name}.{name} does not predict or transform on "
                         f"the estimator it receives")


@rule(
    id="SCIKIT-LEARN-C230",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class AutoPropagatedCallbacksImplementTheirProtocol:
    """Pre-condition: each callback the agent wrote or edited that is meant to propagate
    to sub-estimators.
    Pass condition: it implements the `AutoPropagatedCallback` protocol -- the base plus
    `max_propagation_depth`.

    Heuristic on the **pre-condition** (§6.3): "meant to be propagated" is an intention,
    recognised by *either* mark the protocol leaves -- the base class or the one member it
    adds -- so a callback carrying one and not the other is selected and fails, which is
    the rule's content (§7.1).
    """

    MEMBER = "max_propagation_depth"

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in _callbacks(b):
            declares = (_class_attribute(info, self.MEMBER) is not None
                        or self.MEMBER in info.methods)
            if not (declares or info.inherits("AutoPropagatedCallback")):
                continue
            out.append(class_target(path, info, "auto-propagated",
                                    (path, info, declares)))
        return out

    def pass_condition(self, t: Target):
        path, info, declares = t.payload
        if not info.inherits("AutoPropagatedCallback"):
            return Violated(f"{path}::{info.name} declares {self.MEMBER} but does not "
                            f"implement the AutoPropagatedCallback protocol")
        if not declares:
            return Violated(f"{path}::{info.name} implements AutoPropagatedCallback "
                            f"without the {self.MEMBER} member the protocol adds")
        return Satisfied(f"{path}::{info.name} implements AutoPropagatedCallback with "
                         f"{self.MEMBER}")


@rule(
    id="SCIKIT-LEARN-C231",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class SetupAndTeardownDoNotResetState:
    """Pre-condition: each `setup` or `teardown` the agent wrote or edited on a callback.
    Pass condition: it assigns no attribute an empty or zero value.

    A prohibition with its antecedent on the permitted act -- defining the lifecycle hooks
    -- so a callback that accumulates correctly is recorded (§7.1). Heuristic on the
    **pass condition** (§6.2): "reset the state" is recognised as assigning an empty
    container, `0` or `None` to an instance attribute, which is what a reset looks like;
    a reset performed by calling `.clear()` on a stored collection is caught too, but one
    routed through a helper is not.
    """

    RESET_VALUES = ("[]", "{}", "()", "0", "None", "set()", "list()", "dict()",
                    "defaultdict(list)")

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in _callbacks(b):
            for name in ("setup", "teardown"):
                node = info.method(name)
                if node is not None:
                    out.append(method_target(path, info, name, node, "no-reset"))
        return out

    def pass_condition(self, t: Target):
        path, info, name, node = t.payload
        for attribute, value in self_assignments(node).items():
            if _source(value).strip() in self.RESET_VALUES:
                return Violated(f"{path}::{info.name}.{name} resets `{attribute}` to "
                                f"`{_source(value)}`, dropping what earlier fits "
                                f"collected")
        for child in ast.walk(node):
            if (isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute)
                    and child.func.attr == "clear"
                    and _source(child.func.value).startswith("self.")):
                return Violated(f"{path}::{info.name}.{name} clears "
                                f"`{_source(child.func.value)}`, dropping what earlier "
                                f"fits collected")
        return Satisfied(f"{path}::{info.name}.{name} leaves the callback's state intact "
                         f"so it accumulates across fits")
