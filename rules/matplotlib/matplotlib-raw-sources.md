# matplotlib/matplotlib: off-nav rule sources (raw, verbatim)

Repo: `matplotlib/matplotlib` @ `main`
Docs: https://matplotlib.org/devdocs/
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
| `.github/ISSUE_TEMPLATE/bug_report.yml` | rules | ok | expect X-ISSUE |
| `.github/ISSUE_TEMPLATE/config.yml` | rules | ok | expect X-ISSUE |
| `.github/ISSUE_TEMPLATE/documentation.yml` | rules | ok | expect X-ISSUE |
| `.github/ISSUE_TEMPLATE/feature_request.yml` | rules | ok | expect X-ISSUE |
| `.github/ISSUE_TEMPLATE/maintenance.yml` | rules | ok | expect X-ISSUE |
| `.github/ISSUE_TEMPLATE/tag_proposal.yml` | rules | ok | expect X-ISSUE |
| `.github/PULL_REQUEST_TEMPLATE.md` | rules | ok | obligations hide in HTML comments |
| `.pre-commit-config.yaml` | context | ok | decides the Auto-fix column |
| `CODE_OF_CONDUCT.md` | rules | ok | expect X-GOV |
| `README.md` | context | ok | check for canonical test invocation |
| `pyproject.toml` | context | ok | may hold lint config |
| `tox.ini` | context | ok | may hold lint config |

---

## `.github/CONTRIBUTING.md`

Role: **rules**. rule source or redirect

```markdown
Please refer to the [contributing guide](https://matplotlib.org/devel/index.html).

```

---

## `.github/ISSUE_TEMPLATE/bug_report.yml`

Role: **rules**. expect X-ISSUE

```yaml
---
name: Bug Report
description: Report a bug or issue with Matplotlib.
title: "[Bug]: "
body:
  - type: textarea
    id: summary
    attributes:
      label: Bug summary
      description: Describe the bug in 1-2 short sentences
    validations:
      required: true
  - type: textarea
    id: reproduction
    attributes:
      label: Code for reproduction
      description: >-
        If possible, please provide a minimum self-contained example.  If you
        have used generative AI as an aid see
        https://matplotlib.org/devdocs/devel/contribute.html#restrictions-on-generative-ai-usage
      placeholder: Paste your code here. This field is automatically formatted as Python code.
      render: Python
    validations:
      required: true
  - type: textarea
    id: actual
    attributes:
      label: Actual outcome
      description: >-
        Paste the output produced by the code provided above, e.g.
        console output, images/videos produced by the code, any relevant screenshots/screencasts, etc.
    validations:
      required: true
  - type: textarea
    id: expected
    attributes:
      label: Expected outcome
      description: Describe (or provide a visual example of) the expected outcome from the code snippet.
    validations:
      required: true
  - type: textarea
    id: details
    attributes:
      label: Additional information
      description: |
        - What are the conditions under which this bug happens? input parameters, edge cases, etc?
        - Has this worked in earlier versions?
        - Do you know why this bug is happening?
        - Do you maybe even know a fix?
  - type: input
    id: operating-system
    attributes:
      label: Operating system
      description: Windows, OS/X, Arch, Debian, Ubuntu, etc.
  - type: input
    id: matplotlib-version
    attributes:
      label: Matplotlib Version
      description: "From Python prompt: `import matplotlib; print(matplotlib.__version__)`"
    validations:
      required: true
  - type: input
    id: matplotlib-backend
    attributes:
      label: Matplotlib Backend
      description: "From Python prompt: `import matplotlib; print(matplotlib.get_backend())`"
  - type: input
    id: python-version
    attributes:
      label: Python version
      description: "In console: `python --version`"
  - type: input
    id: jupyter-version
    attributes:
      label: Jupyter version
      description: "In console: `jupyter notebook --version` or `jupyter lab --version`"
  - type: dropdown
    id: install
    attributes:
      label: Installation
      description: How did you install matplotlib?
      options:
        - pip
        - conda
        - pixi
        - uv
        - Linux package manager
        - from source (.tar.gz)
        - git checkout

```

---

## `.github/ISSUE_TEMPLATE/config.yml`

Role: **rules**. expect X-ISSUE

```yaml
# Reference:
# https://help.github.com/en/github/building-a-strong-community/configuring-issue-templates-for-your-repository#configuring-the-template-chooser
---
blank_issues_enabled: true  # default
contact_links:
  - name: Question/Support/Other
    url: https://discourse.matplotlib.org
    about: If you have a usage question
  - name: Chat with devs
    url: https://discourse.matplotlib.org/chat/c/matplotlib/2
    about: Ask short questions about contributing to Matplotlib

```

---

## `.github/ISSUE_TEMPLATE/documentation.yml`

Role: **rules**. expect X-ISSUE

```yaml
---
name: Documentation
description: Create a report to help us improve the documentation
title: "[Doc]: "
labels: [Documentation]
body:
  - type: input
    id: link
    attributes:
      label: Documentation Link
      description: >-
        Link to any documentation or examples that you are referencing. Suggested improvements should be based
        on [the development version of the docs](https://matplotlib.org/devdocs/)
      placeholder: https://matplotlib.org/devdocs/...
  - type: textarea
    id: problem
    attributes:
      label: Problem
      description: What is missing, unclear, or wrong in the documentation?
      placeholder: |
        * I found [...] to be unclear because [...]
        * [...] made me think that [...] when really it should be [...]
        * There is no example showing how to do [...]
    validations:
      required: true
  - type: textarea
    id: improvement
    attributes:
      label: Suggested improvement
      placeholder: |
        * This line should be be changed to say [...]
        * Include a paragraph explaining [...]
        * Add a figure showing [...]

```

---

## `.github/ISSUE_TEMPLATE/feature_request.yml`

Role: **rules**. expect X-ISSUE

```yaml
---
name: Feature Request
description: Suggest something to add to Matplotlib!
title: "[ENH]: "
labels: [New feature]
body:
  - type: markdown
    attributes:
      value: >-
        Please search the [issues](https://github.com/matplotlib/matplotlib/issues) for relevant feature
        requests before creating a new feature request.
  - type: textarea
    id: problem
    attributes:
      label: Problem
      description: Briefly describe the problem this feature will solve. (2-4 sentences)
      placeholder: |
        * I'm always frustrated when [...] because [...]
        * I would like it if [...] happened when I [...] because [...]
        * Here is a sample image of what I am asking for [...]
    validations:
      required: true
  - type: textarea
    id: solution
    attributes:
      label: Proposed solution
      description: Describe a way to accomplish the goals of this feature request.

```

---

## `.github/ISSUE_TEMPLATE/maintenance.yml`

Role: **rules**. expect X-ISSUE

```yaml
---
name: Maintenance
description: Help improve performance, usability and/or consistency.
title: "[MNT]: "
labels: [Maintenance]
body:
  - type: textarea
    id: summary
    attributes:
      label: Summary
      description: Please provide 1-2 short sentences that succinctly describes what could be improved.
    validations:
      required: true
  - type: textarea
    id: fix
    attributes:
      label: Proposed fix
      description: Please describe how you think this could be improved.

```

---

## `.github/ISSUE_TEMPLATE/tag_proposal.yml`

Role: **rules**. expect X-ISSUE

```yaml
---
name: Tag Proposal
description: Suggest a new tag or subcategory for the gallery of examples
title: "[Tag]: "
labels: ["Documentation: tags"]
body:
  - type: markdown
    attributes:
      value: >-
        Please search the [tag glossary]() for relevant tags before creating a new tag proposal.
  - type: textarea
    id: need
    attributes:
      label: Need
      description: Briefly describe the need this tag will fill. (1-4 sentences)
      placeholder: |
        * A tag is needed for examples that share [...]
        * Existing tags do not work because [...]
        * Current gallery examples that would use this tag include [...]
        * Indicate which subcategory this tag falls under, or whether a new subcategory is proposed.
    validations:
      required: true
  - type: textarea
    id: solution
    attributes:
      label: Proposed solution
      description: >-
        What should the tag be? All tags are in the format `subcategory: tag`

```

---

## `.github/PULL_REQUEST_TEMPLATE.md`

Role: **rules**. obligations hide in HTML comments

```markdown
<!-- Thank you for your contribution! -->
<!-- 👉 Please check our development guide https://matplotlib.org/devdocs/devel/index.html -->
<!-- 👉 Tips for pull requests: https://matplotlib.org/devdocs/devel/pr_guide.html#pull-request-guidelines -->

## PR summary
<!-- ✍️ Describe what issue is resolved and why you chose this solution in your own words (no AI please). -->
<!-- 👉 Tip: Use "Closes #0000" to link the related issue -->


## AI Disclosure
<!-- ✍️ Describe if and how AI is used. See https://matplotlib.org/devdocs/devel/contribute.html#use-of-generative-ai -->


## PR quality check
<!-- ✍️ Please check the relevant boxes below: "x" to indicate completion, "N/A" if the item is not applicable -->

- [ ] Use an expressive title, e.g. "Fix title font property precedence"
- [ ] New and changed code is [tested](https://matplotlib.org/devdocs/devel/testing.html)
- [ ] Plotting related features are demonstrated in an [example](https://matplotlib.org/devdocs/devel/document.html#write-examples-and-tutorials)
- [ ] New features and API changes have  [release notes](https://matplotlib.org/devdocs/devel/api_changes.html#announce-changes-deprecations-and-new-features)
- [ ] Documentation complies with [general](https://matplotlib.org/devdocs/devel/document.html#write-rest-pages) and [docstring](https://matplotlib.org/devdocs/devel/document.html#write-docstrings) guidelines

```

---

## `.pre-commit-config.yaml`

Role: **context**. decides the Auto-fix column

```yaml
---
ci:
  autofix_prs: false
  autoupdate_schedule: 'quarterly'
exclude: |
  (?x)^(
    extern|
    subprojects/packagefiles|
    LICENSE|
    lib/matplotlib/mpl-data|
    doc/devel/gitwash|
    doc/release/prev|
    doc/api/prev|
    lib/matplotlib/tests/data/tinypages
    )
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: 3e8a8703264a2f4a69428a0aa4dcb512790b2c8c  # frozen: v6.0.0
    hooks:
      - id: check-added-large-files
      - id: check-docstring-first
        exclude: lib/matplotlib/typing.py  # docstring used for attribute flagged by check
      - id: end-of-file-fixer
        exclude_types: [diff, svg]
      - id: mixed-line-ending
      - id: name-tests-test
        args: ["--pytest-test-first"]
      - id: no-commit-to-branch  # Default is master and main.
      - id: trailing-whitespace
        exclude_types: [diff, svg]
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: d2823d321df3af8f878f7ee3414dc94d037145b9  # frozen: v2.1.0
    hooks:
      - id: mypy
        additional_dependencies:
          - pandas-stubs
          - types-pillow
          - types-python-dateutil
          - types-psutil
          - types-docutils
          - types-PyYAML
        args: ["--config-file=pyproject.toml", "lib/matplotlib"]
        files: lib/matplotlib  # Only run when files in lib/matplotlib are changed.
        pass_filenames: false
  - repo: https://github.com/astral-sh/ruff-pre-commit
    # Ruff version.
    rev: c59bba8fb259db0fec2bbb77ad8ba51ea7341b56  # frozen: v0.15.20
    hooks:
      # Run the linter.
      - id: ruff-check
        args: [--fix, --show-fixes]
  - repo: https://github.com/codespell-project/codespell
    rev: 2ccb47ff45ad361a21071a7eedda4c37e6ae8c5a  # frozen: v2.4.2
    hooks:
      - id: codespell
        files: ^.*\.(py|c|cpp|h|m|md|rst|yml)$
        args:
          - "--ignore-words"
          - "ci/codespell-ignore-words.txt"
          - "--skip"
          - "doc/project/credits.rst"
  - repo: https://github.com/pycqa/isort
    rev: a333737ed43df02b18e6c95477ea1b285b3de15a  # frozen: 8.0.1
    hooks:
      - id: isort
        name: isort (python)
        files: ^galleries/tutorials/|^galleries/examples/|^galleries/plot_types/
  - repo: https://github.com/rstcheck/rstcheck
    rev: d8774e96810795967ed9603f445b4e751e7b313f  # frozen: v6.3.0
    hooks:
      - id: rstcheck
        additional_dependencies:
          - sphinx>=1.8.1
        args: ["--sphinx-source-dir", "doc"]
  - repo: https://github.com/adrienverge/yamllint
    rev: cba56bcde1fdd01c1deb3f945e69764c291a6530  # frozen: v1.38.0
    hooks:
      - id: yamllint
        args: ["--strict", "--config-file=.yamllint.yml"]
  - repo: https://github.com/shellcheck-py/shellcheck-py
    rev: 745eface02aef23e168a8afb6b5737818efbea95  # frozen: v0.11.0.1
    hooks:
      - id: shellcheck
  - repo: https://github.com/zizmorcore/zizmor-pre-commit
    rev: e3eebf65325ccc992422292cb7a4baee967cf815  # frozen: v1.26.1
    hooks:
      - id: zizmor
  - repo: https://github.com/simple-icons/svglint
    rev: 8402586b94f073686e46707a163082e270ee5768  # frozen: v4.2.1
    hooks:
      - id: svglint
        # Override the top-level exclude so that mpl-data/images/ toolbar
        # icons are also linted.  Exemptions for the intentional interactive
        # SVG examples are handled in .svglintrc.mjs.
        exclude: '^$'
  - repo: https://github.com/python-jsonschema/check-jsonschema
    rev: 5030dca3047414c338091455ac41803200ec1f0f  # frozen: 0.37.3
    hooks:
      # TODO: Re-enable this when https://github.com/microsoft/azure-pipelines-vscode/issues/567 is fixed.
      # - id: check-azure-pipelines
      - id: check-dependabot
      - id: check-github-workflows
      # NOTE: If any of the below schema files need to be changed, be sure to
      # update the `ci/vendor_schemas.py` script.
      - id: check-jsonschema
        name: "Validate AppVeyor config"
        files: ^\.appveyor\.yml$
        args: ["--verbose", "--schemafile", "ci/schemas/appveyor.json"]
      - id: check-jsonschema
        name: "Validate CircleCI config"
        files: ^\.circleci/config\.yml$
        args: ["--verbose", "--schemafile", "ci/schemas/circleciconfig.json"]
      - id: check-jsonschema
        name: "Validate GitHub funding file"
        files: ^\.github/FUNDING\.yml$
        args: ["--verbose", "--schemafile", "ci/schemas/github-funding.json"]
      - id: check-jsonschema
        name: "Validate GitHub issue config"
        files: ^\.github/ISSUE_TEMPLATE/config\.yml$
        args: ["--verbose", "--schemafile", "ci/schemas/github-issue-config.json"]
      - id: check-jsonschema
        name: "Validate GitHub issue templates"
        files: ^\.github/ISSUE_TEMPLATE/.*\.yml$
        exclude: ^\.github/ISSUE_TEMPLATE/config\.yml$
        args: ["--verbose", "--schemafile", "ci/schemas/github-issue-forms.json"]
      - id: check-jsonschema
        name: "Validate CodeCov config"
        files: ^\.github/codecov\.yml$
        args: ["--verbose", "--schemafile", "ci/schemas/codecov.json"]
      - id: check-jsonschema
        name: "Validate GitHub labeler config"
        files: ^\.github/labeler\.yml$
        args: ["--verbose", "--schemafile", "ci/schemas/pull-request-labeler-5.json"]
      - id: check-jsonschema
        name: "Validate Conda environment file"
        files: ^environment\.yml$
        args: ["--verbose", "--schemafile", "ci/schemas/conda-environment.json"]
  - repo: https://github.com/oxipng/oxipng
    rev: 628e241e23f368097883807fa6e985ccf7c00357  # frozen: v10.1.1
    hooks:
      - id: oxipng

```

---

## `CODE_OF_CONDUCT.md`

Role: **rules**. expect X-GOV

```markdown
<!--placeholder page so Github knows we have a CoC-->

Our Code of Conduct is at
https://matplotlib.org/stable/project/code_of_conduct.html

It is rendered from `doc/project/code_of_conduct.rst`

```

---

## `README.md`

Role: **context**. check for canonical test invocation

```markdown
[![PyPi](https://img.shields.io/pypi/v/matplotlib)](https://pypi.org/project/matplotlib/)
[![Conda](https://img.shields.io/conda/vn/conda-forge/matplotlib)](https://anaconda.org/conda-forge/matplotlib)
[![Downloads](https://img.shields.io/pypi/dm/matplotlib)](https://pypi.org/project/matplotlib)
[![NUMFocus](https://img.shields.io/badge/powered%20by-NumFOCUS-orange.svg?style=flat&colorA=E1523D&colorB=007D8A)](https://numfocus.org)
[![LFX Health Score](https://insights.linuxfoundation.org/api/badge/health-score?project=matplotlib)](https://insights.linuxfoundation.org/project/matplotlib)

[![Discourse help forum](https://img.shields.io/badge/help_forum-discourse-blue.svg)](https://discourse.matplotlib.org)
[![Discourse chat](https://img.shields.io/badge/chat-discourse-mediumaquamarine)](https://discourse.matplotlib.org/chat/c/matplotlib/2)
[![GitHub issues](https://img.shields.io/badge/issue_tracking-github-blue.svg)](https://github.com/matplotlib/matplotlib/issues)
[![Contributing](https://img.shields.io/badge/PR-Welcome-%23FF8300.svg?)](https://matplotlib.org/stable/devel/index.html)

[![GitHub actions status](https://github.com/matplotlib/matplotlib/workflows/Tests/badge.svg)](https://github.com/matplotlib/matplotlib/actions?query=workflow%3ATests)
[![Azure pipelines status](https://dev.azure.com/matplotlib/matplotlib/_apis/build/status/matplotlib.matplotlib?branchName=main)](https://dev.azure.com/matplotlib/matplotlib/_build/latest?definitionId=1&branchName=main)
[![AppVeyor status](https://ci.appveyor.com/api/projects/status/github/matplotlib/matplotlib?branch=main&svg=true)](https://ci.appveyor.com/project/matplotlib/matplotlib)
[![Codecov status](https://codecov.io/github/matplotlib/matplotlib/badge.svg?branch=main&service=github)](https://app.codecov.io/gh/matplotlib/matplotlib)
[![EffVer Versioning](https://img.shields.io/badge/version_scheme-EffVer-0097a7)](https://jacobtomlinson.dev/effver)

![Matplotlib logotype](https://matplotlib.org/stable/_static/logo2.svg)

Matplotlib is a comprehensive library for creating static, animated, and
interactive visualizations in Python.

Check out our [home page](https://matplotlib.org/) for more information.

![image](https://matplotlib.org/stable/_static/readme_preview.png)

Matplotlib produces publication-quality figures in a variety of hardcopy
formats and interactive environments across platforms. Matplotlib can be
used in Python scripts, Python/IPython shells, web application servers,
and various graphical user interface toolkits.

## Install

See the [install
documentation](https://matplotlib.org/stable/users/installing/index.html),
which is generated from `/doc/install/index.rst`

## Contribute

You've discovered a bug or something else you want to change — excellent!

You've worked out a way to fix it — even better!

You want to tell us about it — best of all!

Start at the [contributing
guide](https://matplotlib.org/devdocs/devel/contribute.html)!

## Contact

[Discourse](https://discourse.matplotlib.org/) is the discussion forum
for general questions and discussions and our recommended starting
point.

Our active mailing lists (which are mirrored on Discourse) are:

-   [Users](https://mail.python.org/mailman/listinfo/matplotlib-users)
    mailing list: <matplotlib-users@python.org>
-   [Announcement](https://mail.python.org/mailman/listinfo/matplotlib-announce)
    mailing list: <matplotlib-announce@python.org>
-   [Development](https://mail.python.org/mailman/listinfo/matplotlib-devel)
    mailing list: <matplotlib-devel@python.org>

[Discourse Chat](https://discourse.matplotlib.org/chat/c/matplotlib/2) is for
coordinating development and asking questions directly related to contributing
to matplotlib.

## Citing Matplotlib

If Matplotlib contributes to a project that leads to publication, please
acknowledge this by citing Matplotlib.

[A ready-made citation
entry](https://matplotlib.org/stable/users/project/citing.html) is
available.

```

---

## `pyproject.toml`

Role: **context**. may hold lint config

```toml
[project]
name = "matplotlib"
authors = [
  {email = "matplotlib-users@python.org"},
  {name = "John D. Hunter, Michael Droettboom"}
]
description = "Python plotting package"
readme = "README.md"
license = { file = "LICENSE/LICENSE" }
dynamic = ["version"]
classifiers=[
    "Development Status :: 5 - Production/Stable",
    "Framework :: Matplotlib",
    "Intended Audience :: Science/Research",
    "Intended Audience :: Education",
    "License :: OSI Approved :: Python Software Foundation License",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: 3.14",
    "Topic :: Scientific/Engineering :: Visualization",
]

# When updating the list of dependencies, add an api_changes/development
# entry and also update the following places:
# - the `build` dependency group below
# - lib/matplotlib/__init__.py (matplotlib._check_versions())
# - ci/minver-requirements.txt
# - doc/install/dependencies.rst
# - environment.yml
dependencies = [
    "contourpy >= 1.2.1",
    "cycler >= 0.12.0",
    "fonttools >= 4.28.2",
    "kiwisolver >= 1.3.1",
    "numpy >= 2.0",
    "packaging >= 20.0",
    "pillow >= 9",
    "pyparsing >= 3",
    "python-dateutil >= 2.7",
]
# Also keep in sync with find_program of meson.build.
requires-python = ">=3.12"

[project.urls]
"Homepage" = "https://matplotlib.org"
"Download" = "https://matplotlib.org/stable/install/index.html"
"Documentation" = "https://matplotlib.org"
"Source Code" = "https://github.com/matplotlib/matplotlib"
"Bug Tracker" = "https://github.com/matplotlib/matplotlib/issues"
"Forum" = "https://discourse.matplotlib.org/"
"Donate" = "https://numfocus.org/donate-to-matplotlib"

[build-system]
build-backend = "mesonpy"
# Also keep in sync with dependency groups below.
requires = [
    # meson-python 0.17.x breaks symlinks in sdists. You can remove this pin if
    # you really need it and aren't using an sdist.
    "meson-python>=0.13.2,!=0.17.*",
    "pybind11>=3",
    # setuptools_scm 10 breaks versioning in editable installs. You can remove this pin
    # if you're a downstream distributor just building wheels or your equivalent.
    "setuptools_scm>=7,<10",
]

[dependency-groups]
build = [
    # Should be the same as `[project] dependencies` above.
    "contourpy >= 1.2.1",
    "cycler >= 0.12.0",
    "fonttools >= 4.28.2",
    "kiwisolver >= 1.3.1",
    "numpy >= 2.0",
    "packaging >= 20.0",
    "pillow >= 9",
    "pyparsing >= 3",
    "python-dateutil >= 2.7",

    # Should be the same as `[build-system] requires` above.
    "meson-python>=0.13.1,!=0.17.*",
    "pybind11>=3",
    "setuptools_scm>=7,<10",
    # Not required by us but setuptools_scm without a version, so _if_
    # installed, then setuptools_scm 8 requires at least this version.
    # Unfortunately, we can't do a sort of minimum-if-installed dependency, so
    # we need to keep this for now until setuptools_scm _fully_ drops
    # setuptools.
    "setuptools>=64",
]
dev = [
    {include-group = "build"},
    {include-group = "doc"},
    {include-group = "test"},
    {include-group = "test-extra"},
    "pre-commit",
]
# Requirements for building docs
#
# You will first need a matching Matplotlib installation
# e.g (from the Matplotlib root directory)
#     pip install --group build --no-build-isolation --editable .
#
# Install the documentation requirements with:
#     pip install --group doc
#
doc = [
    "sphinx>=5.1.0,!=6.1.2",
    "colour-science",
    "ipython",
    "ipywidgets",
    "ipykernel",
    "numpydoc>=1.0",
    "mpl-sphinx-theme~=3.11.0",
    "pyyaml",
    "PyStemmer",
    "sphinxcontrib-svg2pdfconverter>=1.1.0",
    "sphinxcontrib-video>=0.2.1",
    "sphinx-copybutton",
    "sphinx-design",
    "sphinx-gallery[parallel]>=0.17.0",
    "sphinx-tags>=0.4.0",
]

# pip requirements for all the CI builds
test = [
    "black<27",
    "certifi",
    "coverage!=6.3",
    "psutil; sys_platform != 'cygwin'",
    "pytest!=4.6.0,!=5.4.0,!=8.1.0",
    "pytest-cov",
    "pytest-rerunfailures!=16.0",
    "pytest-timeout",
    "pytest-xdist",
    "pytest-xvfb",
    "tornado",
]

# Extra pip requirements
test-extra = [
    "ipykernel",
    # jupyter/nbconvert#1970 for the 7.3 series exclusions
    "nbconvert[execute]!=6.0.0,!=6.0.1,!=7.3.0,!=7.3.1",
    "nbformat!=5.0.0,!=5.0.1",
    "pandas!=0.25.0",
    "pikepdf",
    "pytz",
    "xarray",
]

# Extra pip requirements for the GitHub Actions mypy build
typing = [
    "mypy>=1.14",
    "typing-extensions>=4.6",
    # Extra stubs distributed separately from the main pypi package
    "pandas-stubs",
    "types-pillow",
    "types-python-dateutil",
    "types-psutil",
    "sphinx",
]

[tool.meson-python.args]
install = ['--tags=data,python-runtime,runtime']

[tool.setuptools_scm]
version_scheme = "release-branch-semver"
local_scheme = "node-and-date"
parentdir_prefix_version = "matplotlib-"
fallback_version = "0.0+UNKNOWN"

[tool.isort]
known_pydata = "numpy, matplotlib.pyplot"
known_firstparty = "matplotlib,mpl_toolkits"
sections = "FUTURE,STDLIB,THIRDPARTY,PYDATA,FIRSTPARTY,LOCALFOLDER"
force_sort_within_sections = true
line_length = 88

[tool.ruff]
extend-exclude = [
    "build",
    "doc/gallery",
    "doc/tutorials",
    "tools/gh_api.py",
]
line-length = 88

[tool.ruff.lint]
ignore = [
    "D100",
    "D101",
    "D102",
    "D103",
    "D104",
    "D105",
    "D106",
    "D107",
    "D200",
    "D202",
    "D204",
    "D205",
    "D301",
    "D400",
    "D401",
    "D403",
    "D404",
    "E266",
    "E305",
    "E306",
    "E721",
    "E741",
    "F841",
]
preview = true
explicit-preview-rules = true
select = [
    "D",
    "E",
    "F",
    "W",
    "UP035",
    # The following error codes require the preview mode to be enabled.
    "E111",
    "E112",
    "E113",
    "E114",
    "E115",
    "E116",
    "E117",
    "E201",
    "E202",
    "E203",
    "E204",
    "E211",
    "E221",
    "E222",
    "E223",
    "E224",
    "E225",
    # "E226",  Produces 2559 errors, so skip this one.
    "E227",
    "E228",
    "E231",
    # "E241",  Produces 1475 errors, so skip this one.
    "E242",
    "E251",
    "E252",
    "E261",
    "E262",
    "E265",
    "E266",
    "E271",
    "E272",
    "E273",
    "E274",
    "E275",
    "E301",
    "E302",
    "E303",
    "E304",
    "E305",
    "E306",
    "E502",
    "E703",
]

# The following error codes are not supported by ruff v0.2.0
# They are planned and should be selected once implemented
# even if they are deselected by default.
# These are primarily whitespace/corrected by autoformatters (which we don't use).
# See https://github.com/charliermarsh/ruff/issues/2402 for status on implementation
external = [
  "E122",
]

[tool.ruff.lint.pydocstyle]
convention = "numpy"

[tool.ruff.lint.per-file-ignores]
"*.pyi" = ["E501"]
"*.ipynb" = ["E402"]
"doc/conf.py" = ["E402"]
"galleries/examples/images_contours_and_fields/tricontour_demo.py" = ["E201"]
"galleries/examples/images_contours_and_fields/tripcolor_demo.py" = ["E201"]
"galleries/examples/images_contours_and_fields/triplot_demo.py" = ["E201"]
"galleries/examples/lines_bars_and_markers/marker_reference.py" = ["E402"]
"galleries/examples/misc/table_demo.py" = ["E201"]
"galleries/examples/subplots_axes_and_figures/demo_constrained_layout.py" = ["E402"]
"galleries/examples/text_labels_and_annotations/custom_legends.py" = ["E402"]
"galleries/examples/ticks/date_concise_formatter.py" = ["E402"]
"galleries/examples/ticks/date_formatters_locators.py" = ["F401"]
"galleries/examples/user_interfaces/embedding_in_gtk3_panzoom_sgskip.py" = ["E402"]
"galleries/examples/user_interfaces/embedding_in_gtk3_sgskip.py" = ["E402"]
"galleries/examples/user_interfaces/embedding_in_gtk4_panzoom_sgskip.py" = ["E402"]
"galleries/examples/user_interfaces/embedding_in_gtk4_sgskip.py" = ["E402"]
"galleries/examples/user_interfaces/gtk3_spreadsheet_sgskip.py" = ["E402"]
"galleries/examples/user_interfaces/gtk4_spreadsheet_sgskip.py" = ["E402"]
"galleries/examples/user_interfaces/mpl_with_glade3_sgskip.py" = ["E402"]
"galleries/examples/user_interfaces/pylab_with_gtk3_sgskip.py" = ["E402"]
"galleries/examples/user_interfaces/pylab_with_gtk4_sgskip.py" = ["E402"]

"lib/matplotlib/__init__.py" = ["F822"]
"lib/matplotlib/_cm.py" = ["E202", "E203", "E302"]
"lib/matplotlib/_mathtext.py" = ["E221"]
"lib/matplotlib/_mathtext_data.py" = ["E203"]
"lib/matplotlib/backends/backend_template.py" = ["F401"]
"lib/matplotlib/pylab.py" = ["F401", "F403"]
"lib/matplotlib/tests/test_mathtext.py" = ["E501"]
"lib/matplotlib/transforms.py" = ["E201"]
"lib/matplotlib/tri/_triinterpolate.py" = ["E201", "E221"]
"lib/mpl_toolkits/axes_grid1/axes_size.py" = ["E272"]
"lib/mpl_toolkits/axisartist/angle_helper.py" = ["E221"]
"lib/mpl_toolkits/mplot3d/proj3d.py" = ["E201"]

"galleries/users_explain/quick_start.py" = ["E402"]
"galleries/users_explain/artists/patheffects_guide.py" = ["E402"]
"galleries/users_explain/artists/transforms_tutorial.py" = ["E402"]
"galleries/users_explain/colors/blend_modes.py" = ["E402"]
"galleries/users_explain/colors/colors.py" = ["E402"]
"galleries/tutorials/artists.py" = ["E402"]
"galleries/users_explain/axes/constrainedlayout_guide.py" = ["E402"]
"galleries/users_explain/axes/legend_guide.py" = ["E402"]
"galleries/users_explain/axes/tight_layout_guide.py" = ["E402"]
"galleries/users_explain/animations/animations.py" = ["E501"]
"galleries/tutorials/pyplot.py" = ["E402", "E501"]
"galleries/users_explain/text/annotations.py" = ["E402", "E501"]
"galleries/users_explain/text/text_intro.py" = ["E402"]
"galleries/users_explain/text/text_props.py" = ["E501"]

[tool.mypy]
ignore_missing_imports = true
enable_error_code = [
  "ignore-without-code",
  "redundant-expr",
  "truthy-bool",
]
exclude = [
  #stubtest
  ".*/matplotlib/(sphinxext|backends|pylab|testing/jpl_units)",
  #mypy precommit
  "galleries/",
  "doc/",
  "lib/mpl_toolkits/",
  #removing tests causes errors in backends
  "lib/matplotlib/tests/",
  # tinypages is used for testing the sphinx ext,
  # stubtest will import and run, opening a figure if not excluded
  ".*/tinypages",
  # pylab's numpy wildcard imports cause re-def failures since numpy 2.2
  "lib/matplotlib/pylab.py",
]
files = [
  "lib/matplotlib",
]
follow_imports = "silent"
warn_unreachable = true

[tool.rstcheck]
ignore_directives = [
    # matplotlib.sphinxext.mathmpl
    "mathmpl",
    # matplotlib.sphinxext.plot_directive
    "plot",
    # sphinxext.math_symbol_table
    "math_symbol_table",
    # sphinxext.redirect_from
    "redirect-from",
    # sphinx-design
    "card",
    "dropdown",
    "grid",
    "tab-set",
    # sphinx-gallery
    "minigallery",
    "image-sg",
    # sphinx.ext.autodoc
    "automodule",
    "autoclass",
    "autofunction",
    "autodata",
    "automethod",
    "autoattribute",
    "autoproperty",
    # sphinx.ext.autosummary
    "autosummary",
    # sphinx.ext.ifconfig
    "ifconfig",
    # sphinx.ext.inheritance_diagram
    "inheritance-diagram",
    # sphinx-tags
    "tags",
    # include directive is causing attribute errors
    "include"
]
ignore_roles = [
    # matplotlib.sphinxext.mathmpl
    "mathmpl",
    "math-stix",
    # matplotlib.sphinxext.roles
    "rc",
    # sphinxext.github
    "ghissue",
    "ghpull",
    "ghuser",
    # sphinx-design
    "octicon",
]
ignore_substitutions = [
    "Artist",
    "Axes",
    "Axis",
    "Figure",
    "release"
]

ignore_messages = [
    "Hyperlink target \".*\" is not referenced.",
    "Duplicate implicit target name: \".*\".",
    "Duplicate explicit target name: \".*\".",
    # sphinx.ext.intersphinx directives
    "No role entry for \"external+.*\".",
    "Unknown interpreted text role \"external+.*\"."
]

[tool.pytest.ini_options]
# Because tests can be run from an installed copy, most of our Pytest
# configuration is in the `pytest_configure` function in
# `lib/matplotlib/testing/conftest.py`.
minversion = "7.0"
testpaths = ["lib"]
addopts = [
    "--import-mode=importlib",
]

[tool.cibuildwheel]
skip = "*-musllinux_aarch64"
manylinux-x86_64-image = "manylinux2014"

before-build = "rm -rf {package}/build"
test-command = [
    # "python {package}/ci/check_wheel_licenses.py {wheel}",
    "python {package}/ci/check_version_number.py",
]
test-environment = "PIP_PREFER_BINARY=true"

[tool.cibuildwheel.macos.environment]
MACOSX_DEPLOYMENT_TARGET = "10.14"

[tool.cibuildwheel.pyodide]
test-requires = "pytest"
test-command = [
    # Wheels are built without test images, so copy them into the testing directory.
    "basedir=$(python -c 'import pathlib, matplotlib; print(pathlib.Path(matplotlib.__file__).parent.parent)')",
    "cp -a {package}/lib/matplotlib/tests/data $basedir/matplotlib/tests/",
    """
    for subdir in matplotlib mpl_toolkits/axes_grid1 mpl_toolkits/axisartist mpl_toolkits/mplot3d; do
        cp -a {package}/lib/${subdir}/tests/baseline_images $basedir/${subdir}/tests/
    done""",
    # Test installed, not repository, copy as we aren't using an editable install.
    """\
    pytest -p no:cacheprovider --pyargs \
        matplotlib mpl_toolkits.axes_grid1 mpl_toolkits.axisartist mpl_toolkits.mplot3d \
	-k 'not test_complex_shaping'""",
]
[tool.cibuildwheel.pyodide.environment]
# Exception handling is needed for pybind11:
# https://github.com/pybind/pybind11/pull/5298
# And the pyemscripten_2025_0 platform and above uses -fwasm-exceptions for this.
# https://pyodide.org/en/stable/development/abi/313.html
CFLAGS = "-fwasm-exceptions"
CXXFLAGS = "-fwasm-exceptions"
LDFLAGS = "-fwasm-exceptions"

[tool.cibuildwheel.windows]
before-build = [
    "pip install delvewheel",
    "rm -rf {package}/build",
]
repair-wheel-command = "delvewheel repair -w {dest_dir} {wheel}"

[tool.cibuildwheel.windows.config-settings]
# On Windows, we explicitly request MSVC compilers (as GitHub Action runners have
# MinGW on PATH that would be picked otherwise), switch to a static build for
# runtimes, but use dynamic linking for `VCRUNTIME140.dll`, `VCRUNTIME140_1.dll`,
# and the UCRT. This avoids requiring specific versions of `MSVCP140.dll`, while
# keeping shared state with the rest of the Python process/extensions.
setup-args = [
    "--vsenv",
    "-Db_vscrt=mt",
    "-Dcpp_link_args=['ucrt.lib','vcruntime.lib','/nodefaultlib:libucrt.lib','/nodefaultlib:libvcruntime.lib']",
]

[[tool.cibuildwheel.overrides]]
select = "cp314*"
manylinux-x86_64-image = "manylinux_2_28"

```

---

## `tox.ini`

Role: **context**. may hold lint config

```ini
# Tox (http://tox.testrun.org/) is a tool for running tests
# in multiple virtualenvs. This configuration file will run the
# test suite on all supported python versions. To use it, "pip install tox"
# and then run "tox" from this directory.

[tox]
envlist = py312, py313, py314, stubtest

[testenv]
changedir = /tmp
setenv =
    MPLCONFIGDIR={envtmpdir}/.matplotlib
    PIP_USER = 0
    PIP_ISOLATED = 1
    SETUPTOOLS_SCM_PRETEND_VERSION_FOR_MATPLOTLIB = 0.0.0

usedevelop = True
commands =
    pytest --pyargs matplotlib.tests  {posargs}
deps =
    pytest

[testenv:pytz]
changedir = /tmp
commands =
    pytest -m pytz {toxinidir}
deps =
    pytest
    pytz

[testenv:stubtest]
changedir = {tox_root}
commands =
    python tools/stubtest.py
usedevelop = False
dependency_groups =
    build
    typing

```
