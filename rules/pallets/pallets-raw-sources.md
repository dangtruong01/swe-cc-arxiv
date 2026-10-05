# pallets/flask: off-nav rule sources (raw, verbatim)

Repo: `pallets/flask` @ `main`
Docs: https://flask.palletsprojects.com/en/3.1.x/
Docs version at pull time: **UNRESOLVED**

Any doc page served on a different version is a fetch failure, not a row.

Raw source, HTML comments intact. The rendered GitHub view strips comments,
and in template files the comments carry the actual obligations. Extract from
this text, not from a rendered page.

Role `context` means the file informs Section context and Auto-fix but never
produces sheet rows.

| Path | Role | Status | Note |
|---|---|---|---|
| `.github/ISSUE_TEMPLATE/bug-report.md` | rules | ok | expect X-ISSUE |
| `.github/ISSUE_TEMPLATE/config.yml` | rules | ok | expect X-ISSUE |
| `.github/ISSUE_TEMPLATE/feature-request.md` | rules | ok | expect X-ISSUE |
| `.github/pull_request_template.md` | rules | ok | obligations hide in HTML comments |
| `.pre-commit-config.yaml` | context | ok | decides the Auto-fix column |
| `README.md` | context | ok | check for canonical test invocation |
| `docs/contributing.rst` | rules | ok | rule source or redirect | DUPLICATE RISK: source of a rendered doc page, do not extract twice |
| `pyproject.toml` | context | ok | may hold lint config |

---

## `.github/ISSUE_TEMPLATE/bug-report.md`

Role: **rules**. expect X-ISSUE

```markdown
---
name: Bug report
about: Report a bug in Flask (not other projects which depend on Flask)
---

<!--
This issue tracker is a tool to address bugs in Flask itself. Please use
GitHub Discussions or the Pallets Discord for questions about your own code.

Replace this comment with a clear outline of what the bug is.
-->

<!--
Describe how to replicate the bug.

Include a minimal reproducible example that demonstrates the bug.
Include the full traceback if there was an exception.
-->

<!--
Describe the expected behavior that should have happened but didn't.
-->

Environment:

- Python version:
- Flask version:

```

---

## `.github/ISSUE_TEMPLATE/config.yml`

Role: **rules**. expect X-ISSUE

```yaml
blank_issues_enabled: false
contact_links:
  - name: Security issue
    url: https://github.com/pallets/flask/security/advisories/new
    about: Do not report security issues publicly. Create a private advisory.
  - name: Questions on GitHub Discussions
    url: https://github.com/pallets/flask/discussions/
    about: Ask questions about your own code on the Discussions tab.
  - name: Questions on Discord
    url: https://discord.gg/pallets
    about: Ask questions about your own code on our Discord chat.

```

---

## `.github/ISSUE_TEMPLATE/feature-request.md`

Role: **rules**. expect X-ISSUE

```markdown
---
name: Feature request
about: Suggest a new feature for Flask
---

<!--
Replace this comment with a description of what the feature should do.
Include details such as links to relevant specs or previous discussions.
-->

<!--
Replace this comment with an example of the problem which this feature
would resolve. Is this problem solvable without changes to Flask, such
as by subclassing or using an extension?
-->

```

---

## `.github/pull_request_template.md`

Role: **rules**. obligations hide in HTML comments

```markdown
<!--
Before opening a PR, open a ticket describing the issue or feature the
PR will address. An issue is not required for fixing typos in
documentation, or other simple non-code changes.

Replace this comment with a description of the change. Describe how it
addresses the linked ticket.
-->

<!--
Link to relevant issues or previous PRs, one per line. Use "fixes" to
automatically close an issue.

fixes #<issue number>
-->

<!--
Ensure each step in CONTRIBUTING.rst is complete, especially the following:

- Add tests that demonstrate the correct behavior of the change. Tests
  should fail without the change.
- Add or update relevant docs, in the docs folder and in code.
- Add an entry in CHANGES.rst summarizing the change and linking to the issue.
- Add `.. versionchanged::` entries in any relevant code docs.
-->

```

---

## `.pre-commit-config.yaml`

Role: **context**. decides the Auto-fix column

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: cb8c523fd4835aba42af70f4cad5568db4df0b6c  # frozen: v0.16.0
    hooks:
      - id: ruff-check
      - id: ruff-format
  - repo: https://github.com/astral-sh/uv-pre-commit
    rev: 5900cba2cfe6d20f562458d4d308ac55569f92eb  # frozen: 0.12.0
    hooks:
      - id: uv-lock
  - repo: https://github.com/codespell-project/codespell
    rev: 57b21406f092110c18776e39b0bda50d37c945c8  # frozen: v2.4.3
    hooks:
      - id: codespell
        additional_dependencies:
          - tomli
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: 3e8a8703264a2f4a69428a0aa4dcb512790b2c8c  # frozen: v6.0.0
    hooks:
      - id: check-merge-conflict
      - id: debug-statements
      - id: fix-byte-order-marker
      - id: trailing-whitespace
      - id: end-of-file-fixer

```

---

## `README.md`

Role: **context**. check for canonical test invocation

```markdown
<div align="center"><img src="https://raw.githubusercontent.com/pallets/flask/refs/heads/stable/docs/_static/flask-name.svg" alt="" height="150"></div>

# Flask

Flask is a lightweight [WSGI] web application framework. It is designed
to make getting started quick and easy, with the ability to scale up to
complex applications. It began as a simple wrapper around [Werkzeug]
and [Jinja], and has become one of the most popular Python web
application frameworks.

Flask offers suggestions, but doesn't enforce any dependencies or
project layout. It is up to the developer to choose the tools and
libraries they want to use. There are many extensions provided by the
community that make adding new functionality easy.

[WSGI]: https://wsgi.readthedocs.io/
[Werkzeug]: https://werkzeug.palletsprojects.com/
[Jinja]: https://jinja.palletsprojects.com/

## A Simple Example

```python
# save this as app.py
from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello, World!"
```

```
$ flask run
  * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```

## Donate

The Pallets organization develops and supports Flask and the libraries
it uses. In order to grow the community of contributors and users, and
allow the maintainers to devote more time to the projects, [please
donate today].

[please donate today]: https://palletsprojects.com/donate

## Contributing

See our [detailed contributing documentation][contrib] for many ways to
contribute, including reporting issues, requesting features, asking or answering
questions, and making PRs.

[contrib]: https://palletsprojects.com/contributing/

```

---

## `docs/contributing.rst`

Role: **rules**. rule source or redirect | DUPLICATE RISK: source of a rendered doc page, do not extract twice

```rst
Contributing
============

See the Pallets `detailed contributing documentation <contrib_>`_ for many ways
to contribute, including reporting issues, requesting features, asking or
answering questions, and making PRs.

.. _contrib: https://palletsprojects.com/contributing/

```

---

## `pyproject.toml`

Role: **context**. may hold lint config

```toml
[project]
name = "Flask"
version = "3.2.0.dev"
description = "A simple framework for building complex web applications."
readme = "README.md"
license = "BSD-3-Clause"
license-files = ["LICENSE.txt"]
maintainers = [{name = "Pallets", email = "contact@palletsprojects.com"}]
classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Environment :: Web Environment",
    "Framework :: Flask",
    "Intended Audience :: Developers",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    "Topic :: Internet :: WWW/HTTP :: WSGI",
    "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    "Topic :: Software Development :: Libraries :: Application Frameworks",
    "Typing :: Typed",
]
requires-python = ">=3.10"
dependencies = [
    "blinker>=1.9.0",
    "click>=8.1.3",
    "itsdangerous>=2.2.0",
    "jinja2>=3.1.2",
    "markupsafe>=2.1.1",
    "werkzeug>=3.1.0",
]

[project.optional-dependencies]
async = ["asgiref>=3.2"]
dotenv = ["python-dotenv"]

[dependency-groups]
dev = [
    "ruff",
    "tox",
    "tox-uv",
]
docs = [
    "pallets-sphinx-themes",
    "sphinx<9",
    "sphinx-tabs",
    "sphinxcontrib-log-cabinet",
]
docs-auto = [
    "sphinx-autobuild",
]
gha-update = [
    "gha-update ; python_full_version >= '3.12'",
]
pre-commit = [
    "pre-commit",
    "pre-commit-uv",
]
tests = [
    "asgiref",
    "pytest",
    "python-dotenv",
]
typing = [
    "asgiref",
    "cryptography",
    "mypy",
    "pyright",
    "pytest",
    "python-dotenv",
    "types-contextvars",
    "types-dataclasses",
]

[project.urls]
Donate = "https://palletsprojects.com/donate"
Documentation = "https://flask.palletsprojects.com/"
Changes = "https://flask.palletsprojects.com/page/changes/"
Source = "https://github.com/pallets/flask/"
Chat = "https://discord.gg/pallets"

[project.scripts]
flask = "flask.cli:main"

[build-system]
requires = ["flit_core>=3.11,<4"]
build-backend = "flit_core.buildapi"

[tool.flit.module]
name = "flask"

[tool.flit.sdist]
include = [
    "docs/",
    "examples/",
    "tests/",
    "CHANGES.rst",
    "uv.lock"
]
exclude = [
    "docs/_build/",
]

[tool.uv]
default-groups = ["dev", "pre-commit", "tests", "typing"]

[tool.pytest.ini_options]
testpaths = ["tests"]
filterwarnings = [
    "error",
]

[tool.coverage.run]
branch = true
source = ["flask", "tests"]

[tool.coverage.paths]
source = ["src", "*/site-packages"]

[tool.coverage.report]
exclude_also = [
    "if t.TYPE_CHECKING",
    "raise NotImplementedError",
    ": \\.{3}",
]

[tool.mypy]
python_version = "3.10"
files = ["src", "tests/type_check"]
show_error_codes = true
pretty = true
strict = true

[[tool.mypy.overrides]]
module = [
    "asgiref.*",
    "dotenv.*",
    "cryptography.*",
    "importlib_metadata",
]
ignore_missing_imports = true

[tool.pyright]
pythonVersion = "3.10"
include = ["src", "tests/type_check"]
typeCheckingMode = "basic"

[tool.ruff]
src = ["src"]
fix = true
show-fixes = true
output-format = "full"

[tool.ruff.lint]
select = [
    "B",  # flake8-bugbear
    "E",  # pycodestyle error
    "F",  # pyflakes
    "I",  # isort
    "UP",  # pyupgrade
    "W",  # pycodestyle warning
]

[tool.ruff.lint.isort]
force-single-line = true
order-by-type = false

[tool.codespell]
ignore-words-list = "te"

[tool.tox]
env_list = [
    "py3.15",
    "py3.14", "py3.14t",
    "py3.13", "py3.12", "py3.11", "py3.10",
    "pypy3.11",
    "tests-min", "tests-dev",
    "style",
    "typing",
    "docs",
]

[tool.tox.env_run_base]
description = "pytest on latest dependency versions"
runner = "uv-venv-lock-runner"
package = "wheel"
wheel_build_env = ".pkg"
constrain_package_deps = true
use_frozen_constraints = true
dependency_groups = ["tests"]
env_tmp_dir = "{toxworkdir}/tmp/{envname}"
commands = [[
    "pytest", "-v", "--tb=short", "--basetemp={env_tmp_dir}",
    {replace = "posargs", default = [], extend = true},
]]

[tool.tox.env.tests-min]
description = "pytest on minimum dependency versions"
base_python = ["3.14"]
commands = [
    [
        "uv", "pip", "install",
        "blinker==1.9.0",
        "click==8.1.3",
        "itsdangerous==2.2.0",
        "jinja2==3.1.2",
        "markupsafe==2.1.1",
        "werkzeug==3.1.0",
    ],
    [
        "pytest", "-v", "--tb=short", "--basetemp={env_tmp_dir}",
        {replace = "posargs", default = [], extend = true},
    ],
]

[tool.tox.env.tests-dev]
description = "pytest on development dependency versions (git main branch)"
base_python = ["3.10"]
commands = [
    [
        "uv", "pip", "install",
        "https://github.com/pallets-eco/blinker/archive/refs/heads/main.tar.gz",
        "https://github.com/pallets/click/archive/refs/heads/main.tar.gz",
        "https://github.com/pallets/itsdangerous/archive/refs/heads/main.tar.gz",
        "https://github.com/pallets/jinja/archive/refs/heads/main.tar.gz",
        "https://github.com/pallets/markupsafe/archive/refs/heads/main.tar.gz",
        "https://github.com/pallets/werkzeug/archive/refs/heads/main.tar.gz",
    ],
    [
        "pytest", "-v", "--tb=short", "--basetemp={env_tmp_dir}",
        {replace = "posargs", default = [], extend = true},
    ],
]

[tool.tox.env.style]
description = "run all pre-commit hooks on all files"
dependency_groups = ["pre-commit"]
skip_install = true
commands = [["pre-commit", "run", "--all-files"]]

[tool.tox.env.typing]
description = "run static type checkers"
dependency_groups = ["typing"]
commands = [
    ["mypy"],
    ["pyright"],
]

[tool.tox.env.docs]
description = "build docs"
dependency_groups = ["docs"]
commands = [["sphinx-build", "-E", "-W", "-b", "dirhtml", "docs", "docs/_build/dirhtml"]]

[tool.tox.env.docs-auto]
description = "continuously rebuild docs and start a local server"
dependency_groups = ["docs", "docs-auto"]
commands = [["sphinx-autobuild", "-W", "-b", "dirhtml", "--watch", "src", "docs", "docs/_build/dirhtml"]]

[tool.tox.env.update-actions]
description = "update GitHub Actions pins"
labels = ["update"]
dependency_groups = ["gha-update"]
skip_install = true
commands = [["gha-update"]]

[tool.tox.env.update-pre_commit]
description = "update pre-commit pins"
labels = ["update"]
dependency_groups = ["pre-commit"]
skip_install = true
commands = [["pre-commit", "autoupdate", "--freeze", "-j4"]]

[tool.tox.env.update-requirements]
description = "update uv lock"
labels = ["update"]
dependency_groups = []
no_default_groups = true
skip_install = true
commands = [["uv", "lock", {replace = "posargs", default = ["-U"], extend = true}]]

```
