# mwaskom/seaborn: off-nav rule sources (raw, verbatim)

Repo: `mwaskom/seaborn` @ `master`
Docs: https://seaborn.pydata.org/
Docs version at pull time: **UNRESOLVED**

Any doc page served on a different version is a fetch failure, not a row.

Raw source, HTML comments intact. The rendered GitHub view strips comments,
and in template files the comments carry the actual obligations. Extract from
this text, not from a rendered page.

Role `context` means the file informs Section context and Auto-fix but never
produces sheet rows.

| Path | Role | Status | Note |
|---|---|---|---|
| `.github/CONTRIBUTING.md` | rules | ok | rule source or redirect |
| `.pre-commit-config.yaml` | context | ok | decides the Auto-fix column |
| `README.md` | context | ok | check for canonical test invocation |
| `pyproject.toml` | context | ok | may hold lint config |

---

## `.github/CONTRIBUTING.md`

Role: **rules**. rule source or redirect

```markdown
Contributing to seaborn
=======================

General support
---------------

General support questions ("how do I do X?") are most at home on [StackOverflow](https://stackoverflow.com/), which has a larger audience of people who will see your post and may be able to offer assistance. Your chance of getting a quick answer will be higher if you include runnable code, a precise statement of what you are hoping to achieve, and a clear explanation of the problems that you have encountered.

Reporting bugs
--------------

If you think you've encountered a bug in seaborn, please report it on the [Github issue tracker](https://github.com/mwaskom/seaborn/issues/new). To be useful, bug reports *must* include the following information:

- A reproducible code example that demonstrates the problem
- The output that you are seeing (an image of a plot, or the error message)
- A clear explanation of why you think something is wrong
- The specific versions of seaborn and matplotlib that you are working with

Bug reports are easiest to address if they can be demonstrated using one of the example datasets from the seaborn docs (i.e. with `seaborn.load_dataset`). Otherwise, it is preferable that your example generate synthetic data to reproduce the problem. If you can only demonstrate the issue with your actual dataset, you will need to share it, ideally as a csv (do not share data as a pickle file).

If you've encountered an error, searching the specific text of the message before opening a new issue can often help you solve the problem quickly and avoid making a duplicate report.

Because matplotlib handles the actual rendering, errors or incorrect outputs may be due to a problem in matplotlib rather than one in seaborn. It can save time if you try to reproduce the issue in an example that uses only matplotlib, so that you can report it in the right place. But it is alright to skip this step if it's not obvious how to do it.


New features
------------

If you think there is a new feature that should be added to seaborn, you can open an issue to discuss it. But please be aware that current development efforts are mostly focused on standardizing the API and internals, and there may be relatively low enthusiasm for novel features that do not fit well into short- and medium-term development plans.

```

---

## `.pre-commit-config.yaml`

Role: **context**. decides the Auto-fix column

```yaml
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.3.0
    hooks:
    -   id: check-yaml
    -   id: end-of-file-fixer
    -   id: trailing-whitespace
        exclude: \.svg$
-   repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.20
    hooks:
    -   id: ruff
        exclude: seaborn/(cm\.py|external/)
        types: [file, python]
-   repo: https://github.com/astral-sh/ty-pre-commit
    rev: v0.0.56
    hooks:
    -   id: ty
        # ty resolves imports from the environment; install the scientific stack
        # plus stubs. Scope comes from [tool.ty.src] in pyproject.toml.
        args: [--no-default-groups, --extra=stats, --group=typecheck]

```

---

## `README.md`

Role: **context**. check for canonical test invocation

```markdown
<img src="https://raw.githubusercontent.com/mwaskom/seaborn/master/doc/_static/logo-wide-lightbg.svg"><br>

--------------------------------------

seaborn: statistical data visualization
=======================================

[![PyPI Version](https://img.shields.io/pypi/v/seaborn.svg)](https://pypi.org/project/seaborn/)
[![License](https://img.shields.io/pypi/l/seaborn.svg)](https://github.com/mwaskom/seaborn/blob/master/LICENSE.md)
[![DOI](https://joss.theoj.org/papers/10.21105/joss.03021/status.svg)](https://doi.org/10.21105/joss.03021)
[![Tests](https://github.com/mwaskom/seaborn/workflows/CI/badge.svg)](https://github.com/mwaskom/seaborn/actions)
[![Code Coverage](https://codecov.io/gh/mwaskom/seaborn/branch/master/graph/badge.svg)](https://codecov.io/gh/mwaskom/seaborn)

Seaborn is a Python visualization library based on matplotlib. It provides a high-level interface for drawing attractive statistical graphics.


Documentation
-------------

Online documentation is available at [seaborn.pydata.org](https://seaborn.pydata.org).

The docs include a [tutorial](https://seaborn.pydata.org/tutorial.html), [example gallery](https://seaborn.pydata.org/examples/index.html), [API reference](https://seaborn.pydata.org/api.html), [FAQ](https://seaborn.pydata.org/faq), and other useful information.

To build the documentation locally, please refer to [`doc/README.md`](doc/README.md).

Dependencies
------------

Seaborn supports Python 3.10+.

Installation requires [numpy](https://numpy.org/), [pandas](https://pandas.pydata.org/), and [matplotlib](https://matplotlib.org/). Some advanced statistical functionality requires [scipy](https://www.scipy.org/) and/or [statsmodels](https://www.statsmodels.org/).


Installation
------------

The latest stable release (and required dependencies) can be installed from PyPI:

    uv pip install seaborn

It is also possible to include optional statistical dependencies:

    uv pip install seaborn[stats]

Seaborn can also be installed with conda:

    conda install seaborn

Note that the main anaconda repository lags PyPI in adding new releases, but conda-forge (`-c conda-forge`) typically updates quickly.

Citing
------

A paper describing seaborn has been published in the [Journal of Open Source Software](https://joss.theoj.org/papers/10.21105/joss.03021). The paper provides an introduction to the key features of the library, and it can be used as a citation if seaborn proves integral to a scientific publication.

Testing
-------

Testing seaborn requires installing additional dependencies; they will be installed when running `uv sync` with a source checkout.

To test the code, run `make test` in the source directory. This will exercise the unit tests (using [pytest](https://docs.pytest.org/)) and generate a coverage report.

Code style is enforced with `ruff` using the settings in the [`pyproject.toml`](./pyproject.toml) file. Run `make lint` to check. Alternately, you can use `pre-commit` to automatically run lint checks on any files you are committing: just run `pre-commit install` to set it up, and then commit as usual going forward.

Development
-----------

Seaborn development takes place on Github: https://github.com/mwaskom/seaborn

Please submit bugs that you encounter to the [issue tracker](https://github.com/mwaskom/seaborn/issues) with a reproducible example demonstrating the problem. Questions about usage are more at home on StackOverflow, where there is a [seaborn tag](https://stackoverflow.com/questions/tagged/seaborn).

```

---

## `pyproject.toml`

Role: **context**. may hold lint config

```toml
[build-system]
requires = ["flit_core >=3.2,<4"]
build-backend = "flit_core.buildapi"

[project]
name = "seaborn"
description = "Statistical data visualization"
authors = [{name = "Michael Waskom", email = "mwaskom@gmail.com"}]
readme = "README.md"
license = {file = "LICENSE.md"}
dynamic = ["version"]
classifiers = [
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: BSD License",
    "Topic :: Scientific/Engineering :: Visualization",
    "Topic :: Multimedia :: Graphics",
    "Operating System :: OS Independent",
    "Framework :: Matplotlib",
]
requires-python = ">=3.10"
dependencies = [
    "numpy>=2.0",
    "pandas>=2.2",
    "matplotlib>=3.9",
]

[project.optional-dependencies]
stats = [
    "scipy>=1.14",
    "statsmodels>=0.14.3",
]

[dependency-groups]
test = [
    "pytest==9.1.1",
    "pytest-cov==7.1.0",
    "pytest-xdist==3.8.0",
]
lint = [
    "ruff==0.15.20",
]
# Type checking requires Python >=3.12 to pull in scientific Python stubs
typecheck = [
    "ty==0.0.56",
    "pandas-stubs==3.0.3.260530 ; python_version >= '3.12'",
    "scipy-stubs==1.18.0.0 ; python_version >= '3.12'",
]
docs = [
    "numpydoc==1.6.0",
    "nbconvert==7.17.1",
    "ipykernel==7.3.0",
    "sphinx==9.1.0",
    "sphinx-copybutton==0.5.2",
    "sphinx-issues==5.0.1",
    "sphinx-design==0.7.0",
    "pyyaml==6.0.3",
    "pydata_sphinx_theme==0.19.0",
]
dev = [
    {include-group = "test"},
    {include-group = "lint"},
    {include-group = "typecheck"},
    "seaborn[stats]",
    "pre-commit==4.6.0",
    "flit==3.12.0",
    "jupyterlab==4.6.1",
]

[tool.uv]
default-groups = "all"

[tool.uv.dependency-groups]
docs = { requires-python = ">=3.12" }

[project.urls]
Source = "https://github.com/mwaskom/seaborn"
Docs = "http://seaborn.pydata.org"

[tool.flit.sdist]
exclude = ["doc/_static/*.svg"]

[tool.pytest.ini_options]
filterwarnings = [
   "ignore:The --rsyncdir command line argument and rsyncdirs config variable are deprecated.:DeprecationWarning",
   "ignore:\\s*Pyarrow will become a required dependency of pandas:DeprecationWarning",
   "ignore:datetime.datetime.utcfromtimestamp\\(\\) is deprecated:DeprecationWarning",
 ]

[tool.ruff]
line-length = 88
extend-exclude = ["seaborn/cm.py", "seaborn/external"]

[tool.ruff.lint]
select = ["E", "W", "F"]
ignore = ["E741", "F522"]

[tool.ty.environment]
python = "./.venv"
python-version = "3.13"

[tool.ty.src]
include = ["seaborn/_core", "seaborn/_marks", "seaborn/_stats"]

[tool.ty.rules]
# A number of ty checks are ignored because the code was originally written using mypy
# with much weaker upstream typing (i.e. in numpy / pandas / matplotlib)
# Gradually address these and remove the rule ignores over time.
possibly-missing-submodule = "ignore"  # `import matplotlib as mpl` -> `mpl.text.Text` idiom
invalid-method-override = "ignore"      # intentional Mark._plot / Scale._get_* signatures
invalid-argument-type = "ignore"        # matplotlib/pandas/numpy arg types stricter than usage
unresolved-attribute = "ignore"         # attributes on `Axis | None` and numpy unions
not-subscriptable = "ignore"            # subscripting numpy `ArrayLike` unions
not-iterable = "ignore"                 # iterating numpy `ArrayLike` unions
unsupported-operator = "ignore"         # arithmetic on pandas/numpy/scipy unions
invalid-assignment = "ignore"           # assigning to matplotlib-typed slots
no-matching-overload = "ignore"         # matplotlib overloaded APIs
call-non-callable = "ignore"            # object-typed matplotlib slots
call-top-callable = "ignore"            # numpy callables with unknown signatures
invalid-return-type = "ignore"          # return values widened by stub unions

[tool.coverage.run]
omit = [
    "seaborn/widgets.py",
    "seaborn/external/*",
    "seaborn/colors/*",
    "seaborn/cm.py",
    "seaborn/conftest.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]

```
