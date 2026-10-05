"""Unit tests for the shared Python extractor (docs/checker-authoring.md §9).

The point of most of these is position. Ownership is decided by line number
(invariant 5), so an example reported one line off can be credited to the wrong author,
and nothing downstream would notice -- the rule would simply judge somebody else's code.
"""

from __future__ import annotations

import textwrap

from compliance.extractors import python_ast as pa

MODULE = textwrap.dedent('''\
    """Module docstring.

    Examples
    ========

    >>> 1 + 1
    2
    """
    from sympy.testing.pytest import raises, XFAIL
    import numpy as np
    from sympy import *


    class Widget(object):
        """A widget.

        Examples
        ========

        >>> from sympy.abc import x
        >>> Widget(x)
        Widget(x)
        """

        def spin(self):
            """Spin it.

            >>> Widget(1).spin()
            None
            """
            return None


    @XFAIL
    def test_spin():
        assert Widget(1).spin() is None
        raises(TypeError, lambda: Widget())
        try:
            Widget()
        except TypeError:
            pass
''')


def parse():
    return pa.parse_module(MODULE, "sympy/widget.py")


def test_a_syntax_error_is_recorded_not_raised():
    module = pa.parse_module("def f(:\n    pass\n", "broken.py")
    assert module.ok is False and module.error
    assert module.functions == ()


def test_missing_source_is_recorded_as_unavailable():
    assert pa.parse_module(None, "gone.py").ok is False


def test_every_doctest_example_lands_on_its_own_prompt_line():
    """The regression that motivated the rewrite: examples were reported one line early,
    because the offset was taken from the `def` rather than the docstring's first line."""
    module = parse()
    lines = MODULE.split("\n")
    assert module.doctests
    for example in module.doctests:
        assert ">>>" in lines[example.lineno - 1], (example.lineno, example.source)


def test_docstring_positions_cover_their_own_text():
    module = parse()
    lines = MODULE.split("\n")
    for docstring in module.docstrings:
        first = docstring.text.split("\n")[0]
        assert first in lines[docstring.lineno - 1]


def test_class_docstring_does_not_own_its_methods_lines():
    """`enclosing` ownership rests on this: editing a method must not make the class
    docstring's doctests the agent's to answer for."""
    module = parse()
    widget = next(d for d in module.docstrings if d.owner == "Widget")
    spin = next(f for f in module.functions if f.name == "spin")
    assert spin.lineno in range(*widget.def_span)
    assert not (set(range(spin.lineno, spin.end_lineno + 1)) & widget.def_own_lines)


def test_import_map_resolves_a_short_name_to_its_origin():
    module = parse()
    assert module.origin("raises") == "sympy.testing.pytest.raises"
    assert module.origin("np") == "numpy"
    assert module.origin("Widget") == "Widget"  # never imported, comes back unchanged


def test_star_imports_are_reported_separately():
    assert parse().star_imports() == ("sympy",)


def test_functions_carry_decorators_and_spans():
    module = parse()
    test_spin = next(f for f in module.functions if f.name == "test_spin")
    assert test_spin.is_test and test_spin.has_decorator("XFAIL")
    assert test_spin.qualname == "test_spin"
    assert test_spin.end_lineno > test_spin.lineno


def test_try_blocks_and_asserts_are_collected():
    module = parse()
    assert len(module.tries) == 1
    assert len(module.asserts) == 1


def test_enclosing_function_finds_the_innermost_definition():
    module = parse()
    spin = next(f for f in module.functions if f.name == "spin")
    assert module.enclosing_function(spin.end_lineno).name == "spin"


def test_parsing_is_memoised_but_still_a_pure_function():
    assert pa.parse_module(MODULE, "x.py") is pa.parse_module(MODULE, "x.py")
    assert pa.parse_module(MODULE, "x.py").source == MODULE


def test_is_test_path():
    assert pa.is_test_path("sympy/geometry/tests/test_point.py")
    assert pa.is_test_path("sympy/foo/test_bar.py")
    assert not pa.is_test_path("sympy/geometry/point.py")
