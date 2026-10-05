# pylint-dev/pylint: off-nav rule sources (raw, verbatim)

Repo: `pylint-dev/pylint` @ `main`
Docs: https://pylint.readthedocs.io/en/latest/
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
| `.github/ISSUE_TEMPLATE/BUG-REPORT.yml` | rules | ok | expect X-ISSUE |
| `.github/ISSUE_TEMPLATE/FEATURE-REQUEST.yml` | rules | ok | expect X-ISSUE |
| `.github/ISSUE_TEMPLATE/QUESTION.yml` | rules | ok | expect X-ISSUE |
| `.github/ISSUE_TEMPLATE/config.yml` | rules | ok | expect X-ISSUE |
| `.github/PULL_REQUEST_TEMPLATE.md` | rules | ok | obligations hide in HTML comments |
| `.pre-commit-config.yaml` | context | ok | decides the Auto-fix column |
| `CODE_OF_CONDUCT.md` | rules | ok | expect X-GOV |
| `README.rst` | context | ok | check for canonical test invocation |
| `pyproject.toml` | context | ok | may hold lint config |
| `towncrier.toml` | context | ok | changelog tooling config |
| `tox.ini` | context | ok | may hold lint config |

---

## `.github/CONTRIBUTING.md`

Role: **rules**. rule source or redirect

```markdown
Please read the
[contribute doc](https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/contribute.html).

```

---

## `.github/ISSUE_TEMPLATE/BUG-REPORT.yml`

Role: **rules**. expect X-ISSUE

```yaml
name: 🐛 Bug report
description: Report a bug in pylint
labels: ["Needs triage :inbox_tray:"]
body:
  - type: markdown
    attributes:
      value: |
        **Thank you for wanting to report a bug in pylint!**

        ⚠ Please make sure that this [issue wasn't already requested][issue search], or already implemented in the main branch.


        [issue search]: https://github.com/pylint-dev/pylint/issues?q=is%3Aissue+is%3Aopen+

  - type: textarea
    id: what-happened
    attributes:
      label: Bug description
      description:
        What is the bug about? Please provide the code that is causing the issue, and
        configurations used if required
      placeholder: |
        # Please disable message unrelated to the bug
        # pylint: disable=missing-docstring,
        <a> = b + 1
      render: python
    validations:
      required: true
  - type: textarea
    id: configuration
    attributes:
      label: Configuration
      description:
        Please provide the part of the configuration that is causing the bug if required
        (Leave this part blank if the configuration is not relevant)
      placeholder: |
        # Leave this blank if the configuration is not relevant!

        [MAIN]
        load-plugins=
            pylint.extensions.code_style

        [MESSAGE CONTROL]
        enable=
            useless-suppression

        # ...
      render: ini
  - type: textarea
    id: cmd-used
    attributes:
      label: Command used
      description: What was the command used to invoke pylint?
      placeholder: |
        pylint a.py
      render: shell
    validations:
      required: true
  - type: textarea
    id: current-behavior
    attributes:
      label: Pylint output
      description: What is the current pylint output?
      placeholder: |
        ************* Module a
        a.py:3:1: E0001: invalid syntax (<unknown>, line 1) (syntax-error)
      render: python
    validations:
      required: true
  - type: textarea
    id: future-behavior
    attributes:
      label: Expected behavior
      description:
        What would you expect instead? For example expected output or behavior
    validations:
      required: true
  - type: textarea
    id: python-interpreter
    attributes:
      label: Pylint version
      description: >-
        Please copy and paste the result of `pylint --version` or specify the range of
        versions affected.
      placeholder: |
        pylint 3.3.0
        astroid 3.3.0
        Python 3.12.0 (v3.12.0:0fb18b02c8, Oct  2 2023, 09:45:56)
      render: shell
    validations:
      required: true
  - type: textarea
    attributes:
      label: OS / Environment
      description: >-
        Provide all relevant information below, e.g. OS version, terminal etc.
      placeholder: Fedora 33, Cygwin, etc.
  - type: textarea
    id: additional-deps
    attributes:
      label: Additional dependencies
      description:
        If applicable ie, if we can't reproduce without it. Please copy and paste the
        result of `pip freeze`.
      placeholder: |
        pandas==0.23.2
        marshmallow==3.10.0
      render: python

```

---

## `.github/ISSUE_TEMPLATE/FEATURE-REQUEST.yml`

Role: **rules**. expect X-ISSUE

```yaml
name: ✨ Feature request
description: Suggest an idea for pylint
labels: ["Needs triage :inbox_tray:"]
body:
  - type: markdown
    attributes:
      value: |
        **Thank you for wanting to make a suggestion for pylint!**

        ⚠ Please make sure that [this feature wasn't already requested][issue search] or already implemented in the main branch.


        [issue search]: https://github.com/pylint-dev/pylint/issues?q=is%3Aissue+is%3Aopen+

  - type: textarea
    id: current-problem
    attributes:
      label: Current problem
      description:
        What are you trying to do, that you are unable to achieve with pylint as it
        currently stands?
      placeholder: >-
        I'm trying to do X and I'm missing feature Y for this to be easily achievable.
    validations:
      required: true
  - type: textarea
    id: proposed-solution
    attributes:
      label: Desired solution
      description: A clear and concise description of what you want to happen.
      placeholder: >-
        When I do X, I want to achieve Y in a situation when Z.
    validations:
      required: true
  - type: textarea
    attributes:
      label: Additional context
      description: >
        Add any other context, links, etc. about the feature here. Describe how the
        feature would be used, why it is needed and what it would solve.

        **HINT:** You can paste https://gist.github.com links for larger files.
      placeholder: >-
        I asked on https://stackoverflow.com/... and the community advised me to do X, Y
        and Z.

```

---

## `.github/ISSUE_TEMPLATE/QUESTION.yml`

Role: **rules**. expect X-ISSUE

```yaml
name: 🤔 Support question
description: Questions about pylint that are not covered in the documentation
labels: ["Needs triage :inbox_tray:", "Question", "Documentation :green_book:"]
body:
  - type: markdown
    attributes:
      value: >
        **Thank you for wanting to report a problem with pylint documentation!**


        Please fill out your suggestions below. If the problem seems straightforward,
        feel free to go ahead and submit a pull request instead!


        ⚠ Verify first that your issue is not [already reported on GitHub][issue
        search].

        💬 If you are seeking community support, please consider [starting a discussion
        on Discord][Discussions].


        [issue search]:
        https://github.com/pylint-dev/pylint/issues?q=is%3Aissue+is%3Aopen+

        [Discussions]: https://discord.com/invite/Egy6P8AMB5

  - type: textarea
    id: question
    attributes:
      label: Question
    validations:
      required: true
  - type: textarea
    id: documentation
    attributes:
      label: Documentation for future user
      description:
        Where did you expect this information to be? What do we need to add or what do
        we need to reorganize?
    validations:
      required: true
  - type: textarea
    attributes:
      label: Additional context
      description: >
        Add any other context, links, etc. about the question here.
      placeholder: >-
        I asked on https://stackoverflow.com/... and the community advised me to do X, Y
        and Z.

```

---

## `.github/ISSUE_TEMPLATE/config.yml`

Role: **rules**. expect X-ISSUE

```yaml
blank_issues_enabled: true
contact_links:
  - name: 💬 Discord
    url: https://discord.com/invite/Egy6P8AMB5
    about: Astroid and pylint informal dev discussion

```

---

## `.github/PULL_REQUEST_TEMPLATE.md`

Role: **rules**. obligations hide in HTML comments

```markdown
<!--
Thank you for submitting a PR to pylint!

To ease the process of reviewing your PR, do make sure to complete the following boxes.

- [ ] Document your change, if it is a non-trivial one.
  - A maintainer might label the issue ``skip-news`` if the change does not need to be in the changelog.
  - Otherwise, create a news fragment with ``towncrier create <IssueNumber>.<type>`` which will be
    included in the changelog. ``<type>`` can be one of the types defined in `./towncrier.toml`.
    If necessary you can write details or offer examples on how the new change is supposed to work.
  - Generating the doc is done with ``tox -e docs``
- [ ] Relate your change to an issue in the tracker if such an issue exists (Refs #1234, Closes #1234)
- [ ] Write comprehensive commit messages and/or a good description of what the PR does.
- [ ] Keep the change small, separate the consensual changes from the opinionated one.
  Don't hesitate to open multiple PRs if the change requires it. If your review is so
  big it requires to actually plan and allocate time to review, it's more likely
  that it's going to go stale.
- [ ] If you used multiple emails or multiple names when contributing, add your mails
      and preferred name in ``script/.contributors_aliases.json``
-->

## Type of Changes

<!-- Leave the corresponding lines for the applicable type of change: -->

|     | Type                   |
| --- | ---------------------- |
| ✓   | :bug: Bug fix          |
| ✓   | :sparkles: New feature |
| ✓   | :hammer: Refactoring   |
| ✓   | :scroll: Docs          |

## Description

<!-- If this PR references an issue without fixing it: -->

Refs #XXXX

<!-- If this PR fixes an issue, use the following to automatically close when we merge: -->

Closes #XXXX

```

---

## `.pre-commit-config.yaml`

Role: **context**. decides the Auto-fix column

```yaml
ci:
  skip: [pylint]

repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: trailing-whitespace
        exclude: tests(/\w*)*/functional/t/trailing_whitespaces.py|tests/pyreverse/data/.*.html|doc/data/messages/t/trailing-whitespace/bad.py
      #      - id: file-contents-sorter # commented out because it does not preserve comments order
      #        args: ["--ignore-case", "--unique"]
      #        files: "custom_dict.txt"
      - id: end-of-file-fixer
        exclude: |
          (?x)^(
            tests(/\w*)*/functional/m/missing/missing_final_newline.py|
            tests/functional/t/trailing_newlines.py|
            doc/data/messages/t/trailing-newlines/bad.py|
            doc/data/messages/m/missing-final-newline/bad/lf.py|
            doc/data/messages/m/missing-final-newline/bad/crlf.py
          )$
  - repo: https://github.com/zizmorcore/zizmor-pre-commit
    rev: v1.30.0
    hooks:
      - id: zizmor
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: "v0.16.5"
    hooks:
      - id: ruff-check
        args: ["--fix"]
        exclude: doc/data/messages
      - id: ruff-check
        name: ruff-doc
        files: doc/data/messages
        # Please exclude using doc/data/ruff.toml
        # exclude: ""  # Leave empty
  - repo: https://github.com/Pierre-Sassoulas/copyright_notice_precommit
    rev: 0.1.2
    hooks:
      - id: copyright-notice
        args: ["--notice=script/copyright.txt", "--enforce-all"]
        exclude: tests(/\w*)*/functional/|tests/input|doc/data/messages|examples/|setup.py|tests(/\w*)*data/
        types: [python]
  - repo: https://github.com/PyCQA/isort
    rev: 9.0.1
    hooks:
      - id: isort
        exclude: doc/data/messages/
  - repo: https://github.com/psf/black-pre-commit-mirror
    rev: 26.5.1
    hooks:
      - id: black
        args: [--safe, --quiet]
        exclude: &fixtures tests(/\w*)*/functional/|tests/input|doc/data/messages|tests(/\w*)*data/
      - id: black
        name: black-doc
        args: [--safe, --quiet]
        files: doc/data/messages/
        exclude: |
          (?x)^(
            doc/data/messages/b/bad-indentation/bad.py|
            doc/data/messages/i/inconsistent-quotes/bad.py|
            doc/data/messages/i/invalid-format-index/bad.py|
            doc/data/messages/l/line-too-long/bad.py|
            doc/data/messages/m/missing-final-newline/bad/crlf.py|
            doc/data/messages/m/missing-final-newline/bad/lf.py|
            doc/data/messages/m/multiple-statements/bad.py|
            doc/data/messages/r/redundant-u-string-prefix/bad.py|
            doc/data/messages/s/superfluous-parens/bad/example_1.py|
            doc/data/messages/s/syntax-error/bad.py|
            doc/data/messages/t/too-many-ancestors/bad.py|
            doc/data/messages/t/trailing-comma-tuple/bad.py|
            doc/data/messages/t/trailing-newlines/bad.py|
            doc/data/messages/t/trailing-whitespace/bad.py|
            doc/data/messages/u/unnecessary-semicolon/bad.py|
            # black checks that it did not change the meaning of the code by
            # parsing it with the interpreter it runs on, which cannot parse
            # PEP 798 unpacking before Python 3.15
            doc/data/messages/u/using-comprehension-unpacking-in-unsupported-version/bad.py
          )$
  - repo: https://github.com/Pierre-Sassoulas/black-disable-checker
    rev: v1.1.3
    hooks:
      - id: black-disable-checker
  - repo: local
    hooks:
      - id: pylint
        name: pylint
        entry: pylint
        language: system
        types: [python]
        # Not that problematic to run in parallel see Pre-commit
        # integration in the doc for details
        # require_serial: true
        args: ["-rn", "-sn", "--rcfile=pylintrc", "--fail-on=I"]
        exclude: tests(/\w*)*/functional/|tests/input|tests(/\w*)*data/|doc/
      - id: pyright
        name: pyright
        description: "Python command line wrapper for pyright, a static type checker"
        entry: pyright
        language: python
        "types_or": [python, pyi]
        require_serial: true
        minimum_pre_commit_version: "2.9.2"
        exclude: tests(/\w*)*/functional/|tests/input|tests(/.*)+/conftest.py|doc/data/messages|tests(/\w*)*data/
        stages: [manual]
      # We define an additional manual step to allow running pylint with a spelling
      # checker in CI.
      - id: pylint
        alias: pylint-with-spelling
        name: pylint
        entry: pylint
        language: system
        types: [python]
        args:
          [
            "-rn",
            "-sn",
            "--rcfile=pylintrc",
            "--fail-on=I",
            "--spelling-dict=en",
            "--output-format=github",
          ]
        exclude: tests(/\w*)*/functional/|tests/input|tests(/\w*)*data/|doc/
        stages: [manual]
      - id: check-newsfragments
        name: Check newsfragments
        entry: python3 -m script.check_newsfragments
        language: system
        types: [text]
        files: ^(doc/whatsnew/fragments)
        exclude: doc/whatsnew/fragments/_.*.rst
  - repo: https://github.com/rstcheck/rstcheck
    rev: "v6.3.0"
    hooks:
      - id: rstcheck
        args: ["--report-level=warning"]
        files: ^(doc/(.*/)*.*\.rst)
        additional_dependencies: ["Sphinx==7.4.3"]
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v2.3.1
    hooks:
      - id: mypy
        name: mypy
        args: []
        additional_dependencies:
          ["isort>=5", "platformdirs==2.2.0", "py==1.11", "tomlkit>=0.10.1"]
        exclude: tests(/\w*)*/functional/|tests/input|tests(/.*)+/conftest.py|doc/data/messages|tests(/\w*)*data/
  - repo: https://github.com/rbubley/mirrors-prettier
    rev: v3.9.6
    hooks:
      - id: prettier
        args: [--prose-wrap=always, --print-width=88]
        exclude: (tests(/\w*)*data/|.github/FUNDING.yml)
  - repo: https://github.com/DanielNoord/pydocstringformatter
    rev: v1.0.0
    hooks:
      - id: pydocstringformatter
        exclude: *fixtures
        args: ["--max-summary-lines=2", "--linewrap-full-docstring"]
        files: "pylint"
  - repo: https://github.com/PyCQA/bandit
    rev: 1.9.4
    hooks:
      - id: bandit
        args: ["-r", "-lll"]
        exclude: *fixtures
  - repo: https://github.com/codespell-project/codespell
    rev: v2.4.3
    hooks:
      - id: codespell
        args: ["--toml=pyproject.toml"]
        additional_dependencies:
          - tomli
  - repo: https://github.com/tox-dev/pyproject-fmt
    rev: "v2.29.0"
    hooks:
      - id: pyproject-fmt
  - repo: https://github.com/abravalheri/validate-pyproject
    rev: "0.26"
    hooks:
      - id: validate-pyproject

```

---

## `CODE_OF_CONDUCT.md`

Role: **rules**. expect X-GOV

```markdown
# Contributor Covenant Code of Conduct

## Our Pledge

We as members, contributors, and leaders pledge to make participation in our community a
harassment-free experience for everyone, regardless of age, body size, visible or
invisible disability, ethnicity, sex characteristics, gender identity and expression,
level of experience, education, socio-economic status, nationality, personal appearance,
race, religion, or sexual identity and orientation.

We pledge to act and interact in ways that contribute to an open, welcoming, diverse,
inclusive, and healthy community.

## Our Standards

Examples of behavior that contributes to a positive environment for our community
include:

- Demonstrating empathy and kindness toward other people
- Being respectful of differing opinions, viewpoints, and experiences
- Giving and gracefully accepting constructive feedback
- Accepting responsibility and apologizing to those affected by our mistakes, and
  learning from the experience
- Focusing on what is best not just for us as individuals, but for the overall community

Examples of unacceptable behavior include:

- The use of sexualized language or imagery, and sexual attention or advances of any
  kind
- Trolling, insulting or derogatory comments, and personal or political attacks
- Public or private harassment
- Publishing others' private information, such as a physical or email address, without
  their explicit permission
- Other conduct which could reasonably be considered inappropriate in a professional
  setting

## Enforcement Responsibilities

Community leaders are responsible for clarifying and enforcing our standards of
acceptable behavior and will take appropriate and fair corrective action in response to
any behavior that they deem inappropriate, threatening, offensive, or harmful.

Community leaders have the right and responsibility to remove, edit, or reject comments,
commits, code, wiki edits, issues, and other contributions that are not aligned to this
Code of Conduct, and will communicate reasons for moderation decisions when appropriate.

## Scope

This Code of Conduct applies within all community spaces, and also applies when an
individual is officially representing the community in public spaces. Examples of
representing our community include using an official e-mail address, posting via an
official social media account, or acting as an appointed representative at an online or
offline event.

## Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported to
the community leaders responsible for enforcement at pierre.sassoulas at gmail.com. All
complaints will be reviewed and investigated promptly and fairly.

All community leaders are obligated to respect the privacy and security of the reporter
of any incident.

## Enforcement Guidelines

Community leaders will follow these Community Impact Guidelines in determining the
consequences for any action they deem in violation of this Code of Conduct:

### 1. Correction

**Community Impact**: Use of inappropriate language or other behavior deemed
unprofessional or unwelcome in the community.

**Consequence**: A private, written warning from community leaders, providing clarity
around the nature of the violation and an explanation of why the behavior was
inappropriate. A public apology may be requested.

### 2. Warning

**Community Impact**: A violation through a single incident or series of actions.

**Consequence**: A warning with consequences for continued behavior. No interaction with
the people involved, including unsolicited interaction with those enforcing the Code of
Conduct, for a specified period of time. This includes avoiding interactions in
community spaces as well as external channels like social media. Violating these terms
may lead to a temporary or permanent ban.

### 3. Temporary Ban

**Community Impact**: A serious violation of community standards, including sustained
inappropriate behavior.

**Consequence**: A temporary ban from any sort of interaction or public communication
with the community for a specified period of time. No public or private interaction with
the people involved, including unsolicited interaction with those enforcing the Code of
Conduct, is allowed during this period. Violating these terms may lead to a permanent
ban.

### 4. Permanent Ban

**Community Impact**: Demonstrating a pattern of violation of community standards,
including sustained inappropriate behavior, harassment of an individual, or aggression
toward or disparagement of classes of individuals.

**Consequence**: A permanent ban from any sort of public interaction within the
community.

## Attribution

This Code of Conduct is adapted from the [Contributor Covenant][homepage], version 2.0,
available at https://www.contributor-covenant.org/version/2/0/code_of_conduct.html.

Community Impact Guidelines were inspired by
[Mozilla's code of conduct enforcement ladder](https://github.com/mozilla/diversity).

[homepage]: https://www.contributor-covenant.org

For answers to common questions about this code of conduct, see the FAQ at
https://www.contributor-covenant.org/faq. Translations are available at
https://www.contributor-covenant.org/translations.

```

---

## `README.rst`

Role: **context**. check for canonical test invocation

```rst
`Pylint`_
=========

.. _`Pylint`: https://pylint.readthedocs.io/

.. This is used inside the doc to recover the start of the introduction

.. image:: https://github.com/pylint-dev/pylint/actions/workflows/tests.yaml/badge.svg?branch=main
    :target: https://github.com/pylint-dev/pylint/actions

.. image:: https://codecov.io/gh/pylint-dev/pylint/branch/main/graph/badge.svg?token=ZETEzayrfk
    :target: https://codecov.io/gh/pylint-dev/pylint

.. image:: https://img.shields.io/pypi/v/pylint.svg
    :alt: PyPI Package version
    :target: https://pypi.python.org/pypi/pylint

.. image:: https://readthedocs.org/projects/pylint/badge/?version=latest
    :target: https://pylint.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/ambv/black

.. image:: https://img.shields.io/badge/linting-pylint-yellowgreen
    :target: https://github.com/pylint-dev/pylint

.. image:: https://results.pre-commit.ci/badge/github/pylint-dev/pylint/main.svg
   :target: https://results.pre-commit.ci/latest/github/pylint-dev/pylint/main
   :alt: pre-commit.ci status

.. image:: https://bestpractices.coreinfrastructure.org/projects/6328/badge
   :target: https://bestpractices.coreinfrastructure.org/projects/6328
   :alt: CII Best Practices

.. image:: https://img.shields.io/ossf-scorecard/github.com/PyCQA/pylint?label=openssf%20scorecard&style=flat
   :target: https://api.securityscorecards.dev/projects/github.com/PyCQA/pylint
   :alt: OpenSSF Scorecard

.. image:: https://img.shields.io/discord/825463413634891776.svg
   :target: https://discord.gg/qYxpadCgkx
   :alt: Discord

What is Pylint?
---------------

Pylint is a `static code analyser`_ for Python 2 or 3. The latest version supports Python
3.10.0 and above.

.. _`static code analyser`: https://en.wikipedia.org/wiki/Static_code_analysis

Pylint analyses your code without actually running it. It checks for errors, enforces a
coding standard, looks for `code smells`_, and can make suggestions about how the code
could be refactored.

.. _`code smells`: https://martinfowler.com/bliki/CodeSmell.html

Install
-------

.. This is used inside the doc to recover the start of the short text for installation

For command line use, pylint is installed with::

    pip install pylint

Or if you want to also check spelling with ``enchant`` (you might need to
`install the enchant C library <https://pyenchant.github.io/pyenchant/install.html#installing-the-enchant-c-library>`_):

.. code-block:: sh

   pip install pylint[spelling]

It can also be integrated in most editors or IDEs. More information can be found
`in the documentation`_.

.. _in the documentation: https://pylint.readthedocs.io/en/latest/user_guide/installation/index.html

.. This is used inside the doc to recover the end of the short text for installation

What differentiates Pylint?
---------------------------

Pylint is not trusting your typing and is inferring the actual values of nodes (for a
start because there was no typing when pylint started off) using its internal code
representation (astroid). If your code is ``import logging as argparse``, Pylint
can check and know that ``argparse.error(...)`` is in fact a logging call and not an
argparse call. This makes pylint slower, but it also lets pylint find more issues if
your code is not fully typed.

    [inference] is the killer feature that keeps us using [pylint] in our project despite how painfully slow it is.
    - `Realist pylint user`_, 2022

.. _`Realist pylint user`: https://github.com/charliermarsh/ruff/issues/970#issuecomment-1381067064

pylint, not afraid of being a little slower than it already is, is also a lot more thorough than other linters.
There are more checks, including some opinionated ones that are deactivated by default
but can be enabled using configuration.

How to use pylint
-----------------

Pylint isn't smarter than you: it may warn you about things that you have
conscientiously done or check for some things that you don't care about.
During adoption, especially in a legacy project where pylint was never enforced,
it's best to start with the ``--errors-only`` flag, then disable
convention and refactor messages with ``--disable=C,R`` and progressively
re-evaluate and re-enable messages as your priorities evolve.

Pylint is highly configurable and permits to write plugins in order to add your
own checks (for example, for internal libraries or an internal rule). Pylint also has an
ecosystem of existing plugins for popular frameworks and third-party libraries.

.. note::

    Pylint supports the Python standard library out of the box. Third-party
    libraries are not always supported, so a plugin might be needed. A good place
    to start is ``PyPI`` which often returns a plugin by searching for
    ``pylint <library>``. `pylint-pydantic`_, `pylint-django`_ and
    `pylint-sonarjson`_ are examples of such plugins. More information about plugins
    and how to load them can be found at `plugins`_.

.. _`plugins`: https://pylint.readthedocs.io/en/latest/development_guide/how_tos/plugins.html#plugins
.. _`pylint-pydantic`: https://pypi.org/project/pylint-pydantic
.. _`pylint-django`: https://github.com/pylint-dev/pylint-django
.. _`pylint-sonarjson`: https://github.com/cnescatlab/pylint-sonarjson-catlab

Advised linters alongside pylint
--------------------------------

Projects that you might want to use alongside pylint include ruff_ (**really** fast,
with builtin auto-fix and a large number of checks taken from popular linters, but
implemented in ``rust``) or flake8_ (a framework to implement your own checks in python using ``ast`` directly),
mypy_, pyright_ / pylance or pyre_ (typing checks), bandit_ (security oriented checks), black_ and
isort_ (auto-formatting), autoflake_ (automated removal of unused imports or variables), pyupgrade_
(automated upgrade to newer python syntax) and pydocstringformatter_ (automated pep257).

.. _ruff: https://github.com/astral-sh/ruff
.. _flake8: https://github.com/PyCQA/flake8
.. _bandit: https://github.com/PyCQA/bandit
.. _mypy: https://github.com/python/mypy
.. _pyright: https://github.com/microsoft/pyright
.. _pyre: https://github.com/facebook/pyre-check
.. _black: https://github.com/psf/black
.. _autoflake: https://github.com/myint/autoflake
.. _pyupgrade: https://github.com/asottile/pyupgrade
.. _pydocstringformatter: https://github.com/DanielNoord/pydocstringformatter
.. _isort: https://pycqa.github.io/isort/

Additional tools included in pylint
-----------------------------------

Pylint ships with two additional tools:

- pyreverse_ (standalone tool that generates package and class diagrams.)
- symilar_  (duplicate code finder that is also integrated in pylint)

.. _pyreverse: https://pylint.readthedocs.io/en/latest/additional_tools/pyreverse/index.html
.. _symilar: https://pylint.readthedocs.io/en/latest/additional_tools/symilar/index.html


.. This is used inside the doc to recover the end of the introduction

Contributing
------------

.. This is used inside the doc to recover the start of the short text for contribution

We welcome all forms of contributions such as updates for documentation, new code, checking issues for duplicates or telling us
that we can close them, confirming that issues still exist, `creating issues because
you found a bug or want a feature`_, etc. Everything is much appreciated!

Please follow the `code of conduct`_ and check `the Contributor Guides`_ if you want to
make a code contribution.

.. _creating issues because you found a bug or want a feature: https://pylint.readthedocs.io/en/latest/contact.html#bug-reports-feedback
.. _code of conduct: https://github.com/pylint-dev/pylint/blob/main/CODE_OF_CONDUCT.md
.. _the Contributor Guides: https://pylint.readthedocs.io/en/latest/development_guide/contribute.html

.. This is used inside the doc to recover the end of the short text for contribution

Show your usage
-----------------

You can place this badge in your README to let others know your project uses pylint.

    .. image:: https://img.shields.io/badge/linting-pylint-yellowgreen
        :target: https://github.com/pylint-dev/pylint

Learn how to add a badge to your documentation in `the badge documentation`_.

.. _the badge documentation: https://pylint.readthedocs.io/en/latest/user_guide/installation/badge.html

License
-------

pylint is, with a few exceptions listed below, `GPLv2 <https://github.com/pylint-dev/pylint/blob/main/LICENSE>`_.

The icon files are licensed under the `CC BY-SA 4.0 <https://creativecommons.org/licenses/by-sa/4.0/>`_ license:

- `doc/logo.png <https://raw.githubusercontent.com/pylint-dev/pylint/main/doc/logo.png>`_
- `doc/logo.svg <https://raw.githubusercontent.com/pylint-dev/pylint/main/doc/logo.svg>`_

Support
-------

Please check `the contact information`_.

.. _`the contact information`: https://pylint.readthedocs.io/en/latest/contact.html

.. |tideliftlogo| image:: https://raw.githubusercontent.com/pylint-dev/pylint/main/doc/media/Tidelift_Logos_RGB_Tidelift_Shorthand_On-White.png
   :width: 200
   :alt: Tidelift

.. list-table::
   :widths: 10 100

   * - |tideliftlogo|
     - Professional support for pylint is available as part of the `Tidelift
       Subscription`_.  Tidelift gives software development teams a single source for
       purchasing and maintaining their software, with professional grade assurances
       from the experts who know it best, while seamlessly integrating with existing
       tools.

.. _Tidelift Subscription: https://tidelift.com/subscription/pkg/pypi-pylint?utm_source=pypi-pylint&utm_medium=referral&utm_campaign=readme

```

---

## `pyproject.toml`

Role: **context**. may hold lint config

```toml
[build-system]
build-backend = "setuptools.build_meta"
requires = [ "setuptools>=77" ]

[project]
name = "pylint"
description = "python code static checker"
readme = "README.rst"
keywords = [ "lint", "linter", "python", "static code analysis" ]
license = "GPL-2.0-OR-later"
license-files = [ "LICENSE", "CONTRIBUTORS.txt" ]
authors = [
  { name = "Python Code Quality Authority", email = "code-quality@python.org" },
]
requires-python = ">=3.10.0"
classifiers = [
  "Development Status :: 6 - Mature",
  "Environment :: Console",
  "Intended Audience :: Developers",
  "Operating System :: OS Independent",
  "Programming Language :: Python",
  "Programming Language :: Python :: 3 :: Only",
  "Programming Language :: Python :: 3.10",
  "Programming Language :: Python :: 3.11",
  "Programming Language :: Python :: 3.12",
  "Programming Language :: Python :: 3.13",
  "Programming Language :: Python :: 3.14",
  "Programming Language :: Python :: 3.15",
  "Programming Language :: Python :: Implementation :: CPython",
  "Programming Language :: Python :: Implementation :: PyPy",
  "Topic :: Software Development :: Debuggers",
  "Topic :: Software Development :: Quality Assurance",
  "Topic :: Software Development :: Testing",
  "Typing :: Typed",
]
dynamic = [ "version" ]
# All the dependencies of the project will be configured here, once pip fully supports PEP735
# TODO: Remove all requirements.txt files and use this section instead once pip supports PEP735
dependencies = [
  # Also upgrade test-min dependency group and requirements_test_min.txt.
  # Pinned to dev of second minor update to allow editable installs and fix primer issues,
  # see https://github.com/pylint-dev/astroid/issues/1341
  "astroid>=4.2.0b5,<=4.3",
  "colorama>=0.4.5; sys_platform=='win32'",
  # Python 3.15 support has not been released yet, so we pin to a specific commit that supports it.
  "dill @ git+https://github.com/uqfoundation/dill@2308ffb0d0c605b9c050fa4c9fd5793d65c67022 ; python_version>='3.15'",
  "dill>=0.2; python_version<'3.11'",
  "dill>=0.3.6; python_version>='3.11'",
  "dill>=0.3.7; python_version>='3.12'",
  "isort>=5,!=5.13,<10",
  "mccabe>=0.6,<0.8",
  "platformdirs>=2.2",
  "tomli>=1.1; python_version<'3.11'",
  "tomlkit>=0.10.1",
  "typing-extensions>=3.10; python_version<'3.10'",
]
optional-dependencies.spelling = [ "pyenchant~=3.2" ]
optional-dependencies.testutils = [ "gitpython>3" ]
urls."Bug Tracker" = "https://github.com/pylint-dev/pylint/issues"
urls."Discord Server" = "https://discord.com/invite/Egy6P8AMB5"
urls."Docs: Contributor Guide" = """\
  https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/index.html\
  """
urls."Docs: User Guide" = "https://pylint.readthedocs.io/en/latest/"
urls."Source Code" = "https://github.com/pylint-dev/pylint"
urls."What's New" = "https://pylint.readthedocs.io/en/latest/whatsnew/4/"
urls.homepage = "https://github.com/pylint-dev/pylint"
scripts.pylint = "pylint:run_pylint"
scripts.pylint-config = "pylint:_run_pylint_config"
scripts.pyreverse = "pylint:run_pyreverse"
scripts.symilar = "pylint:run_symilar"

[dependency-groups]
dev = [
  "contributors-txt>=1",
  "pre-commit",
  "tbump~=6.11.0",
]
test = [
  "coverage~=7.10",
  "pytest-cov>=6.2,<8",
  "pytest-xdist~=3.8",
  "six",
  "tox>=3",
  { include-group = "test-min" },
]
docs = [
  "furo==2025.12.19",
  "sphinx==8.2.3",
  "sphinx-reredirects<1",
  "towncrier>=24.8,<26",
]
# Configuration for the build system
test-min = [
  # Base test dependencies
  "astroid==4.2.0b5",                   # Pinned to a specific version for tests
  "py~=1.11.0",
  "pytest>=8.4,<10",
  "pytest-benchmark~=5.1",
  "pytest-timeout~=2.4",
  "requests",
  "setuptools; python_version>='3.12'",
  "towncrier>=24.8,<26",
  "typing-extensions~=4.15",
]

[tool.setuptools]
packages.find.include = [ "pylint*" ]
# Simulate editable_mode=compat, described at:
# https://github.com/pypa/setuptools/issues/3767
# TODO: remove after solving root cause described at:
# https://github.com/pylint-dev/astroid/pull/2267#issuecomment-1666642781
package-dir."" = "."
package-data.pylint = [ "py.typed", "testutils/testing_pylintrc" ]
dynamic.version = { attr = "pylint.__pkginfo__.__version__" }

[tool.ruff]
# ruff is less lenient than pylint and does not make any exceptions
# (for docstrings, strings and comments in particular).
line-length = 115
extend-exclude = [
  "tests/**/data/",
  "tests/**/functional/",
  "tests/input/",
  "tests/regrtest_data/",
]
lint.extend-select = [
  "B",   # bugbear
  "D",   # pydocstyle
  "E",   # pycodestyle
  "F",   # pyflakes
  "I",   # isort
  "PIE", # flake8-pie
  "PTH", # flake8-pathlib
  "PYI", # flake8-pyi
  "RET", # flake8-return
  "RUF", # ruff
  "UP",  # pyupgrade
  "W",   # pycodestyle
]
lint.ignore = [
  "B905",   # `zip()` without an explicit `strict=` parameter
  "BLE001", # Do not catch blind exception: `Exception`
  "D100",   # Missing docstring in public module
  "D101",   # Missing docstring in public class
  "D102",   # Missing docstring in public method
  "D103",   # Missing docstring in public function
  "D104",   # Missing docstring in public package
  "D105",   # Missing docstring in magic method
  "D106",   # Missing docstring in public nested class
  "D107",   # Missing docstring in `__init__`
  "D205",   # 1 blank line required between summary line and description
  "D400",   # First line should end with a period
  "D401",   # First line of docstring should be in imperative mood
  "DTZ003", # `datetime.datetime.utcnow()` used
  "DTZ005", # `datetime.datetime.now()` called without a `tz` argument
  "EXE001", # Shebang is present but file is not executable
  "FLY002", # Consider f-string instead of string join
  "ISC004", # Implicitly concatenated string in a collection literal
  "LOG015", # `logging` call on the root logger
  "PT031",  # `pytest.warns()` block should contain a single simple statement
  "PTH100", # `os.path.abspath()` should be replaced by `Path.resolve()`
  "PTH103", # `os.makedirs()` should be replaced by `Path.mkdir(parents=True)`
  "PTH107", # `os.remove()` should be replaced by `Path.unlink()`
  "PTH108", # `os.unlink()` should be replaced by `Path.unlink()`
  "PTH109", # `os.getcwd()` should be replaced by `Path.cwd()`
  "PTH110", # `os.path.exists()` should be replaced by `Path.exists()`
  "PTH111", # `os.path.expanduser()` should be replaced by `Path.expanduser()`
  "PTH112", # `os.path.isdir()` should be replaced by `Path.is_dir()`
  "PTH113", # `os.path.isfile()` should be replaced by `Path.is_file()`
  "PTH118", # `os.path.join()` should be replaced by `Path` with `/` operator
  "PTH119", # `os.path.basename()` should be replaced by `Path.name`
  "PTH120", # `os.path.dirname()` should be replaced by `Path.parent`
  "PTH122", # `os.path.splitext()` should be replaced by `Path.suffix`, `Path.stem`, and `Path.parent`
  "PTH123", # `open()` should be replaced by `Path.open()`
  "PTH207", # Replace `glob` with `Path.glob` or `Path.rglob`
  "PTH208", # Use `pathlib.Path.iterdir()` instead"
  "RUF012", # mutable default values in class attributes
  "S102",   # Use of `exec` detected
  "SIM102", # Use a single `if` statement instead of nested `if` statements
  "SIM103", # Return the condition directly
  "SIM114", # Combine `if` branches using logical `or` operator
  "SIM115", # Use a context manager for opening files
  "SIM117", # Use a single `with` statement with multiple contexts
  "TRY004", # Prefer `TypeError` exception for invalid type
  "YTT204", # `sys.version_info.minor` compared to integer
]
lint.pydocstyle.convention = "pep257"

[tool.isort]
profile = "black"
extra_standard_library = [ "_string" ]
known_third_party = [ "astroid", "isort", "mccabe", "platformdirs", "pytest", "six", "sphinx", "toml" ]
src_paths = [ "pylint" ]
skip_glob = [
  "astroid/**",
  "tests/data/**",
  "tests/extensions/data/**",
  "tests/functional/**",
  "tests/input/**",
  "tests/regrtest_data/**",
  "venv/**",
]

[tool.codespell]
ignore-words = [ "custom_dict.txt" ]
# Disabled the spelling files for obvious reason, but also,
# the test file with typing extension imported as 'te' and:
# tests/functional/i/implicit/implicit_str_concat_latin1.py:
#   - bad encoding
# pylint/pyreverse/diagrams.py and tests/pyreverse/test_diagrams.py:
#   - An API from pyreverse use 'classe', and would need to be deprecated
# pylint/checkers/imports.py:
#   - 'THIRDPARTY' is a value from isort that would need to be handled even
#   if isort fix the typo in newer versions
# tests/functional/m/member/member_checks.py:
#   - typos are voluntary to create credible 'no-member'
skip = """\
  tests/checkers/unittest_spelling.py,CODE_OF_CONDUCT.md,CONTRIBUTORS.txt,pylint/checkers/imports.py,pylint/pyreverse/d\
  iagrams.py,tests/pyreverse/test_diagrams.py,tests/functional/i/implicit/implicit_str_concat_latin1.py,tests/functiona\
  l/m/member/member_checks.py,tests/functional/t/type/typevar_naming_style_rgx.py,tests/functional/t/type/typevar_namin\
  g_style_default.py,tests/functional/m/member/member_checks_async.py,\
  """

[tool.pyproject-fmt]
max_supported_python = "3.15"

[tool.mypy]
# TODO: Remove this once pytest has annotations
disallow_untyped_decorators = false
warn_unused_ignores = true
enable_error_code = "ignore-without-code"
strict = true
scripts_are_modules = true
show_error_codes = true

[[tool.mypy.overrides]]
module = [
  "_pytest.*",
  "_string",
  "astroid.*",
  # `colorama` ignore is needed for Windows environment
  "colorama",
  "contributors_txt",
  "coverage",
  "dill",
  "enchant.*",
  "git.*",
  "mccabe",
  "pytest",
  "pytest_benchmark.*",
  "sphinx.*",
]
ignore_missing_imports = true

# For local tests: Enable follow_untyped_imports overwrite for astroid
# [[tool.mypy.overrides]]
# module = ["astroid.*"]
# follow_untyped_imports = true
[tool.pyright]
pythonVersion = "3.10"
typeCheckingMode = "basic"
include = [
  "pylint",
  # not checking the tests yet, but we could
]
reportArgumentType = "none"  # 12 issues
reportAttributeAccessIssue = "none"  # 11 issues
reportCallIssue = "none"  # 1 issue
reportGeneralTypeIssues = "none"  # 1 issue
reportInvalidTypeForm = "none"  # 6 issues
reportInvalidTypeVarUse = "none"  # 2 warnings
reportMissingImports = "none"  # pytest / astroid are not detected
reportOptionalCall = "none"  # 2 issues
reportOptionalMemberAccess = "none"  # 150 issues

[tool.pytest]
ini_options.testpaths = [ "tests" ]
ini_options.python_files = [ "*test_*.py" ]
ini_options.addopts = "--strict-markers"
ini_options.markers = [
  "benchmark: Baseline of pylint performance, if this regress something serious happened",
  "needs_two_cores: Checks that need 2 or more cores to be meaningful",
  "primer_stdlib: Checks for crashes and errors when running pylint on stdlib",
  "timeout: Marks from pytest-timeout.",
]
ini_options.filterwarnings = [
  "error",
  # Added in Python 3.14
  "ignore:'break' in a 'finally' block:SyntaxWarning",
  "ignore:'continue' in a 'finally' block:SyntaxWarning",
  "ignore:'return' in a 'finally' block:SyntaxWarning",
]

[tool.aliases]
test = "pytest"

```

---

## `towncrier.toml`

Role: **context**. changelog tooling config

```toml
[tool.towncrier]
version = "4.0.0-dev0"
directory = "doc/whatsnew/fragments"
filename = "doc/whatsnew/4/4.1/index.rst"
template = "doc/whatsnew/fragments/_template.rst"
issue_format = "`#{issue} <https://github.com/pylint-dev/pylint/issues/{issue}>`_"
wrap = false  # doesn't wrap links correctly if beginning with indentation

# Definition of fragment types.
# We want the changelog to show in the same order as the fragment types
# are defined here. Therefore we have to use the array-style fragment definition.
# The table-style definition, although more concise, would be sorted alphabetically.
# https://github.com/twisted/towncrier/issues/437
[[tool.towncrier.type]]
directory = "breaking"
name = "Breaking Changes"
showcontent = true

[[tool.towncrier.type]]
directory = "user_action"
name = "Changes requiring user actions"
showcontent = true

[[tool.towncrier.type]]
directory = "feature"
name = "New Features"
showcontent = true

[[tool.towncrier.type]]
directory = "new_check"
name = "New Checks"
showcontent = true

[[tool.towncrier.type]]
directory = "removed_check"
name = "Removed Checks"
showcontent = true

[[tool.towncrier.type]]
directory = "extension"
name = "Extensions"
showcontent = true

[[tool.towncrier.type]]
directory = "false_positive"
name = "False Positives Fixed"
showcontent = true

[[tool.towncrier.type]]
directory = "false_negative"
name = "False Negatives Fixed"
showcontent = true

[[tool.towncrier.type]]
directory = "bugfix"
name = "Other Bug Fixes"
showcontent = true

[[tool.towncrier.type]]
directory = "other"
name = "Other Changes"
showcontent = true

[[tool.towncrier.type]]
directory = "internal"
name = "Internal Changes"
showcontent = true

[[tool.towncrier.type]]
directory = "performance"
name = "Performance Improvements"
showcontent = true

```

---

## `tox.ini`

Role: **context**. may hold lint config

```ini
[tox]
minversion = 3.0
envlist = formatting, py310, py311, py312, py313, py314, py315, pypy, benchmark
skip_missing_interpreters = true
requires = pip >=21.3.1
isolated_build = true

[testenv:pylint]
deps =
    -r {toxinidir}/requirements_test.txt
commands =
    pre-commit run pylint --all-files

[testenv:formatting]
basepython = python3
deps =
    -r {toxinidir}/requirements_test.txt
commands =
    pre-commit run --all-files

[testenv:mypy]
basepython = python3
deps =
    pre-commit~=2.20
commands =
    pre-commit run mypy --all-files

[testenv]
setenv =
    COVERAGE_FILE = {toxinidir}/.coverage.{envname}
deps =
    !pypy: -r {toxinidir}/requirements_test.txt
    pypy: -r {toxinidir}/requirements_test_min.txt
commands =
    ; Run tests, ensuring all benchmark tests do not run
    pytest --benchmark-disable {toxinidir}/tests/ {posargs:}

[testenv:spelling]
deps =
    -r {toxinidir}/requirements_test.txt
commands =
    pytest {toxinidir}/tests/ {posargs:} -k unittest_spelling

[testenv:coverage-html]
setenv =
    COVERAGE_FILE = {toxinidir}/.coverage
deps =
    -r {toxinidir}/requirements_test.txt
skip_install = true
commands =
    coverage combine
    coverage html --ignore-errors --rcfile={toxinidir}/.coveragerc

[testenv:docs]
changedir = doc/
deps =
    -r {toxinidir}/doc/requirements.txt
commands =
    # Readthedoc launch a slightly different command see '.readthedocs.yaml'
    # sphinx-build -T -W -E --keep-going -b html -d _build/doctrees -D language=en . _build/html
    # Changes were made for performance reasons, add or remove only if you can't reproduce.
    sphinx-build -T -W -j auto --keep-going -b html -d _build/doctrees -D language=en . _build/html
    # -E: don't use a saved environment, always read all files
    # -j auto: build in parallel with N processes where possible (special value "auto" will set N to cpu-count)

[testenv:test_doc]
deps =
    -r {toxinidir}/requirements_test.txt
commands =
    pytest {toxinidir}/doc/test_messages_documentation.py

[testenv:benchmark]
deps =
    -r {toxinidir}/requirements_test.txt
    pygal
commands =
    ; Run the only the benchmark tests, grouping output and forcing .json output so we
    ; can compare benchmark runs
    pytest --exitfirst \
    --failed-first \
    --benchmark-only \
    --benchmark-save=batch_files \
    --benchmark-save-data \
    --benchmark-autosave {toxinidir}/tests \
    --benchmark-group-by="group" \
    {posargs:}

```
