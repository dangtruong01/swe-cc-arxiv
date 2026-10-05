"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

Most of the no-target cases here are doing one specific job: showing that the five rules
scoped `created` really are scoped by *span*, not by file. A checker class that was already
in the module and was merely edited must find no target under C066, C069, C070, C100 and
C016, and an edit inside one of its methods is the input that proves it.

C100 carries a second exclusion case: a checker added under `pylint/extensions/` finds no
target, because C054 is the row that governs extension checkers (spec §7.5).
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.pylint_dev.language_style  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
CHECKERS = "pylint/checkers/my_checker.py"

CHECKER = '''\
from pylint.checkers import BaseChecker


class MyChecker(BaseChecker):
    name = "my-checker"
    msgs = {
        "W1234": (
            "Something is wrong",
            "something-wrong",
            "Emitted when something is wrong.",
        ),
    }

    def visit_classdef(self, node):
        self.add_message("something-wrong", node=node)


def register(linter):
    linter.register_checker(MyChecker(linter))
'''


@pytest.fixture(scope="module")
def corpus():
    """pylint-dev's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("pylint-dev"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


def added(path, text):
    """A module the agent wrote from scratch."""
    body = text.split("\n")
    return make_file(path, [(n, line) for n, line in enumerate(body, 1)],
                     head_text=text, is_new=True)


def edited(path, text, *, lines, base=None):
    """A module that already existed, of which the agent wrote ``lines``."""
    body = text.split("\n")
    return make_file(path, [(n, body[n - 1]) for n in lines],
                     head_text=text, base_text=base, is_new=False)


def checker(*, name=True, msgs=None, handler="visit_classdef", emits="something-wrong",
            register_fn=True, extra=""):
    """The fixture checker, varied one component at a time."""
    msgs = msgs if msgs is not None else '''\
    msgs = {
        "W1234": (
            "Something is wrong",
            "something-wrong",
            "Emitted when something is wrong.",
        ),
    }
'''
    lines = ["from pylint.checkers import BaseChecker", "", "",
             "class MyChecker(BaseChecker):"]
    if name:
        lines.append('    name = "my-checker"')
    lines.extend(msgs.rstrip("\n").split("\n"))
    lines.extend(["", f"    def {handler}(self, node):",
                  f'        self.add_message("{emits}", node=node)'])
    if extra:
        lines.extend(["", *extra.rstrip("\n").split("\n")])
    if register_fn:
        lines.extend(["", "", "def register(linter):",
                      "    linter.register_checker(MyChecker(linter))"])
    return "\n".join(lines) + "\n"


# --- C016 a new checker's message id is not already used ------------------------------


TWO_CHECKERS_ONE_ID = '''\
from pylint.checkers import BaseChecker


class FirstChecker(BaseChecker):
    name = "first"
    msgs = {"W1234": ("A", "a-thing", "A.")}


class SecondChecker(BaseChecker):
    name = "second"
    msgs = {"W1234": ("B", "b-thing", "B.")}
'''


def test_c016_passes_when_the_new_message_id_clashes_with_nothing(corpus):
    bundle = make_bundle(files=[added(CHECKERS, CHECKER)])
    assert verdict("PYLINT-DEV-C016", bundle, corpus).verdict == "pass"


def test_c016_fails_when_two_checkers_declare_the_same_id(corpus):
    bundle = make_bundle(files=[added(CHECKERS, TWO_CHECKERS_ONE_ID)])
    row = verdict("PYLINT-DEV-C016", bundle, corpus)
    assert row.verdict == "fail" and "also declared by" in row.notes


def test_c016_finds_no_target_when_the_change_declares_no_message(corpus):
    bundle = make_bundle(files=[edited(CHECKERS, CHECKER, lines=[15])])
    row = verdict("PYLINT-DEV-C016", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C066 a new checker class declares a name -----------------------------------------


def test_c066_passes_when_the_class_declares_a_name(corpus):
    bundle = make_bundle(files=[added(CHECKERS, checker())])
    assert verdict("PYLINT-DEV-C066", bundle, corpus).verdict == "pass"


def test_c066_fails_when_the_class_has_no_name_attribute(corpus):
    bundle = make_bundle(files=[added(CHECKERS, checker(name=False))])
    row = verdict("PYLINT-DEV-C066", bundle, corpus)
    assert row.verdict == "fail" and "no `name` attribute" in row.notes


def test_c066_finds_no_target_when_the_class_was_only_edited(corpus):
    bundle = make_bundle(files=[edited(CHECKERS, CHECKER, lines=[15])])
    row = verdict("PYLINT-DEV-C066", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C067 every emitted message is declared -------------------------------------------


def test_c067_passes_when_the_emitted_symbol_is_declared(corpus):
    bundle = make_bundle(files=[added(CHECKERS, checker())])
    assert verdict("PYLINT-DEV-C067", bundle, corpus).verdict == "pass"


def test_c067_fails_when_the_checker_emits_an_undeclared_symbol(corpus):
    bundle = make_bundle(files=[added(CHECKERS, checker(emits="never-declared"))])
    row = verdict("PYLINT-DEV-C067", bundle, corpus)
    assert row.verdict == "fail" and "never-declared" in row.notes


def test_c067_finds_no_target_when_the_message_name_is_not_a_literal(corpus):
    source = checker().replace('self.add_message("something-wrong", node=node)',
                               "self.add_message(symbol, node=node)")
    row = verdict("PYLINT-DEV-C067", make_bundle(files=[added(CHECKERS, source)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C068 node handlers are named for the lowered astroid class -----------------------


def test_c068_passes_on_a_lowered_class_name(corpus):
    bundle = make_bundle(files=[added(CHECKERS, checker(handler="visit_functiondef"))])
    assert verdict("PYLINT-DEV-C068", bundle, corpus).verdict == "pass"


def test_c068_fails_when_the_node_name_is_spelled_with_underscores(corpus):
    bundle = make_bundle(files=[added(CHECKERS, checker(handler="visit_function_def"))])
    row = verdict("PYLINT-DEV-C068", bundle, corpus)
    assert row.verdict == "fail" and "function_def" in row.notes


def test_c068_finds_no_target_when_the_checker_has_no_node_handler(corpus):
    bundle = make_bundle(files=[added(CHECKERS, checker(handler="close"))])
    row = verdict("PYLINT-DEV-C068", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C069 a module-level register function --------------------------------------------


def test_c069_passes_when_the_module_registers_its_checker(corpus):
    bundle = make_bundle(files=[added(CHECKERS, checker())])
    assert verdict("PYLINT-DEV-C069", bundle, corpus).verdict == "pass"


def test_c069_fails_when_the_module_has_no_register_function(corpus):
    bundle = make_bundle(files=[added(CHECKERS, checker(register_fn=False))])
    row = verdict("PYLINT-DEV-C069", bundle, corpus)
    assert row.verdict == "fail" and "register" in row.notes


def test_c069_finds_no_target_when_no_checker_class_was_added(corpus):
    bundle = make_bundle(files=[edited(CHECKERS, CHECKER, lines=[15])])
    row = verdict("PYLINT-DEV-C069", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C070 the message id's format -----------------------------------------------------


SHORT_ID = '''\
    msgs = {
        "W123": (
            "Something is wrong",
            "something-wrong",
            "Emitted when something is wrong.",
        ),
    }
'''
TWO_IDS = '''\
    msgs = {
        "W1234": ("A", "a-thing", "A."),
        "W1235": ("B", "b-thing", "B."),
    }
'''
MIXED_PREFIXES = '''\
    msgs = {
        "W1234": ("A", "a-thing", "A."),
        "W9901": ("B", "b-thing", "B."),
    }
'''


def test_c070_passes_on_a_category_letter_and_four_digits(corpus):
    bundle = make_bundle(files=[added(CHECKERS, checker())])
    assert verdict("PYLINT-DEV-C070", bundle, corpus).verdict == "pass"


def test_c070_fails_on_a_three_digit_message_id(corpus):
    bundle = make_bundle(files=[added(CHECKERS, checker(msgs=SHORT_ID))])
    row = verdict("PYLINT-DEV-C070", bundle, corpus)
    assert row.verdict == "fail" and "W123" in row.notes


def test_c070_finds_no_target_when_no_message_was_declared(corpus):
    bundle = make_bundle(files=[edited(CHECKERS, CHECKER, lines=[15])])
    row = verdict("PYLINT-DEV-C070", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C072 one two-digit prefix per checker --------------------------------------------


def test_c072_passes_when_the_ids_share_a_prefix(corpus):
    bundle = make_bundle(files=[added(CHECKERS, checker(msgs=TWO_IDS))])
    assert verdict("PYLINT-DEV-C072", bundle, corpus).verdict == "pass"


def test_c072_fails_when_the_checker_mixes_prefixes(corpus):
    bundle = make_bundle(files=[added(CHECKERS, checker(msgs=MIXED_PREFIXES))])
    row = verdict("PYLINT-DEV-C072", bundle, corpus)
    assert row.verdict == "fail" and "mixes message id prefixes" in row.notes


def test_c072_finds_no_target_when_the_checker_declares_one_message(corpus):
    bundle = make_bundle(files=[added(CHECKERS, checker())])
    row = verdict("PYLINT-DEV-C072", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C073 the symbol changes with the id ----------------------------------------------


def renamed(old_id, new_id, old_symbol, new_symbol):
    base = checker(msgs=f'    msgs = {{"{old_id}": ("A", "{old_symbol}", "A.")}}\n',
                   emits=old_symbol)
    head = checker(msgs=f'    msgs = {{"{new_id}": ("A", "{new_symbol}", "A.")}}\n',
                   emits=new_symbol)
    body = head.split("\n")
    return make_file(CHECKERS, [(n, line) for n, line in enumerate(body, 1)],
                     head_text=head, base_text=base, is_new=False)


def test_c073_passes_when_both_the_id_and_the_symbol_changed(corpus):
    bundle = make_bundle(files=[renamed("W1234", "W5678", "old-thing", "new-thing")])
    assert verdict("PYLINT-DEV-C073", bundle, corpus).verdict == "pass"


def test_c073_fails_when_the_id_changed_and_the_symbol_did_not(corpus):
    bundle = make_bundle(files=[renamed("W1234", "W5678", "old-thing", "old-thing")])
    row = verdict("PYLINT-DEV-C073", bundle, corpus)
    assert row.verdict == "fail" and "still declared" in row.notes


def test_c073_finds_no_target_when_no_message_id_went_away(corpus):
    bundle = make_bundle(files=[renamed("W1234", "W1234", "a-thing", "a-thing")])
    row = verdict("PYLINT-DEV-C073", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C075 a shared message says so ----------------------------------------------------


def two_checkers(shared: bool):
    option = ', {"shared": True}' if shared else ""
    return f'''\
from pylint.checkers import BaseChecker


class FirstChecker(BaseChecker):
    name = "first"
    msgs = {{"W1234": ("A", "a-thing", "A."{option})}}


class SecondChecker(BaseChecker):
    name = "second"
    msgs = {{"W1234": ("A", "a-thing", "A."{option})}}
'''


def test_c075_passes_when_both_declarations_set_shared(corpus):
    bundle = make_bundle(files=[added(CHECKERS, two_checkers(shared=True))])
    assert verdict("PYLINT-DEV-C075", bundle, corpus).verdict == "pass"


def test_c075_fails_when_a_shared_message_is_not_flagged(corpus):
    bundle = make_bundle(files=[added(CHECKERS, two_checkers(shared=False))])
    row = verdict("PYLINT-DEV-C075", bundle, corpus)
    assert row.verdict == "fail" and "shared" in row.notes


def test_c075_finds_no_target_when_no_message_is_shared(corpus):
    bundle = make_bundle(files=[added(CHECKERS, checker())])
    row = verdict("PYLINT-DEV-C075", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C076 get_map_data and reduce_map_data as a pair ----------------------------------


PAIR = '''\
    def get_map_data(self):
        return self.stats

    def reduce_map_data(self, linter, data):
        self.stats = data
'''
HALF_PAIR = '''\
    def get_map_data(self):
        return self.stats
'''


def test_c076_passes_when_both_methods_are_defined(corpus):
    bundle = make_bundle(files=[added(CHECKERS, checker(extra=PAIR))])
    assert verdict("PYLINT-DEV-C076", bundle, corpus).verdict == "pass"


def test_c076_fails_when_only_half_the_pair_is_defined(corpus):
    bundle = make_bundle(files=[added(CHECKERS, checker(extra=HALF_PAIR))])
    row = verdict("PYLINT-DEV-C076", bundle, corpus)
    assert row.verdict == "fail" and "matched pair" in row.notes


def test_c076_finds_no_target_when_the_checker_reduces_nothing(corpus):
    bundle = make_bundle(files=[added(CHECKERS, checker())])
    row = verdict("PYLINT-DEV-C076", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C080 the proxy base in an isinstance tuple ---------------------------------------


GUARD = '''\
from astroid import bases, nodes


def check(node):
    if isinstance(node, %s):
        return node.qname()
    return None
'''
REMOVED_GUARD = ("    if hasattr(node, 'qname'):",)


def replaced_guard(types, *, removed=REMOVED_GUARD):
    text = GUARD % types
    return make_file("pylint/checkers/utils.py",
                     [(5, text.split("\n")[4])], head_text=text,
                     removed_lines=removed, is_new=False)


def test_c080_passes_when_the_tuple_names_the_proxy_base(corpus):
    bundle = make_bundle(files=[replaced_guard("(nodes.ClassDef, bases.Instance)")])
    assert verdict("PYLINT-DEV-C080", bundle, corpus).verdict == "pass"


def test_c080_fails_when_the_proxy_base_is_omitted(corpus):
    bundle = make_bundle(files=[replaced_guard("nodes.ClassDef")])
    row = verdict("PYLINT-DEV-C080", bundle, corpus)
    assert row.verdict == "fail" and "proxy base" in row.notes


def test_c080_finds_no_target_when_no_hasattr_guard_was_removed(corpus):
    bundle = make_bundle(files=[replaced_guard("nodes.ClassDef", removed=())])
    row = verdict("PYLINT-DEV-C080", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C100 a new checker class lives under pylint/checkers/ ----------------------------


def test_c100_passes_when_the_class_is_under_checkers(corpus):
    bundle = make_bundle(files=[added(CHECKERS, checker())])
    assert verdict("PYLINT-DEV-C100", bundle, corpus).verdict == "pass"


def test_c100_fails_when_the_class_is_added_elsewhere_in_the_package(corpus):
    bundle = make_bundle(files=[added("pylint/my_checker.py", checker())])
    row = verdict("PYLINT-DEV-C100", bundle, corpus)
    assert row.verdict == "fail" and "outside" in row.notes


def test_c100_finds_no_target_for_an_extension_checker(corpus):
    """The §7.5 exclusion: extension checkers are C054's business, not this rule's."""
    bundle = make_bundle(files=[added("pylint/extensions/my_checker.py", checker())])
    row = verdict("PYLINT-DEV-C100", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0
