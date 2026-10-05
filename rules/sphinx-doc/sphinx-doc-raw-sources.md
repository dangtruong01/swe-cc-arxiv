# sphinx-doc/sphinx: off-nav rule sources (raw, verbatim)

Repo: `sphinx-doc/sphinx` @ `master`
Docs: https://www.sphinx-doc.org/en/master/
Docs version at pull time: **UNRESOLVED**

Any doc page served on a different version is a fetch failure, not a row.

Raw source, HTML comments intact. The rendered GitHub view strips comments,
and in template files the comments carry the actual obligations. Extract from
this text, not from a rendered page.

Role `context` means the file informs Section context and Auto-fix but never
produces sheet rows.

| Path | Role | Status | Note |
|---|---|---|---|
| `.github/ISSUE_TEMPLATE/bug-report.yml` | rules | ok | expect X-ISSUE |
| `.github/ISSUE_TEMPLATE/config.yml` | rules | ok | expect X-ISSUE |
| `.github/ISSUE_TEMPLATE/feature_request.md` | rules | ok | expect X-ISSUE |
| `.github/PULL_REQUEST_TEMPLATE.md` | rules | ok | obligations hide in HTML comments |
| `CONTRIBUTING.rst` | rules | ok | rule source or redirect |
| `README.rst` | context | ok | check for canonical test invocation |
| `doc/internals/contributing.rst` | rules | ok | rule source or redirect | DUPLICATE RISK: source of a rendered doc page, do not extract twice |
| `pyproject.toml` | context | ok | may hold lint config |
| `tox.ini` | context | ok | may hold lint config |

---

## `.github/ISSUE_TEMPLATE/bug-report.yml`

Role: **rules**. expect X-ISSUE

```yaml
name: Bug report
description: Something is not working correctly.
labels: "type:bug"

body:
  - type: textarea
    attributes:
      label: Describe the bug
      description: >-
        A clear and concise description of what the bug is, including the 
        expected behaviour and what has gone wrong.
        
        Please include screenshots, if applicable.
    validations:
      required: true

  - type: textarea
    attributes:
      label: How to Reproduce
      description: >-
        Please provide steps to reproduce this bug, with the smallest possible
        set of source files. For normal bugs this should ideally be one 
        ``index.rst`` file, and for ``sphinx.ext.autodoc`` bugs, this should
        ideally be a single ``index.rst`` file, and a single example Python 
        module.
      placeholder: |
        Minimal method (you can also paste the contents of ``index.rst`` and
        ``conf.py`` into this report):
        ```bash
        $ echo "Content demonstrating the bug..." > index.rst
        $ echo "" > conf.py
        $ sphinx-build -M html . _build
        $ # open _build/html/index and see bla bla
        ```
        
        ``git clone`` method (this is advised against, to help the Sphinx team):
        ```bash
        $ git clone https://github.com/.../some_project
        $ cd some_project
        $ pip install -r requirements.txt
        $ cd docs
        $ make html SPHINXOPTS="-D language=de"
        $ # open _build/html/index and see bla bla
        ```
    validations:
      required: true

  - type: markdown
    attributes:
      value: |
        ## Environment info

  - type: textarea
    attributes:
      label: Environment Information
      render: text
      description: >-
        Install the latest Sphinx 
        ``pip install -U "sphinx>=5.3"``
        then run ``sphinx-build --bug-report`` or ``python -m sphinx --bug-report``.
        and paste the output here.
    validations:
      required: true
  - type: textarea
    attributes:
      label: Sphinx extensions
      render: python
      description: >-
        Attempt to reproduce your error with the smallest set of extensions possible.
        This makes it easier to determine where the problem you are encountering is.
        
        e.g. ``["sphinx.ext.autodoc", "recommonmark"]``
    validations:
      required: false
  - type: textarea
    attributes:
      label: Additional context
      description: >-
        Add any other context about the problem here, for example:
        
        * Any other tools used (Browser, TeX, etc) with versions
        * Reference to another issue or pull request
        * URL to some external resource

```

---

## `.github/ISSUE_TEMPLATE/config.yml`

Role: **rules**. expect X-ISSUE

```yaml
# Ref: https://help.github.com/en/github/building-a-strong-community/configuring-issue-templates-for-your-repository#configuring-the-template-chooser
blank_issues_enabled: false  # default: true
contact_links:
- name: Question
  url: https://stackoverflow.com/questions/tagged/python-sphinx
  about: For Q&A purpose, please use Stackoverflow with the tag python-sphinx
- name: Discussion
  url: https://github.com/sphinx-doc/sphinx/discussions
  about: For general discussion, please use GitHub Discussions.

```

---

## `.github/ISSUE_TEMPLATE/feature_request.md`

Role: **rules**. expect X-ISSUE

```markdown
---
name: Feature request
about: Suggest an idea for this project
title: '<short description for the feature>'
labels: 'type:proposal'
assignees: ''

---

**Is your feature request related to a problem? Please describe.**
A clear and concise description of what the problem is. Ex. I'm always frustrated when [...]

**Describe the solution you'd like**
A clear and concise description of what you want to happen.

**Describe alternatives you've considered**
A clear and concise description of any alternative solutions or features you've considered.

**Additional context**
Add any other context or screenshots about the feature request here.

- [e.g. URL or Ticket]


```

---

## `.github/PULL_REQUEST_TEMPLATE.md`

Role: **rules**. obligations hide in HTML comments

```markdown
<!--
Thank you for creating this pull request and for spending time to help Sphinx!
Our contributors' guide can be found online: https://www.sphinx-doc.org/en/master/internals/contributing.html
Ask any questions at https://github.com/sphinx-doc/sphinx/discussions
-->


## Purpose

<!--
A description of the purpose of this pull request.
Ensure that all relevant information is included for reviewers,
including any environment-specific details.

* If you plan to add tests or documentation after opening this PR,
  please note it here.
* For user-visible changes, remember to add an entry to CHANGES.rst.
* Please add your name to AUTHORS.rst if you haven't already!
-->


## References

<!--
Please add any relevant links here, especially including any 
GitHub issues or Pull Requests that this PR would resolve.
This helps to ensure that reviewers have context from
previous discussions or decisions.
-->

- <...>
- <...>
- <...>


## AI Disclosure

<!--
If AI was used in the preparation of this pull request, please disclose the
tool(s) used, how they were used, and specify what code or text is AI generated.
If no AI tools were used, please write "No AI tools used" in this section.
Please read our policy on AI generated code:
https://www.sphinx-doc.org/en/master/internals/ai-policy.html

In particular, all interaction is to be done by humans, including submission
of pull requests.
-->

```

---

## `CONTRIBUTING.rst`

Role: **rules**. rule source or redirect

```rst
======================
Contributing to Sphinx
======================

Interested in contributing to Sphinx? Hurrah! We welcome all forms of
contribution, including code patches, documentation improvements and bug
reports/feature requests.

Our contributing guide can be found online at:

https://www.sphinx-doc.org/en/master/internals/contributing.html

You can also browse it from this repository from
``doc/internals/contributing.rst``

Sphinx uses GitHub to host source code, track patches and bugs, and more.
Please make an effort to provide as much detail as possible when filing
bugs.

```

---

## `README.rst`

Role: **context**. check for canonical test invocation

```rst
========
 Sphinx
========

.. image:: https://img.shields.io/pypi/v/sphinx.svg
   :target: https://pypi.org/project/Sphinx/
   :alt: Package on PyPI

.. image:: https://github.com/sphinx-doc/sphinx/actions/workflows/main.yml/badge.svg
   :target: https://github.com/sphinx-doc/sphinx/actions/workflows/main.yml
   :alt: Build Status

.. image:: https://readthedocs.org/projects/sphinx/badge/?version=master
   :target: https://www.sphinx-doc.org/
   :alt: Documentation Status

.. image:: https://img.shields.io/badge/License-BSD%202--Clause-blue.svg
   :target: https://opensource.org/licenses/BSD-2-Clause
   :alt: BSD 2 Clause

**Sphinx makes it easy to create intelligent and beautiful documentation.**

Sphinx uses reStructuredText as its markup language, and many of its strengths
come from the power and straightforwardness of reStructuredText and its parsing
and translating suite, the Docutils.

Features
========

* **Output formats**: HTML, PDF, plain text, EPUB, TeX, manual pages, and more
* **Extensive cross-references**: semantic markup and automatic links
  for functions, classes, glossary terms and similar pieces of information
* **Hierarchical structure**: easy definition of a document tree, with automatic
  links to siblings, parents and children
* **Automatic indices**: general index as well as a module index
* **Code highlighting**: automatic highlighting using the Pygments highlighter
* **Templating**: Flexible HTML output using the Jinja 2 templating engine
* **Extension ecosystem**: Many extensions are available, for example for
  automatic function documentation or working with Jupyter notebooks.
* **Language Support**: Python, C, C++, JavaScript, mathematics, and many other
  languages through extensions.

For more information, refer to `the documentation`_.

Installation
============

The following command installs Sphinx from the `Python Package Index`_. You will
need a working installation of Python and pip.

.. code-block:: shell

   pip install -U sphinx

Contributing
============

We appreciate all contributions! Refer to `the contributors guide`_ for
information.

.. _the documentation: https://www.sphinx-doc.org/
.. _the contributors guide: https://www.sphinx-doc.org/en/master/internals/contributing.html
.. _Python Package Index: https://pypi.org/project/Sphinx/

```

---

## `doc/internals/contributing.rst`

Role: **rules**. rule source or redirect | DUPLICATE RISK: source of a rendered doc page, do not extract twice

```rst
======================
Contributing to Sphinx
======================

There are many ways you can contribute to Sphinx, be it filing bug reports or
feature requests, writing new documentation or submitting patches for new or
fixed behavior. This guide serves to illustrate how you can get started with
this.


Get help
--------

The Sphinx community maintains a number of mailing lists and IRC channels.

Stack Overflow with tag `python-sphinx`_
    Questions and answers about use and development.

`GitHub Discussions Q&A`__
    Question-and-answer style forum for discussions.

    __ https://github.com/orgs/sphinx-doc/discussions/categories/q-a

sphinx-users <sphinx-users@googlegroups.com>
    Mailing list for user support.

sphinx-dev <sphinx-dev@googlegroups.com>
    Mailing list for development related discussions.

#sphinx-doc on irc.libera.chat
    IRC channel for development questions and user support.

.. _python-sphinx: https://stackoverflow.com/questions/tagged/python-sphinx


Bug Reports and Feature Requests
--------------------------------

If you have encountered a problem with Sphinx or have an idea for a new
feature, please submit it to the `issue tracker`_ on GitHub.

For bug reports, please include the output produced during the build process
and also the log file Sphinx creates after it encounters an unhandled
exception.
The location of this file should be shown towards the end of the error message.
Please also include the output of :program:`sphinx-build --bug-report`.

Including or providing a link to the source files involved may help us fix the
issue.  If possible, try to create a minimal project that produces the error
and post that instead.

.. _`issue tracker`: https://github.com/sphinx-doc/sphinx/issues


Contribute code
---------------

The Sphinx source code is managed using Git and is `hosted on GitHub`_.  The
recommended way for new contributors to submit code to Sphinx is to fork this
repository and submit a pull request after committing changes to their fork.
The pull request will then need to be approved by one of the core developers
before it is merged into the main repository.

.. _hosted on GitHub: https://github.com/sphinx-doc/sphinx


.. _contribute-get-started:

Getting started
~~~~~~~~~~~~~~~

Before starting on a patch, we recommend checking for open issues
or opening a fresh issue to start a discussion around a feature idea or a bug.
If you feel uncomfortable or uncertain about an issue or your changes,
feel free to `start a discussion`_.

.. _start a discussion: https://github.com/orgs/sphinx-doc/discussions/

These are the basic steps needed to start developing on Sphinx.

#. Create an account on GitHub.

#. Fork_ the main Sphinx repository (`sphinx-doc/sphinx`_)
   using the GitHub interface.

   .. _Fork: https://github.com/sphinx-doc/sphinx/fork
   .. _sphinx-doc/sphinx: https://github.com/sphinx-doc/sphinx

#. Clone the forked repository to your machine.

   .. code-block:: shell

      git clone https://github.com/<USERNAME>/sphinx
      cd sphinx

#. Install uv and set up your environment.

   We recommend using :program:`uv` for dependency management.
   Install it with:

   .. code-block:: shell

      python -m pip install -U uv

   Then, set up your environment:

   .. code-block:: shell

       uv sync

   **Alternative:** If you prefer not to use :program:`uv`, you can use
   :program:`pip`:

   .. code-block:: shell

       python -m venv .venv
       . .venv/bin/activate
       python -m pip install -e .

#. Create a new working branch. Choose any name you like.

   .. code-block:: shell

      git switch -c feature-xyz

#. Hack, hack, hack.

   Write your code along with tests that shows that the bug was fixed or that
   the feature works as expected.

#. Add a bullet point to :file:`CHANGES.rst` if the fix or feature is not trivial
   (small doc updates, typo fixes), then commit:

   .. code-block:: shell

      git commit -m 'Add useful new feature that does this.'

#. Push changes in the branch to your forked repository on GitHub:

   .. code-block:: shell

      git push origin feature-xyz

#. Submit a pull request from your branch to the ``master`` branch.

   GitHub recognizes certain phrases that can be used to automatically
   update the issue tracker.
   For example, including 'Closes #42' in the body of your pull request
   will close issue #42 if the PR is merged.

#. Wait for a core developer or contributor to review your changes.

   You may be asked to address comments on the review. If so, please avoid
   force pushing to the branch. Sphinx uses the *squash merge* strategy when
   merging PRs, so follow-up commits will all be combined.


Coding style
~~~~~~~~~~~~

Please follow these guidelines when writing code for Sphinx:

* Try to use the same code style as used in the rest of the project.

* For non-trivial changes, please update the :file:`CHANGES.rst` file.
  If your changes alter existing behavior, please document this.

* New features should be documented.
  Include examples and use cases where appropriate.
  If possible, include a sample that is displayed in the generated output.

* When adding a new configuration variable,
  be sure to :doc:`document it </usage/configuration>`
  and update :file:`sphinx/cmd/quickstart.py` if it's important enough.

* Add appropriate unit tests.

Style and type checks can be run as follows:

.. code-block:: shell

    uv run ruff check
    uv run ruff format
    uv run mypy


Unit tests
~~~~~~~~~~

Sphinx is tested using pytest_ for Python code and Jasmine_ for JavaScript.

.. _pytest: https://docs.pytest.org/en/latest/
.. _Jasmine: https://jasmine.github.io/

To run Python unit tests, we recommend using :program:`tox`, which provides a number
of targets and allows testing against multiple different Python environments:

* To list all possible targets:

  .. code-block:: shell

     tox -av

* To run unit tests for a specific Python version, such as Python 3.14:

  .. code-block:: shell

     tox -e py314

* Arguments to :program:`pytest` can be passed via :program:`tox`,
  e.g., in order to run a particular test:

  .. code-block:: shell

     tox -e py314 tests/test_module.py::test_new_feature

You can also test by installing dependencies in your local environment:

  .. code-block:: shell

     uv run pytest

Or with :program:`pip`:

  .. code-block:: shell

     python -m pip install . --group test
     pytest

To run JavaScript tests, use :program:`npm`:

.. code-block:: shell

   npm install
   npm run test

.. tip::

   :program:`jasmine` requires a Firefox binary to use as a test browser.

   On Unix systems, you can check the presence and location of the ``firefox``
   binary at the command-line by running ``command -v firefox``.

New unit tests should be included in the :file:`tests/` directory where necessary:

* For bug fixes, first add a test that fails without your changes and passes
  after they are applied.

* Tests that need a :program:`sphinx-build` run should be integrated in one of the
  existing test modules if possible.

* Tests should be quick and only test the relevant components, as we aim that
  *the test suite should not take more than a minute to run*.
  In general, avoid using the ``app`` fixture and ``app.build()``
  unless a full integration test is required.

.. versionadded:: 1.8

   Sphinx also runs JavaScript tests.

.. versionchanged:: 1.5.2
   Sphinx was switched from nose to pytest.


Contribute documentation
------------------------

Contributing to documentation involves modifying the source files
found in the :file:`doc/` folder.
To get started, you should first follow :ref:`contribute-get-started`,
and then take the steps below to work with the documentation.

The following sections describe how to get started with contributing
documentation, as well as key aspects of a few different tools that we use.

.. todo:: Add a more extensive documentation contribution guide.


Build the documentation
~~~~~~~~~~~~~~~~~~~~~~~

To build the documentation, run the following command:

.. code-block:: shell

   sphinx-build -M html ./doc ./build/sphinx --fail-on-warning

This will parse the Sphinx documentation's source files and generate HTML for
you to preview in :file:`build/sphinx/html`.

You can also build a **live version of the documentation** that you can preview
in the browser. It will detect changes and reload the page any time you make
edits.
To do so, use `sphinx-autobuild`_ to run the following command:

.. code-block:: shell

   sphinx-autobuild ./doc ./build/sphinx/

.. _sphinx-autobuild: https://github.com/sphinx-doc/sphinx-autobuild

Translations
------------

The parts of messages in Sphinx that go into builds are translated into several
locales.  The translations are kept as gettext ``.po`` files translated from the
master template :file:`sphinx/locale/sphinx.pot`.

These Sphinx core messages are translated using the online `Transifex
<https://explore.transifex.com/sphinx-doc/sphinx-1/>`__ platform.

Translated strings from the platform are pulled into the Sphinx repository
by a maintainer before a new release.

We do not accept pull requests altering the translation files directly.
Instead, please contribute translations via the Transifex platform.

Translations notes for maintainers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The `transifex CLI <https://developers.transifex.com/docs/cli>`__ (``tx``)
can be used to pull translations in ``.po`` format from Transifex.
To do this, go to :file:`sphinx/locale` and then run ``tx pull -f -l LANG``
where ``LANG`` is an existing language identifier.
It is good practice to run ``python utils/babel_runner.py update`` afterwards
to make sure the ``.po`` file has the canonical Babel formatting.

Sphinx uses `Babel <https://babel.pocoo.org/en/latest/>`_ to extract messages
and maintain the catalog files.  The :file:`utils` directory contains a helper
script, :file:`utils/babel_runner.py`.

* Use ``python babel_runner.py extract`` to update the ``.pot`` template.
* Use ``python babel_runner.py update`` to update all existing language
  catalogs in ``sphinx/locale/*/LC_MESSAGES`` with the current messages in the
  template file.
* Use ``python babel_runner.py compile`` to compile the ``.po`` files to binary
  ``.mo`` files and ``.js`` files.

When an updated ``.po`` file is submitted, run
``python babel_runner.py compile`` to commit both the source and the compiled
catalogs.

When a new locale is added, add a new directory with the ISO 639-1 language
identifier and put ``sphinx.po`` in there.  Don't forget to update the possible
values for :confval:`language` in :file:`doc/usage/configuration.rst`.


Debugging tips
--------------

* Delete the build cache before building documents if you make changes in the
  code by running the command ``make clean`` or using the
  :option:`sphinx-build --fresh-env` option.

* Use the :option:`sphinx-build --pdb` option to run ``pdb`` on exceptions.

* Use ``node.pformat()`` and ``node.asdom().toxml()`` to generate a printable
  representation of the document structure.

* Set the configuration variable :confval:`keep_warnings` to ``True`` so
  warnings will be displayed in the generated output.

* Set the configuration variable :confval:`nitpicky` to ``True`` so that Sphinx
  will complain about references without a known target.

* Set the debugging options in the `Docutils configuration file
  <https://docutils.sourceforge.io/docs/user/config.html>`_.


Updating generated files
------------------------

* JavaScript stemming algorithms in :file:`sphinx/search/non-minified-js/*.js`
  and stopword files in :file:`sphinx/search/_stopwords/`
  are generated from the `Snowball project`_
  by running :file:`utils/generate_snowball.py`.

  Minified files in :file:`sphinx/search/minified-js/*.js` are generated from
  non-minified ones using :program:`uglifyjs` (installed via npm).
  See :file:`sphinx/search/minified-js/README.rst`.

  .. _Snowball project: https://snowballstem.org/

* The :file:`searchindex.js` files found in
  the :file:`tests/js/fixtures/*` directories
  are generated by using the standard Sphinx HTML builder
  on the corresponding input projects found in :file:`tests/js/roots/*`.
  The fixtures provide test data used by the Sphinx JavaScript unit tests,
  and can be regenerated by running
  the :file:`utils/generate_js_fixtures.py` script.

```

---

## `pyproject.toml`

Role: **context**. may hold lint config

```toml
[build-system]
requires = ["flit_core>=3.12"]
build-backend = "flit_core.buildapi"

# project metadata
[project]
name = "Sphinx"
description = "Python documentation generator"
readme = "README.rst"
urls.Changelog = "https://www.sphinx-doc.org/en/master/changes.html"
urls.Code = "https://github.com/sphinx-doc/sphinx"
urls.Documentation = "https://www.sphinx-doc.org/"
urls.Download = "https://pypi.org/project/Sphinx/"
urls.Homepage = "https://www.sphinx-doc.org/"
urls."Issue tracker" = "https://github.com/sphinx-doc/sphinx/issues"
license = "BSD-2-Clause"
license-files = [
    "LICENSE.rst",
]
requires-python = ">=3.12"

# Classifiers list: https://pypi.org/classifiers/
classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Environment :: Console",
    "Environment :: Web Environment",
    "Intended Audience :: Developers",
    "Intended Audience :: Education",
    "Intended Audience :: End Users/Desktop",
    "Intended Audience :: Information Technology",
    "Intended Audience :: Other Audience",
    "Intended Audience :: Science/Research",
    "Intended Audience :: System Administrators",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: 3.14",
    "Programming Language :: Python :: 3.15",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Python :: Implementation :: PyPy",
    "Framework :: Sphinx",
    "Framework :: Sphinx :: Domain",
    "Framework :: Sphinx :: Extension",
    "Framework :: Sphinx :: Theme",
    "Topic :: Documentation",
    "Topic :: Documentation :: Sphinx",
    "Topic :: Education",
    "Topic :: Internet :: WWW/HTTP :: Site Management",
    "Topic :: Internet :: WWW/HTTP :: Site Management :: Link Checking",
    "Topic :: Printing",
    "Topic :: Software Development",
    "Topic :: Software Development :: Documentation",
    "Topic :: Text Editors :: Documentation",
    "Topic :: Text Processing",
    "Topic :: Text Processing :: General",
    "Topic :: Text Processing :: Indexing",
    "Topic :: Text Processing :: Markup",
    "Topic :: Text Processing :: Markup :: HTML",
    "Topic :: Text Processing :: Markup :: LaTeX",
    "Topic :: Text Processing :: Markup :: Markdown",
    "Topic :: Text Processing :: Markup :: reStructuredText",
    "Topic :: Text Processing :: Markup :: XML",
    "Topic :: Utilities",
    "Typing :: Typed",
]
dependencies = [
    "sphinxcontrib-applehelp>=1.0.7",
    "sphinxcontrib-devhelp>=1.0.6",
    "sphinxcontrib-htmlhelp>=2.0.6",
    "sphinxcontrib-jsmath>=1.0.1",
    "sphinxcontrib-qthelp>=1.0.6",
    "sphinxcontrib-serializinghtml>=1.1.9",
    "Jinja2>=3.1",
    "Pygments>=2.17",
    "docutils>=0.21,<0.23",
    "snowballstemmer>=2.2",
    "babel>=2.13",
    "alabaster>=0.7.14",
    "imagesize>=1.3",
    "requests>=2.30.0",
    "roman-numerals>=1.0.0",
    "packaging>=23.0",
    "colorama>=0.4.6; sys_platform == 'win32'",
]
dynamic = ["version"]

[[project.authors]]
name = "Adam Turner"
email = "aa-turner@users.noreply.github.com"

[[project.authors]]
name = "Georg Brandl"
email = "georg@python.org"

[project.scripts]
sphinx-build = "sphinx.cmd.build:main"
sphinx-quickstart = "sphinx.cmd.quickstart:main"
sphinx-apidoc = "sphinx.ext.apidoc:main"
sphinx-autogen = "sphinx.ext.autosummary.generate:main"

[dependency-groups]
docs = [
    "sphinxcontrib-websupport",
]
lint = [
    "ruff==0.14.9",
    "sphinx-lint>=0.9",
]
package = [
    "build",
    "pypi-attestations==0.0.28",
    "twine>=6.1",
]
test = [
    "pytest>=9.0",
    "pytest-xdist[psutil]>=3.4",
    "cython>=3.0",  # for Cython compilation
    "defusedxml>=0.7.1",  # for secure XML/HTML parsing
    "setuptools>=70.0",  # for Cython compilation
    "typing_extensions>=4.9",  # for typing_extensions.Unpack
]
translations = [
    "babel>=2.13",
    "Jinja2>=3.1",
]
types = [
    "mypy==1.19.1",
    "pyrefly",
    "pyright==1.1.407",
    # Newer releases report hundreds of diagnostics with the current rule ignores.
    "ty==0.0.10",
    { include-group = "type-stubs" },
]
type-stubs = [
    # align with versions used elsewhere
    "types-colorama==0.4.15.20250801",
    "types-defusedxml==0.7.0.20250822",
    "types-docutils==0.22.3.20251115",
    "types-Pillow==10.2.0.20240822",
    "types-Pygments==2.19.0.20251121",
    "types-requests==2.32.4.20250913",
    "types-urllib3==1.26.25.14",
]

[tool.flit.module]
name = "sphinx"

[tool.flit.sdist]
include = [
    "LICENSE.rst",
    "AUTHORS.rst",
    "CHANGES.rst",
    # Documentation
    "doc/",
    "CODE_OF_CONDUCT.rst",  # used as an include in the Documentation
    "EXAMPLES.rst",  # used as an include in the Documentation
    # Tests
    "tests/",
    "tox.ini",
    # Utilities
    "utils/",
    "babel.cfg",
]
exclude = [
    "doc/_build",
]

[tool.mypy]
files = [
    "doc/conf.py",
    "doc/development/tutorials/examples/autodoc_intenum.py",
    "doc/development/tutorials/examples/helloworld.py",
    "sphinx",
    "tests",
    "utils",
]
exclude = [
    "tests/roots",
]
python_version = "3.12"
strict = true
show_column_numbers = true
show_error_context = true
strict_equality = false
warn_return_any = false
enable_error_code = [
    "type-arg",
    "redundant-self",
    "truthy-iterable",
    "ignore-without-code",
    "unused-awaitable",
]

[[tool.mypy.overrides]]
module = [
    "sphinx.domains.c",
    "sphinx.domains.c._ast",
    "sphinx.domains.c._parser",
    "sphinx.domains.c._symbol",
    "sphinx.domains.cpp",
    "sphinx.domains.cpp._ast",
    "sphinx.domains.cpp._parser",
    "sphinx.domains.cpp._symbol",
]
strict_optional = false

[[tool.mypy.overrides]]
module = [
    "imagesize",
    "pyximport",
    "snowballstemmer",
]
ignore_missing_imports = true

[[tool.mypy.overrides]]
module = [
    # tests/
    "tests.test_search",
    # tests/test_config
    "tests.test_config.test_config",
    # tests/test_directives
    "tests.test_directives.test_directive_other",
    # tests/test_domains
    "tests.test_domains.test_domain_c",
    "tests.test_domains.test_domain_cpp",
    "tests.test_domains.test_domain_js",
    "tests.test_domains.test_domain_py",
    "tests.test_domains.test_domain_py_fields",
    "tests.test_domains.test_domain_py_pyfunction",
    "tests.test_domains.test_domain_py_pyobject",
    "tests.test_domains.test_domain_std",
    # tests/test_environment
    "tests.test_environment.test_environment_toctree",
    # tests/test_ext_autodoc
    "tests.test_ext_autodoc.test_ext_autodoc",
    "tests.test_ext_autodoc.test_ext_autodoc_mock",
    # tests/test_ext_autosummary
    "tests.test_ext_autosummary.test_ext_autosummary",
    # tests/test_ext_intersphinx
    "tests.test_ext_intersphinx.test_ext_intersphinx",
    # tests/test_ext_napoleon
    "tests.test_ext_napoleon.test_ext_napoleon_docstring",
    # tests/test_extensions
    "tests.test_extensions.test_ext_apidoc",
    "tests.test_extensions.test_ext_inheritance_diagram",
    # tests/test_util
    "tests.test_util.test_util_inspect",
    "tests.test_util.test_util_nodes",
    "tests.test_util.test_util_typing",
]
check_untyped_defs = false
disable_error_code = [
    "annotation-unchecked",
]
disallow_untyped_calls = false
disallow_untyped_defs = false

[[tool.mypy.overrides]]
module = ["tests.test_util.typing_test_data"]
ignore_errors = true

[tool.coverage.run]
branch = true
parallel = true
source = ['sphinx']

[tool.coverage.report]
exclude_lines = [
    # Have to re-enable the standard pragma
    'pragma: no cover',
    # Don't complain if tests don't hit defensive assertion code:
    'raise NotImplementedError',
    # Don't complain if non-runnable code isn't run:
    'if __name__ == .__main__.:',
]
ignore_errors = true

[tool.pyright]
typeCheckingMode = "strict"
include = [
    "doc/conf.py",
    "doc/development/tutorials/examples/autodoc_intenum.py",
    "doc/development/tutorials/examples/helloworld.py",
    "sphinx",
    "tests",
    "utils",
]
exclude = [
    "tests/roots",
]

reportArgumentType = "none"
reportAssignmentType = "none"
reportAttributeAccessIssue = "none"
reportCallIssue = "none"
reportConstantRedefinition = "none"
reportGeneralTypeIssues = "none"
reportIncompatibleMethodOverride = "none"
reportIncompatibleVariableOverride = "none"
reportIndexIssue = "none"
reportInvalidTypeForm = "none"
reportMissingImports = "none"
reportMissingModuleSource = "none"
reportMissingParameterType = "none"
reportMissingTypeArgument = "none"
reportMissingTypeStubs = "none"
reportOperatorIssue = "none"
reportOptionalMemberAccess = "none"
reportOptionalSubscript = "none"
reportPossiblyUnboundVariable = "none"
reportPrivateUsage = "none"
reportRedeclaration = "none"
reportReturnType = "none"
reportUnknownArgumentType = "none"
reportUnknownLambdaType = "none"
reportUnknownMemberType = "none"
reportUnknownParameterType = "none"
reportUnknownVariableType = "none"
reportUnnecessaryComparison = "none"
reportUnnecessaryIsInstance = "none"
reportUntypedBaseClass = "none"
reportUntypedNamedTuple = "none"
reportUnusedClass = "none"
reportUnusedFunction = "none"
reportUnusedImport = "none"
reportUnusedVariable = "none"

[tool.uv]
default-groups = "all"

```

---

## `tox.ini`

Role: **context**. may hold lint config

```ini
[tox]
minversion = 4.2.0
envlist = py{312,313,314,315}

[testenv]
usedevelop = True
passenv =
    https_proxy
    http_proxy
    no_proxy
    COLORTERM
    PERL
    PERL5LIB
    PYTEST_ADDOPTS
    DO_EPUBCHECK
    EPUBCHECK_PATH
    TERM
    CLEAN
    BUILDER
    READTHEDOCS
description =
    py{312,313,314,315}: Run unit tests against {envname}.
dependency_groups =
    test
setenv =
    PYTHONWARNINGS = error
    PYTEST_ADDOPTS = {env:PYTEST_ADDOPTS:} --color yes
commands=
    python -X dev -X warn_default_encoding -m pytest --durations 25 {posargs}

[testenv:lint]
description =
    Run linters.
dependency_groups =
    lint
    package
    test
    types
# If you update any of these commands, don't forget to update the equivalent
# GitHub Workflow step
commands =
    ruff check .
    mypy
    pyright

[testenv:docs]
description =
    Build documentation.
dependency_groups =
    docs
commands =
    python -c "import shutil; shutil.rmtree('./build/sphinx', ignore_errors=True) if '{env:CLEAN:}' else None"
    sphinx-build -M {env:BUILDER:html} ./doc ./build/sphinx --fail-on-warning {posargs}

[testenv:docs-live]
description =
    Build documentation.
dependency_groups =
    docs
deps =
    sphinx-autobuild
commands =
    sphinx-autobuild ./doc ./build/sphinx/

[testenv:bindep]
description =
    Install binary dependencies.
deps =
    bindep
commands =
    bindep test

[testenv:ruff]
description =
    Run ruff formatting and linting.
dependency_groups =
    lint
commands =
    ruff format .
    ruff check --fix .

[testenv:mypy]
description =
    Run mypy type checking.
dependency_groups =
    types
commands =
    mypy {posargs}

[testenv:prettier]
description =
    Run the Prettier JavaScript formatter.
commands =
    npx prettier@3.5 --write "sphinx/themes/**/*.js" "!sphinx/themes/bizstyle/static/css3-mediaqueries*.js" "tests/js/**/*.{js,mjs}" "!tests/js/fixtures/**"

```
