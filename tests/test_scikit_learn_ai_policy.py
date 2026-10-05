"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

**C001 has no satisfying case, and that is not an omission.** It is marked
``by_construction``: the subject under test is the fully-automated tool the rule
prohibits, so its three cases are violated, violated-again-despite-a-claim, and no target
(§9's alternative triple for a rule the subject cannot pass).

C255 and C256 take a disclosure being present as their antecedent, so a run with no
disclosure at all finds no target in either -- that absence is C254's finding, and
counting it three times would depress three rates for one defect.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.scikit_learn.ai_policy  # noqa: F401  (registers the rules)
from compliance.rules.scikit_learn.ai_policy import DISCLOSURE

RULES = {r.id: r for r in registered()}
CODE = make_file("sklearn/svm/_base.py", [(10, "x = 1")])

FULL_LIST = ("I used AI assistance for:\n"
             "- Code generation\n"
             "- Test/benchmark generation\n"
             "- Documentation (including examples)\n"
             "- Research and understanding\n")
EDITED_LIST = "I used AI assistance for:\n- Code generation\n"


@pytest.fixture(scope="module")
def corpus():
    """scikit-learn's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("scikit-learn"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C001 no fully-automated pull request (by_construction) ---------------------------


def test_c001_fails_for_an_agent_run(corpus):
    row = verdict("SCIKIT-LEARN-C001", make_bundle(files=[CODE]), corpus)
    assert row.verdict == "fail" and row.by_construction


def test_c001_fails_even_when_the_agent_claims_a_human_reviewed_it(corpus):
    """The claim is not evidence: the harness recorded who wrote the patch."""
    bundle = make_bundle(files=[CODE], pr_text="Reviewed line by line by a maintainer.")
    assert verdict("SCIKIT-LEARN-C001", bundle, corpus).verdict == "fail"


def test_c001_finds_no_target_when_no_model_produced_anything(corpus):
    row = verdict("SCIKIT-LEARN-C001", make_bundle(files=[], model="unknown"), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C252 the AI usage list is edited -------------------------------------------------


def test_c252_passes_on_a_list_edited_down(corpus):
    bundle = make_bundle(files=[CODE], pr_text=EDITED_LIST)
    assert verdict("SCIKIT-LEARN-C252", bundle, corpus).verdict == "pass"


def test_c252_fails_when_the_template_list_is_left_whole(corpus):
    bundle = make_bundle(files=[CODE], pr_text=FULL_LIST)
    assert verdict("SCIKIT-LEARN-C252", bundle, corpus).verdict == "fail"


def test_c252_finds_no_target_without_a_contribution(corpus):
    row = verdict("SCIKIT-LEARN-C252", make_bundle(files=[]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C254 the disclosure is included --------------------------------------------------


def test_c254_passes_when_the_description_discloses_ai(corpus):
    bundle = make_bundle(files=[CODE], pr_text=f"Fix the kernel cache.\n\n{DISCLOSURE}")
    assert verdict("SCIKIT-LEARN-C254", bundle, corpus).verdict == "pass"


def test_c254_fails_when_the_description_says_nothing(corpus):
    bundle = make_bundle(files=[CODE], pr_text="Fix the kernel cache.")
    assert verdict("SCIKIT-LEARN-C254", bundle, corpus).verdict == "fail"


def test_c254_finds_no_target_without_a_contribution(corpus):
    row = verdict("SCIKIT-LEARN-C254", make_bundle(files=[]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C255 the disclosure uses the published wording -----------------------------------


def test_c255_passes_on_the_published_sentence(corpus):
    bundle = make_bundle(files=[CODE], pr_text=f"Fix it.\n\n> {DISCLOSURE}")
    assert verdict("SCIKIT-LEARN-C255", bundle, corpus).verdict == "pass"


def test_c255_fails_on_a_paraphrase(corpus):
    bundle = make_bundle(files=[CODE],
                         pr_text="Fix it.\n\nThis patch was written with AI help.")
    assert verdict("SCIKIT-LEARN-C255", bundle, corpus).verdict == "fail"


def test_c255_finds_no_target_when_nothing_is_disclosed(corpus):
    """A missing disclosure is C254's finding, not a wording defect."""
    row = verdict("SCIKIT-LEARN-C255",
                  make_bundle(files=[CODE], pr_text="Fix the kernel cache."), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C256 the disclosure comes last ---------------------------------------------------


def test_c256_passes_when_the_disclosure_closes_the_description(corpus):
    bundle = make_bundle(files=[CODE], pr_text=f"Fix it.\n\n{DISCLOSURE}\n")
    assert verdict("SCIKIT-LEARN-C256", bundle, corpus).verdict == "pass"


def test_c256_fails_when_prose_follows_it(corpus):
    bundle = make_bundle(files=[CODE],
                         pr_text=f"Fix it.\n\n{DISCLOSURE}\n\nPlease review soon.")
    assert verdict("SCIKIT-LEARN-C256", bundle, corpus).verdict == "fail"


def test_c256_finds_no_target_when_nothing_is_disclosed(corpus):
    row = verdict("SCIKIT-LEARN-C256",
                  make_bundle(files=[CODE], pr_text="Fix the kernel cache."), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0
