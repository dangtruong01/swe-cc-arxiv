# psf/requests: off-nav rule sources (raw, verbatim)

Repo: `psf/requests` @ `main`
Docs: https://requests.readthedocs.io/en/latest/
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
| `.github/ISSUE_TEMPLATE/Bug_report.md` | rules | ok | expect X-ISSUE |
| `.github/ISSUE_TEMPLATE/Custom.md` | rules | ok | expect X-ISSUE |
| `.github/ISSUE_TEMPLATE/Feature_request.md` | rules | ok | expect X-ISSUE |
| `.pre-commit-config.yaml` | context | ok | decides the Auto-fix column |
| `README.md` | context | ok | check for canonical test invocation |
| `docs/dev/contributing.rst` | rules | ok | rule source or redirect | DUPLICATE RISK: source of a rendered doc page, do not extract twice |
| `pyproject.toml` | context | ok | may hold lint config |
| `tox.ini` | context | ok | may hold lint config |

---

## `.github/CONTRIBUTING.md`

Role: **rules**. rule source or redirect

```markdown
# Contribution Guidelines

Before opening any issues or proposing any pull requests, please read
our [Contributor's Guide](https://requests.readthedocs.io/en/latest/dev/contributing/)
as well as our [AI Policy](/.github/AI_POLICY.md).

To get the greatest chance of helpful responses, please also observe the
following additional notes.

## Questions

The GitHub issue tracker is for *bug reports* and *feature requests*. Please do
not use it to ask questions about how to use Requests. These questions should
instead be directed to [Stack Overflow](https://stackoverflow.com/). Make sure
that your question is tagged with the `python-requests` tag when asking it on
Stack Overflow, to ensure that it is answered promptly and accurately.

## Good Bug Reports

Please be aware of the following things when filing bug reports:

1. Avoid raising duplicate issues. *Please* use the GitHub issue search feature
   to check whether your bug report or feature request has been mentioned in
   the past. Duplicate bug reports and feature requests are a huge maintenance
   burden on the limited resources of the project. If it is clear from your
   report that you would have struggled to find the original, that's ok, but
   if searching for a selection of words in your issue title would have found
   the duplicate then the issue will likely be closed extremely abruptly.
2. When filing bug reports about exceptions or tracebacks, please include the
   *complete* traceback. Partial tracebacks, or just the exception text, are
   not helpful. Issues that do not contain complete tracebacks may be closed
   without warning.
3. Make sure you provide a suitable amount of information to work with. This
   means you should provide:

   - Guidance on **how to reproduce the issue**. Ideally, this should be a
     *small* code sample that can be run immediately by the maintainers.
     Failing that, let us know what you're doing, how often it happens, what
     environment you're using, etc. Be thorough: it prevents us needing to ask
     further questions.
   - Tell us **what you expected to happen**. When we run your example code,
     what are we expecting to happen? What does "success" look like for your
     code?
   - Tell us **what actually happens**. It's not helpful for you to say "it
     doesn't work" or "it fails". Tell us *how* it fails: do you get an
     exception? A hang? A non-200 status code? How was the actual result
     different from your expected result?
   - Tell us **what version of Requests you're using**, and
     **how you installed it**. Different versions of Requests behave
     differently and have different bugs, and some distributors of Requests
     ship patches on top of the code we supply.

   If you do not provide all of these things, it will take us much longer to
   fix your problem. If we ask you to clarify these and you never respond, we
   will close your issue without fixing it.

## Good Pull Requests

1. Avoid raising duplicate pull requests. *Please* use the GitHub pull request
   search feature to check whether someone else has already filed a pull
   request.
2. When filing a pull request, always include tests that fail without your
   changes thus preventing the fix from regressing.
3. Always run the test suite locally
4. Write commit messages that explain _why_ a change was made beyond "Fixes
   #NNNN". Why is this the right fix? What other options were ruled out? etc.

```

---

## `.github/ISSUE_TEMPLATE/Bug_report.md`

Role: **rules**. expect X-ISSUE

```markdown
---
name: Bug report
about: Create a report to help us improve

---

<!-- Summary. -->

## Expected Result

<!-- What you expected. -->

## Actual Result

<!-- What happened instead. -->

## Reproduction Steps

```python
import requests

```

## System Information

    $ python -m requests.help

```json
{
  "paste": "here"
}
```

<!-- This command is only available on Requests v2.16.4 and greater. Otherwise,
please provide some basic information about your system (Python version,
operating system, &c). -->

```

---

## `.github/ISSUE_TEMPLATE/Custom.md`

Role: **rules**. expect X-ISSUE

```markdown
---
name: Request for Help
about: Guidance on using Requests.
labels:
- "Question/Not a bug"
- "actions/autoclose-qa"

---

Please refer to our [Stack Overflow tag](https://stackoverflow.com/questions/tagged/python-requests) for guidance.

```

---

## `.github/ISSUE_TEMPLATE/Feature_request.md`

Role: **rules**. expect X-ISSUE

```markdown
---
name: Feature request
about: Suggest an idea for this project
labels:
- "Feature Request"
- "actions/autoclose-feat"

---

Requests is not accepting feature requests at this time.

```

---

## `.pre-commit-config.yaml`

Role: **context**. decides the Auto-fix column

```yaml
exclude: 'docs/|ext/'

repos:
- repo: https://github.com/pre-commit/pre-commit-hooks
  rev: v6.0.0
  hooks:
  - id: check-case-conflict
  - id: check-merge-conflict
  - id: check-toml
  - id: check-yaml
  - id: end-of-file-fixer
  - id: mixed-line-ending
    args: [--fix=auto]
  - id: trailing-whitespace
- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.16.3
  hooks:
    - id: ruff-check
      args: [--fix]
    - id: ruff-format
      exclude: tests/test_lowlevel.py

```

---

## `README.md`

Role: **context**. check for canonical test invocation

```markdown
# Requests

[![Version](https://img.shields.io/pypi/v/requests.svg?maxAge=86400)](https://pypi.org/project/requests/)
[![Supported Versions](https://img.shields.io/pypi/pyversions/requests.svg)](https://pypi.org/project/requests)
[![Downloads](https://static.pepy.tech/badge/requests/month)](https://pepy.tech/project/requests)
[![Contributors](https://img.shields.io/github/contributors/psf/requests.svg)](https://github.com/psf/requests/graphs/contributors)
[![Documentation](https://readthedocs.org/projects/requests/badge/?version=latest)](https://requests.readthedocs.io)

**Requests** is a simple, yet elegant, HTTP library.

```python
>>> import requests
>>> r = requests.get('https://httpbin.org/basic-auth/user/pass', auth=('user', 'pass'))
>>> r.status_code
200
>>> r.headers['content-type']
'application/json; charset=utf8'
>>> r.encoding
'utf-8'
>>> r.text
'{"authenticated": true, ...'
>>> r.json()
{'authenticated': True, ...}
```

Requests allows you to send HTTP/1.1 requests extremely easily. There’s no need to manually add query strings to your URLs, or to form-encode your `PUT` & `POST` data — but nowadays, just use the `json` method!

Requests is one of the most downloaded Python packages today, pulling in around `300M downloads / week` — according to GitHub, Requests is currently [depended upon](https://github.com/psf/requests/network/dependents?package_id=UGFja2FnZS01NzA4OTExNg%3D%3D) by `4,000,000+` repositories.

## Installing Requests and Supported Versions

Requests is available on PyPI:

```console
$ python -m pip install requests
```

Requests officially supports Python 3.10+.

## Supported Features & Best–Practices

Requests is ready for the demands of building robust and reliable HTTP–speaking applications, for the needs of today.

- Keep-Alive & Connection Pooling
- International Domains and URLs
- Sessions with Cookie Persistence
- Browser-style TLS/SSL Verification
- Basic & Digest Authentication
- Familiar `dict`–like Cookies
- Automatic Content Decompression and Decoding
- Multi-part File Uploads
- SOCKS Proxy Support
- Connection Timeouts
- Streaming Downloads
- Automatic honoring of `.netrc`
- Chunked HTTP Requests

## Cloning the repository

When cloning the Requests repository, you may need to add the `-c
fetch.fsck.badTimezone=ignore` flag to avoid an error about a bad commit timestamp (see
[this issue](https://github.com/psf/requests/issues/2690) for more background):

```shell
git clone -c fetch.fsck.badTimezone=ignore https://github.com/psf/requests.git
```

You can also apply this setting to your global Git config:

```shell
git config --global fetch.fsck.badTimezone ignore
```

---

[![Kenneth Reitz](https://raw.githubusercontent.com/psf/requests/main/ext/kr.png)](https://kennethreitz.org) [![Python Software Foundation](https://raw.githubusercontent.com/psf/requests/main/ext/psf.png)](https://www.python.org/psf)

```

---

## `docs/dev/contributing.rst`

Role: **rules**. rule source or redirect | DUPLICATE RISK: source of a rendered doc page, do not extract twice

```rst
.. _contributing:

Contributor's Guide
===================

If you're reading this, you're probably interested in contributing to Requests.
Thank you very much! Open source projects live-and-die based on the support
they receive from others, and the fact that you're even considering
contributing to the Requests project is *very* generous of you.

This document lays out guidelines and advice for contributing to this project.
If you're thinking of contributing, please start by reading this document and
getting a feel for how contributing to this project works. If you have any
questions, feel free to reach out to either `Nate Prewitt`_, `Ian Cordasco`_,
or `Seth Michael Larson`_, the primary maintainers.

.. _Ian Cordasco: https://www.coglib.com/~icordasc/
.. _Nate Prewitt: https://www.nateprewitt.com/
.. _Seth Michael Larson: https://sethmlarson.dev/

The guide is split into sections based on the type of contribution you're
thinking of making, with a section that covers general guidelines for all
contributors.

Code of Conduct
---------------

The Python community is made up of members from around the globe with a diverse
set of skills, personalities, and experiences. It is through these differences
that our community experiences great successes and continued growth. When you're
working with members of the community, follow the
`Python Software Foundation Code of Conduct`_ to help steer your interactions
and keep Python a positive, successful, and growing community.

.. _Python Software Foundation Code of Conduct: https://policies.python.org/python.org/code-of-conduct/

.. _early-feedback:

Get Early Feedback
------------------

If you are contributing, do not feel the need to sit on your contribution until
it is perfectly polished and complete. It helps everyone involved for you to
seek feedback as early as you possibly can. Submitting an early, unfinished
version of your contribution for feedback in no way prejudices your chances of
getting that contribution accepted, and can save you from putting a lot of work
into a contribution that is not suitable for the project.

Contribution Suitability
------------------------

Our project maintainers have the last word on whether or not a contribution is
suitable for Requests. All contributions will be considered carefully, but from
time to time, contributions will be rejected because they do not suit the
current goals or needs of the project.

If your contribution is rejected, don't despair! As long as you followed these
guidelines, you will have a much better chance of getting your next
contribution accepted.


Code Contributions
------------------

Steps for Submitting Code
~~~~~~~~~~~~~~~~~~~~~~~~~

When contributing code, you'll want to follow this checklist:

1. Fork the repository on GitHub.
2. Run the tests to confirm they all pass on your system. If they don't, you'll
   need to investigate why they fail. If you're unable to diagnose this
   yourself, raise it as a bug report by following the guidelines in this
   document: :ref:`bug-reports`.
3. Write tests that demonstrate your bug or feature. Ensure that they fail.
4. Make your change.
5. Run the entire test suite again, confirming that all tests pass *including
   the ones you just added*.
6. Send a GitHub Pull Request to the main repository's ``main`` branch.
   GitHub Pull Requests are the expected method of code collaboration on this
   project.

The following sub-sections go into more detail on some of the points above.

Code Review
~~~~~~~~~~~

Contributions will not be merged until they've been code reviewed. You should
implement any code review feedback unless you strongly object to it. In the
event that you object to the code review feedback, you should make your case
clearly and calmly. If, after doing so, the feedback is judged to still apply,
you must either apply the feedback or withdraw your contribution.

Code Style
~~~~~~~~~~

Requests uses a collection of tools to ensure the code base has a consistent
style as it grows. We have these orchestrated using a tool called
`pre-commit`_. This can be installed locally and run over your changes prior
to opening a PR, and will also be run as part of the CI approval process
before a change is merged.

You can find the full list of formatting requirements specified in the
`.pre-commit-config.yaml`_ at the top level directory of Requests.

.. _pre-commit: https://pre-commit.com/
.. _.pre-commit-config.yaml: https://github.com/psf/requests/blob/main/.pre-commit-config.yaml

New Contributors
~~~~~~~~~~~~~~~~

If you are new or relatively new to Open Source, welcome! Requests aims to
be a gentle introduction to the world of Open Source. If you're concerned about
how best to contribute, please consider mailing a maintainer (listed above) and
asking for help.

Please also check the :ref:`early-feedback` section.


Documentation Contributions
---------------------------

Documentation improvements are always welcome! The documentation files live in
the ``docs/`` directory of the codebase. They're written in
`reStructuredText`_, and use `Sphinx`_ to generate the full suite of
documentation.

When contributing documentation, please do your best to follow the style of the
documentation files. This means a soft-limit of 79 characters wide in your text
files and a semi-formal, yet friendly and approachable, prose style.

When presenting Python code, use single-quoted strings (``'hello'`` instead of
``"hello"``).

.. _reStructuredText: https://docutils.sourceforge.net/rst.html
.. _Sphinx: https://www.sphinx-doc.org/en/master/


.. _bug-reports:

Bug Reports
-----------

Bug reports are hugely important! Before you raise one, though, please check
through the `GitHub issues`_, **both open and closed**, to confirm that the bug
hasn't been reported before. Duplicate bug reports are a huge drain on the time
of other contributors, and should be avoided as much as possible.

.. _GitHub issues: https://github.com/psf/requests/issues


Feature Requests
----------------

Requests is in a perpetual feature freeze, only the BDFL can add or approve of
new features. The maintainers believe that Requests is a feature-complete
piece of software at this time.

One of the most important skills to have while maintaining a largely-used
open source project is learning the ability to say "no" to suggested changes,
while keeping an open ear and mind.

If you believe there is a feature missing, feel free to raise a feature
request, but please do be aware that the overwhelming likelihood is that your
feature request will not be accepted.

```

---

## `pyproject.toml`

Role: **context**. may hold lint config

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "requests"
description = "Python HTTP for Humans."
readme = "README.md"
license = {text = "Apache-2.0"}
authors = [
    { name = "Kenneth Reitz", email = "me@kennethreitz.org" },
]
maintainers = [
    {name = "Ian Stapleton Cordasco", email="graffatcolmingov@gmail.com"},
    {name = "Nate Prewitt", email="nate.prewitt@gmail.com"}
]
requires-python = ">=3.10"
dependencies = [
    "charset_normalizer>=2,<4",
    "idna>=2.5,<4",
    "urllib3>=1.26,<3",
    "certifi>=2023.5.7"
]
dynamic = ["version"]

classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Environment :: Web Environment",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: Apache Software License",
    "Natural Language :: English",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: 3.14",
    "Programming Language :: Python :: 3.15",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Python :: Implementation :: PyPy",
    "Programming Language :: Python :: Free Threading :: 2 - Beta",
    "Topic :: Internet :: WWW/HTTP",
    "Topic :: Software Development :: Libraries"
]

[project.urls]
Documentation = "https://requests.readthedocs.io"
Source = "https://github.com/psf/requests"

[project.optional-dependencies]
security = []
socks = ["PySocks>=1.5.6, !=1.5.7"]
use_chardet_on_py3 = ["chardet>=3.0.2,<8"]

[dependency-groups]
test = [
    "requests[socks]",
    "pytest-httpbin==2.1.0",
    "httpbin~=0.10.0",
    "pytest-cov",
    "pytest-mock",
    "pytest-xdist",
    "pytest>=3",
    "trustme",
]
typecheck = [
    "pyright",
    "typing_extensions",
    "chardet",
    "cryptography",
    "PyOpenSSL",
]

[tool.setuptools]
license-files = ["LICENSE", "NOTICE"]

[tool.setuptools.dynamic]
version = {attr = "requests.__version__.__version__"}

[tool.setuptools.packages.find]
where = ["src"]

[tool.ruff]
target-version = "py310"
src = ["src/requests", "tests"]
exclude = ["docs/", "ext/"]

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # pyflakes
    "I",      # isort
    "UP",     # pyupgrade
    "T10",    # flake8-debugger (replaces debug-statements hook)
]
ignore = ["E203", "E501", "UP031"]
per-file-ignores = {"src/requests/__init__.py" = ["E402", "F401"], "src/requests/compat.py" = ["E402", "F401"], "tests/compat.py" = ["F401"]}

[tool.ruff.lint.isort]
known-first-party = ["requests"]

[tool.ruff.format]
# Use black-compatible formatting
quote-style = "double"
indent-style = "space"

[tool.pytest.ini_options]
addopts = "--doctest-modules"
doctest_optionflags = "NORMALIZE_WHITESPACE ELLIPSIS"
minversion = "6.2"
testpaths = ["tests"]


[tool.pyright]
include = ["src/requests"]
typeCheckingMode = "strict"
# linting rules unrelated to type checking
reportPrivateUsage = false
reportPrivateImportUsage = false
reportUnnecessaryIsInstance = false
reportUnusedImport = false  # duplicate of Ruff's F401 rule

```

---

## `tox.ini`

Role: **context**. may hold lint config

```ini
[tox]
envlist = py{310,311,312,313,314}-{default, use_chardet_on_py3}

[testenv]
deps = -rrequirements-dev.txt
extras =
    security
    socks
commands =
    pytest {posargs:tests}

[testenv:default]

[testenv:use_chardet_on_py3]
extras =
    security
    socks
    use_chardet_on_py3

```
