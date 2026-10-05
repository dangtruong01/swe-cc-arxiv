"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

The no-target case is doing most of the work in this module. Nearly every rule here fires
on a *kind* of class -- an estimator, a transformer, a classifier, a Display, a callback --
and the third test is what pins that the kind is recognised rather than assumed: an
ordinary class must find no target, or the pack would grade every class in the patch
against the estimator contract.

Three pairs are partitioned rather than overlapping, and each partition is pinned by a
no-target test of its own: C151/C152 by whether the docstring documents the attribute,
C169/C171 by mixin versus `labels_`, and C223/C224 by whether the file is inside
`sklearn/`.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.scikit_learn.language_style  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}


@pytest.fixture(scope="module")
def corpus():
    """scikit-learn's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("scikit-learn"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


def source(text, path="sklearn/svm/_classes.py", base=None, new=False):
    lines = text.split("\n")
    return make_file(path, [(n, line) for n, line in enumerate(lines, 1)],
                     head_text=text, base_text=base, is_new=new)


def edited(text, authored, path="sklearn/svm/_classes.py"):
    """A file that existed before the run, with only ``authored`` lines rewritten."""
    lines = text.split("\n")
    return make_file(path, [(n, lines[n - 1]) for n in authored], head_text=text)


#: An estimator already in the tree; the agent rewrote one line of its fit.
EXISTING_ESTIMATOR = ("class SVC(ClassifierMixin, BaseEstimator):\n"
                      '    """Estimator."""\n'
                      "\n"
                      "    def fit(self, X, y=None):\n"
                      "        self.coef_ = X\n"
                      "        return self\n")


#: An ordinary class, so that "an estimator" is something the pre-conditions must find.
PLAIN_CLASS = source("class Config:\n"
                     '    """Settings."""\n\n'
                     "    def __init__(self, alpha=1.0):\n"
                     "        self.alpha = alpha\n")


# --- C116 / C117 renamed public names --------------------------------------------------

RENAME_BASE = "def zero_one(y, p):\n    return 0\n"

RENAME_KEPT = (
    "from sklearn.utils import deprecated\n"
    "\n"
    '@deprecated("zero_one was deprecated in 0.15 and will be removed in 0.17")\n'
    "def zero_one(y, p):\n"
    "    return zero_one_loss(y, p)\n"
    "\n"
    "def zero_one_loss(y, p):\n"
    "    return 0\n")

RENAME_DROPPED = "def zero_one_loss(y, p):\n    return 0\n"


def test_c116_passes_when_the_old_name_survives_and_warns(corpus):
    bundle = make_bundle(files=[source(RENAME_KEPT, base=RENAME_BASE)])
    assert verdict("SCIKIT-LEARN-C116", bundle, corpus).verdict == "pass"


def test_c116_fails_when_the_old_name_is_deleted(corpus):
    bundle = make_bundle(files=[source(RENAME_DROPPED, base=RENAME_BASE)])
    assert verdict("SCIKIT-LEARN-C116", bundle, corpus).verdict == "fail"


def test_c116_finds_no_target_when_nothing_was_renamed(corpus):
    bundle = make_bundle(files=[source(RENAME_BASE, base=RENAME_BASE)])
    row = verdict("SCIKIT-LEARN-C116", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c117_passes_when_the_shim_delegates(corpus):
    bundle = make_bundle(files=[source(RENAME_KEPT, base=RENAME_BASE)])
    assert verdict("SCIKIT-LEARN-C117", bundle, corpus).verdict == "pass"


def test_c117_fails_when_no_shim_was_left(corpus):
    bundle = make_bundle(files=[source(RENAME_DROPPED, base=RENAME_BASE)])
    assert verdict("SCIKIT-LEARN-C117", bundle, corpus).verdict == "fail"


def test_c117_finds_no_target_when_nothing_was_renamed(corpus):
    bundle = make_bundle(files=[source(RENAME_BASE, base=RENAME_BASE)])
    row = verdict("SCIKIT-LEARN-C117", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C118 the deprecated API reference is updated -------------------------------------

DEPRECATION = source(
    "from sklearn.utils import deprecated\n"
    "\n"
    '@deprecated("deprecated in 0.15, removed in 0.17")\n'
    "def zero_one(y, p):\n"
    '    """Score.\n\n    .. deprecated:: 0.15\n    """\n'
    "    return 0\n")


def api_reference(*lines):
    return make_file("doc/api_reference.py",
                     [(n, line) for n, line in enumerate(lines, 1)])


def test_c118_passes_when_the_reference_file_is_updated(corpus):
    bundle = make_bundle(files=[DEPRECATION,
                                api_reference('DEPRECATED_API_REFERENCE = {"zero_one"}')])
    assert verdict("SCIKIT-LEARN-C118", bundle, corpus).verdict == "pass"


def test_c118_fails_when_it_is_untouched(corpus):
    assert verdict("SCIKIT-LEARN-C118", make_bundle(files=[DEPRECATION]),
                   corpus).verdict == "fail"


def test_c118_finds_no_target_without_a_deprecation(corpus):
    row = verdict("SCIKIT-LEARN-C118", make_bundle(files=[PLAIN_CLASS]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C119 / C120 deprecated members ---------------------------------------------------


def test_c119_passes_when_the_member_carries_the_decorator(corpus):
    text = ("class SVC:\n"
            '    """Classifier."""\n\n'
            "    @deprecated('use classes_')\n"
            "    @property\n"
            "    def labels_(self):\n"
            '        """The labels.\n\n        .. deprecated:: 0.15\n        """\n'
            "        return None\n")
    assert verdict("SCIKIT-LEARN-C119", make_bundle(files=[source(text)]),
                   corpus).verdict == "pass"


def test_c119_fails_when_only_the_docstring_announces_it(corpus):
    text = ("class SVC:\n"
            '    """Classifier."""\n\n'
            "    @property\n"
            "    def labels_(self):\n"
            '        """The labels.\n\n        .. deprecated:: 0.15\n        """\n'
            "        return None\n")
    assert verdict("SCIKIT-LEARN-C119", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c119_finds_no_target_without_an_announced_deprecation(corpus):
    row = verdict("SCIKIT-LEARN-C119", make_bundle(files=[PLAIN_CLASS]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c120_passes_when_deprecated_is_written_on_top(corpus):
    text = ("class SVC:\n"
            "    @deprecated('use classes_')\n"
            "    @property\n"
            "    def labels_(self):\n"
            "        return None\n")
    assert verdict("SCIKIT-LEARN-C120", make_bundle(files=[source(text)]),
                   corpus).verdict == "pass"


def test_c120_fails_when_property_is_written_on_top(corpus):
    text = ("class SVC:\n"
            "    @property\n"
            "    @deprecated('use classes_')\n"
            "    def labels_(self):\n"
            "        return None\n")
    assert verdict("SCIKIT-LEARN-C120", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c120_finds_no_target_on_a_plain_property(corpus):
    text = ("class SVC:\n"
            "    @property\n"
            "    def labels_(self):\n"
            "        return None\n")
    row = verdict("SCIKIT-LEARN-C120", make_bundle(files=[source(text)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C121 / C122 deprecated parameters ------------------------------------------------

DEPRECATED_PARAM_DOC = (
    'def zero_one(y, p, normalize="deprecated"):\n'
    '    """Score.\n'
    "\n"
    "    Parameters\n"
    "    ----------\n"
    "    normalize : bool\n"
    "        Deprecated since 0.15.\n"
    '    """\n')


def test_c121_passes_when_a_future_warning_is_raised(corpus):
    text = DEPRECATED_PARAM_DOC + ("    warnings.warn('normalize is deprecated', "
                                   "FutureWarning)\n    return 0\n")
    assert verdict("SCIKIT-LEARN-C121", make_bundle(files=[source(text)]),
                   corpus).verdict == "pass"


def test_c121_fails_when_none_is(corpus):
    text = DEPRECATED_PARAM_DOC + "    return 0\n"
    assert verdict("SCIKIT-LEARN-C121", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c121_finds_no_target_when_no_parameter_is_deprecated(corpus):
    text = ('def zero_one(y, p):\n'
            '    """Score.\n\n    Parameters\n    ----------\n'
            "    y : ndarray\n        The labels.\n"
            '    """\n    return 0\n')
    row = verdict("SCIKIT-LEARN-C121", make_bundle(files=[source(text)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c122_passes_when_the_warning_is_raised_in_fit(corpus):
    text = ("class SVC(BaseEstimator):\n"
            "    def __init__(self, normalize='deprecated'):\n"
            "        self.normalize = normalize\n\n"
            "    def fit(self, X, y):\n"
            "        warnings.warn('normalize is deprecated', FutureWarning)\n"
            "        return self\n")
    assert verdict("SCIKIT-LEARN-C122", make_bundle(files=[source(text)]),
                   corpus).verdict == "pass"


def test_c122_fails_when_it_is_raised_in_init(corpus):
    text = ("class SVC(BaseEstimator):\n"
            "    def __init__(self, normalize='deprecated'):\n"
            "        warnings.warn('normalize is deprecated', FutureWarning)\n"
            "        self.normalize = normalize\n\n"
            "    def fit(self, X, y):\n"
            "        return self\n")
    assert verdict("SCIKIT-LEARN-C122", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c122_finds_no_target_when_the_estimator_warns_about_nothing(corpus):
    text = ("class SVC(BaseEstimator):\n"
            "    def fit(self, X, y):\n        return self\n")
    row = verdict("SCIKIT-LEARN-C122", make_bundle(files=[source(text)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C123 / C124 deprecation messages -------------------------------------------------


def message(text):
    return source("from sklearn.utils import deprecated\n"
                  "\n"
                  f'@deprecated("{text}")\n'
                  "def zero_one(y, p):\n"
                  "    return 0\n")


def test_c123_passes_when_both_versions_are_named(corpus):
    bundle = make_bundle(files=[message("deprecated in 0.15, removed in 0.17")])
    assert verdict("SCIKIT-LEARN-C123", bundle, corpus).verdict == "pass"


def test_c123_fails_when_only_one_is(corpus):
    bundle = make_bundle(files=[message("deprecated in 0.15")])
    assert verdict("SCIKIT-LEARN-C123", bundle, corpus).verdict == "fail"


def test_c123_finds_no_target_without_a_deprecation_message(corpus):
    row = verdict("SCIKIT-LEARN-C123", make_bundle(files=[PLAIN_CLASS]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c124_passes_when_removal_is_two_releases_later(corpus):
    bundle = make_bundle(files=[message("deprecated in 0.18, removed in 0.20")])
    assert verdict("SCIKIT-LEARN-C124", bundle, corpus).verdict == "pass"


def test_c124_fails_when_the_dev_version_is_quoted(corpus):
    bundle = make_bundle(files=[message("deprecated in 0.18-dev, removed in 0.20")])
    assert verdict("SCIKIT-LEARN-C124", bundle, corpus).verdict == "fail"


def test_c124_finds_no_target_when_the_message_names_one_version(corpus):
    """One version is C123's finding, not a wrong removal window."""
    row = verdict("SCIKIT-LEARN-C124",
                  make_bundle(files=[message("deprecated in 0.15")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C130 a changing default goes through a sentinel ----------------------------------

DEFAULT_BASE = "def kmeans(X, n_clusters=5):\n    return X\n"


def test_c130_passes_on_a_sentinel_with_a_warning(corpus):
    head = ('def kmeans(X, n_clusters="warn"):\n'
            "    warnings.warn('the default changes in 1.7', FutureWarning)\n"
            "    return X\n")
    bundle = make_bundle(files=[source(head, base=DEFAULT_BASE)])
    assert verdict("SCIKIT-LEARN-C130", bundle, corpus).verdict == "pass"


def test_c130_fails_when_the_default_is_changed_outright(corpus):
    head = "def kmeans(X, n_clusters=10):\n    return X\n"
    bundle = make_bundle(files=[source(head, base=DEFAULT_BASE)])
    assert verdict("SCIKIT-LEARN-C130", bundle, corpus).verdict == "fail"


def test_c130_finds_no_target_when_no_default_changed(corpus):
    bundle = make_bundle(files=[source(DEFAULT_BASE, base=DEFAULT_BASE)])
    row = verdict("SCIKIT-LEARN-C130", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C136 / C139 / C141 / C143 the constructor ----------------------------------------


def estimator(init_body, extra="", bases="BaseEstimator", doc='    """Estimator."""'):
    text = (f"class SVC({bases}):\n"
            f"{doc}\n\n"
            f"{init_body}\n"
            f"{extra}"
            "    def fit(self, X, y=None):\n"
            "        self.coef_ = X\n"
            "        return self\n")
    return source(text)


PLAIN_INIT = ("    def __init__(self, alpha=1.0):\n"
              "        self.alpha = alpha\n")


def test_c136_passes_when_init_takes_no_data(corpus):
    assert verdict("SCIKIT-LEARN-C136", make_bundle(files=[estimator(PLAIN_INIT)]),
                   corpus).verdict == "pass"


def test_c136_fails_when_init_takes_training_data(corpus):
    init = ("    def __init__(self, X, y):\n"
            "        self.X = X\n        self.y = y\n")
    assert verdict("SCIKIT-LEARN-C136", make_bundle(files=[estimator(init)]),
                   corpus).verdict == "fail"


def test_c136_finds_no_target_on_a_class_that_is_not_an_estimator(corpus):
    row = verdict("SCIKIT-LEARN-C136", make_bundle(files=[PLAIN_CLASS]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c139_passes_when_every_keyword_becomes_an_attribute(corpus):
    assert verdict("SCIKIT-LEARN-C139", make_bundle(files=[estimator(PLAIN_INIT)]),
                   corpus).verdict == "pass"


def test_c139_fails_when_one_is_dropped(corpus):
    init = ("    def __init__(self, alpha=1.0, beta=2.0):\n"
            "        self.alpha = alpha\n")
    assert verdict("SCIKIT-LEARN-C139", make_bundle(files=[estimator(init)]),
                   corpus).verdict == "fail"


def test_c139_finds_no_target_when_init_takes_no_keyword(corpus):
    init = "    def __init__(self):\n        pass\n"
    row = verdict("SCIKIT-LEARN-C139", make_bundle(files=[estimator(init)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c141_passes_on_a_constructor_that_only_stores(corpus):
    assert verdict("SCIKIT-LEARN-C141", make_bundle(files=[estimator(PLAIN_INIT)]),
                   corpus).verdict == "pass"


def test_c141_fails_on_input_validation_in_init(corpus):
    init = ("    def __init__(self, alpha=1.0):\n"
            "        if alpha < 0:\n"
            "            raise ValueError('alpha must be positive')\n"
            "        self.alpha = alpha\n")
    assert verdict("SCIKIT-LEARN-C141", make_bundle(files=[estimator(init)]),
                   corpus).verdict == "fail"


def test_c141_finds_no_target_on_a_class_that_is_not_an_estimator(corpus):
    row = verdict("SCIKIT-LEARN-C141", make_bundle(files=[PLAIN_CLASS]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c143_passes_when_init_sets_no_fitted_attribute(corpus):
    assert verdict("SCIKIT-LEARN-C143", make_bundle(files=[estimator(PLAIN_INIT)]),
                   corpus).verdict == "pass"


def test_c143_fails_when_it_sets_one(corpus):
    init = ("    def __init__(self, alpha=1.0):\n"
            "        self.alpha = alpha\n"
            "        self.coef_ = None\n")
    assert verdict("SCIKIT-LEARN-C143", make_bundle(files=[estimator(init)]),
                   corpus).verdict == "fail"


def test_c143_finds_no_target_on_a_class_that_is_not_an_estimator(corpus):
    row = verdict("SCIKIT-LEARN-C143", make_bundle(files=[PLAIN_CLASS]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C142 mutable constructor arguments are copied ------------------------------------


def test_c142_passes_when_the_argument_is_copied_first(corpus):
    text = ("class SVC(BaseEstimator):\n"
            "    def __init__(self, groups=None):\n"
            "        self.groups = groups\n\n"
            "    def fit(self, X, y=None):\n"
            "        groups = copy(self.groups)\n"
            "        self.groups.append(0)\n"
            "        return self\n")
    assert verdict("SCIKIT-LEARN-C142", make_bundle(files=[source(text)]),
                   corpus).verdict == "pass"


def test_c142_fails_when_it_is_mutated_in_place(corpus):
    text = ("class SVC(BaseEstimator):\n"
            "    def __init__(self, groups=None):\n"
            "        self.groups = groups\n\n"
            "    def fit(self, X, y=None):\n"
            "        self.groups.append(0)\n"
            "        return self\n")
    assert verdict("SCIKIT-LEARN-C142", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c142_finds_no_target_when_nothing_is_mutated(corpus):
    row = verdict("SCIKIT-LEARN-C142", make_bundle(files=[estimator(PLAIN_INIT)]),
                  corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C144 fit checks that X and y agree ------------------------------------------------


def test_c144_passes_when_a_validation_helper_is_called(corpus):
    text = ("class SVC(BaseEstimator):\n"
            "    def fit(self, X, y):\n"
            "        X, y = check_X_y(X, y)\n"
            "        return self\n")
    assert verdict("SCIKIT-LEARN-C144", make_bundle(files=[source(text)]),
                   corpus).verdict == "pass"


def test_c144_fails_when_nothing_checks_the_shapes(corpus):
    text = ("class SVC(BaseEstimator):\n"
            "    def fit(self, X, y):\n"
            "        self.coef_ = X\n"
            "        return self\n")
    assert verdict("SCIKIT-LEARN-C144", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c144_finds_no_target_when_fit_takes_no_y(corpus):
    text = ("class Scaler(BaseEstimator):\n"
            "    def fit(self, X):\n        return self\n")
    row = verdict("SCIKIT-LEARN-C144", make_bundle(files=[source(text)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C145 unsupervised fit accepts an ignored y ---------------------------------------


def test_c145_passes_on_y_none_in_second_place(corpus):
    text = ("class Scaler(TransformerMixin, BaseEstimator):\n"
            "    def fit(self, X, y=None):\n        return self\n\n"
            "    def transform(self, X):\n        return X\n")
    assert verdict("SCIKIT-LEARN-C145", make_bundle(files=[source(text)]),
                   corpus).verdict == "pass"


def test_c145_fails_when_fit_takes_no_y(corpus):
    text = ("class Scaler(TransformerMixin, BaseEstimator):\n"
            "    def fit(self, X):\n        return self\n\n"
            "    def transform(self, X):\n        return X\n")
    assert verdict("SCIKIT-LEARN-C145", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c145_finds_no_target_on_a_classifier(corpus):
    text = ("class SVC(ClassifierMixin, BaseEstimator):\n"
            "    def fit(self, X, y):\n        return self\n")
    row = verdict("SCIKIT-LEARN-C145", make_bundle(files=[source(text)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C146 composite methods take y in second place ------------------------------------


def test_c146_passes_when_y_is_second(corpus):
    text = ("class Scaler:\n"
            "    def fit_transform(self, X, y=None):\n        return X\n")
    assert verdict("SCIKIT-LEARN-C146", make_bundle(files=[source(text)]),
                   corpus).verdict == "pass"


def test_c146_fails_when_it_is_not(corpus):
    text = ("class Scaler:\n"
            "    def fit_transform(self, X, copy=True):\n        return X\n")
    assert verdict("SCIKIT-LEARN-C146", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c146_finds_no_target_when_none_of_the_four_is_implemented(corpus):
    row = verdict("SCIKIT-LEARN-C146", make_bundle(files=[PLAIN_CLASS]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C147 fit returns self -------------------------------------------------------------


def test_c147_passes_when_fit_returns_self(corpus):
    assert verdict("SCIKIT-LEARN-C147", make_bundle(files=[estimator(PLAIN_INIT)]),
                   corpus).verdict == "pass"


def test_c147_fails_when_it_returns_nothing(corpus):
    text = ("class SVC(BaseEstimator):\n"
            "    def fit(self, X, y=None):\n        self.coef_ = X\n")
    assert verdict("SCIKIT-LEARN-C147", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c147_finds_no_target_on_a_class_without_fit(corpus):
    row = verdict("SCIKIT-LEARN-C147", make_bundle(files=[PLAIN_CLASS]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C148 data-independent parameters belong to __init__ -------------------------------


def test_c148_passes_when_the_extra_argument_is_data_dependent(corpus):
    text = ("class SVC(BaseEstimator):\n"
            "    def fit(self, X, y=None, eval_set=None):\n        return self\n")
    assert verdict("SCIKIT-LEARN-C148", make_bundle(files=[source(text)]),
                   corpus).verdict == "pass"


def test_c148_fails_on_a_hyper_parameter_in_fit(corpus):
    text = ("class SVC(BaseEstimator):\n"
            "    def fit(self, X, y=None, n_iter=10):\n        return self\n")
    assert verdict("SCIKIT-LEARN-C148", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c148_finds_no_target_when_fit_takes_nothing_extra(corpus):
    text = ("class SVC(BaseEstimator):\n"
            "    def fit(self, X, y=None):\n        return self\n")
    row = verdict("SCIKIT-LEARN-C148", make_bundle(files=[source(text)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C151 / C152 learned attribute names ----------------------------------------------

DOCUMENTED = ('    """Estimator.\n'
              "\n"
              "    Attributes\n"
              "    ----------\n"
              "    coef_ : ndarray\n"
              "        The weights.\n"
              '    """')


def learner(assignment, doc=DOCUMENTED):
    text = ("class SVC(BaseEstimator):\n"
            f"{doc}\n\n"
            "    def __init__(self, alpha=1.0):\n"
            "        self.alpha = alpha\n\n"
            "    def fit(self, X, y=None):\n"
            f"        {assignment}\n"
            "        return self\n")
    return source(text)


def test_c151_passes_on_a_trailing_underscore(corpus):
    assert verdict("SCIKIT-LEARN-C151", make_bundle(files=[learner("self.coef_ = X")]),
                   corpus).verdict == "pass"


def test_c151_fails_on_a_documented_attribute_without_one(corpus):
    doc = DOCUMENTED.replace("coef_ : ndarray", "coef : ndarray")
    bundle = make_bundle(files=[learner("self.coef = X", doc=doc)])
    assert verdict("SCIKIT-LEARN-C151", bundle, corpus).verdict == "fail"


def test_c151_finds_no_target_for_an_undocumented_attribute(corpus):
    """An undocumented learned attribute is C152's finding, not this rule's."""
    row = verdict("SCIKIT-LEARN-C151",
                  make_bundle(files=[learner("self._cache = X")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c152_passes_on_a_leading_underscore(corpus):
    assert verdict("SCIKIT-LEARN-C152", make_bundle(files=[learner("self._cache = X")]),
                   corpus).verdict == "pass"


def test_c152_fails_on_an_undocumented_public_attribute(corpus):
    assert verdict("SCIKIT-LEARN-C152", make_bundle(files=[learner("self.cache = X")]),
                   corpus).verdict == "fail"


def test_c152_finds_no_target_for_a_documented_attribute(corpus):
    """A documented attribute is C151's, so the two never grade the same name."""
    row = verdict("SCIKIT-LEARN-C152",
                  make_bundle(files=[learner("self.coef_ = X")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C155 / C156 the input-shape attributes -------------------------------------------


def test_c155_passes_when_fit_sets_n_features_in(corpus):
    assert verdict("SCIKIT-LEARN-C155",
                   make_bundle(files=[learner("self.n_features_in_ = X.shape[1]")]),
                   corpus).verdict == "pass"


def test_c155_fails_when_it_does_not(corpus):
    assert verdict("SCIKIT-LEARN-C155", make_bundle(files=[learner("self.coef_ = X")]),
                   corpus).verdict == "fail"


def test_c155_finds_no_target_on_a_class_that_is_not_an_estimator(corpus):
    row = verdict("SCIKIT-LEARN-C155", make_bundle(files=[PLAIN_CLASS]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c156_passes_when_the_validation_helper_sets_it(corpus):
    assert verdict("SCIKIT-LEARN-C156",
                   make_bundle(files=[learner("X = validate_data(self, X)")]),
                   corpus).verdict == "pass"


def test_c156_fails_when_nothing_sets_it(corpus):
    assert verdict("SCIKIT-LEARN-C156", make_bundle(files=[learner("self.coef_ = X")]),
                   corpus).verdict == "fail"


def test_c156_finds_no_target_on_a_class_that_is_not_an_estimator(corpus):
    row = verdict("SCIKIT-LEARN-C156", make_bundle(files=[PLAIN_CLASS]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C158 / C159 new estimators and their bases ---------------------------------------


def new_estimator(bases):
    text = (f"class MyEstimator({bases}):\n"
            '    """Estimator."""\n\n'
            "    def fit(self, X, y=None):\n        return self\n")
    return source(text, path="sklearn/cluster/_my.py", new=True)


def test_c158_passes_when_baseestimator_is_inherited(corpus):
    assert verdict("SCIKIT-LEARN-C158",
                   make_bundle(files=[new_estimator("ClassifierMixin, BaseEstimator")]),
                   corpus).verdict == "pass"


def test_c158_fails_when_it_is_not(corpus):
    assert verdict("SCIKIT-LEARN-C158", make_bundle(files=[new_estimator("object")]),
                   corpus).verdict == "fail"


def test_c158_finds_no_target_for_a_class_that_was_only_edited(corpus):
    """"A new estimator" means one the agent brought into being, not one it touched."""
    row = verdict("SCIKIT-LEARN-C158",
                  make_bundle(files=[edited(EXISTING_ESTIMATOR, [5])]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c159_passes_when_the_mixin_is_on_the_left(corpus):
    assert verdict("SCIKIT-LEARN-C159",
                   make_bundle(files=[new_estimator("ClassifierMixin, BaseEstimator")]),
                   corpus).verdict == "pass"


def test_c159_fails_when_it_is_on_the_right(corpus):
    assert verdict("SCIKIT-LEARN-C159",
                   make_bundle(files=[new_estimator("BaseEstimator, ClassifierMixin")]),
                   corpus).verdict == "fail"


def test_c159_finds_no_target_without_a_mixin(corpus):
    row = verdict("SCIKIT-LEARN-C159",
                  make_bundle(files=[new_estimator("BaseEstimator")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C160 __sklearn_clone__ returns an instance ---------------------------------------


def test_c160_passes_when_it_returns_something(corpus):
    text = ("class Frozen(BaseEstimator):\n"
            "    def __sklearn_clone__(self):\n        return self\n")
    assert verdict("SCIKIT-LEARN-C160", make_bundle(files=[source(text)]),
                   corpus).verdict == "pass"


def test_c160_fails_when_it_returns_nothing(corpus):
    text = ("class Frozen(BaseEstimator):\n"
            "    def __sklearn_clone__(self):\n        pass\n")
    assert verdict("SCIKIT-LEARN-C160", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c160_finds_no_target_when_clone_is_not_overridden(corpus):
    row = verdict("SCIKIT-LEARN-C160", make_bundle(files=[PLAIN_CLASS]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C161 / C162 transformers ----------------------------------------------------------


def test_c161_passes_on_the_mixin_plus_transform(corpus):
    text = ("class Scaler(TransformerMixin, BaseEstimator):\n"
            "    def fit(self, X, y=None):\n        return self\n\n"
            "    def transform(self, X):\n        return X\n")
    assert verdict("SCIKIT-LEARN-C161", make_bundle(files=[source(text)]),
                   corpus).verdict == "pass"


def test_c161_fails_when_the_mixin_is_missing(corpus):
    text = ("class Scaler(BaseEstimator):\n"
            "    def transform(self, X):\n        return X\n")
    assert verdict("SCIKIT-LEARN-C161", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c161_finds_no_target_on_a_class_that_is_not_a_transformer(corpus):
    row = verdict("SCIKIT-LEARN-C161", make_bundle(files=[PLAIN_CLASS]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c162_passes_when_transform_keeps_every_row(corpus):
    text = ("class Scaler(TransformerMixin, BaseEstimator):\n"
            "    def transform(self, X):\n        return X * 2\n")
    assert verdict("SCIKIT-LEARN-C162", make_bundle(files=[source(text)]),
                   corpus).verdict == "pass"


def test_c162_fails_when_it_drops_rows(corpus):
    text = ("class Scaler(TransformerMixin, BaseEstimator):\n"
            "    def transform(self, X):\n        return X.dropna()\n")
    assert verdict("SCIKIT-LEARN-C162", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c162_finds_no_target_without_a_transform_method(corpus):
    row = verdict("SCIKIT-LEARN-C162", make_bundle(files=[PLAIN_CLASS]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C163 / C164 regressors and classifiers -------------------------------------------


def test_c163_passes_on_the_mixin_plus_predict(corpus):
    text = ("class RidgeRegressor(RegressorMixin, BaseEstimator):\n"
            "    def predict(self, X):\n        return X\n")
    assert verdict("SCIKIT-LEARN-C163", make_bundle(files=[source(text)]),
                   corpus).verdict == "pass"


def test_c163_fails_when_the_mixin_is_missing(corpus):
    text = ("class RidgeRegressor(BaseEstimator):\n"
            "    def predict(self, X):\n        return X\n")
    assert verdict("SCIKIT-LEARN-C163", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c163_finds_no_target_on_a_class_that_is_not_a_regressor(corpus):
    row = verdict("SCIKIT-LEARN-C163", make_bundle(files=[PLAIN_CLASS]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c164_passes_when_the_mixin_is_inherited(corpus):
    text = ("class SVClassifier(ClassifierMixin, BaseEstimator):\n"
            "    def predict(self, X):\n        return X\n")
    assert verdict("SCIKIT-LEARN-C164", make_bundle(files=[source(text)]),
                   corpus).verdict == "pass"


def test_c164_fails_when_it_is_not(corpus):
    text = ("class SVClassifier(BaseEstimator):\n"
            "    def predict(self, X):\n        return X\n")
    assert verdict("SCIKIT-LEARN-C164", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c164_finds_no_target_on_a_class_that_is_not_a_classifier(corpus):
    row = verdict("SCIKIT-LEARN-C164", make_bundle(files=[PLAIN_CLASS]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C165 / C166 / C167 / C168 the label contract -------------------------------------


def classifier(fit_body, extra=""):
    text = ("class SVClassifier(ClassifierMixin, BaseEstimator):\n"
            "    def fit(self, X, y):\n"
            f"{fit_body}"
            "        return self\n"
            f"{extra}")
    return source(text)


ENCODING_FIT = "        self.classes_, y = np.unique(y, return_inverse=True)\n"
NAIVE_FIT = "        self.coef_ = X\n"


def test_c165_passes_when_the_labels_are_encoded(corpus):
    assert verdict("SCIKIT-LEARN-C165", make_bundle(files=[classifier(ENCODING_FIT)]),
                   corpus).verdict == "pass"


def test_c165_fails_when_y_is_used_raw(corpus):
    assert verdict("SCIKIT-LEARN-C165", make_bundle(files=[classifier(NAIVE_FIT)]),
                   corpus).verdict == "fail"


def test_c165_finds_no_target_on_a_class_that_is_not_a_classifier(corpus):
    row = verdict("SCIKIT-LEARN-C165", make_bundle(files=[PLAIN_CLASS]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c166_passes_when_classes_is_stored(corpus):
    assert verdict("SCIKIT-LEARN-C166", make_bundle(files=[classifier(ENCODING_FIT)]),
                   corpus).verdict == "pass"


def test_c166_fails_when_it_is_not(corpus):
    assert verdict("SCIKIT-LEARN-C166", make_bundle(files=[classifier(NAIVE_FIT)]),
                   corpus).verdict == "fail"


def test_c166_finds_no_target_on_a_class_that_is_not_a_classifier(corpus):
    row = verdict("SCIKIT-LEARN-C166", make_bundle(files=[PLAIN_CLASS]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


PROBA = "\n    def predict_proba(self, X):\n        return X\n"


def test_c167_passes_when_classes_comes_from_np_unique(corpus):
    bundle = make_bundle(files=[classifier(ENCODING_FIT, extra=PROBA)])
    assert verdict("SCIKIT-LEARN-C167", bundle, corpus).verdict == "pass"


def test_c167_fails_when_classes_is_assigned_from_a_literal(corpus):
    bundle = make_bundle(files=[classifier("        self.classes_ = [0, 1]\n",
                                           extra=PROBA)])
    assert verdict("SCIKIT-LEARN-C167", bundle, corpus).verdict == "fail"


def test_c167_finds_no_target_without_a_scoring_method(corpus):
    row = verdict("SCIKIT-LEARN-C167", make_bundle(files=[classifier(ENCODING_FIT)]),
                  corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c168_passes_when_predict_reads_classes(corpus):
    extra = "\n    def predict(self, X):\n        return self.classes_[X]\n"
    assert verdict("SCIKIT-LEARN-C168",
                   make_bundle(files=[classifier(ENCODING_FIT, extra=extra)]),
                   corpus).verdict == "pass"


def test_c168_fails_when_it_does_not(corpus):
    extra = "\n    def predict(self, X):\n        return X.argmax(axis=1)\n"
    assert verdict("SCIKIT-LEARN-C168",
                   make_bundle(files=[classifier(ENCODING_FIT, extra=extra)]),
                   corpus).verdict == "fail"


def test_c168_finds_no_target_without_a_predict_method(corpus):
    row = verdict("SCIKIT-LEARN-C168", make_bundle(files=[classifier(ENCODING_FIT)]),
                  corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C169 / C171 clustering algorithms -------------------------------------------------


def test_c169_passes_when_the_mixin_is_inherited(corpus):
    text = ("class KMeans(ClusterMixin, BaseEstimator):\n"
            "    def fit(self, X, y=None):\n"
            "        self.labels_ = X\n        return self\n")
    assert verdict("SCIKIT-LEARN-C169", make_bundle(files=[source(text)]),
                   corpus).verdict == "pass"


def test_c169_fails_when_labels_are_set_without_the_mixin(corpus):
    text = ("class KMeans(BaseEstimator):\n"
            "    def fit(self, X, y=None):\n"
            "        self.labels_ = X\n        return self\n")
    assert verdict("SCIKIT-LEARN-C169", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c169_finds_no_target_on_a_class_that_clusters_nothing(corpus):
    row = verdict("SCIKIT-LEARN-C169", make_bundle(files=[PLAIN_CLASS]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c171_passes_when_labels_are_set(corpus):
    text = ("class KMeans(ClusterMixin, BaseEstimator):\n"
            "    def fit(self, X, y=None):\n"
            "        self.labels_ = X\n        return self\n")
    assert verdict("SCIKIT-LEARN-C171", make_bundle(files=[source(text)]),
                   corpus).verdict == "pass"


def test_c171_fails_when_the_mixin_is_inherited_but_labels_are_not_set(corpus):
    text = ("class KMeans(ClusterMixin, BaseEstimator):\n"
            "    def fit(self, X, y=None):\n"
            "        self.centers_ = X\n        return self\n")
    assert verdict("SCIKIT-LEARN-C171", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c171_finds_no_target_on_a_class_that_clusters_nothing(corpus):
    row = verdict("SCIKIT-LEARN-C171", make_bundle(files=[PLAIN_CLASS]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C173 Tags subclass attributes carry defaults --------------------------------------


def test_c173_passes_when_the_attribute_has_a_default(corpus):
    text = ("class MyTags(Tags):\n"
            "    my_tag: bool = True\n")
    assert verdict("SCIKIT-LEARN-C173", make_bundle(files=[source(text)]),
                   corpus).verdict == "pass"


def test_c173_fails_when_it_has_none(corpus):
    text = ("class MyTags(Tags):\n"
            "    my_tag: bool\n")
    assert verdict("SCIKIT-LEARN-C173", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c173_finds_no_target_on_a_class_that_is_not_a_tags_subclass(corpus):
    row = verdict("SCIKIT-LEARN-C173", make_bundle(files=[PLAIN_CLASS]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C175 __init_subclass__ and auto_wrap_output_keys ----------------------------------


def test_c175_passes_when_the_hook_ignores_the_keyword(corpus):
    text = ("class Base:\n"
            "    def __init_subclass__(cls, **kwargs):\n"
            "        super().__init_subclass__(**kwargs)\n")
    assert verdict("SCIKIT-LEARN-C175", make_bundle(files=[source(text)]),
                   corpus).verdict == "pass"


def test_c175_fails_when_it_depends_on_it(corpus):
    text = ("class Base:\n"
            "    def __init_subclass__(cls, auto_wrap_output_keys=None, **kwargs):\n"
            "        cls._wrap = auto_wrap_output_keys\n")
    assert verdict("SCIKIT-LEARN-C175", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c175_finds_no_target_without_the_hook(corpus):
    row = verdict("SCIKIT-LEARN-C175", make_bundle(files=[PLAIN_CLASS]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C176 __sklearn_is_fitted__ --------------------------------------------------------


def test_c176_passes_on_a_no_argument_boolean(corpus):
    text = ("class SVC(BaseEstimator):\n"
            "    def __sklearn_is_fitted__(self):\n"
            "        return hasattr(self, 'coef_')\n")
    assert verdict("SCIKIT-LEARN-C176", make_bundle(files=[source(text)]),
                   corpus).verdict == "pass"


def test_c176_fails_when_it_takes_an_argument(corpus):
    text = ("class SVC(BaseEstimator):\n"
            "    def __sklearn_is_fitted__(self, deep=True):\n"
            "        return True\n")
    assert verdict("SCIKIT-LEARN-C176", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c176_finds_no_target_when_the_method_is_absent(corpus):
    row = verdict("SCIKIT-LEARN-C176", make_bundle(files=[PLAIN_CLASS]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C177 / C178 / C179 the documentation link ----------------------------------------


def test_c177_passes_when_both_attributes_are_overridden(corpus):
    text = ("class SVC(BaseEstimator):\n"
            '    _doc_link_module = "sklearn"\n'
            '    _doc_link_template = "https://example.org/{estimator_name}"\n')
    assert verdict("SCIKIT-LEARN-C177", make_bundle(files=[source(text)]),
                   corpus).verdict == "pass"


def test_c177_fails_when_only_one_is(corpus):
    text = ("class SVC(BaseEstimator):\n"
            '    _doc_link_module = "sklearn"\n')
    assert verdict("SCIKIT-LEARN-C177", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c177_finds_no_target_when_the_link_is_not_customised(corpus):
    row = verdict("SCIKIT-LEARN-C177", make_bundle(files=[PLAIN_CLASS]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c178_passes_on_the_top_level_module_name(corpus):
    text = ("class SVC(BaseEstimator):\n"
            '    _doc_link_module = "sklearn"\n')
    assert verdict("SCIKIT-LEARN-C178", make_bundle(files=[source(text)]),
                   corpus).verdict == "pass"


def test_c178_fails_on_a_submodule_name(corpus):
    text = ("class SVC(BaseEstimator):\n"
            '    _doc_link_module = "sklearn.svm"\n')
    assert verdict("SCIKIT-LEARN-C178", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c178_finds_no_target_when_the_attribute_is_absent(corpus):
    row = verdict("SCIKIT-LEARN-C178", make_bundle(files=[PLAIN_CLASS]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c179_passes_when_a_dict_is_returned(corpus):
    text = ("class SVC(BaseEstimator):\n"
            "    def _doc_link_url_param_generator(self):\n"
            '        return {"version": "1.5"}\n')
    assert verdict("SCIKIT-LEARN-C179", make_bundle(files=[source(text)]),
                   corpus).verdict == "pass"


def test_c179_fails_when_something_else_is(corpus):
    text = ("class SVC(BaseEstimator):\n"
            "    def _doc_link_url_param_generator(self):\n"
            '        return "1.5"\n')
    assert verdict("SCIKIT-LEARN-C179", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c179_finds_no_target_when_the_method_is_absent(corpus):
    row = verdict("SCIKIT-LEARN-C179", make_bundle(files=[PLAIN_CLASS]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C181 / C182 / C183 / C185 general coding style -----------------------------------


def test_c181_passes_on_an_underscored_name(corpus):
    text = "def count_samples(X):\n    return len(X)\n"
    assert verdict("SCIKIT-LEARN-C181",
                   make_bundle(files=[source(text, new=True)]), corpus).verdict == "pass"


def test_c181_fails_on_a_camel_case_name(corpus):
    text = "def countSamples(X):\n    return len(X)\n"
    assert verdict("SCIKIT-LEARN-C181",
                   make_bundle(files=[source(text, new=True)]), corpus).verdict == "fail"


def test_c181_finds_no_target_for_a_function_that_was_only_edited(corpus):
    row = verdict("SCIKIT-LEARN-C181",
                  make_bundle(files=[edited(EXISTING_ESTIMATOR, [5])]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c182_passes_on_one_statement_per_line(corpus):
    text = "def f(X):\n    if X:\n        return 1\n    return 0\n"
    assert verdict("SCIKIT-LEARN-C182", make_bundle(files=[source(text)]),
                   corpus).verdict == "pass"


def test_c182_fails_on_an_inline_control_flow_body(corpus):
    text = "def f(X):\n    if X: return 1\n    return 0\n"
    assert verdict("SCIKIT-LEARN-C182", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c182_finds_no_target_when_no_package_line_was_written(corpus):
    doc = make_file("doc/modules/svm.rst", [(1, "Support vector machines")])
    row = verdict("SCIKIT-LEARN-C182", make_bundle(files=[doc]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c183_passes_on_an_absolute_import(corpus):
    text = "from sklearn.utils import check_array\n"
    assert verdict("SCIKIT-LEARN-C183", make_bundle(files=[source(text)]),
                   corpus).verdict == "pass"


def test_c183_fails_on_a_relative_import(corpus):
    text = "from ..utils import check_array\n"
    assert verdict("SCIKIT-LEARN-C183", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c183_finds_no_target_when_nothing_is_imported(corpus):
    text = "ALPHA = 1.0\n"
    row = verdict("SCIKIT-LEARN-C183", make_bundle(files=[source(text)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c185_passes_on_an_explicit_import(corpus):
    text = "from sklearn.utils import check_array\n"
    assert verdict("SCIKIT-LEARN-C185", make_bundle(files=[source(text)]),
                   corpus).verdict == "pass"


def test_c185_fails_on_a_star_import(corpus):
    text = "from sklearn.utils import *\n"
    assert verdict("SCIKIT-LEARN-C185", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c185_finds_no_target_when_nothing_is_imported(corpus):
    text = "ALPHA = 1.0\n"
    row = verdict("SCIKIT-LEARN-C185", make_bundle(files=[source(text)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C189 / C190 input validation ------------------------------------------------------


def test_c189_passes_on_asarray(corpus):
    text = "def f(X):\n    X = np.asarray(X)\n    return X\n"
    assert verdict("SCIKIT-LEARN-C189", make_bundle(files=[source(text)]),
                   corpus).verdict == "pass"


def test_c189_fails_on_asanyarray(corpus):
    text = "def f(X):\n    X = np.asanyarray(X)\n    return X\n"
    assert verdict("SCIKIT-LEARN-C189", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c189_finds_no_target_when_nothing_is_converted(corpus):
    text = "def f(X):\n    return X\n"
    row = verdict("SCIKIT-LEARN-C189", make_bundle(files=[source(text)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c190_passes_when_check_array_is_called(corpus):
    text = "def transform(X):\n    X = check_array(X)\n    return X\n"
    assert verdict("SCIKIT-LEARN-C190", make_bundle(files=[source(text)]),
                   corpus).verdict == "pass"


def test_c190_fails_when_it_is_not(corpus):
    text = "def transform(X):\n    return X + 1\n"
    assert verdict("SCIKIT-LEARN-C190", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c190_finds_no_target_on_a_private_helper(corpus):
    text = "def _transform(X):\n    return X + 1\n"
    row = verdict("SCIKIT-LEARN-C190", make_bundle(files=[source(text)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C191 / C192 randomness in package code --------------------------------------------


def test_c191_passes_on_an_explicit_generator(corpus):
    text = ("def sample(n, random_state=None):\n"
            "    rng = check_random_state(random_state)\n"
            "    return rng.normal(size=n)\n")
    assert verdict("SCIKIT-LEARN-C191", make_bundle(files=[source(text)]),
                   corpus).verdict == "pass"


def test_c191_fails_on_the_module_level_routine(corpus):
    text = "def sample(n):\n    return np.random.random(n)\n"
    assert verdict("SCIKIT-LEARN-C191", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c191_finds_no_target_in_deterministic_code(corpus):
    text = "def sample(n):\n    return np.zeros(n)\n"
    row = verdict("SCIKIT-LEARN-C191", make_bundle(files=[source(text)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c192_passes_when_random_state_is_taken_and_used(corpus):
    text = ("def sample(n, random_state=None):\n"
            "    rng = check_random_state(random_state)\n"
            "    return rng.normal(size=n)\n")
    assert verdict("SCIKIT-LEARN-C192", make_bundle(files=[source(text)]),
                   corpus).verdict == "pass"


def test_c192_fails_when_the_keyword_is_missing(corpus):
    text = ("def sample(n):\n"
            "    rng = np.random.RandomState(0)\n"
            "    return rng.normal(size=n)\n")
    assert verdict("SCIKIT-LEARN-C192", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c192_finds_no_target_in_deterministic_code(corpus):
    text = "def sample(n):\n    return np.zeros(n)\n"
    row = verdict("SCIKIT-LEARN-C192", make_bundle(files=[source(text)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C193 / C194 / C196 random_state on estimators --------------------------------------


def random_estimator(init, fit_body="        return self\n"):
    text = ("class SVC(BaseEstimator):\n"
            f"{init}\n"
            "    def fit(self, X, y=None):\n"
            f"{fit_body}")
    return source(text)


GOOD_RANDOM_INIT = ("    def __init__(self, random_state=None):\n"
                    "        self.random_state = random_state\n")


def test_c193_passes_on_random_state_defaulting_to_none(corpus):
    bundle = make_bundle(files=[random_estimator(GOOD_RANDOM_INIT)])
    assert verdict("SCIKIT-LEARN-C193", bundle, corpus).verdict == "pass"


def test_c193_fails_on_a_seed_default(corpus):
    init = ("    def __init__(self, random_state=0):\n"
            "        self.random_state = random_state\n")
    assert verdict("SCIKIT-LEARN-C193", make_bundle(files=[random_estimator(init)]),
                   corpus).verdict == "fail"


def test_c193_finds_no_target_on_a_deterministic_estimator(corpus):
    bundle = make_bundle(files=[random_estimator(PLAIN_INIT)])
    row = verdict("SCIKIT-LEARN-C193", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c194_passes_when_the_argument_is_stored_unmodified(corpus):
    bundle = make_bundle(files=[random_estimator(GOOD_RANDOM_INIT)])
    assert verdict("SCIKIT-LEARN-C194", bundle, corpus).verdict == "pass"


def test_c194_fails_when_it_is_resolved_in_init(corpus):
    init = ("    def __init__(self, random_state=None):\n"
            "        self.random_state = check_random_state(random_state)\n")
    assert verdict("SCIKIT-LEARN-C194", make_bundle(files=[random_estimator(init)]),
                   corpus).verdict == "fail"


def test_c194_finds_no_target_without_the_keyword(corpus):
    bundle = make_bundle(files=[random_estimator(PLAIN_INIT)])
    row = verdict("SCIKIT-LEARN-C194", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c196_passes_when_the_generator_is_stored_as_random_state_(corpus):
    fit = ("        self.random_state_ = check_random_state(self.random_state)\n"
           "        return self\n")
    bundle = make_bundle(files=[random_estimator(GOOD_RANDOM_INIT, fit)])
    assert verdict("SCIKIT-LEARN-C196", bundle, corpus).verdict == "pass"


def test_c196_fails_when_it_is_stored_elsewhere(corpus):
    fit = ("        self.rng_ = check_random_state(self.random_state)\n"
           "        return self\n")
    bundle = make_bundle(files=[random_estimator(GOOD_RANDOM_INIT, fit)])
    assert verdict("SCIKIT-LEARN-C196", bundle, corpus).verdict == "fail"


def test_c196_finds_no_target_when_fit_builds_no_generator(corpus):
    bundle = make_bundle(files=[random_estimator(GOOD_RANDOM_INIT)])
    row = verdict("SCIKIT-LEARN-C196", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C199 to C207 Display classes and plotting -----------------------------------------


def display(body):
    return source("class RocCurveDisplay:\n" + body,
                  path="sklearn/metrics/_plot/roc_curve.py")


FULL_DISPLAY = ("    def __init__(self, fpr=None, tpr=None):\n"
                "        self.fpr = fpr\n"
                "        self.tpr = tpr\n\n"
                "    @classmethod\n"
                "    def from_predictions(cls, y_true, y_pred):\n"
                "        viz = cls()\n"
                "        return viz.plot()\n\n"
                "    def plot(self, ax=None, name=None):\n"
                "        if isinstance(ax, list):\n"
                "            raise ValueError('one axes expected')\n"
                "        self.ax_ = ax\n"
                "        return self\n")


def test_c199_passes_when_a_constructor_class_method_exists(corpus):
    assert verdict("SCIKIT-LEARN-C199", make_bundle(files=[display(FULL_DISPLAY)]),
                   corpus).verdict == "pass"


def test_c199_fails_when_neither_does(corpus):
    body = "    def plot(self, ax=None):\n        self.ax_ = ax\n        return self\n"
    assert verdict("SCIKIT-LEARN-C199", make_bundle(files=[display(body)]),
                   corpus).verdict == "fail"


def test_c199_finds_no_target_on_a_class_that_is_not_a_display(corpus):
    row = verdict("SCIKIT-LEARN-C199", make_bundle(files=[PLAIN_CLASS]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c200_passes_when_init_only_stores_computed_data(corpus):
    assert verdict("SCIKIT-LEARN-C200", make_bundle(files=[display(FULL_DISPLAY)]),
                   corpus).verdict == "pass"


def test_c200_fails_when_init_takes_the_estimator(corpus):
    body = ("    def __init__(self, estimator):\n"
            "        self.estimator = estimator\n\n"
            "    def plot(self, ax=None):\n        return self\n")
    assert verdict("SCIKIT-LEARN-C200", make_bundle(files=[display(body)]),
                   corpus).verdict == "fail"


def test_c200_finds_no_target_when_the_display_has_no_constructor(corpus):
    body = "    def plot(self, ax=None):\n        self.ax_ = ax\n        return self\n"
    row = verdict("SCIKIT-LEARN-C200", make_bundle(files=[display(body)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c201_passes_on_visualization_only_parameters(corpus):
    assert verdict("SCIKIT-LEARN-C201", make_bundle(files=[display(FULL_DISPLAY)]),
                   corpus).verdict == "pass"


def test_c201_fails_when_plot_takes_the_data(corpus):
    body = "    def plot(self, X, ax=None):\n        self.ax_ = ax\n        return self\n"
    assert verdict("SCIKIT-LEARN-C201", make_bundle(files=[display(body)]),
                   corpus).verdict == "fail"


def test_c201_finds_no_target_on_a_class_that_is_not_a_display(corpus):
    row = verdict("SCIKIT-LEARN-C201", make_bundle(files=[PLAIN_CLASS]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c202_passes_when_plot_stores_its_artists(corpus):
    assert verdict("SCIKIT-LEARN-C202", make_bundle(files=[display(FULL_DISPLAY)]),
                   corpus).verdict == "pass"


def test_c202_fails_when_it_stores_none(corpus):
    body = "    def plot(self, ax=None):\n        return self\n"
    assert verdict("SCIKIT-LEARN-C202", make_bundle(files=[display(body)]),
                   corpus).verdict == "fail"


def test_c202_finds_no_target_on_a_class_that_is_not_a_display(corpus):
    row = verdict("SCIKIT-LEARN-C202", make_bundle(files=[PLAIN_CLASS]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c203_passes_when_the_class_method_returns_the_plot(corpus):
    assert verdict("SCIKIT-LEARN-C203", make_bundle(files=[display(FULL_DISPLAY)]),
                   corpus).verdict == "pass"


def test_c203_fails_when_it_returns_the_display(corpus):
    body = ("    @classmethod\n"
            "    def from_predictions(cls, y_true, y_pred):\n"
            "        return cls()\n\n"
            "    def plot(self, ax=None):\n        return self\n")
    assert verdict("SCIKIT-LEARN-C203", make_bundle(files=[display(body)]),
                   corpus).verdict == "fail"


def test_c203_finds_no_target_without_a_constructor_class_method(corpus):
    body = "    def plot(self, ax=None):\n        self.ax_ = ax\n        return self\n"
    row = verdict("SCIKIT-LEARN-C203", make_bundle(files=[display(body)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c204_passes_when_the_axes_are_checked(corpus):
    assert verdict("SCIKIT-LEARN-C204", make_bundle(files=[display(FULL_DISPLAY)]),
                   corpus).verdict == "pass"


def test_c204_fails_when_they_are_not(corpus):
    body = "    def plot(self, ax=None):\n        self.ax_ = ax\n        return self\n"
    assert verdict("SCIKIT-LEARN-C204", make_bundle(files=[display(body)]),
                   corpus).verdict == "fail"


def test_c204_finds_no_target_when_plot_takes_no_axes(corpus):
    body = "    def plot(self):\n        self.ax_ = None\n        return self\n"
    row = verdict("SCIKIT-LEARN-C204", make_bundle(files=[display(body)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C206 / C207 importing matplotlib --------------------------------------------------


def test_c206_passes_on_an_import_inside_the_function(corpus):
    text = ("def plot_roc(display):\n"
            "    check_matplotlib_support('plot_roc')\n"
            "    import matplotlib.pyplot as plt\n"
            "    return plt\n")
    assert verdict("SCIKIT-LEARN-C206",
                   make_bundle(files=[source(text, path="sklearn/metrics/_plot/roc.py")]),
                   corpus).verdict == "pass"


def test_c206_fails_on_a_module_level_import(corpus):
    text = ("import matplotlib.pyplot as plt\n\n"
            "def plot_roc(display):\n    return plt\n")
    assert verdict("SCIKIT-LEARN-C206",
                   make_bundle(files=[source(text, path="sklearn/metrics/_plot/roc.py")]),
                   corpus).verdict == "fail"


def test_c206_finds_no_target_in_a_module_that_never_imports_it(corpus):
    row = verdict("SCIKIT-LEARN-C206", make_bundle(files=[PLAIN_CLASS]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c207_passes_when_the_support_check_comes_first(corpus):
    text = ("def plot_roc(display):\n"
            "    check_matplotlib_support('plot_roc')\n"
            "    import matplotlib.pyplot as plt\n"
            "    return plt\n")
    assert verdict("SCIKIT-LEARN-C207",
                   make_bundle(files=[source(text, path="sklearn/metrics/_plot/roc.py")]),
                   corpus).verdict == "pass"


def test_c207_fails_when_it_is_missing(corpus):
    text = ("def plot_roc(display):\n"
            "    import matplotlib.pyplot as plt\n"
            "    return plt\n")
    assert verdict("SCIKIT-LEARN-C207",
                   make_bundle(files=[source(text, path="sklearn/metrics/_plot/roc.py")]),
                   corpus).verdict == "fail"


def test_c207_finds_no_target_without_a_local_matplotlib_import(corpus):
    text = "def plot_roc(display):\n    return display\n"
    row = verdict("SCIKIT-LEARN-C207",
                  make_bundle(files=[source(text, path="sklearn/metrics/_plot/roc.py")]),
                  corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C221 to C231 callbacks -------------------------------------------------------------


CALLBACK_ESTIMATOR = ("class SVC(CallbackSupportMixin, BaseEstimator):\n"
                      "    def fit(self, X, y=None):\n"
                      "        self._init_callback_context()\n"
                      "        return self\n")


def test_c221_passes_when_the_mixin_is_inherited(corpus):
    assert verdict("SCIKIT-LEARN-C221",
                   make_bundle(files=[source(CALLBACK_ESTIMATOR)]),
                   corpus).verdict == "pass"


def test_c221_fails_when_it_is_not(corpus):
    text = ("class SVC(BaseEstimator):\n"
            "    def fit(self, X, y=None):\n"
            "        self._init_callback_context()\n"
            "        return self\n")
    assert verdict("SCIKIT-LEARN-C221", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c221_finds_no_target_on_an_estimator_without_callbacks(corpus):
    row = verdict("SCIKIT-LEARN-C221", make_bundle(files=[estimator(PLAIN_INIT)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c222_passes_when_fit_creates_the_root_context(corpus):
    assert verdict("SCIKIT-LEARN-C222",
                   make_bundle(files=[source(CALLBACK_ESTIMATOR)]),
                   corpus).verdict == "pass"


def test_c222_fails_when_it_does_not(corpus):
    text = ("class SVC(CallbackSupportMixin, BaseEstimator):\n"
            "    def fit(self, X, y=None):\n        return self\n")
    assert verdict("SCIKIT-LEARN-C222", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c222_finds_no_target_on_an_estimator_without_callbacks(corpus):
    row = verdict("SCIKIT-LEARN-C222", make_bundle(files=[estimator(PLAIN_INIT)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


THIRD_PARTY = "my_package/estimator.py"


def test_c223_passes_when_a_third_party_fit_is_decorated(corpus):
    text = ("class MyEstimator(CallbackSupportMixin, BaseEstimator):\n"
            "    @with_callbacks\n"
            "    def fit(self, X, y=None):\n"
            "        self._init_callback_context()\n"
            "        return self\n")
    assert verdict("SCIKIT-LEARN-C223",
                   make_bundle(files=[source(text, path=THIRD_PARTY)]),
                   corpus).verdict == "pass"


def test_c223_fails_when_it_is_not(corpus):
    text = ("class MyEstimator(CallbackSupportMixin, BaseEstimator):\n"
            "    def fit(self, X, y=None):\n"
            "        self._init_callback_context()\n"
            "        return self\n")
    assert verdict("SCIKIT-LEARN-C223",
                   make_bundle(files=[source(text, path=THIRD_PARTY)]),
                   corpus).verdict == "fail"


def test_c223_finds_no_target_inside_the_package(corpus):
    """A built-in estimator is C224's, and the two must not grade the same class."""
    row = verdict("SCIKIT-LEARN-C223", make_bundle(files=[source(CALLBACK_ESTIMATOR)]),
                  corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c224_passes_when_a_built_in_fit_is_undecorated(corpus):
    assert verdict("SCIKIT-LEARN-C224", make_bundle(files=[source(CALLBACK_ESTIMATOR)]),
                   corpus).verdict == "pass"


def test_c224_fails_when_it_uses_with_callbacks(corpus):
    text = ("class SVC(CallbackSupportMixin, BaseEstimator):\n"
            "    @with_callbacks\n"
            "    def fit(self, X, y=None):\n"
            "        self._init_callback_context()\n"
            "        return self\n")
    assert verdict("SCIKIT-LEARN-C224", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c224_finds_no_target_outside_the_package(corpus):
    text = ("class MyEstimator(CallbackSupportMixin, BaseEstimator):\n"
            "    @with_callbacks\n"
            "    def fit(self, X, y=None):\n"
            "        self._init_callback_context()\n"
            "        return self\n")
    row = verdict("SCIKIT-LEARN-C224",
                  make_bundle(files=[source(text, path=THIRD_PARTY)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


FULL_CALLBACK = ("class ProgressCallback:\n"
                 "    def setup(self, estimator, **kwargs):\n"
                 "        self.records.append(estimator)\n\n"
                 "    def on_fit_task_begin(self, task, *, estimator=None):\n"
                 "        self.records.append(estimator)\n\n"
                 "    def on_fit_task_end(self, task):\n"
                 "        self.records.append(task)\n\n"
                 "    def teardown(self, estimator, **kwargs):\n"
                 "        self.records.append(estimator)\n")


def test_c225_passes_on_the_full_protocol(corpus):
    assert verdict("SCIKIT-LEARN-C225", make_bundle(files=[source(FULL_CALLBACK)]),
                   corpus).verdict == "pass"


def test_c225_fails_when_a_hook_is_missing(corpus):
    text = ("class ProgressCallback:\n"
            "    def on_fit_task_begin(self, task):\n        pass\n")
    assert verdict("SCIKIT-LEARN-C225", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c225_finds_no_target_on_a_class_that_is_not_a_callback(corpus):
    row = verdict("SCIKIT-LEARN-C225", make_bundle(files=[PLAIN_CLASS]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c226_passes_when_every_declared_argument_is_used(corpus):
    assert verdict("SCIKIT-LEARN-C226", make_bundle(files=[source(FULL_CALLBACK)]),
                   corpus).verdict == "pass"


def test_c226_fails_on_an_unused_optional_argument(corpus):
    text = ("class ProgressCallback:\n"
            "    def on_fit_task_begin(self, task, *, estimator=None):\n"
            "        self.records.append(task)\n")
    assert verdict("SCIKIT-LEARN-C226", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c226_finds_no_target_when_the_hook_declares_none(corpus):
    text = ("class ProgressCallback:\n"
            "    def on_fit_task_begin(self, task):\n"
            "        self.records.append(task)\n")
    row = verdict("SCIKIT-LEARN-C226", make_bundle(files=[source(text)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c227_passes_when_the_optional_arguments_are_keyword_only(corpus):
    assert verdict("SCIKIT-LEARN-C227", make_bundle(files=[source(FULL_CALLBACK)]),
                   corpus).verdict == "pass"


def test_c227_fails_on_a_positional_default(corpus):
    text = ("class ProgressCallback:\n"
            "    def on_fit_task_begin(self, task, estimator=None):\n"
            "        self.records.append(estimator)\n")
    assert verdict("SCIKIT-LEARN-C227", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c227_finds_no_target_when_the_hook_takes_no_optional_argument(corpus):
    text = ("class ProgressCallback:\n"
            "    def on_fit_task_begin(self, task):\n"
            "        self.records.append(task)\n")
    row = verdict("SCIKIT-LEARN-C227", make_bundle(files=[source(text)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c229_passes_when_the_hook_only_records_the_estimator(corpus):
    assert verdict("SCIKIT-LEARN-C229", make_bundle(files=[source(FULL_CALLBACK)]),
                   corpus).verdict == "pass"


def test_c229_fails_when_it_predicts_on_it(corpus):
    text = ("class ProgressCallback:\n"
            "    def on_fit_task_end(self, task, *, estimator=None):\n"
            "        self.records.append(estimator.predict(self.X))\n")
    assert verdict("SCIKIT-LEARN-C229", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c229_finds_no_target_when_the_hook_receives_no_estimator(corpus):
    text = ("class ProgressCallback:\n"
            "    def on_fit_task_begin(self, task):\n"
            "        self.records.append(task)\n")
    row = verdict("SCIKIT-LEARN-C229", make_bundle(files=[source(text)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c230_passes_on_the_protocol_and_its_member(corpus):
    text = ("class ProgressCallback(AutoPropagatedCallback):\n"
            "    max_propagation_depth = 2\n\n"
            "    def on_fit_task_begin(self, task):\n"
            "        self.records.append(task)\n")
    assert verdict("SCIKIT-LEARN-C230", make_bundle(files=[source(text)]),
                   corpus).verdict == "pass"


def test_c230_fails_when_the_member_is_declared_without_the_protocol(corpus):
    text = ("class ProgressCallback:\n"
            "    max_propagation_depth = 2\n\n"
            "    def on_fit_task_begin(self, task):\n"
            "        self.records.append(task)\n")
    assert verdict("SCIKIT-LEARN-C230", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c230_finds_no_target_on_a_callback_that_does_not_propagate(corpus):
    row = verdict("SCIKIT-LEARN-C230", make_bundle(files=[source(FULL_CALLBACK)]),
                  corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c231_passes_when_setup_keeps_the_state(corpus):
    assert verdict("SCIKIT-LEARN-C231", make_bundle(files=[source(FULL_CALLBACK)]),
                   corpus).verdict == "pass"


def test_c231_fails_when_setup_resets_it(corpus):
    text = ("class ProgressCallback:\n"
            "    def setup(self, estimator):\n"
            "        self.records = []\n\n"
            "    def on_fit_task_begin(self, task):\n"
            "        self.records.append(task)\n")
    assert verdict("SCIKIT-LEARN-C231", make_bundle(files=[source(text)]),
                   corpus).verdict == "fail"


def test_c231_finds_no_target_when_the_callback_defines_neither_hook(corpus):
    text = ("class ProgressCallback:\n"
            "    def on_fit_task_begin(self, task):\n"
            "        self.records.append(task)\n")
    row = verdict("SCIKIT-LEARN-C231", make_bundle(files=[source(text)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0
