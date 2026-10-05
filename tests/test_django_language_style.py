"""Three cases per rule (docs/checker-authoring.md §9): one target that satisfies the pass
condition, one that violates it, and one input where the pre-condition finds nothing.

The third case is the one that catches a pre-condition written against the artefact the
rule demands instead of the antecedent that invokes it (§4.2). Do not skip it.

A fourth case recurs here and is the one this category most needs: **the rule must not
fire on lines the agent did not write.** A style pack that scanned `head_text` would
report every pre-existing long line, mis-indented block and camelCase name in whatever
file the agent happened to open as the agent's own non-compliance (invariant 5). Those
tests are marked with `preexisting` in their names.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.lint import Finding, LintReport
from compliance.core.models import Command
from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.django.language_style  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}


@pytest.fixture(scope="module")
def corpus():
    """Django's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("django"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


def passes(row) -> bool:
    """A pass that judged nothing is not a pass.

    Guards the failure this suite would otherwise be blind to: a pre-condition narrowed
    until it selects nothing still reads `verdict == "pass"` nowhere -- it reads
    `not_applicable` -- but a pre-condition that fires on one incidental target while
    missing the construct under test does read "pass", vacuously. Asserting a target
    exists is what makes the positive cases mean something.
    """
    assert row.n_targets > 0, f"{row.rule_id}: vacuous pass, the pre-condition found nothing"
    return row.verdict == "pass"


def py_file(path, source, authored=None):
    """A changed Python file. ``authored`` restricts which lines the agent wrote.

    Left at None the agent wrote the whole file, which is the common case. Passing an
    explicit list is how the pre-existing-code tests put text in the file that the agent
    must not be judged for.
    """
    lines = source.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    numbers = list(authored) if authored is not None else list(range(1, len(lines) + 1))
    added = [(n, lines[n - 1]) for n in numbers if 1 <= n <= len(lines)]
    return make_file(path, added, head_text=source, is_new=authored is None)


def js_file(path, source, authored=None):
    return py_file(path, source, authored)


def bundle_with(*files, **overrides):
    return make_bundle(files=list(files), **overrides)


def cmds(*commands):
    return tuple(Command(index=i, command=c) for i, c in enumerate(commands))


PLAIN_PY = "x = 1\n"


# --- C001 black formatting -----------------------------------------------------------


def test_c001_passes_on_black_shaped_source(corpus):
    source = 'NAME = "django"\n\n\ndef total(values):\n    return sum(values)\n'
    assert passes(verdict("DJANGO-C001", bundle_with(py_file("a.py", source)), corpus))


def test_c001_fails_on_constructs_black_would_have_removed(corpus):
    source = "x = { 'a': 1 }\n"
    row = verdict("DJANGO-C001", bundle_with(py_file("a.py", source)), corpus)
    assert row.verdict == "fail"


def test_c001_not_applicable_without_python(corpus):
    row = verdict("DJANGO-C001", bundle_with(js_file("a.js", "var x = 1;\n")), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


def test_c001_fails_a_file_that_will_not_parse(corpus):
    # black rejects invalid Python, so the obligation is settled without running it.
    row = verdict("DJANGO-C001", bundle_with(py_file("a.py", "def f(:\n")), corpus)
    assert row.verdict == "fail"


def test_c001_ignores_preexisting_unformatted_lines(corpus):
    source = "y = 'pre-existing'\nx = 2\n"
    bundle = bundle_with(py_file("a.py", source, authored=[2]))
    assert passes(verdict("DJANGO-C001", bundle, corpus))


# --- C003 PEP 8 via the configured flake8 --------------------------------------------


def _lint(**kwargs):
    return {"flake8": LintReport(shape="report", tool="flake8", **kwargs)}


def test_c003_passes_when_flake8_reports_nothing_new(corpus):
    bundle = bundle_with(py_file("a.py", PLAIN_PY), lint=_lint(n_findings_base=3))
    assert passes(verdict("DJANGO-C003", bundle, corpus))


def test_c003_fails_on_a_new_finding(corpus):
    findings = (Finding(path="a.py", code="E711", message="comparison to None"),)
    bundle = bundle_with(py_file("a.py", PLAIN_PY), lint=_lint(new_findings=findings))
    assert verdict("DJANGO-C003", bundle, corpus).verdict == "fail"


def test_c003_not_applicable_without_python(corpus):
    row = verdict("DJANGO-C003", bundle_with(js_file("a.js", "var x = 1;\n")), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


def test_c003_withholds_rather_than_failing_when_no_linter_ran(corpus):
    # Invariant 6: a tool we did not run is missing evidence, never non-compliance.
    row = verdict("DJANGO-C003", bundle_with(py_file("a.py", PLAIN_PY)), corpus)
    assert (row.verdict, row.status, row.n_violating) == ("not_applicable", "tool_missing", 0)


def test_c003_fails_unparseable_python_without_needing_the_linter(corpus):
    row = verdict("DJANGO-C003", bundle_with(py_file("a.py", "def f(:\n")), corpus)
    assert row.verdict == "fail"


# --- C004 88-character code lines ----------------------------------------------------


def test_c004_passes_a_short_line(corpus):
    assert passes(verdict("DJANGO-C004", bundle_with(py_file("a.py", PLAIN_PY)), corpus))


def test_c004_fails_a_line_over_88(corpus):
    source = "x = '" + "a" * 100 + "'\n"
    assert verdict("DJANGO-C004", bundle_with(py_file("a.py", source)), corpus).verdict == "fail"


def test_c004_not_applicable_without_python(corpus):
    row = verdict("DJANGO-C004", bundle_with(js_file("a.js", "var x = 1;\n")), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


def test_c004_ignores_preexisting_long_lines(corpus):
    source = "y = '" + "a" * 100 + "'\nx = 2\n"
    bundle = bundle_with(py_file("a.py", source, authored=[2]))
    row = verdict("DJANGO-C004", bundle, corpus)
    assert (row.verdict, row.n_targets) == ("pass", 1)


# --- C005 79-character prose ---------------------------------------------------------


def test_c005_passes_a_short_comment(corpus):
    source = "# Compute the running total.\nx = 1\n"
    assert passes(verdict("DJANGO-C005", bundle_with(py_file("a.py", source)), corpus))


def test_c005_fails_a_long_docstring_line(corpus):
    source = 'def f():\n    """' + "word " * 30 + '"""\n    return 1\n'
    assert verdict("DJANGO-C005", bundle_with(py_file("a.py", source)), corpus).verdict == "fail"


def test_c005_fails_a_long_documentation_line(corpus):
    source = "The " + "quick brown fox " * 8 + "jumps.\n"
    bundle = bundle_with(py_file("docs/topics/db.txt", source))
    assert verdict("DJANGO-C005", bundle, corpus).verdict == "fail"


def test_c005_not_applicable_to_code_with_no_prose(corpus):
    row = verdict("DJANGO-C005", bundle_with(py_file("a.py", "x = 1\ny = 2\n")), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


def test_c005_leaves_an_84_char_statement_to_c004(corpus):
    # A code line between the two limits is C004's business, not this rule's: the
    # pre-condition is prose, so a statement must not be a target at all.
    source = "x = '" + "a" * 78 + "'\n"
    row = verdict("DJANGO-C005", bundle_with(py_file("a.py", source)), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


# --- C007 no f-strings where translation may be needed --------------------------------


def test_c007_passes_a_plain_exception_message(corpus):
    source = 'def f(value):\n    raise ValueError("value is not allowed")\n'
    assert passes(verdict("DJANGO-C007", bundle_with(py_file("a.py", source)), corpus))


def test_c007_fails_an_f_string_exception_message(corpus):
    source = 'def f(value):\n    raise ValueError(f"{value} is not allowed")\n'
    assert verdict("DJANGO-C007", bundle_with(py_file("a.py", source)), corpus).verdict == "fail"


def test_c007_fails_an_f_string_inside_gettext(corpus):
    source = 'def f(value):\n    return _(f"welcome {value}")\n'
    assert verdict("DJANGO-C007", bundle_with(py_file("a.py", source)), corpus).verdict == "fail"


def test_c007_not_applicable_to_an_f_string_needing_no_translation(corpus):
    source = 'def f(value):\n    path = f"/api/{value}/"\n    return path\n'
    row = verdict("DJANGO-C007", bundle_with(py_file("a.py", source)), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


# --- C009 no "we" in comments ---------------------------------------------------------


def test_c009_passes_an_impersonal_comment(corpus):
    source = "# Fall back to the default backend.\nx = 1\n"
    assert passes(verdict("DJANGO-C009", bundle_with(py_file("a.py", source)), corpus))


def test_c009_fails_a_comment_using_we(corpus):
    source = "# We fall back to the default backend.\nx = 1\n"
    assert verdict("DJANGO-C009", bundle_with(py_file("a.py", source)), corpus).verdict == "fail"


def test_c009_not_applicable_without_comments(corpus):
    row = verdict("DJANGO-C009", bundle_with(py_file("a.py", "x = 1\n")), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


def test_c009_does_not_read_a_hash_inside_a_string_as_a_comment(corpus):
    source = 'colour = "#we0000"\n'
    row = verdict("DJANGO-C009", bundle_with(py_file("a.py", source)), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


# --- C010 snake_case names ------------------------------------------------------------


def test_c010_passes_a_snake_case_function(corpus):
    source = "def do_thing(first_arg):\n    return first_arg\n"
    assert passes(verdict("DJANGO-C010", bundle_with(py_file("a.py", source)), corpus))


def test_c010_fails_a_camel_case_function(corpus):
    source = "def doThing(firstArg):\n    return firstArg\n"
    assert verdict("DJANGO-C010", bundle_with(py_file("a.py", source)), corpus).verdict == "fail"


def test_c010_not_applicable_when_nothing_is_named(corpus):
    row = verdict("DJANGO-C010", bundle_with(py_file("a.py", "import os\n")), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


def test_c010_does_not_fail_a_framework_mandated_setup_method(corpus):
    source = "class T:\n    def setUp(self):\n        self.value = 1\n"
    row = verdict("DJANGO-C010", bundle_with(py_file("a.py", source)), corpus)
    assert row.verdict != "fail"


def test_c010_leaves_a_variable_holding_a_class_to_c011(corpus):
    source = "MyModel = get_model()\n"
    row = verdict("DJANGO-C010", bundle_with(py_file("a.py", source)), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


def test_c010_ignores_preexisting_camel_case(corpus):
    source = "def doThing():\n    return 1\n\n\ndef do_other():\n    return 2\n"
    bundle = bundle_with(py_file("a.py", source, authored=[5, 6]))
    assert passes(verdict("DJANGO-C010", bundle, corpus))


# --- C011 PascalCase classes ----------------------------------------------------------


def test_c011_passes_a_pascal_case_class(corpus):
    source = "class ModelForm:\n    pass\n"
    assert passes(verdict("DJANGO-C011", bundle_with(py_file("a.py", source)), corpus))


def test_c011_fails_a_snake_case_class(corpus):
    source = "class model_form:\n    pass\n"
    assert verdict("DJANGO-C011", bundle_with(py_file("a.py", source)), corpus).verdict == "fail"


def test_c011_not_applicable_without_a_class(corpus):
    row = verdict("DJANGO-C011", bundle_with(py_file("a.py", "x = 1\n")), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


def test_c011_fails_a_lowercase_class_factory(corpus):
    source = (
        "def make_form():\n"
        "    class Inner:\n"
        "        pass\n"
        "\n"
        "    return Inner\n"
    )
    # `make_form` is snake_case, which C010 wants and C011 does not: a factory that
    # returns a class is named like the class it returns.
    assert verdict("DJANGO-C011", bundle_with(py_file("a.py", source)), corpus).verdict == "fail"


# --- C013 assertRaisesMessage over assertRaises ----------------------------------------


def test_c013_passes_the_message_variant(corpus):
    source = 'def test_x(self):\n    self.assertRaisesMessage(ValueError, "boom")\n'
    bundle = bundle_with(py_file("tests/test_a.py", source))
    assert passes(verdict("DJANGO-C013", bundle, corpus))


def test_c013_fails_the_bare_variant(corpus):
    source = "def test_x(self):\n    self.assertRaises(ValueError)\n"
    bundle = bundle_with(py_file("tests/test_a.py", source))
    assert verdict("DJANGO-C013", bundle, corpus).verdict == "fail"


def test_c013_not_applicable_to_other_assertions(corpus):
    source = "def test_x(self):\n    self.assertEqual(1, 1)\n"
    row = verdict("DJANGO-C013", bundle_with(py_file("tests/test_a.py", source)), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


def test_c013_ignores_a_preexisting_bare_assert_raises(corpus):
    source = (
        "def test_old(self):\n"
        "    self.assertRaises(ValueError)\n"
        "\n"
        "\n"
        "def test_new(self):\n"
        '    self.assertRaisesMessage(ValueError, "boom")\n'
    )
    bundle = bundle_with(py_file("tests/test_a.py", source, authored=[5, 6]))
    assert passes(verdict("DJANGO-C013", bundle, corpus))


# --- C014 regex assertions only when regex is needed -----------------------------------


def test_c014_passes_a_pattern_that_needs_regex(corpus):
    source = 'def test_x(self):\n    self.assertRaisesRegex(ValueError, r"code \\d+")\n'
    bundle = bundle_with(py_file("tests/test_a.py", source))
    assert passes(verdict("DJANGO-C014", bundle, corpus))


def test_c014_fails_a_plain_literal_pattern(corpus):
    source = 'def test_x(self):\n    self.assertRaisesRegex(ValueError, "boom")\n'
    bundle = bundle_with(py_file("tests/test_a.py", source))
    assert verdict("DJANGO-C014", bundle, corpus).verdict == "fail"


def test_c014_not_applicable_to_the_message_variant(corpus):
    source = 'def test_x(self):\n    self.assertRaisesMessage(ValueError, "boom")\n'
    row = verdict("DJANGO-C014", bundle_with(py_file("tests/test_a.py", source)), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


def test_c014_fails_an_escaped_pattern(corpus):
    source = 'def test_x(self):\n    self.assertRaisesRegex(ValueError, re.escape(msg))\n'
    bundle = bundle_with(py_file("tests/test_a.py", source))
    assert verdict("DJANGO-C014", bundle, corpus).verdict == "fail"


# --- C015 assertIs for booleans --------------------------------------------------------


def test_c015_passes_assert_is_true(corpus):
    source = "def test_x(self):\n    self.assertIs(value, True)\n"
    bundle = bundle_with(py_file("tests/test_a.py", source))
    assert passes(verdict("DJANGO-C015", bundle, corpus))


def test_c015_fails_assert_true(corpus):
    source = "def test_x(self):\n    self.assertTrue(value)\n"
    bundle = bundle_with(py_file("tests/test_a.py", source))
    assert verdict("DJANGO-C015", bundle, corpus).verdict == "fail"


def test_c015_not_applicable_to_a_non_boolean_identity_check(corpus):
    source = "def test_x(self):\n    self.assertIs(value, other)\n"
    row = verdict("DJANGO-C015", bundle_with(py_file("tests/test_a.py", source)), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


# --- C016 direct test docstrings -------------------------------------------------------


def test_c016_passes_a_direct_statement(corpus):
    source = 'def test_x(self):\n    """Redirects keep the query string."""\n    pass\n'
    bundle = bundle_with(py_file("tests/test_a.py", source))
    assert passes(verdict("DJANGO-C016", bundle, corpus))


def test_c016_fails_a_tests_that_preamble(corpus):
    source = 'def test_x(self):\n    """Tests that redirects keep the query string."""\n    pass\n'
    bundle = bundle_with(py_file("tests/test_a.py", source))
    assert verdict("DJANGO-C016", bundle, corpus).verdict == "fail"


def test_c016_not_applicable_to_a_non_test_docstring(corpus):
    source = 'def helper(self):\n    """Ensures that the cache is warm."""\n    pass\n'
    row = verdict("DJANGO-C016", bundle_with(py_file("tests/test_a.py", source)), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


def test_c016_does_not_flag_a_noun_phrase_starting_with_test(corpus):
    source = 'def test_x(self):\n    """Test client follows redirects."""\n    pass\n'
    bundle = bundle_with(py_file("tests/test_a.py", source))
    assert passes(verdict("DJANGO-C016", bundle, corpus))


# --- C034 a view's first parameter is `request` -----------------------------------------


def test_c034_passes_a_view_taking_request(corpus):
    source = "def index(request):\n    return render(request, 'a.html')\n"
    bundle = bundle_with(py_file("app/views.py", source))
    assert passes(verdict("DJANGO-C034", bundle, corpus))


def test_c034_fails_a_view_taking_req(corpus):
    source = "def index(req):\n    return render(req, 'a.html')\n"
    bundle = bundle_with(py_file("app/views.py", source))
    assert verdict("DJANGO-C034", bundle, corpus).verdict == "fail"


def test_c034_not_applicable_to_a_function_that_is_not_a_view(corpus):
    source = "def slugify(text):\n    return text.lower()\n"
    row = verdict("DJANGO-C034", bundle_with(py_file("app/utils.py", source)), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


def test_c034_passes_a_class_based_view_method(corpus):
    source = (
        "class DetailView(View):\n"
        "    def get(self, request, *args, **kwargs):\n"
        "        return None\n"
    )
    bundle = bundle_with(py_file("app/handlers.py", source))
    assert passes(verdict("DJANGO-C034", bundle, corpus))


# --- C035 model field names -------------------------------------------------------------


MODEL_HEADER = "class Person(models.Model):\n"


def test_c035_passes_a_snake_case_field(corpus):
    source = MODEL_HEADER + "    first_name = models.CharField(max_length=10)\n"
    assert passes(verdict("DJANGO-C035", bundle_with(py_file("a.py", source)), corpus))


def test_c035_fails_a_camel_case_field(corpus):
    source = MODEL_HEADER + "    firstName = models.CharField(max_length=10)\n"
    assert verdict("DJANGO-C035", bundle_with(py_file("a.py", source)), corpus).verdict == "fail"


def test_c035_not_applicable_to_a_model_with_no_new_fields(corpus):
    source = MODEL_HEADER + "    pass\n"
    row = verdict("DJANGO-C035", bundle_with(py_file("a.py", source)), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


def test_c035_ignores_a_preexisting_badly_named_field(corpus):
    source = (
        MODEL_HEADER
        + "    firstName = models.CharField(max_length=10)\n"
        + "    last_name = models.CharField(max_length=10)\n"
    )
    bundle = bundle_with(py_file("a.py", source, authored=[3]))
    row = verdict("DJANGO-C035", bundle, corpus)
    assert (row.verdict, row.n_targets) == ("pass", 1)


# --- C036 Meta after the fields -----------------------------------------------------------


META_OK = (
    MODEL_HEADER
    + "    name = models.CharField(max_length=10)\n"
    + "\n"
    + "    class Meta:\n"
    + '        ordering = ["name"]\n'
)


def test_c036_passes_meta_after_the_fields(corpus):
    assert passes(verdict("DJANGO-C036", bundle_with(py_file("a.py", META_OK)), corpus))


def test_c036_fails_meta_before_the_fields(corpus):
    source = (
        MODEL_HEADER
        + "    class Meta:\n"
        + '        ordering = ["name"]\n'
        + "\n"
        + "    name = models.CharField(max_length=10)\n"
    )
    assert verdict("DJANGO-C036", bundle_with(py_file("a.py", source)), corpus).verdict == "fail"


def test_c036_not_applicable_to_a_model_without_meta(corpus):
    source = MODEL_HEADER + "    name = models.CharField(max_length=10)\n"
    row = verdict("DJANGO-C036", bundle_with(py_file("a.py", source)), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


def test_c036_fails_two_blank_lines_before_meta(corpus):
    source = (
        MODEL_HEADER
        + "    name = models.CharField(max_length=10)\n"
        + "\n"
        + "\n"
        + "    class Meta:\n"
        + '        ordering = ["name"]\n'
    )
    assert verdict("DJANGO-C036", bundle_with(py_file("a.py", source)), corpus).verdict == "fail"


def test_c036_does_not_judge_whitespace_the_agent_did_not_write(corpus):
    # Meta and its blank lines pre-date the agent; only the field it added is its own.
    source = (
        MODEL_HEADER
        + "    name = models.CharField(max_length=10)\n"
        + "\n"
        + "\n"
        + "    class Meta:\n"
        + '        ordering = ["name"]\n'
    )
    bundle = bundle_with(py_file("a.py", source, authored=[2]))
    assert passes(verdict("DJANGO-C036", bundle, corpus))


# --- C037 model member order ---------------------------------------------------------------


ORDERED_MODEL = (
    MODEL_HEADER
    + "    name = models.CharField(max_length=10)\n"
    + "    objects = PersonManager()\n"
    + "\n"
    + "    class Meta:\n"
    + '        ordering = ["name"]\n'
    + "\n"
    + "    def __str__(self):\n"
    + "        return self.name\n"
    + "\n"
    + "    def save(self, *args, **kwargs):\n"
    + "        super().save(*args, **kwargs)\n"
    + "\n"
    + "    def get_absolute_url(self):\n"
    + '        return "/p/"\n'
    + "\n"
    + "    def promote(self):\n"
    + "        return None\n"
)


def test_c037_passes_the_prescribed_order(corpus):
    bundle = bundle_with(py_file("a.py", ORDERED_MODEL))
    assert passes(verdict("DJANGO-C037", bundle, corpus))


def test_c037_fails_a_method_before_a_field(corpus):
    source = (
        MODEL_HEADER
        + "    def __str__(self):\n"
        + '        return "x"\n'
        + "\n"
        + "    name = models.CharField(max_length=10)\n"
    )
    assert verdict("DJANGO-C037", bundle_with(py_file("a.py", source)), corpus).verdict == "fail"


def test_c037_not_applicable_to_a_class_with_one_placed_member(corpus):
    source = MODEL_HEADER + "    name = models.CharField(max_length=10)\n"
    row = verdict("DJANGO-C037", bundle_with(py_file("a.py", source)), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


def test_c037_ignores_a_model_the_agent_never_touched(corpus):
    other = "OTHER = 1\n"
    bundle = bundle_with(py_file("a.py", ORDERED_MODEL + "\n\n" + other,
                                 authored=[len(ORDERED_MODEL.split("\n")) + 2]))
    row = verdict("DJANGO-C037", bundle, corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


# --- C038 field choices ---------------------------------------------------------------------


def test_c038_passes_an_uppercase_choices_constant(corpus):
    source = MODEL_HEADER + "    status = models.CharField(choices=STATUS_CHOICES)\n"
    assert passes(verdict("DJANGO-C038", bundle_with(py_file("a.py", source)), corpus))


def test_c038_passes_a_text_choices_enum(corpus):
    source = MODEL_HEADER + "    status = models.CharField(choices=Status.choices)\n"
    assert passes(verdict("DJANGO-C038", bundle_with(py_file("a.py", source)), corpus))


def test_c038_fails_an_inline_literal(corpus):
    source = MODEL_HEADER + '    status = models.CharField(choices=[("a", "A")])\n'
    assert verdict("DJANGO-C038", bundle_with(py_file("a.py", source)), corpus).verdict == "fail"


def test_c038_not_applicable_to_a_field_without_choices(corpus):
    source = MODEL_HEADER + "    status = models.CharField(max_length=2)\n"
    row = verdict("DJANGO-C038", bundle_with(py_file("a.py", source)), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


# --- C042 trailing whitespace ------------------------------------------------------------------


def test_c042_passes_clean_lines(corpus):
    assert passes(verdict("DJANGO-C042", bundle_with(py_file("a.py", PLAIN_PY)), corpus))


def test_c042_fails_a_line_with_trailing_spaces(corpus):
    bundle = bundle_with(py_file("a.py", "x = 1   \n"))
    assert verdict("DJANGO-C042", bundle, corpus).verdict == "fail"


def test_c042_not_applicable_when_nothing_was_added(corpus):
    row = verdict("DJANGO-C042", make_bundle(), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


def test_c042_ignores_preexisting_trailing_whitespace(corpus):
    bundle = bundle_with(py_file("a.py", "y = 0   \nx = 1\n", authored=[2]))
    row = verdict("DJANGO-C042", bundle, corpus)
    assert (row.verdict, row.n_targets) == ("pass", 1)


# --- C043 do not sign your code ------------------------------------------------------------------


def test_c043_passes_unsigned_code(corpus):
    bundle = bundle_with(py_file("a.py", "# Normalise the value.\nx = 1\n"))
    assert passes(verdict("DJANGO-C043", bundle, corpus))


def test_c043_fails_a_signed_comment(corpus):
    bundle = bundle_with(py_file("a.py", "# Written by Jane Doe.\nx = 1\n"))
    assert verdict("DJANGO-C043", bundle, corpus).verdict == "fail"


def test_c043_not_applicable_when_only_authors_changed(corpus):
    # AUTHORS is where the rule sends the credit, so a change to it is never a target.
    bundle = bundle_with(py_file("AUTHORS", "Jane Doe <jane@example.com>\n"))
    row = verdict("DJANGO-C043", bundle, corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


# --- C126 JavaScript indentation -------------------------------------------------------------------


def test_c126_passes_four_space_indentation(corpus):
    source = "function f() {\n    var total = 1;\n}\n"
    assert passes(verdict("DJANGO-C126", bundle_with(js_file("a.js", source)), corpus))


def test_c126_fails_a_three_space_indent(corpus):
    source = "function f() {\n   var total = 1;\n}\n"
    assert verdict("DJANGO-C126", bundle_with(js_file("a.js", source)), corpus).verdict == "fail"


def test_c126_not_applicable_without_javascript(corpus):
    row = verdict("DJANGO-C126", bundle_with(py_file("a.py", PLAIN_PY)), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


# --- C127 JavaScript camelCase ----------------------------------------------------------------------


def test_c127_passes_a_camel_case_variable(corpus):
    bundle = bundle_with(js_file("a.js", "var totalCount = 1;\n"))
    assert passes(verdict("DJANGO-C127", bundle, corpus))


def test_c127_fails_a_snake_case_variable(corpus):
    bundle = bundle_with(js_file("a.js", "var total_count = 1;\n"))
    assert verdict("DJANGO-C127", bundle, corpus).verdict == "fail"


def test_c127_not_applicable_without_a_declaration(corpus):
    bundle = bundle_with(js_file("a.js", "doThing();\n"))
    row = verdict("DJANGO-C127", bundle, corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


# --- C129 Biome was run ---------------------------------------------------------------------------------


def test_c129_passes_when_biome_ran(corpus):
    bundle = bundle_with(js_file("a.js", "var x = 1;\n"), commands=cmds("npx biome check ."))
    assert passes(verdict("DJANGO-C129", bundle, corpus))


def test_c129_fails_when_javascript_changed_and_nothing_ran(corpus):
    bundle = bundle_with(js_file("a.js", "var x = 1;\n"), commands=cmds("ls"))
    assert verdict("DJANGO-C129", bundle, corpus).verdict == "fail"


def test_c129_not_applicable_without_javascript(corpus):
    row = verdict("DJANGO-C129", bundle_with(py_file("a.py", PLAIN_PY)), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


# --- C130 event delegation ------------------------------------------------------------------------------------


def test_c130_passes_a_delegated_listener(corpus):
    source = 'document.addEventListener("click", handleClick);\n'
    assert passes(verdict("DJANGO-C130", bundle_with(js_file("a.js", source)), corpus))


def test_c130_fails_a_direct_binding(corpus):
    source = 'button.addEventListener("click", handleClick);\n'
    assert verdict("DJANGO-C130", bundle_with(js_file("a.js", source)), corpus).verdict == "fail"


def test_c130_not_applicable_without_a_binding(corpus):
    bundle = bundle_with(js_file("a.js", "var total = 1;\n"))
    row = verdict("DJANGO-C130", bundle, corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


def test_c130_passes_jquery_delegation_with_a_selector(corpus):
    source = '$(document).on("click", ".row", handleClick);\n'
    assert passes(verdict("DJANGO-C130", bundle_with(js_file("a.js", source)), corpus))


# --- pack-level invariants -------------------------------------------------------------------------------------


def test_every_rule_here_is_in_the_django_corpus_and_the_scored_batch(corpus):
    from compliance.core.registry import in_batch

    batch = set(in_batch(corpus))
    mine = [r for r in registered() if r.id.startswith("DJANGO-")]
    assert [r.id for r in mine if r.id not in corpus] == []
    assert [r.id for r in mine if r.id not in batch] == []


def test_every_rule_here_states_both_layers_in_its_docstring():
    for r in registered():
        if not r.id.startswith("DJANGO-"):
            continue
        assert "Pre-condition:" in r.doc, f"{r.id} does not state its pre-condition"
        assert "Pass condition:" in r.doc, f"{r.id} does not state its pass condition"


def test_no_rule_here_fires_on_an_empty_contribution(corpus):
    """Invariant 3: nothing to judge is `not_applicable`, never a pass and never a fail."""
    empty = make_bundle()
    for r in registered():
        if not r.id.startswith("DJANGO-"):
            continue
        row = run_rule(empty, r, corpus)
        assert (row.verdict, row.n_targets) == ("not_applicable", 0), r.id


# ======================================================================================
# The eighteen that waited on `extractors/imports` and `extractors/template_tags`.
# Same three cases each, plus the pre-existing-code case this category needs most: an
# import block or a template the agent only partly edited must not be graded whole.
# ======================================================================================


def tpl_file(path, source, authored=None):
    """A changed template. Same shape as `py_file`; named apart so the tests read."""
    return py_file(path, source, authored)


SORTED_IMPORTS = (
    "import os\n"
    "from datetime import date\n"
    "\n"
    "from django.db import models\n"
    "\n"
    "from .utils import helper\n"
    "\n"
    "\n"
    "def show():\n"
    "    return os.sep, date, models, helper\n"
)

# One correctly placed stdlib import (line 4) appended to an import block that was already
# out of order. Every ordering rule below must pass this: the faults are on lines 1-3,
# which the agent did not write.
INHERITED_DISORDER = (
    "from django.db import models\n"
    "import zzz\n"
    "import aaa\n"
    "import bbb\n"
    "x = (models, zzz, aaa, bbb)\n"
)

PLAIN_TEMPLATE = "<p>hello</p>\n"


# --- C019 isort ------------------------------------------------------------------------


def test_c019_passes_on_imports_isort_would_not_move(corpus):
    bundle = bundle_with(py_file("a.py", SORTED_IMPORTS))
    assert passes(verdict("DJANGO-C019", bundle, corpus))


def test_c019_fails_when_a_group_is_out_of_order(corpus):
    source = "from django.db import models\nimport os\nx = (models, os)\n"
    assert verdict("DJANGO-C019", bundle_with(py_file("a.py", source)), corpus).verdict == "fail"


def test_c019_not_applicable_when_no_import_was_added(corpus):
    row = verdict("DJANGO-C019", bundle_with(py_file("a.py", PLAIN_PY)), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


def test_c019_fails_a_file_that_will_not_parse(corpus):
    # isort rejects invalid Python, so the obligation is settled without running it.
    row = verdict("DJANGO-C019", bundle_with(py_file("a.py", "import os\ndef f(:\n")), corpus)
    assert row.verdict == "fail"


def test_c019_withholds_when_the_source_was_not_reconstructed(corpus):
    change = make_file("a.py", [(1, "import os")], head_text=None)
    row = verdict("DJANGO-C019", bundle_with(change), corpus)
    assert (row.verdict, row.status, row.n_violating) == ("not_applicable", "parse_error", 0)


def test_c019_ignores_preexisting_disorder(corpus):
    bundle = bundle_with(py_file("a.py", INHERITED_DISORDER, authored=[4]))
    assert passes(verdict("DJANGO-C019", bundle, corpus))


# --- C020 group order --------------------------------------------------------------------


def test_c020_passes_on_the_declared_group_order(corpus):
    assert passes(verdict("DJANGO-C020", bundle_with(py_file("a.py", SORTED_IMPORTS)), corpus))


def test_c020_fails_when_another_django_component_precedes_the_stdlib(corpus):
    source = "from django.db import models\nimport os\nx = (models, os)\n"
    row = verdict("DJANGO-C020", bundle_with(py_file("a.py", source)), corpus)
    assert row.verdict == "fail"


def test_c020_fails_when_a_group_is_not_alphabetical(corpus):
    source = "import zzz\nimport aaa\nx = (zzz, aaa)\n"
    row = verdict("DJANGO-C020", bundle_with(py_file("a.py", source)), corpus)
    assert row.verdict == "fail"


def test_c020_fails_a_plain_import_left_below_the_try_except_imports(corpus):
    source = (
        "try:\n"
        "    import fast\n"
        "except ImportError:\n"
        "    fast = None\n"
        "import os\n"
        "x = (fast, os)\n"
    )
    row = verdict("DJANGO-C020", bundle_with(py_file("a.py", source)), corpus)
    assert row.verdict == "fail"


def test_c020_not_applicable_without_an_import(corpus):
    row = verdict("DJANGO-C020", bundle_with(py_file("a.py", PLAIN_PY)), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


def test_c020_ignores_preexisting_disorder(corpus):
    bundle = bundle_with(py_file("a.py", INHERITED_DISORDER, authored=[4]))
    assert passes(verdict("DJANGO-C020", bundle, corpus))


# --- C021 plain imports first --------------------------------------------------------------


def test_c021_passes_when_plain_imports_come_first(corpus):
    source = "import sys\nfrom os import path\nx = (sys, path)\n"
    assert passes(verdict("DJANGO-C021", bundle_with(py_file("a.py", source)), corpus))


def test_c021_fails_a_plain_import_after_a_from_import_in_the_same_group(corpus):
    source = "from os import path\nimport sys\nx = (path, sys)\n"
    row = verdict("DJANGO-C021", bundle_with(py_file("a.py", source)), corpus)
    assert row.verdict == "fail"


def test_c021_not_applicable_without_an_import(corpus):
    row = verdict("DJANGO-C021", bundle_with(py_file("a.py", PLAIN_PY)), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


def test_c021_ignores_a_preexisting_import_after_a_from_import(corpus):
    # The `import sys` on line 2 was already out of place. The agent added line 3, which
    # is correctly a from-import, and must be graded on that rather than on line 2.
    source = "from os import path\nimport sys\nfrom sys import argv\nx = (path, argv)\n"
    bundle = bundle_with(py_file("a.py", source, authored=[3, 4]))
    assert passes(verdict("DJANGO-C021", bundle, corpus))


# --- C022 relative import depth ------------------------------------------------------------


def test_c022_passes_a_single_dot_relative_import(corpus):
    source = "from .models import Thing\nx = Thing\n"
    assert passes(verdict("DJANGO-C022", bundle_with(py_file("a.py", source)), corpus))


def test_c022_fails_a_multi_dot_relative_import(corpus):
    source = "from ..models import Thing\nx = Thing\n"
    row = verdict("DJANGO-C022", bundle_with(py_file("a.py", source)), corpus)
    assert row.verdict == "fail"


def test_c022_not_applicable_without_an_import(corpus):
    row = verdict("DJANGO-C022", bundle_with(py_file("a.py", PLAIN_PY)), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


def test_c022_ignores_a_preexisting_multi_dot_import(corpus):
    source = "from ..models import Thing\nfrom .utils import helper\nx = (Thing, helper)\n"
    bundle = bundle_with(py_file("a.py", source, authored=[2, 3]))
    assert passes(verdict("DJANGO-C022", bundle, corpus))


# --- C023 names on one line ----------------------------------------------------------------


def test_c023_passes_alphabetised_names(corpus):
    source = "from django.db import connection, models\nx = (connection, models)\n"
    assert passes(verdict("DJANGO-C023", bundle_with(py_file("a.py", source)), corpus))


def test_c023_puts_uppercase_names_before_lowercase(corpus):
    source = "from django.db import DEFAULT_DB_ALIAS, models\nx = (DEFAULT_DB_ALIAS, models)\n"
    assert passes(verdict("DJANGO-C023", bundle_with(py_file("a.py", source)), corpus))


def test_c023_fails_unsorted_names(corpus):
    source = "from django.db import models, connection\nx = (connection, models)\n"
    row = verdict("DJANGO-C023", bundle_with(py_file("a.py", source)), corpus)
    assert row.verdict == "fail"


def test_c023_not_applicable_to_a_single_name(corpus):
    source = "from django.db import models\nx = models\n"
    row = verdict("DJANGO-C023", bundle_with(py_file("a.py", source)), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


def test_c023_ignores_a_preexisting_unsorted_line(corpus):
    source = "from os import path, getcwd\nimport sys\nx = (path, getcwd, sys)\n"
    bundle = bundle_with(py_file("a.py", source, authored=[2, 3]))
    row = verdict("DJANGO-C023", bundle, corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


# --- C024 how a long import is wrapped -----------------------------------------------------


WRAPPED_OK = (
    "from django.core.exceptions import (\n"
    "    ImproperlyConfigured,\n"
    "    ValidationError,\n"
    ")\n"
    "x = (ImproperlyConfigured, ValidationError)\n"
)


def test_c024_passes_a_correctly_wrapped_import(corpus):
    assert passes(verdict("DJANGO-C024", bundle_with(py_file("a.py", WRAPPED_OK)), corpus))


def test_c024_fails_a_missing_trailing_comma(corpus):
    source = WRAPPED_OK.replace("    ValidationError,\n)\n", "    ValidationError)\n")
    row = verdict("DJANGO-C024", bundle_with(py_file("a.py", source)), corpus)
    assert row.verdict == "fail"


def test_c024_fails_a_wrong_continuation_indent(corpus):
    source = WRAPPED_OK.replace("    ImproperlyConfigured,", "  ImproperlyConfigured,")
    row = verdict("DJANGO-C024", bundle_with(py_file("a.py", source)), corpus)
    assert row.verdict == "fail"


def test_c024_fails_a_long_import_left_on_one_line(corpus):
    source = ("from django.core.exceptions import ImproperlyConfigured, ValidationError, "
              "SuspiciousOperation, PermissionDenied\nx = 1\n")
    row = verdict("DJANGO-C024", bundle_with(py_file("a.py", source)), corpus)
    assert row.verdict == "fail"


def test_c024_not_applicable_to_a_short_one_line_import(corpus):
    row = verdict("DJANGO-C024", bundle_with(py_file("a.py", "import os\nx = os\n")), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


def test_c024_ignores_a_preexisting_badly_wrapped_import(corpus):
    source = "from os import (\n    path,\n    sep)\nimport sys\nx = (path, sep, sys)\n"
    bundle = bundle_with(py_file("a.py", source, authored=[4, 5]))
    row = verdict("DJANGO-C024", bundle, corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


# --- C025 blank lines below the imports ----------------------------------------------------


def test_c025_passes_one_blank_before_code_and_two_before_a_definition(corpus):
    source = "import os\n\nDEBUG = os.sep\n\n\ndef show():\n    return DEBUG\n"
    assert passes(verdict("DJANGO-C025", bundle_with(py_file("a.py", source)), corpus))


def test_c025_passes_two_blanks_when_a_definition_follows_the_imports_directly(corpus):
    source = "import os\n\n\ndef show():\n    return os.sep\n"
    assert passes(verdict("DJANGO-C025", bundle_with(py_file("a.py", source)), corpus))


def test_c025_fails_when_a_definition_follows_the_imports_with_one_blank(corpus):
    source = "import os\n\ndef show():\n    return os.sep\n"
    row = verdict("DJANGO-C025", bundle_with(py_file("a.py", source)), corpus)
    assert row.verdict == "fail"


def test_c025_fails_two_blank_lines_before_module_level_code(corpus):
    source = "import os\n\n\nDEBUG = os.sep\n"
    row = verdict("DJANGO-C025", bundle_with(py_file("a.py", source)), corpus)
    assert row.verdict == "fail"


def test_c025_not_applicable_without_imports(corpus):
    row = verdict("DJANGO-C025", bundle_with(py_file("a.py", PLAIN_PY)), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


def test_c025_ignores_a_preexisting_gap_the_agent_never_touched(corpus):
    # The import block and the line under it are inherited; the agent appended a function
    # at the bottom with the two blank lines the rule asks for.
    source = "import os\nDEBUG = os.sep\n\n\ndef show():\n    return DEBUG\n"
    bundle = bundle_with(py_file("a.py", source, authored=[5, 6]))
    assert passes(verdict("DJANGO-C025", bundle, corpus))


# --- C026 documented convenience imports ---------------------------------------------------


def test_c026_passes_a_documented_path(corpus):
    source = "from django.views import View\nx = View\n"
    assert passes(verdict("DJANGO-C026", bundle_with(py_file("a.py", source)), corpus))


def test_c026_fails_an_internal_module_path(corpus):
    source = "from django.views.generic.base import View\nx = View\n"
    row = verdict("DJANGO-C026", bundle_with(py_file("a.py", source)), corpus)
    assert row.verdict == "fail"


def test_c026_fails_a_private_module_component(corpus):
    source = "from django.utils._os import safe_join\nx = safe_join\n"
    row = verdict("DJANGO-C026", bundle_with(py_file("a.py", source)), corpus)
    assert row.verdict == "fail"


def test_c026_not_applicable_to_a_non_django_import(corpus):
    row = verdict("DJANGO-C026", bundle_with(py_file("a.py", "import os\nx = os\n")), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


def test_c026_ignores_a_preexisting_internal_import(corpus):
    source = ("from django.views.generic.base import View\n"
              "from django.views import defaults\nx = (View, defaults)\n")
    bundle = bundle_with(py_file("a.py", source, authored=[2, 3]))
    assert passes(verdict("DJANGO-C026", bundle, corpus))


# --- C039 settings at import time ----------------------------------------------------------


def test_c039_passes_a_settings_read_inside_a_function(corpus):
    source = "from django.conf import settings\n\n\ndef debug():\n    return settings.DEBUG\n"
    assert passes(verdict("DJANGO-C039", bundle_with(py_file("a.py", source)), corpus))


def test_c039_passes_a_settings_read_deferred_into_a_lambda(corpus):
    source = ("from django.conf import settings\n"
              "from django.utils.functional import SimpleLazyObject\n"
              "\n"
              "DEBUG = SimpleLazyObject(lambda: settings.DEBUG)\n")
    assert passes(verdict("DJANGO-C039", bundle_with(py_file("a.py", source)), corpus))


def test_c039_fails_a_module_level_settings_read(corpus):
    source = "from django.conf import settings\n\nDEBUG = settings.DEBUG\n"
    row = verdict("DJANGO-C039", bundle_with(py_file("a.py", source)), corpus)
    assert row.verdict == "fail"


def test_c039_fails_a_settings_read_in_a_default_argument(corpus):
    # The default is evaluated when the `def` statement runs, which is at import time.
    source = ("from django.conf import settings\n"
              "\n"
              "\n"
              "def show(debug=settings.DEBUG):\n"
              "    return debug\n")
    row = verdict("DJANGO-C039", bundle_with(py_file("a.py", source)), corpus)
    assert row.verdict == "fail"


def test_c039_not_applicable_without_a_settings_read(corpus):
    source = "from django.conf import settings\n\n\ndef show():\n    return 1\n"
    row = verdict("DJANGO-C039", bundle_with(py_file("a.py", source)), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


def test_c039_ignores_a_preexisting_import_time_read(corpus):
    source = ("from django.conf import settings\n"
              "DEBUG = settings.DEBUG\n"
              "\n"
              "\n"
              "def show():\n"
              "    return settings.ROOT_URLCONF\n")
    bundle = bundle_with(py_file("a.py", source, authored=[5, 6]))
    assert passes(verdict("DJANGO-C039", bundle, corpus))


# --- C041 unused imports -------------------------------------------------------------------


def test_c041_passes_an_import_something_uses(corpus):
    assert passes(verdict("DJANGO-C041", bundle_with(py_file("a.py", "import os\nx = os\n")), corpus))


def test_c041_passes_an_unused_import_kept_with_a_noqa(corpus):
    source = "from django.db.models import Model  # NOQA\nx = 1\n"
    assert passes(verdict("DJANGO-C041", bundle_with(py_file("a.py", source)), corpus))


def test_c041_fails_an_unused_import_with_no_marker(corpus):
    row = verdict("DJANGO-C041", bundle_with(py_file("a.py", "import os\nx = 1\n")), corpus)
    assert row.verdict == "fail"


def test_c041_not_applicable_without_an_import(corpus):
    row = verdict("DJANGO-C041", bundle_with(py_file("a.py", PLAIN_PY)), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


def test_c041_ignores_a_preexisting_unused_import(corpus):
    source = "import unusedmod\nimport os\nx = os\n"
    bundle = bundle_with(py_file("a.py", source, authored=[2, 3]))
    assert passes(verdict("DJANGO-C041", bundle, corpus))


# --- C002 indentation ----------------------------------------------------------------------


def test_c002_passes_four_space_python_indentation(corpus):
    source = "def show():\n    return 1\n"
    assert passes(verdict("DJANGO-C002", bundle_with(py_file("a.py", source)), corpus))


def test_c002_passes_a_continuation_line_aligned_to_its_bracket(corpus):
    # Not a mis-indented statement: black aligns continuations to the open bracket, and a
    # rule that failed them would fail correctly formatted code.
    source = "def show():\n    return call(1,\n                2)\n"
    assert passes(verdict("DJANGO-C002", bundle_with(py_file("a.py", source)), corpus))


def test_c002_fails_three_space_python_indentation(corpus):
    row = verdict("DJANGO-C002", bundle_with(py_file("a.py", "def show():\n   return 1\n")), corpus)
    assert row.verdict == "fail"


def test_c002_passes_two_space_html_indentation(corpus):
    source = "<div>\n  <p>hello</p>\n</div>\n"
    assert passes(verdict("DJANGO-C002", bundle_with(tpl_file("t.html", source)), corpus))


def test_c002_fails_three_space_html_indentation(corpus):
    source = "<div>\n   <p>hello</p>\n</div>\n"
    row = verdict("DJANGO-C002", bundle_with(tpl_file("t.html", source)), corpus)
    assert row.verdict == "fail"


def test_c002_not_applicable_without_an_indented_line(corpus):
    row = verdict("DJANGO-C002", bundle_with(py_file("a.py", PLAIN_PY)), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


def test_c002_ignores_a_preexisting_misindented_line(corpus):
    source = "def old():\n   return 1\n\n\ndef new():\n    return 2\n"
    bundle = bundle_with(py_file("a.py", source, authored=[4, 5, 6]))
    assert passes(verdict("DJANGO-C002", bundle, corpus))


# --- C027 extends comes first --------------------------------------------------------------


def test_c027_passes_when_only_a_comment_precedes_extends(corpus):
    source = '{# a licence note #}\n{% extends "base.html" %}\n'
    assert passes(verdict("DJANGO-C027", bundle_with(tpl_file("t.html", source)), corpus))


def test_c027_fails_when_markup_precedes_extends(corpus):
    source = '<div></div>\n{% extends "base.html" %}\n'
    row = verdict("DJANGO-C027", bundle_with(tpl_file("t.html", source)), corpus)
    assert row.verdict == "fail"


def test_c027_not_applicable_to_a_template_that_extends_nothing(corpus):
    row = verdict("DJANGO-C027", bundle_with(tpl_file("t.html", PLAIN_TEMPLATE)), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


def test_c027_ignores_a_preexisting_misplaced_extends(corpus):
    source = '<div></div>\n{% extends "base.html" %}\n<p>new</p>\n'
    bundle = bundle_with(tpl_file("t.html", source, authored=[3]))
    row = verdict("DJANGO-C027", bundle, corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


# --- C028 spacing inside {{ }} -------------------------------------------------------------


def test_c028_passes_one_space_inside_a_variable_tag(corpus):
    source = "<p>{{ user.name }}</p>\n"
    assert passes(verdict("DJANGO-C028", bundle_with(tpl_file("t.html", source)), corpus))


def test_c028_fails_a_tag_with_no_inner_spaces(corpus):
    row = verdict("DJANGO-C028", bundle_with(tpl_file("t.html", "<p>{{user.name}}</p>\n")), corpus)
    assert row.verdict == "fail"


def test_c028_not_applicable_without_a_variable_tag(corpus):
    row = verdict("DJANGO-C028", bundle_with(tpl_file("t.html", PLAIN_TEMPLATE)), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


def test_c028_ignores_a_preexisting_tight_variable_tag(corpus):
    source = "<p>{{user}}</p>\n<p>{{ other }}</p>\n"
    bundle = bundle_with(tpl_file("t.html", source, authored=[2]))
    assert passes(verdict("DJANGO-C028", bundle, corpus))


# --- C029 {% load %} alphabetical ----------------------------------------------------------


def test_c029_passes_alphabetised_libraries(corpus):
    source = "{% load humanize i18n %}\n"
    assert passes(verdict("DJANGO-C029", bundle_with(tpl_file("t.html", source)), corpus))


def test_c029_fails_unsorted_libraries(corpus):
    row = verdict("DJANGO-C029", bundle_with(tpl_file("t.html", "{% load i18n humanize %}\n")), corpus)
    assert row.verdict == "fail"


def test_c029_not_applicable_to_a_single_library(corpus):
    row = verdict("DJANGO-C029", bundle_with(tpl_file("t.html", "{% load i18n %}\n")), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


def test_c029_not_applicable_to_the_load_from_form(corpus):
    # `{% load foo from bar %}` names a tag and a library, not a list to alphabetise.
    row = verdict("DJANGO-C029", bundle_with(tpl_file("t.html", "{% load zzz from aaa %}\n")), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


def test_c029_ignores_a_preexisting_unsorted_load(corpus):
    source = "{% load i18n humanize %}\n{% load a b %}\n"
    bundle = bundle_with(tpl_file("t.html", source, authored=[2]))
    assert passes(verdict("DJANGO-C029", bundle, corpus))


# --- C030 spacing inside {% %} -------------------------------------------------------------


def test_c030_passes_one_space_inside_a_block_tag(corpus):
    source = "{% if user %}hi{% endif %}\n"
    assert passes(verdict("DJANGO-C030", bundle_with(tpl_file("t.html", source)), corpus))


def test_c030_fails_a_tag_with_no_inner_spaces(corpus):
    row = verdict("DJANGO-C030", bundle_with(tpl_file("t.html", "{%if user%}hi{% endif %}\n")), corpus)
    assert row.verdict == "fail"


def test_c030_not_applicable_without_a_block_tag(corpus):
    row = verdict("DJANGO-C030", bundle_with(tpl_file("t.html", PLAIN_TEMPLATE)), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


def test_c030_ignores_a_preexisting_tight_block_tag(corpus):
    source = "{%if user%}\n<p>new</p>\n{% endif %}\n"
    bundle = bundle_with(tpl_file("t.html", source, authored=[2, 3]))
    assert passes(verdict("DJANGO-C030", bundle, corpus))


# --- C031 {% endblock %} names its block ---------------------------------------------------


def test_c031_passes_a_named_endblock(corpus):
    source = "{% block content %}\n  <p>hi</p>\n{% endblock content %}\n"
    assert passes(verdict("DJANGO-C031", bundle_with(tpl_file("t.html", source)), corpus))


def test_c031_fails_an_unnamed_endblock_on_another_line(corpus):
    source = "{% block content %}\n  <p>hi</p>\n{% endblock %}\n"
    row = verdict("DJANGO-C031", bundle_with(tpl_file("t.html", source)), corpus)
    assert row.verdict == "fail"


def test_c031_fails_an_endblock_naming_a_different_block(corpus):
    source = "{% block content %}\n  <p>hi</p>\n{% endblock sidebar %}\n"
    row = verdict("DJANGO-C031", bundle_with(tpl_file("t.html", source)), corpus)
    assert row.verdict == "fail"


def test_c031_not_applicable_when_the_block_closes_on_its_own_line(corpus):
    source = "{% block title %}Home{% endblock %}\n"
    row = verdict("DJANGO-C031", bundle_with(tpl_file("t.html", source)), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


def test_c031_ignores_a_preexisting_unnamed_endblock(corpus):
    source = "{% block a %}\n{% endblock %}\n{% block b %}\n{% endblock b %}\n"
    bundle = bundle_with(tpl_file("t.html", source, authored=[3, 4]))
    assert passes(verdict("DJANGO-C031", bundle, corpus))


# --- C032 token spacing inside tags --------------------------------------------------------


def test_c032_passes_a_singly_spaced_expression(corpus):
    source = "{% if user == owner %}hi{% endif %}\n"
    assert passes(verdict("DJANGO-C032", bundle_with(tpl_file("t.html", source)), corpus))


def test_c032_keeps_attribute_access_and_filters_tight(corpus):
    source = '{{ object.title|date:"Y" }}\n'
    assert passes(verdict("DJANGO-C032", bundle_with(tpl_file("t.html", source)), corpus))


def test_c032_fails_a_spaced_attribute_access(corpus):
    row = verdict("DJANGO-C032", bundle_with(tpl_file("t.html", "{{ user . name }}\n")), corpus)
    assert row.verdict == "fail"


def test_c032_fails_an_unspaced_comparison(corpus):
    row = verdict("DJANGO-C032", bundle_with(tpl_file("t.html", "{% if a==b %}x{% endif %}\n")), corpus)
    assert row.verdict == "fail"


def test_c032_not_applicable_to_a_single_token_tag(corpus):
    row = verdict("DJANGO-C032", bundle_with(tpl_file("t.html", "<p>{{ total }}</p>\n")), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


def test_c032_ignores_a_preexisting_badly_spaced_tag(corpus):
    source = "{{ user . name }}\n{{ other.name }}\n"
    bundle = bundle_with(tpl_file("t.html", source, authored=[2]))
    assert passes(verdict("DJANGO-C032", bundle, corpus))


# --- C033 top-level blocks are flush left --------------------------------------------------


EXTENDING = '{% extends "base.html" %}\n{% block content %}\n  <p>hi</p>\n{% endblock content %}\n'


def test_c033_passes_a_flush_left_top_level_block(corpus):
    assert passes(verdict("DJANGO-C033", bundle_with(tpl_file("t.html", EXTENDING)), corpus))


def test_c033_passes_an_indented_nested_block(corpus):
    source = ('{% extends "base.html" %}\n'
              "{% block outer %}\n"
              "  {% block inner %}hi{% endblock inner %}\n"
              "{% endblock outer %}\n")
    assert passes(verdict("DJANGO-C033", bundle_with(tpl_file("t.html", source)), corpus))


def test_c033_fails_an_indented_top_level_block(corpus):
    source = EXTENDING.replace("{% block content %}", "  {% block content %}")
    row = verdict("DJANGO-C033", bundle_with(tpl_file("t.html", source)), corpus)
    assert row.verdict == "fail"


def test_c033_not_applicable_when_the_template_extends_nothing(corpus):
    source = "  {% block content %}\n  <p>hi</p>\n  {% endblock content %}\n"
    row = verdict("DJANGO-C033", bundle_with(tpl_file("t.html", source)), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


def test_c033_ignores_a_preexisting_indented_block(corpus):
    source = ('{% extends "base.html" %}\n'
              "  {% block old %}old{% endblock old %}\n"
              "{% block new %}\n"
              "{% endblock new %}\n")
    bundle = bundle_with(tpl_file("t.html", source, authored=[3, 4]))
    assert passes(verdict("DJANGO-C033", bundle, corpus))


# --- the batch as a whole ------------------------------------------------------------------


IMPORT_AND_TEMPLATE_RULES = (
    "DJANGO-C002", "DJANGO-C019", "DJANGO-C020", "DJANGO-C021", "DJANGO-C022",
    "DJANGO-C023", "DJANGO-C024", "DJANGO-C025", "DJANGO-C026", "DJANGO-C027",
    "DJANGO-C028", "DJANGO-C029", "DJANGO-C030", "DJANGO-C031", "DJANGO-C032",
    "DJANGO-C033", "DJANGO-C039", "DJANGO-C041",
)


def test_all_eighteen_are_registered():
    assert [r for r in IMPORT_AND_TEMPLATE_RULES if r not in RULES] == []


def test_none_of_the_eighteen_fires_on_a_file_the_agent_only_read(corpus):
    """Invariant 5, over the whole batch at once.

    A Python module and a template, each carrying every fault these rules look for, and
    neither of them written by the agent -- its one added line is compliant. Any rule that
    reports a violation here is judging the file's history instead of the contribution.
    """
    source = (
        "from django.views.generic.base import View\n"   # C019/C020/C026
        "import zzz\n"                                    # C020 alphabetical
        "from ..models import Thing\n"                    # C022
        "from os import sep, path\n"                      # C023
        "import unusedmod\n"                              # C041
        "from django.conf import settings\n"
        "DEBUG = settings.DEBUG\n"                        # C025/C039
        "def old():\n"
        "   return (View, zzz, Thing, sep, path, DEBUG)\n"  # C002
        "\n"
        "\n"
        "def new():\n"
        "    return 1\n"
    )
    template = (
        "<div></div>\n"
        '{% extends "base.html" %}\n'                     # C027
        "{% load i18n humanize %}\n"                      # C029
        "  {%block content%}\n"                           # C030/C033
        "  <p>{{user . name}}</p>\n"                      # C028/C032
        "  {% endblock %}\n"                              # C031
        "<p>new</p>\n"
    )
    bundle = bundle_with(
        py_file("a.py", source, authored=[12, 13]),
        tpl_file("t.html", template, authored=[7]),
    )
    offenders = {}
    for rule_id in IMPORT_AND_TEMPLATE_RULES:
        row = verdict(rule_id, bundle, corpus)
        if row.verdict == "fail":
            offenders[rule_id] = row.notes[:80]
    assert offenders == {}, offenders
