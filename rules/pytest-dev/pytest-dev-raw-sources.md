# pytest-dev/pytest: off-nav rule sources (raw, verbatim)

Repo: `pytest-dev/pytest` @ `main`
Docs: https://docs.pytest.org/en/latest/
Docs version at pull time: **UNRESOLVED**

Any doc page served on a different version is a fetch failure, not a row.

Raw source, HTML comments intact. The rendered GitHub view strips comments,
and in template files the comments carry the actual obligations. Extract from
this text, not from a rendered page.

Role `context` means the file informs Section context and Auto-fix but never
produces sheet rows.

| Path | Role | Status | Note |
|---|---|---|---|
| `.github/ISSUE_TEMPLATE/1_bug_report.md` | rules | ok | expect X-ISSUE |
| `.github/ISSUE_TEMPLATE/2_feature_request.md` | rules | ok | expect X-ISSUE |
| `.github/ISSUE_TEMPLATE/3_security_vulnerability.md` | rules | ok | expect X-ISSUE |
| `.github/ISSUE_TEMPLATE/config.yml` | rules | ok | expect X-ISSUE |
| `.github/PULL_REQUEST_TEMPLATE.md` | rules | ok | obligations hide in HTML comments |
| `.pre-commit-config.yaml` | context | ok | decides the Auto-fix column |
| `CODE_OF_CONDUCT.md` | rules | ok | expect X-GOV |
| `CONTRIBUTING.rst` | rules | ok | rule source or redirect |
| `README.rst` | context | ok | check for canonical test invocation |
| `doc/en/contributing.rst` | rules | ok | rule source or redirect | DUPLICATE RISK: source of a rendered doc page, do not extract twice |
| `pyproject.toml` | context | ok | may hold lint config |
| `tox.ini` | context | ok | may hold lint config |

---

## `.github/ISSUE_TEMPLATE/1_bug_report.md`

Role: **rules**. expect X-ISSUE

```markdown
---
name: 🐛 Bug Report
about: Report errors and problems

---

<!--
Thanks for submitting an issue!

Quick check-list while reporting bugs:
-->

- [ ] a detailed description of the bug or problem you are having
- [ ] output of `pip list` from the virtual environment you are using
- [ ] pytest and operating system versions
- [ ] minimal example if possible

```

---

## `.github/ISSUE_TEMPLATE/2_feature_request.md`

Role: **rules**. expect X-ISSUE

```markdown
---
name: 🚀 Feature Request
about: Ideas for new features and improvements

---

<!--
Thanks for suggesting a feature!

Quick check-list while suggesting features:
-->

#### What's the problem this feature will solve?
<!-- What are you trying to do, that you are unable to achieve with pytest as it currently stands? -->

#### Describe the solution you'd like
<!-- A clear and concise description of what you want to happen. -->

<!-- Provide examples of real-world use cases that this would enable and how it solves the problem described above. -->

#### Alternative Solutions
<!-- Have you tried to workaround the problem using a pytest plugin or other tools? Or a different approach to solving this issue? Please elaborate here. -->

#### Additional context
<!-- Add any other context, links, etc. about the feature here. -->

```

---

## `.github/ISSUE_TEMPLATE/3_security_vulnerability.md`

Role: **rules**. expect X-ISSUE

```markdown
---
name: Security Vulnerability
about: Report security vulnerabilities
---

**Do not submit security vulnerabilities as issues**.

Create a [new Security Advisory](https://github.com/pytest-dev/pytest/security/advisories/new) instead.

```

---

## `.github/ISSUE_TEMPLATE/config.yml`

Role: **rules**. expect X-ISSUE

```yaml
blank_issues_enabled: false
contact_links:
  - name: ❓ Support Question
    url: https://github.com/pytest-dev/pytest/discussions
    about: Use GitHub's new Discussions feature for questions

```

---

## `.github/PULL_REQUEST_TEMPLATE.md`

Role: **rules**. obligations hide in HTML comments

```markdown
<!--
Thanks for submitting a PR, your contribution is really appreciated!

Here is a quick checklist that should be present in PRs.

- [ ] Include documentation when adding new features.
- [ ] Include new tests or update existing tests when applicable.
- [X] Allow maintainers to push and squash when merging my commits. Please uncheck this if you prefer to squash the commits yourself.

If this change fixes an issue, please:

- [ ] Add text like ``closes #XYZW`` to the PR description and/or commits (where ``XYZW`` is the issue number). See the [github docs](https://help.github.com/en/github/managing-your-work-on-github/linking-a-pull-request-to-an-issue#linking-a-pull-request-to-an-issue-using-a-keyword) for more information.

> [!IMPORTANT]
> **Unsupervised agentic contributions are not accepted**. See our [AI/LLM-Assisted Contributions Policy](https://github.com/pytest-dev/pytest/blob/main/CONTRIBUTING.rst#aillm-assisted-contributions-policy).

- [ ] If AI agents were used, they are credited in `Co-authored-by` commit trailers.

Unless your change is trivial or a small documentation fix (e.g., a typo or reword of a small section) please:

- [ ] Create a new changelog file in the `changelog` directory, with a name like `<ISSUE NUMBER>.<TYPE>.rst`. See [changelog/README.rst](https://github.com/pytest-dev/pytest/blob/main/changelog/README.rst) for details.

  Write sentences in the **past or present tense**, examples:

  * *Improved verbose diff output with sequences.*
  * *Terminal summary statistics now use multiple colors.*

  Also make sure to end the sentence with a `.`.

- [ ] Add yourself to `AUTHORS` in alphabetical order.
-->

```

---

## `.pre-commit-config.yaml`

Role: **context**. decides the Auto-fix column

```yaml
minimum_pre_commit_version: "4.4.0"
repos:
- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: "v0.16.5"
  hooks:
    - id: ruff-check
      args: ["--fix"]
    - id: ruff-format
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
- repo: https://github.com/woodruffw/zizmor-pre-commit
  rev: v1.30.0
  hooks:
    - id: zizmor
      args: ["--fix", "--no-progress"]
-   repo: https://github.com/adamchainz/blacken-docs
    rev: 1.20.0
    hooks:
    -   id: blacken-docs
        additional_dependencies: [black==24.1.1]
-   repo: https://github.com/codespell-project/codespell
    rev: v2.4.3
    hooks:
    -   id: codespell
        args: ["--toml=pyproject.toml"]
        additional_dependencies:
          - tomli
-   repo: https://github.com/pre-commit/pygrep-hooks
    rev: v1.10.0
    hooks:
    -   id: python-use-type-annotations
-   repo: https://github.com/pre-commit/mirrors-mypy
    rev: v2.3.1
    hooks:
    -   id: mypy
        files: ^(src/|testing/|scripts/)
        additional_dependencies:
          - iniconfig>=1.1.0
          - attrs>=19.2.0
          - pluggy>=1.5.0
          - packaging
          - tomli
          - types-setuptools
          - types-tabulate
            # for mypy running on python>=3.11 since exceptiongroup is only a dependency
            # on <3.11
          - exceptiongroup>=1.0.0rc8
-   repo: https://github.com/RobertCraigie/pyright-python
    rev: v1.1.411
    hooks:
    -   id: pyright
        files: ^(src/|scripts/)
        additional_dependencies:
          - iniconfig>=1.1.0
          - attrs>=19.2.0
          - pluggy>=1.5.0
          - packaging
          - tomli
          - types-setuptools
          - types-tabulate
            # for mypy running on python>=3.11 since exceptiongroup is only a dependency
            # on <3.11
          - exceptiongroup>=1.0.0rc8
        # Manual because passing pyright is a work in progress.
        stages: [manual]
- repo: https://github.com/pytest-dev/pyproject-fmt
  rev: "v2.12.1"
  hooks:
    - id: pyproject-fmt
      # https://pyproject-fmt.readthedocs.io/en/latest/#calculating-max-supported-python-version
      additional_dependencies: ["tox>=4.9"]
-   repo: https://github.com/asottile/pyupgrade
    rev: v3.21.2
    hooks:
    -   id: pyupgrade
        args:
          - "--py310-plus"
        # Manual because ruff does what pyupgrade does and the two are not out of sync
        # often enough to make launching pyupgrade everytime worth it
        stages: [manual]
-   repo: local
    hooks:
    -   id: pylint
        name: pylint
        entry: pylint
        language: unsupported
        types: [python]
        args: ["-rn", "-sn", "--fail-on=I", "--enable-all-extentions"]
        require_serial: true
        stages: [manual]
    -   id: rst
        name: rst
        entry: rst-lint
        files: ^(RELEASING.rst|README.rst|TIDELIFT.rst)$
        language: python
        additional_dependencies: [pygments, restructuredtext_lint>=2.0.0]
    -   id: changelogs-rst
        name: changelog filenames
        language: fail
        entry: >-
          changelog files must be named
          ####.(
          breaking
          | deprecation
          | feature
          | improvement
          | bugfix
          | vendor
          | doc
          | packaging
          | contrib
          | misc
          )(.#)?(.rst)?
        exclude: >-
          (?x)
          ^
            changelog/(
              \.gitignore
              |\d+\.(
                breaking
                |deprecation
                |feature
                |improvement
                |bugfix
                |vendor
                |doc
                |packaging
                |contrib
                |misc
              )(\.\d+)?(\.rst)?
              |README\.rst
              |_template\.rst
            )
          $
        files: ^changelog/
    -   id: changelogs-user-role
        name: Changelog files should use a non-broken :user:`name` role
        language: pygrep
        entry: :user:([^`]+`?|`[^`]+[\s,])
        pass_filenames: true
        types:
          - file
          - rst
    -   id: py-deprecated
        name: py library is deprecated
        language: pygrep
        entry: >
            (?x)\bpy\.(
                _code\.|
                builtin\.|
                code\.|
                io\.|
                path\.local\.sysfind|
                process\.|
                std\.|
                error\.|
                xml\.
            )
        types: [python]
    -   id: py-path-deprecated
        name: py.path usage is deprecated
        exclude: docs|src/_pytest/deprecated.py|testing/deprecated_test.py|src/_pytest/legacypath.py
        language: pygrep
        entry: \bpy\.path\.local
        types: [python]

```

---

## `CODE_OF_CONDUCT.md`

Role: **rules**. expect X-GOV

```markdown
# Contributor Covenant Code of Conduct

## Our Pledge

In the interest of fostering an open and welcoming environment, we as
contributors and maintainers pledge to making participation in our project and
our community a harassment-free experience for everyone, regardless of age, body
size, disability, ethnicity, sex characteristics, gender identity and expression,
level of experience, education, socio-economic status, nationality, personal
appearance, race, religion, or sexual identity and orientation.

## Our Standards

Examples of behavior that contributes to creating a positive environment
include:

* Using welcoming and inclusive language
* Being respectful of differing viewpoints and experiences
* Gracefully accepting constructive criticism
* Focusing on what is best for the community
* Showing empathy towards other community members

Examples of unacceptable behavior by participants include:

* The use of sexualized language or imagery and unwelcome sexual attention or
 advances
* Trolling, insulting/derogatory comments, and personal or political attacks
* Public or private harassment
* Publishing others' private information, such as a physical or electronic
 address, without explicit permission
* Other conduct which could reasonably be considered inappropriate in a
 professional setting

## Our Responsibilities

Project maintainers are responsible for clarifying the standards of acceptable
behavior and are expected to take appropriate and fair corrective action in
response to any instances of unacceptable behavior.

Project maintainers have the right and responsibility to remove, edit, or
reject comments, commits, code, wiki edits, issues, and other contributions
that are not aligned to this Code of Conduct, or to ban temporarily or
permanently any contributor for other behaviors that they deem inappropriate,
threatening, offensive, or harmful.

## Scope

This Code of Conduct applies both within project spaces and in public spaces
when an individual is representing the project or its community. Examples of
representing a project or community include using an official project e-mail
address, posting via an official social media account, or acting as an appointed
representative at an online or offline event. Representation of a project may be
further defined and clarified by project maintainers.

## Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be
reported by contacting the project team at coc@pytest.org. All
complaints will be reviewed and investigated and will result in a response that
is deemed necessary and appropriate to the circumstances. The project team is
obligated to maintain confidentiality with regard to the reporter of an incident.
Further details of specific enforcement policies may be posted separately.

Project maintainers who do not follow or enforce the Code of Conduct in good
faith may face temporary or permanent repercussions as determined by other
members of the project's leadership.

The coc@pytest.org address is routed to the following people who can also be
contacted individually:

- Brianna Laugher ([@pfctdayelise](https://github.com/pfctdayelise)): brianna@laugher.id.au
- Bruno Oliveira ([@nicoddemus](https://github.com/nicoddemus)): nicoddemus@gmail.com
- Freya Bruhin ([@the-compiler](https://github.com/the-compiler)): pytest@the-compiler.org

## Attribution

This Code of Conduct is adapted from the [Contributor Covenant][homepage], version 1.4,
available at https://www.contributor-covenant.org/version/1/4/code-of-conduct.html

[homepage]: https://www.contributor-covenant.org

For answers to common questions about this code of conduct, see
https://www.contributor-covenant.org/faq

```

---

## `CONTRIBUTING.rst`

Role: **rules**. rule source or redirect

```rst
============================
Contributing
============================

Contributions are highly welcomed and appreciated.  Every little bit of help counts,
so do not hesitate!


.. _submitfeedback:

Feature requests and feedback
-----------------------------

Do you like pytest?  Share some love on social media or in your blog posts!

We'd also like to hear about your propositions and suggestions.  Feel free to
`submit them as issues <https://github.com/pytest-dev/pytest/issues>`_ and:

* Explain in detail how they should work.
* Keep the scope as narrow as possible.  This will make it easier to implement.


.. _reportbugs:

Report bugs
-----------

Report bugs for pytest in the `issue tracker <https://github.com/pytest-dev/pytest/issues>`_.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting,
  specifically the Python interpreter version, installed libraries, and pytest
  version.
* Detailed steps to reproduce the bug.

If you can write a demonstration test that currently fails but should pass
(xfail), that is a very useful commit to make as well, even if you cannot
fix the bug itself.


.. _fixbugs:

Fix bugs
--------

Look through the `GitHub issues for bugs <https://github.com/pytest-dev/pytest/labels/type:%20bug>`_.
See also the `"good first issue" issues <https://github.com/pytest-dev/pytest/labels/good%20first%20issue>`_
that are friendly to new contributors.

`Talk to developers <https://docs.pytest.org/en/stable/contact.html>`_ to find out how you can fix specific bugs. To indicate that you are going
to work on a particular issue, add a comment to that effect on the specific issue.

Don't forget to check the issue trackers of your favourite plugins, too!

.. _writeplugins:

Implement features
------------------

Look through the `GitHub issues for enhancements <https://github.com/pytest-dev/pytest/labels/type:%20enhancement>`_.

`Talk to developers <https://docs.pytest.org/en/stable/contact.html>`_ to find out how you can implement specific
features.

Write documentation
-------------------

Pytest could always use more documentation.  What exactly is needed?

* More complementary documentation.  Have you perhaps found something unclear?
* Documentation translations.  We currently have only English.
* Docstrings.  There can never be too many of them.
* Blog posts, articles and such -- they're all very appreciated.

You can also edit documentation files directly in the GitHub web interface,
without using a local copy.  This can be convenient for small fixes.

.. note::
    Build the documentation locally with the following command:

    .. code:: bash

        $ tox -e docs

    The built documentation should be available in ``doc/en/_build/html``,
    where 'en' refers to the documentation language.

Pytest has an API reference which in large part is
`generated automatically <https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html>`_
from the docstrings of the documented items. Pytest uses the
`Sphinx docstring format <https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html>`_.
For example:

.. code-block:: python

    def my_function(arg: ArgType) -> Foo:
        """Do important stuff.

        More detailed info here, in separate paragraphs from the subject line.
        Use proper sentences -- start sentences with capital letters and end
        with periods.

        Can include annotated documentation:

        :param short_arg: An argument which determines stuff.
        :param long_arg:
            A long explanation which spans multiple lines, overflows
            like this.
        :returns: The result.
        :raises ValueError:
            Detailed information when this can happen.

        .. versionadded:: 6.0

        Including types into the annotations above is not necessary when
        type-hinting is being used (as in this example).
        """


.. _submitplugin:

Submitting Plugins to pytest-dev
--------------------------------

Development of the pytest core, support code, and some plugins happens
in repositories living under the ``pytest-dev`` organisations:

- `pytest-dev on GitHub <https://github.com/pytest-dev>`_

All pytest-dev Contributors team members have write access to all contained
repositories.  Pytest core and plugins are generally developed
using `pull requests`_ to respective repositories.

The objectives of the ``pytest-dev`` organisation are:

* Having a central location for popular pytest plugins
* Sharing some of the maintenance responsibility (in case a maintainer no
  longer wishes to maintain a plugin)

You can submit your plugin by posting a new topic in the `pytest-dev GitHub Discussions
<https://github.com/pytest-dev/pytest/discussions>`_ pointing to your existing pytest plugin repository which must have
the following:

- PyPI presence with packaging metadata that contains a ``pytest-``
  prefixed name, version number, authors, short and long description.

- a `tox configuration <https://tox.readthedocs.io/en/latest/config.html#configuration-discovery>`_
  for running tests using `tox <https://tox.readthedocs.io>`_.

- a ``README`` describing how to use the plugin and on which
  platforms it runs.

- a ``LICENSE`` file containing the licensing information, with
  matching info in its packaging metadata.

- an issue tracker for bug reports and enhancement requests.

- a `changelog <https://keepachangelog.com/>`_.

If no contributor strongly objects and two agree, the repository can then be
transferred to the ``pytest-dev`` organisation.

Here's a rundown of how a repository transfer usually proceeds
(using a repository named ``joedoe/pytest-xyz`` as example):

* ``joedoe`` transfers repository ownership to ``pytest-dev`` administrator ``calvin``.
* ``calvin`` creates ``pytest-xyz-admin`` and ``pytest-xyz-developers`` teams, inviting ``joedoe`` to both as **maintainer**.
* ``calvin`` transfers repository to ``pytest-dev`` and configures team access:

  - ``pytest-xyz-admin`` **admin** access;
  - ``pytest-xyz-developers`` **write** access;

The ``pytest-dev/Contributors`` team has write access to all projects, and
every project administrator is in it. We recommend that each plugin has at least three
people who have the right to release to PyPI.

Repository owners can rest assured that no ``pytest-dev`` administrator will ever make
releases of your repository or take ownership in any way, except in rare cases
where someone becomes unresponsive after months of contact attempts.
As stated, the objective is to share maintenance and avoid "plugin-abandon".


.. _ai-contributions:

AI/LLM-Assisted Contributions Policy
-------------------------------------

We welcome contributions from all developers, including those who use AI/LLM tools
as part of their workflow. We genuinely encourage you to reach for these tools when
they help you learn, explore, and produce better work. However, we have requirements
to protect the time and effort of our reviewers:

**We use these tools ourselves.** Several pytest-core maintainers have access to
Anthropic's open-source grant (including Opus on Claude Max). We reach for AI daily
and value it — which is exactly why this policy is about *human effort*, not about the
tools. The bar is the one we hold ourselves to: understand what you ship, and stand
behind it.

**Real effort earns real investment.** If you have genuinely worked on a change — even
a rough or imperfect one — and can talk about it, we are glad to review it, give
feedback, and help you improve it, AI-assisted or not. What we ask for is your
engagement, not perfection. The line is human effort and accountability, never the
tools you used to get there.

**You are responsible for your contribution.** Regardless of how the code was
produced, the person submitting a pull request must understand the changes and be
able to respond to review feedback. If a reviewer asks questions or requests changes,
they expect to interact with someone who can engage substantively, not an automated
loop replaying prompts.

**Purely agentic contributions are not accepted.** Pull requests that are entirely
generated by AI agents, with no meaningful human review, understanding, or oversight,
will be closed. Every contribution must demonstrate that a human has reviewed,
understood, and taken responsibility for the changes. If you submit it, you own it.

**Unattended automation is an attack on the commons.** A contribution that shows
little to no human effort — unattended agent output, bulk-generated changes, PRs the
author cannot explain — is not collaboration. It is a denial-of-service on a volunteer
team: it spends finite review capacity that belongs to people who are genuinely trying
to learn and build. This is bigger than pytest — flooding *any* open-source project
with unattended AI output is hostile to a shared resource all of us depend on.

**We recognize the patterns, and we ban with prejudice.** Having driven these tools
daily, we know the tell-tale signatures of unattended agent output ("clankers"): the
generic commit prose, the confidently-wrong diffs, the inability to answer a simple
"why," the drive-by PR against an issue the author never engaged with. We will be
honest: the last several months of painful, low-quality bot contributions have left us
trigger-happy, and when those patterns show up we no longer spend a review cycle
coaxing a bot — we close and ban with prejudice. If you are a real person who happens
to trip a false positive, just talk to us; a human who understands their change is
always welcome, and we would far rather talk to you than to a script.

**Credit AI tools via attribution.** If AI agents helped produce your code or
commits, consider adding ``Co-authored-by`` trailers to your commit messages to
credit them. This is not required, but helps reviewers set expectations and is
appreciated.


Context
~~~~~~~

With the advent of unsupervised agentic tools like OpenClaw,
there has been a rise in low-quality contributions
where an agent produces a large number of low-quality pull requests.
Oftentimes this can look similar to a human beginner with new access to tools
and trying to learn, but in practice it is usually an unsupervised agentic tool
generating changes without meaningful human review.

When a human contributor is learning, we are glad to invest time to help,
give feedback, and guide them in the right direction. With fully agentic,
unsupervised tools, that same review effort does not support anyone's learning
or growth. Instead, it diverts limited maintainer time away from improving the
project and supporting engaged contributors.

There is also an asymmetry at play: someone is prioritizing what we review
without making an equivalent investment of time or effort.
When a contributor works on an issue themselves, they invest real time, effectively
earning influence over what the project focuses on. Unsupervised agentic contributions
expect to set that priority at near-zero cost to the sender, while shifting the
entire burden onto maintainers.

Fully agentic contributions invert the intended benefit of these tools: rather than
saving time, they create avoidable review and triage work. There is no accountable
human author thoughtfully iterating on feedback, only automated output driven
by prompts.

From our own experience using coding agents, we know they must be carefully prompted,
supervised, and checked by humans. Even modern models can make serious mistakes when
operating at framework or tooling level, and those mistakes can be subtle and
time-consuming to diagnose.

Running such tools unsupervised on open-source projects imposes this cost on
maintainers and other contributors without their consent. Our goal with this policy
is to set clear expectations, protect reviewer time, and ensure that contributions
remain collaborative, respectful, and sustainable.


.. _`pull requests`:
.. _pull-requests:

Preparing Pull Requests
-----------------------

Short version
~~~~~~~~~~~~~

#. Fork the repository.
#. Fetch tags from upstream if necessary (if you cloned only main `git fetch --tags https://github.com/pytest-dev/pytest`).
#. Enable and install `pre-commit <https://pre-commit.com>`_ to ensure style-guides and code checks are followed.
#. Follow `PEP-8 <https://www.python.org/dev/peps/pep-0008/>`_ for naming.
#. Tests are run using ``tox``::

    tox -e linting,py313

   The test environments above are usually enough to cover most cases locally.

#. Write a ``changelog`` entry: ``changelog/2574.bugfix.rst``, use issue id number
   and one of ``feature``, ``improvement``, ``bugfix``, ``doc``, ``deprecation``,
   ``breaking``, ``vendor``, ``packaging``, ``contrib``, or ``misc`` for the issue type.


#. Unless your change is a trivial or a documentation fix (e.g., a typo or reword of a small section) please
   add yourself to the ``AUTHORS`` file, in alphabetical order.


Long version
~~~~~~~~~~~~

What is a "pull request"?  It informs the project's core developers about the
changes you want to review and merge.  Pull requests are stored on
`GitHub servers <https://github.com/pytest-dev/pytest/pulls>`_.
Once you send a pull request, we can discuss its potential modifications and
even add more commits to it later on. There's an excellent tutorial on how Pull
Requests work in the
`GitHub Help Center <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests>`_.

Here is a simple overview, with pytest-specific bits:

#. Fork the
   `pytest GitHub repository <https://github.com/pytest-dev/pytest>`__.  It's
   fine to use ``pytest`` as your fork repository name because it will live
   under your user.

#. Clone your fork locally using `git <https://git-scm.com/>`_ and create a branch::

    $ git clone git@github.com:YOUR_GITHUB_USERNAME/pytest.git
    $ cd pytest
    $ git fetch --tags https://github.com/pytest-dev/pytest
    # now, create your own branch off "main":

        $ git checkout -b your-bugfix-branch-name main

   Given we have "major.minor.micro" version numbers, bug fixes will usually
   be released in micro releases whereas features will be released in
   minor releases and incompatible changes in major releases.

   You will need the tags to test locally, so be sure you have the tags from the main repository. If you suspect you don't, set the main repository as upstream and fetch the tags::

     $ git remote add upstream https://github.com/pytest-dev/pytest
     $ git fetch upstream --tags

   If you need some help with Git, follow this quick start
   guide: https://git.wiki.kernel.org/index.php/QuickStart

#. Install `pre-commit <https://pre-commit.com>`_ and its hook on the pytest repo::

     $ pip install --user pre-commit
     $ pre-commit install

   Afterwards ``pre-commit`` will run whenever you commit.

   https://pre-commit.com/ is a framework for managing and maintaining multi-language pre-commit hooks
   to ensure code-style and code formatting is consistent.

#. Install tox

   Tox is used to run all the tests and will automatically setup virtualenvs
   to run the tests in.
   (will implicitly use https://virtualenv.pypa.io/en/latest/)::

    $ pip install tox

#. Run all the tests

   You need to have a supported Python version available in your system.  Now
   running tests is as simple as issuing this command::

    $ tox -e linting,py

   This command will run tests via the "tox" tool against your default Python
   version and also perform "lint" coding-style checks.

#. You can now edit your local working copy and run the tests again as necessary. Please follow `PEP-8 <https://www.python.org/dev/peps/pep-0008/>`_ for naming.

   You can pass different options to ``tox``. For example, to run tests on Python 3.13 and pass options to pytest
   (e.g. enter pdb on failure) you can do::

    $ tox -e py313 -- --pdb

   Or to only run tests in a particular test module on Python 3.12::

    $ tox -e py312 -- testing/test_config.py


   When committing, ``pre-commit`` will re-format the files if necessary.

#. If instead of using ``tox`` you prefer to run the tests directly, then we suggest to create a virtual environment and
   install the project together with the ``dev`` :pep:`735` dependency group (requires ``pip`` 25.1+)::

       $ python3 -m venv .venv
       $ source .venv/bin/activate  # Linux
       $ .venv/Scripts/activate.bat  # Windows
       $ pip install -e . --group dev

   Alternatively, with ``uv``::

       $ uv sync --group dev

   Afterwards, you can edit the files and run pytest normally::

       $ pytest testing/test_config.py

#. Create a new changelog entry in ``changelog``. The file should be named ``<issueid>.<type>.rst``,
   where *issueid* is the number of the issue related to the change and *type* is one of
   ``feature``, ``improvement``, ``bugfix``, ``doc``, ``deprecation``, ``breaking``, ``vendor``,
   ``packaging``, ``contrib``, or ``misc``.
   You may skip creating the changelog entry if the change doesn't affect the
   documented behaviour of pytest.

#. Add yourself to ``AUTHORS`` file if not there yet, in alphabetical order.

#. Commit and push once your tests pass and you are happy with your change(s)::

    $ git commit -a -m "<commit message>"
    $ git push -u

#. Finally, submit a pull request through the GitHub website using this data::

    head-fork: YOUR_GITHUB_USERNAME/pytest
    compare: your-branch-name

    base-fork: pytest-dev/pytest
    base: main


Writing Tests
~~~~~~~~~~~~~

Writing tests for plugins or for pytest itself is often done using the `pytester fixture <https://docs.pytest.org/en/stable/reference/reference.html#pytester>`_, as a "black-box" test.

For example, to ensure a simple test passes you can write:

.. code-block:: python

    def test_true_assertion(pytester):
        pytester.makepyfile(
            """
            def test_foo():
                assert True
        """
        )
        result = pytester.runpytest()
        result.assert_outcomes(failed=0, passed=1)


Alternatively, it is possible to make checks based on the actual output of the terminal using
*glob-like* expressions:

.. code-block:: python

    def test_true_assertion(pytester):
        pytester.makepyfile(
            """
            def test_foo():
                assert False
        """
        )
        result = pytester.runpytest()
        result.stdout.fnmatch_lines(["*assert False*", "*1 failed*"])

When choosing a file where to write a new test, take a look at the existing files and see if there's
one file which looks like a good fit. For example, a regression test about a bug in the ``--lf`` option
should go into ``test_cacheprovider.py``, given that this option is implemented in ``cacheprovider.py``.
If in doubt, go ahead and open a PR with your best guess and we can discuss this over the code.

Joining the Development Team
----------------------------

Commit access is an invitation the development team extends once a contributor
has shown a developed sense for the project -- its scope, its conventions, and
what a change costs the people who depend on it.  We look for that across
contributions, reviews and discussions rather than in any single pull request,
so there is nothing to clear on demand; if we haven't reached out yet, that is
not a verdict on your work -- sometimes no-one has thought to offer.

The invitation does not change how you contribute: everyone goes through the
same pull-request-and-review process, and no-one merges their own pull requests
unless already approved.  It does mean you can take a fuller part in the
development process, since you can merge other contributors' pull requests once
you have reviewed them.


Merge/squash guidelines
-----------------------

When a PR is approved and ready to be integrated to the ``main`` branch, one has the option to *merge* the commits unchanged, or *squash* all the commits into a single commit.

Here are some guidelines on how to proceed, based on examples of a single PR commit history:

1. Miscellaneous commits:

   * ``Implement X``
   * ``Fix test_a``
   * ``Add myself to AUTHORS``
   * ``fixup! Fix test_a``
   * ``Update tests/test_integration.py``
   * ``Merge origin/main into PR branch``
   * ``Update tests/test_integration.py``

   In this case, prefer to use the **Squash** merge strategy: the commit history is a bit messy (not in a derogatory way, often one just commits changes because they know the changes will eventually be squashed together), so squashing everything into a single commit is best. You must clean up the commit message, making sure it contains useful details.

2. Separate commits related to the same topic:

   * ``Implement X``
   * ``Add myself to AUTHORS``
   * ``Update CHANGELOG for X``

   In this case, prefer to use the **Squash** merge strategy: while the commit history is not "messy" as in the example above, the individual commits do not bring much value overall, specially when looking at the changes a few months/years down the line.

3. Separate commits, each with their own topic (refactorings, renames, etc), but still have a larger topic/purpose.

   * ``Refactor class X in preparation for feature Y``
   * ``Remove unused method``
   * ``Implement feature Y``

   In this case, prefer to use the **Merge** strategy: each commit is valuable on its own, even if they serve a common topic overall. Looking at the history later, it is useful to have the removal of the unused method separately on its own commit, along with more information (such as how it became unused in the first place).

4. Separate commits, each with their own topic, but without a larger topic/purpose other than improve the code base (using more modern techniques, improve typing, removing clutter, etc).

   * ``Improve internal names in X``
   * ``Add type annotations to Y``
   * ``Remove unnecessary dict access``
   * ``Remove unreachable code due to EOL Python``

   In this case, prefer to use the **Merge** strategy: each commit is valuable on its own, and the information on each is valuable in the long term.


As mentioned, those are overall guidelines, not rules cast in stone. This topic was discussed in `#12633 <https://github.com/pytest-dev/pytest/discussions/12633>`_.


*Backport PRs* (as those created automatically from a ``backport`` label) should always be **squashed**, as they preserve the original PR author.


Backporting bug fixes for the next patch release
------------------------------------------------

Pytest makes a feature release every few weeks or months. In between, patch releases
are made to the previous feature release, containing bug fixes only. The bug fixes
usually fix regressions, but may be any change that should reach users before the
next feature release.

Suppose for example that the latest release was 1.2.3, and you want to include
a bug fix in 1.2.4 (check https://github.com/pytest-dev/pytest/releases for the
actual latest release). The procedure for this is:

#. First, make sure the bug is fixed in the ``main`` branch, with a regular pull
   request, as described above. An exception to this is if the bug fix is not
   applicable to ``main`` anymore.

Automatic method:

Add a ``backport 1.2.x`` label to the PR you want to backport. This will create
a backport PR against the ``1.2.x`` branch.

Manual method:

#. ``git checkout origin/1.2.x -b backport-XXXX`` # use the main PR number here

#. Locate the merge commit on the PR, in the *merged* message, for example:

    nicoddemus merged commit 0f8b462 into pytest-dev:main

#. ``git cherry-pick -x -m1 REVISION`` # use the revision you found above (``0f8b462``).

#. Open a PR targeting ``1.2.x``:

   * Prefix the message with ``[1.2.x]``.
   * Delete the PR body, it usually contains a duplicate commit message.


Who does the backporting
~~~~~~~~~~~~~~~~~~~~~~~~

As mentioned above, bugs should first be fixed on ``main`` (except in rare occasions
that a bug only happens in a previous release). So, who should do the backport procedure described
above?

1. If the bug was fixed by a core developer, it is the main responsibility of that core developer
   to do the backport.
2. However, often the merge is done by another maintainer, in which case it is nice of them to
   do the backport procedure if they have the time.
3. For bugs submitted by non-maintainers, it is expected that a core developer will do
   the backport, normally the one that merged the PR on ``main``.
4. If a non-maintainer notices a bug which is fixed on ``main`` but has not been backported
   (due to maintainers forgetting to apply the *needs backport* or *backport x.x.x* labels, or just plain missing it),
   they are also welcome to open a PR with the backport. The procedure is simple and really
   helps with the maintenance of the project.

All the above are not rules, but merely some guidelines/suggestions on what we should expect
about backports.

Backports should be **squashed** (rather than **merged**), as doing so preserves the original PR author correctly.

Handling stale issues/PRs
-------------------------

Stale issues/PRs are those where pytest contributors have asked for questions/changes
and the authors didn't get around to answer/implement them yet after a somewhat long time, or
the discussion simply died because people seemed to lose interest.

There are many reasons why people don't answer questions or implement requested changes:
they might get busy, lose interest, or just forget about it,
but the fact is that this is very common in open source software.

The pytest team really appreciates every issue and pull request, but being a high-volume project
with many issues and pull requests being submitted daily, we try to reduce the number of stale
issues and PRs by regularly closing them. When an issue/pull request is closed in this manner,
it is by no means a dismissal of the topic being tackled by the issue/pull request, but it
is just a way for us to clear up the queue and make the maintainers' work more manageable. Submitters
can always reopen the issue/pull request in their own time later if it makes sense.

When to close
~~~~~~~~~~~~~

Here are a few general rules the maintainers use to decide when to close issues/PRs because
of lack of inactivity:

* Issues labeled ``question`` or ``needs information``: closed after 14 days inactive.
* Issues labeled ``proposal``: closed after six months inactive.
* Pull requests: after one month, consider pinging the author, update linked issue, or consider closing. For pull requests which are nearly finished, the team should consider finishing it up and merging it.

The above are **not hard rules**, but merely **guidelines**, and can be (and often are!) reviewed on a case-by-case basis.

Closing pull requests
~~~~~~~~~~~~~~~~~~~~~

When closing a Pull Request, we should acknowledge the time, effort, and interest demonstrated by the person who submitted it. As mentioned previously, it is not the intent of the team to dismiss a stalled pull request entirely but to merely to clear up our queue, so a message like the one below is warranted when closing a pull request that went stale:

    Hi <contributor>,

    First of all, we would like to thank you for your time and effort on working on this, the pytest team deeply appreciates it.

    We noticed it has been awhile since you have updated this PR, however. pytest is a high activity project, with many issues/PRs being opened daily, so it is hard for us maintainers to track which PRs are ready for merging, for review, or need more attention.

    So for those reasons, we think it is best to close the PR for now, but with the only intention to clean up our queue, it is by no means a rejection of your changes. We still encourage you to re-open this PR (it is just a click of a button away) when you are ready to get back to it.

    Again we appreciate your time for working on this, and hope you might get back to this at a later time!

    <bye>

Closing issues
--------------

When a pull request is submitted to fix an issue, add text like ``closes #XYZW`` to the PR description and/or commits (where ``XYZW`` is the issue number). See the `GitHub docs <https://help.github.com/en/github/managing-your-work-on-github/linking-a-pull-request-to-an-issue#linking-a-pull-request-to-an-issue-using-a-keyword>`_ for more information.

When an issue is due to user error (e.g. misunderstanding of a functionality), please politely explain to the user why the issue raised is really a non-issue and ask them to close the issue if they have no further questions. If the original requester is unresponsive, the issue will be handled as described in the section `Handling stale issues/PRs`_ above.

```

---

## `README.rst`

Role: **context**. check for canonical test invocation

```rst
.. image:: https://github.com/pytest-dev/pytest/raw/main/doc/en/img/pytest_logo_curves.svg
   :target: https://docs.pytest.org/en/stable/
   :align: center
   :height: 200
   :alt: pytest


------

.. image:: https://img.shields.io/pypi/v/pytest.svg
    :target: https://pypi.org/project/pytest/

.. image:: https://img.shields.io/conda/vn/conda-forge/pytest.svg
    :target: https://anaconda.org/conda-forge/pytest

.. image:: https://img.shields.io/pypi/pyversions/pytest.svg
    :target: https://pypi.org/project/pytest/

.. image:: https://codecov.io/gh/pytest-dev/pytest/branch/main/graph/badge.svg
    :target: https://codecov.io/gh/pytest-dev/pytest
    :alt: Code coverage Status

.. image:: https://github.com/pytest-dev/pytest/actions/workflows/test.yml/badge.svg
    :target: https://github.com/pytest-dev/pytest/actions?query=workflow%3Atest

.. image:: https://results.pre-commit.ci/badge/github/pytest-dev/pytest/main.svg
   :target: https://results.pre-commit.ci/latest/github/pytest-dev/pytest/main
   :alt: pre-commit.ci status

.. image:: https://www.codetriage.com/pytest-dev/pytest/badges/users.svg
    :target: https://www.codetriage.com/pytest-dev/pytest

.. image:: https://readthedocs.org/projects/pytest/badge/?version=latest
    :target: https://pytest.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://img.shields.io/badge/Discord-pytest--dev-blue
    :target: https://discord.com/invite/pytest-dev
    :alt: Discord

.. image:: https://img.shields.io/badge/Libera%20chat-%23pytest-orange
    :target: https://web.libera.chat/#pytest
    :alt: Libera chat


The ``pytest`` framework makes it easy to write small tests, yet
scales to support complex functional testing for applications and libraries.

An example of a simple test:

.. code-block:: python

    # content of test_sample.py
    def inc(x):
        return x + 1


    def test_answer():
        assert inc(3) == 5


To execute it::

    $ pytest
    ============================= test session starts =============================
    collected 1 items

    test_sample.py F

    ================================== FAILURES ===================================
    _________________________________ test_answer _________________________________

        def test_answer():
    >       assert inc(3) == 5
    E       assert 4 == 5
    E        +  where 4 = inc(3)

    test_sample.py:5: AssertionError
    ========================== 1 failed in 0.04 seconds ===========================


Thanks to ``pytest``'s detailed assertion introspection, you can simply use plain ``assert`` statements. See `getting-started <https://docs.pytest.org/en/stable/getting-started.html#our-first-test-run>`_ for more examples.


Features
--------

- Detailed info on failing `assert statements <https://docs.pytest.org/en/stable/how-to/assert.html>`_ (no need to remember ``self.assert*`` names)

- `Auto-discovery
  <https://docs.pytest.org/en/stable/explanation/goodpractices.html#python-test-discovery>`_
  of test modules and functions

- `Modular fixtures <https://docs.pytest.org/en/stable/explanation/fixtures.html>`_ for
  managing small or parametrized long-lived test resources

- Can run `unittest <https://docs.pytest.org/en/stable/how-to/unittest.html>`_ (or trial)
  test suites out of the box

- Python 3.10+ or PyPy3

- Rich plugin architecture, with over 1300+ `external plugins <https://docs.pytest.org/en/latest/reference/plugin_list.html>`_ and thriving community


Documentation
-------------

For full documentation, including installation, tutorials and PDF documents, please see https://docs.pytest.org/en/stable/.


Bugs/Requests
-------------

Please use the `GitHub issue tracker <https://github.com/pytest-dev/pytest/issues>`_ to submit bugs or request features.


Changelog
---------

Consult the `Changelog <https://docs.pytest.org/en/stable/changelog.html>`__ page for fixes and enhancements of each version.


Support pytest
--------------

`Open Collective`_ is an online funding platform for open and transparent communities.
It provides tools to raise money and share your finances in full transparency.

It is the platform of choice for individuals and companies that want to make one-time or
monthly donations directly to the project.

See more details in the `pytest collective`_.

.. _Open Collective: https://opencollective.com
.. _pytest collective: https://opencollective.com/pytest


pytest for enterprise
---------------------

Available as part of the Tidelift Subscription.

The maintainers of pytest and thousands of other packages are working with Tidelift to deliver commercial support and
maintenance for the open source dependencies you use to build your applications.
Save time, reduce risk, and improve code health, while paying the maintainers of the exact dependencies you use.

`Learn more. <https://tidelift.com/subscription/pkg/pypi-pytest?utm_source=pypi-pytest&utm_medium=referral&utm_campaign=enterprise&utm_term=repo>`_

Security
^^^^^^^^

If you have found an issue that you believe is a security vulnerability, please do not create an issue -- instead, report it via a `new security advisory <https://github.com/pytest-dev/pytest/security/advisories/new>`__.


License
-------

Copyright Holger Krekel and others, 2004.

Distributed under the terms of the `MIT`_ license, pytest is free and open source software.

.. _`MIT`: https://github.com/pytest-dev/pytest/blob/main/LICENSE

```

---

## `doc/en/contributing.rst`

Role: **rules**. rule source or redirect | DUPLICATE RISK: source of a rendered doc page, do not extract twice

```rst
.. _contributing:

.. include:: ../../CONTRIBUTING.rst

```

---

## `pyproject.toml`

Role: **context**. may hold lint config

```toml
[build-system]
build-backend = "setuptools.build_meta"
requires = [
    "setuptools>=77",
    "setuptools-scm[toml]>=6.2.3",
]

[project]
name = "pytest"
description = "pytest: simple powerful testing with Python"
readme = "README.rst"
keywords = [
    "test",
    "unittest",
]
license = "MIT"
license-files = [ "LICENSE" ]
authors = [
    { name = "Brianna Laugher" },
    { name = "Bruno Oliveira" },
    { name = "Floris Bruynooghe" },
    { name = "Freya Bruhin" },
    { name = "Holger Krekel" },
    { name = "Others (See AUTHORS)" },
    { name = "Ronny Pfannschmidt" },
]
requires-python = ">=3.10"
classifiers = [
    "Development Status :: 6 - Mature",
    "Intended Audience :: Developers",
    "Operating System :: MacOS",
    "Operating System :: Microsoft :: Windows",
    "Operating System :: POSIX",
    "Operating System :: Unix",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: 3.14",
    "Programming Language :: Python :: 3.15",
    "Topic :: Software Development :: Libraries",
    "Topic :: Software Development :: Testing",
    "Topic :: Utilities",
]
dynamic = [
    "version",
]
dependencies = [
    "colorama>=0.4; sys_platform=='win32'",
    "exceptiongroup>=1; python_version<'3.11'",
    "iniconfig>=2",
    "packaging>=24",
    "pluggy>=1.5,<2",
    "pygments>=2.15",
    "tomli>=2; python_version<'3.11'",
]
# Kept as a published extra because many external repos still install
# `pytest[dev]` / `.[dev]`. Prefer the `dev` dependency group for local
# development of pytest itself (see CONTRIBUTING.rst).
optional-dependencies.dev = [
    # Core test dependencies
    "argcomplete",
    "asynctest; python_version<'3.11'",
    "attrs>=23.1",
    # Test execution and coverage
    "coverage>=7.5",
    "hypothesis>=6.75",
    "mock",
    "numpy>=1.26",
    "pexpect>=4.9",
    "pytest-xdist>=3.5",
    # Additional test dependencies
    "pyyaml",
    "requests",
    "setuptools",
    "xmlschema",
]
urls.Changelog = "https://docs.pytest.org/en/stable/changelog.html"
urls.Contact = "https://docs.pytest.org/en/stable/contact.html"
urls.Funding = "https://docs.pytest.org/en/stable/sponsor.html"
urls.Homepage = "https://docs.pytest.org/en/latest/"
urls.Source = "https://github.com/pytest-dev/pytest"
urls.Tracker = "https://github.com/pytest-dev/pytest/issues"
scripts."py.test" = "_pytest.config:_console_main"
scripts.pytest = "_pytest.config:_console_main"

[dependency-groups]
# Preferred entry point for developing pytest; pulls from optional-dependencies.dev.
dev = [
    "pytest[dev]",
]

[tool.setuptools.package-data]
"_pytest" = [
    "py.typed",
]
"pytest" = [
    "py.typed",
]

[tool.setuptools_scm]
write_to = "src/_pytest/_version.py"

[tool.black]
# See https://black.readthedocs.io/en/stable/usage_and_configuration/the_basics.html#t-target-version
target-version = [ "py310", "py311", "py312", "py313" ]

[tool.ruff]
target-version = "py310"
line-length = 88
src = [
    "src",
]
format.docstring-code-format = true
lint.extend-select = [
    "B",      # bugbear
    "D",      # pydocstyle
    "E",      # pycodestyle
    "F",      # pyflakes
    "FA100",  # add future annotations
    "I",      # isort
    "PGH004", # pygrep-hooks - Use specific rule codes when using noqa
    "PIE",    # flake8-pie
    "PLC",    # pylint convention
    "PLE",    # pylint error
    "PLR",    # pylint refactor
    "PLW",    # pylint warning
    "PYI",    # flake8-pyi
    "RUF",    # ruff
    "T100",   # flake8-debugger
    "UP",     # pyupgrade
    "W",      # pycodestyle
]
lint.ignore = [
    # flake8-async ignore
    "ASYNC115", # Use `lowlevel.checkpoint()` instead of `sleep(0)`
    # bugbear ignore
    "B004", # Using `hasattr(x, "__call__")` to test if x is callable is unreliable.
    "B007", # Loop control variable `i` not used within loop body
    "B009", # Do not call `getattr` with a constant attribute value
    "B010", # [*] Do not call `setattr` with a constant attribute value.
    "B011", # Do not `assert False` (`python -O` removes these calls)
    "B028", # No explicit `stacklevel` keyword argument found
    # flake8-blind-except ignore
    "BLE001", # Do not catch blind exception
    # flake8-comprehensions ignore
    "C408", # Unnecessary `dict()`/`list()`/`tuple()` call (rewrite as a literal)
    # pydocstyle ignore
    "D100", # Missing docstring in public module
    "D101", # Missing docstring in public class
    "D102", # Missing docstring in public method
    "D103", # Missing docstring in public function
    "D104", # Missing docstring in public package
    "D105", # Missing docstring in magic method
    "D106", # Missing docstring in public nested class
    "D107", # Missing docstring in `__init__`
    "D205", # 1 blank line required between summary line and description
    "D209", # [*] Multi-line docstring closing quotes should be on a separate line
    "D400", # First line should end with a period
    "D401", # First line of docstring should be in imperative mood
    "D402", # First line should not be the function's signature
    "D404", # First word of the docstring should not be "This"
    "D415", # First line should end with a period, question mark, or exclamation point
    # flake8-datetimez ignore
    "DTZ001", # `datetime.datetime()` called without a `tzinfo` argument
    "DTZ005", # `datetime.datetime.now()` called without a `tz` argument
    # pytest can do weird low-level things, and we usually know
    # what we're doing when we use type(..) is ...
    "E721", # Do not compare types, use `isinstance()`
    # flynt ignore
    "FLY002", # Consider an f-string instead of string join
    # flake8-implicit-str-concat ignore
    "ISC004", # Unparenthesized implicit string concatenation in collection
    # flake8-logging ignore
    "LOG015", # Call on root logger
    # pylint ignore
    "PLC0105", # `TypeVar` name "E" does not reflect its covariance;
    "PLC0414", # Import alias does not rename original package
    "PLC0415", # import should be at top level of package
    "PLR0124", # Name compared with itself
    "PLR0133", # Two constants compared in a comparison (lots of those in tests)
    "PLR0402", # Use `from x.y import z` in lieu of alias
    "PLR0911", # Too many return statements
    "PLR0912", # Too many branches
    "PLR0913", # Too many arguments in function definition
    "PLR0915", # Too many statements
    "PLR0917", # Too many positional arguments
    "PLR2004", # Magic value used in comparison
    "PLR2044", # Line with empty comment
    "PLR5501", # Use `elif` instead of `else` then `if`
    "PLW0120", # remove the else and dedent its contents
    "PLW0603", # Using the global statement
    "PLW1641", # Does not implement the __hash__ method
    "PLW2901", # for loop variable overwritten by assignment target
    # flake8-pytest-style ignore
    "PT020", # `@pytest.yield_fixture` is deprecated, use `@pytest.fixture`
    "PT025", # `pytest.mark.usefixtures` has no effect on fixtures
    "PT031", # `pytest.warns()` block should contain a single simple statement
    # flake8-use-pathlib ignore
    "PTH124", # `py.path` is in maintenance mode, use `pathlib` instead
    # ruff ignore
    "RUF012", # Mutable class attributes should be annotated with `typing.ClassVar`
    "RUF061", # Use context-manager form of `pytest.raises()`
    # flake8-bandit ignore
    "S102", # Use of `exec` detected
    "S110", # `try`-`except`-`pass` detected, consider logging the exception
    # flake8-simplify ignore
    "SIM102", # Use a single `if` statement instead of nested `if` statements
    "SIM103", # Return the condition directly
    "SIM114", # Combine `if` branches using logical `or` operator
    "SIM115", # Use a context manager for opening files
    "SIM117", # Use a single `with` statement with multiple contexts instead of nested `with` statements
    "SIM201", # Use `!=` instead of `not ... == ...`
    "SIM211", # Use `not ...` instead of `False if ... else True`
    # tryceratops ignore
    "TRY002", # Create your own exception
    "TRY004", # Prefer `TypeError` exception for invalid type
]
lint.per-file-ignores."doc/**/*.py" = [
    "PLR0133", # Two constants compared in a comparison,
    "RUF059",  # Unpacked variable is never used
    "S102",    # Use of `exec` detected
    "TRY002",  # Create your own exception
]
lint.per-file-ignores."src/_pytest/_py/**/*.py" = [
    "B",
    "PYI",
]
lint.per-file-ignores."src/_pytest/_version.py" = [
    "I001",
]
lint.per-file-ignores."testing/**/*.py" = [
    "RUF060", # 'Unnecessary membership test on empty collection', always voluntary in tests
]
# can't be disabled on a line-by-line basis in file
lint.per-file-ignores."testing/code/test_source.py" = [
    "F841",
]
lint.per-file-ignores."testing/python/approx.py" = [
    "B015",
]
lint.extend-safe-fixes = [
    "UP006",
    "UP007",
]
lint.isort.combine-as-imports = true
lint.isort.force-single-line = true
lint.isort.force-sort-within-sections = true
lint.isort.known-local-folder = [
    "pytest",
    "_pytest",
]
lint.isort.lines-after-imports = 2
lint.isort.order-by-type = false
lint.isort.required-imports = [
    "from __future__ import annotations",
]
# In order to be able to format for 88 char in ruff format
lint.pycodestyle.max-line-length = 120
lint.pydocstyle.convention = "pep257"
lint.pyupgrade.keep-runtime-typing = false

[tool.pylint.main]
# Maximum number of characters on a single line.
max-line-length = 120
disable = [
    "abstract-method",
    "arguments-differ",
    "arguments-renamed",
    "assigning-non-slot",
    "attribute-defined-outside-init",
    "bad-builtin",
    "bad-classmethod-argument",
    "bad-dunder-name",
    "bad-mcs-method-argument",
    "broad-exception-caught",
    "broad-exception-raised",
    "cell-var-from-loop",                     # B023 from ruff / flake8-bugbear
    "comparison-of-constants",                # disabled in ruff (PLR0133)
    "comparison-with-callable",
    "comparison-with-itself",                 # PLR0124 from ruff
    "condition-evals-to-constant",
    "confusing-consecutive-elif",
    "consider-alternative-union-syntax",
    "consider-ternary-expression",
    "consider-using-assignment-expr",
    "consider-using-dict-items",
    "consider-using-from-import",             # not activated by default, PLR0402 disabled in ruff
    "consider-using-f-string",
    "consider-using-in",
    "consider-using-namedtuple-or-dataclass",
    "consider-using-ternary",
    "consider-using-tuple",
    "consider-using-with",
    "cyclic-import",
    "deprecated-argument",
    "deprecated-attribute",
    "deprecated-class",
    "differing-param-doc",
    "disallowed-name",                        # foo / bar are used often in tests
    "docstring-first-line-empty",
    "duplicate-code",
    "else-if-used",                           # not activated by default, PLR5501 disabled in ruff
    "empty-comment",                          # not activated by default, PLR2044 disabled in ruff
    "eq-without-hash",                        # PLW1641 disabled in ruff
    "eval-used",
    "exec-used",
    "expression-not-assigned",
    "fixme",
    "global-statement",                       # PLW0603 disabled in ruff
    "import-error",
    "import-outside-toplevel",                # PLC0415 disabled in ruff
    "import-private-name",
    "inconsistent-return-statements",
    "invalid-bool-returned",
    "invalid-name",
    "invalid-repr-returned",
    "invalid-str-returned",
    "keyword-arg-before-vararg",
    "line-too-long",
    "magic-value-comparison",                 # not activated by default, PLR2004 disabled in ruff
    "method-hidden",
    "misplaced-bare-raise",                   # PLE0704 from ruff
    "misplaced-comparison-constant",
    "missing-docstring",
    "missing-param-doc",
    "missing-raises-doc",
    "missing-timeout",
    "missing-type-doc",
    "multiple-statements",                    # multiple-statements-on-one-line-colon (E701) from ruff
    "no-else-break",
    "no-else-continue",
    "no-else-raise",
    "no-else-return",
    "no-member",
    "no-name-in-module",
    "no-self-argument",
    "no-self-use",
    "not-an-iterable",
    "not-callable",
    "pointless-exception-statement",          # https://github.com/pytest-dev/pytest/pull/12379
    "pointless-statement",                    # https://github.com/pytest-dev/pytest/pull/12379
    "pointless-string-statement",             # https://github.com/pytest-dev/pytest/pull/12379
    "possibly-used-before-assignment",
    "protected-access",
    "raise-missing-from",
    "redefined-argument-from-local",
    "redefined-builtin",
    "redefined-loop-name",                    # PLW2901 disabled in ruff
    "redefined-outer-name",
    "redefined-variable-type",
    "reimported",
    "simplifiable-condition",
    "simplifiable-if-expression",
    "singleton-comparison",
    "superfluous-parens",
    "super-init-not-called",
    "too-complex",
    "too-few-public-methods",
    "too-many-ancestors",
    "too-many-arguments",                     # disabled in ruff
    "too-many-branches",                      # disabled in ruff
    "too-many-function-args",
    "too-many-instance-attributes",
    "too-many-lines",
    "too-many-locals",
    "too-many-nested-blocks",
    "too-many-positional-arguments",
    "too-many-public-methods",
    "too-many-return-statements",             # disabled in ruff
    "too-many-statements",                    # disabled in ruff
    "too-many-try-statements",
    "try-except-raise",
    "typevar-name-incorrect-variance",        # PLC0105 disabled in ruff
    "unbalanced-tuple-unpacking",
    "undefined-loop-variable",
    "undefined-variable",
    "unexpected-keyword-arg",
    "unidiomatic-typecheck",
    "unnecessary-comprehension",
    "unnecessary-dunder-call",
    "unnecessary-lambda",
    "unnecessary-lambda-assignment",
    "unpacking-non-sequence",
    "unspecified-encoding",
    "unsubscriptable-object",
    "unused-argument",
    "unused-import",
    "unused-variable",
    "used-before-assignment",
    "use-dict-literal",
    "use-implicit-booleaness-not-comparison",
    "use-implicit-booleaness-not-len",
    "useless-else-on-loop",                   # PLC0414 disabled in ruff
    "useless-import-alias",
    "useless-return",
    "use-set-for-membership",
    "using-constant-test",
    "while-used",
    "wrong-import-order",                     # handled by isort / ruff
    "wrong-import-position",                  # handled by isort / ruff
]

[tool.codespell]
ignore-words-list = "afile,asend,asser,assertio,feld,hove,ned,noes,notin,paramete,parth,tesults,varius,wil"
skip = "AUTHORS,*/plugin_list.rst"
write-changes = true

[tool.check-wheel-contents]
# check-wheel-contents is executed by the build-and-inspect-python-package action.
# W009: Wheel contains multiple toplevel library entries
ignore = "W009"

[tool.pyproject-fmt]
indent = 4
max_supported_python = "3.15"

[tool.pytest]
minversion = "2.0"
addopts = [ "-rfEX", "-p", "pytester" ]
python_files = [
    "test_*.py",
    "*_test.py",
    "testing/python/*.py",
]
python_classes = [
    "Test",
    "Acceptance",
]
python_functions = [
    "test",
]
# NOTE: "doc" is not included here, but gets tested explicitly via "doctesting".
testpaths = [
    "testing",
]
norecursedirs = [
    "testing/example_scripts",
    "testing/plugins_integration",
    ".*",
    "build",
    "dist",
]
strict = true
filterwarnings = [
    'error',
    'default:Using or importing the ABCs:DeprecationWarning:unittest2.*',
    # produced by older pyparsing<=2.2.0.
    'default:Using or importing the ABCs:DeprecationWarning:pyparsing.*',
    'default:the imp module is deprecated in favour of importlib:DeprecationWarning:nose.*',
    # distutils is deprecated in 3.10, scheduled for removal in 3.12
    'ignore:The distutils package is deprecated:DeprecationWarning',
    # produced by pytest-xdist
    'ignore:.*type argument to addoption.*:DeprecationWarning',
    # produced on execnet (pytest-xdist)
    'ignore:.*inspect.getargspec.*deprecated, use inspect.signature.*:DeprecationWarning',
    # pytest's own futurewarnings
    'ignore::pytest.PytestExperimentalApiWarning',
    # Do not cause SyntaxError for invalid escape sequences in py37.
    # Those are caught/handled by pyupgrade, and not easy to filter with the
    # module being the filename (with .py removed).
    'default:invalid escape sequence:DeprecationWarning',
    # ignore not yet fixed warnings for hook markers
    'default:.*not marked using pytest.hook.*',
    'ignore:.*not marked using pytest.hook.*::xdist.*',
    # ignore use of unregistered marks, because we use many to test the implementation
    'ignore::_pytest.warning_types.PytestUnknownMarkWarning',
    # https://github.com/benjaminp/six/issues/341
    'ignore:_SixMetaPathImporter\.exec_module\(\) not found; falling back to load_module\(\):ImportWarning',
    # https://github.com/benjaminp/six/pull/352
    'ignore:_SixMetaPathImporter\.find_spec\(\) not found; falling back to find_module\(\):ImportWarning',
    # https://github.com/pypa/setuptools/pull/2517
    'ignore:VendorImporter\.find_spec\(\) not found; falling back to find_module\(\):ImportWarning',
    # https://github.com/pytest-dev/execnet/pull/127
    'ignore:isSet\(\) is deprecated, use is_set\(\) instead:DeprecationWarning',
    # https://github.com/pytest-dev/pytest/issues/2366
    # https://github.com/pytest-dev/pytest/pull/13057
    'default::pytest.PytestFDWarning',
    # https://github.com/pexpect/pexpect/issues/827
    # CPython emits this from os.forkpty() with stacklevel=1, so it is attributed
    # to stdlib pty (caller of os.forkpty via pty.fork), not ptyprocess. Match on
    # message only: module attribution must not be required if stacklevel changes.
    # Becomes a hard failure under filterwarnings=error only on 3.15+
    # (python/cpython#136796 stopped clearing the warning). Often seen on macOS
    # because Mach task_threads counts extra runtime threads.
    'ignore:.*use of forkpty\(\) may lead to deadlocks in the child:DeprecationWarning',
]
pytester_example_dir = "testing/example_scripts"
markers = [
    # dummy markers for testing
    "foo",
    "bar",
    "baz",
    "number_mark",
    "builtin_matchers_mark",
    "str_mark",
    # conftest.py reorders tests moving slow ones to the end of the list
    "slow",
    # experimental mark for all tests using pexpect
    "uses_pexpect",
    # Disables the `remove_ci_env_var` autouse fixture on a given test that
    # actually inspects whether the CI environment variable is set.
    "keep_ci_var",
]

[tool.coverage.paths]
source = [
    'src/',
    '*/lib/python*/site-packages/',
    '*/pypy*/site-packages/',
    '*\Lib\site-packages\',
]

[tool.coverage.report]
skip_covered = true
show_missing = true
exclude_lines = [
    '\#\s*pragma: no cover',
    '^\s*raise NotImplementedError\b',
    '^\s*return NotImplemented\b',
    '^\s*assert False(,|$)',
    '^\s*case unreachable:',
    '^\s*assert_never\(',
    '^\s*if TYPE_CHECKING:',
    '^\s*(el)?if TYPE_CHECKING:',
    '^\s*@overload( |$)',
    '^\s*def .+: \.\.\.$',
    '^\s*@pytest\.mark\.xfail',
]

[tool.coverage.run]
include = [
    'src/*',
    'testing/*',
    '*/lib/python*/site-packages/_pytest/*',
    '*/lib/python*/site-packages/pytest.py',
    '*/pypy*/site-packages/_pytest/*',
    '*/pypy*/site-packages/pytest.py',
    '*\Lib\site-packages\_pytest\*',
    '*\Lib\site-packages\pytest.py',
]
parallel = true
branch = true
patch = [ "subprocess" ]
# The sysmon core (default since Python 3.14) is much slower.
# Perhaps: https://github.com/coveragepy/coveragepy/issues/2082
core = "ctrace"

[tool.towncrier]
package = "pytest"
package_dir = "src"
filename = "doc/en/changelog.rst"
directory = "changelog/"
title_format = "pytest {version} ({project_date})"
template = "changelog/_template.rst"

# NOTE: The types are declared because:
# NOTE: - there is no mechanism to override just the value of
# NOTE:   `tool.towncrier.type.misc.showcontent`;
# NOTE: - and, we want to declare extra non-default types for
# NOTE:   clarity and flexibility.

[[tool.towncrier.type]]
# When something public gets removed in a breaking way. Could be
# deprecated in an earlier release.
directory = "breaking"
name = "Removals and backward incompatible breaking changes"
showcontent = true

[[tool.towncrier.type]]
# Declarations of future API removals and breaking changes in behavior.
directory = "deprecation"
name = "Deprecations (removal in next major release)"
showcontent = true

[[tool.towncrier.type]]
# New behaviors, public APIs. That sort of stuff.
directory = "feature"
name = "New features"
showcontent = true

[[tool.towncrier.type]]
# New behaviors in existing features.
directory = "improvement"
name = "Improvements in existing functionality"
showcontent = true

[[tool.towncrier.type]]
# Something we deemed an improper undesired behavior that got corrected
# in the release to match pre-agreed expectations.
directory = "bugfix"
name = "Bug fixes"
showcontent = true

[[tool.towncrier.type]]
# Updates regarding bundling dependencies.
directory = "vendor"
name = "Vendored libraries"
showcontent = true

[[tool.towncrier.type]]
# Notable updates to the documentation structure or build process.
directory = "doc"
name = "Improved documentation"
showcontent = true

[[tool.towncrier.type]]
# Notes for downstreams about unobvious side effects and tooling. Changes
# in the test invocation considerations and runtime assumptions.
directory = "packaging"
name = "Packaging updates and notes for downstreams"
showcontent = true

[[tool.towncrier.type]]
# Stuff that affects the contributor experience. e.g. Running tests,
# building the docs, setting up the development environment.
directory = "contrib"
name = "Contributor-facing changes"
showcontent = true

[[tool.towncrier.type]]
# Changes that are hard to assign to any of the above categories.
directory = "misc"
name = "Miscellaneous internal changes"
showcontent = true

[tool.mypy]
files = [
    "src",
    "testing",
    "scripts",
]
mypy_path = [
    "src",
]
python_version = "3.10"
check_untyped_defs = true
disallow_any_generics = true
disallow_untyped_defs = true
ignore_missing_imports = true
show_error_codes = true
strict_equality = true
warn_redundant_casts = true
warn_return_any = true
warn_unreachable = true
warn_unused_configs = true
no_implicit_reexport = true
warn_unused_ignores = true
enable_error_code = [ "deprecated" ]

[tool.pyright]
include = [
    "src",
    "testing",
    "scripts",
]
extraPaths = [
    "src",
]
pythonVersion = "3.10"
typeCheckingMode = "basic"
reportMissingImports = "none"
reportMissingModuleSource = "none"

```

---

## `tox.ini`

Role: **context**. may hold lint config

```ini
[tox]
requires =
    tox >= 4
    tox-uv >= 1.25
envlist =
    linting
    py310
    py311
    py312
    py313
    py314
    py315
    pypy3
    py310-{pexpect,xdist,twisted24,twisted25,asynctest,numpy,pluggymain,pylib}
    doctesting
    doctesting-coverage
    plugins
    py310-freeze
    docs
    docs-checklinks

    # checks that 3.11 native ExceptionGroup works with exceptiongroup
    # not included in CI.
    py311-exceptiongroup



[pkgenv]
# NOTE: This section tweaks how Tox manages the PEP 517 build
# NOTE: environment where it assembles wheels (editable and regular)
# NOTE: for further installing them into regular testenvs.
#
# NOTE: `[testenv:.pkg]` does not work due to a regression in tox v4.14.1
# NOTE: so `[pkgenv]` is being used in place of it.
# Refs:
# * https://github.com/tox-dev/tox/pull/3237
# * https://github.com/tox-dev/tox/issues/3238
# * https://github.com/tox-dev/tox/issues/3292
# * https://hynek.me/articles/turbo-charge-tox/
#
# NOTE: The `SETUPTOOLS_SCM_PRETEND_VERSION_FOR_PYTEST` environment
# NOTE: variable allows enforcing a pre-determined version for use in
# NOTE: the wheel being installed into usual testenvs.
pass_env =
  SETUPTOOLS_SCM_PRETEND_VERSION_FOR_PYTEST


[testenv]
description =
    run the tests
    coverage: collecting coverage
    exceptiongroup: against `exceptiongroup`
    nobyte: in no-bytecode mode
    lsof: with `--lsof` pytest CLI option
    numpy: against `numpy`
    pexpect: against `pexpect`
    pluggymain: against the bleeding edge `pluggy` from Git
    pylib: against `py` lib
    twisted24: against the unit test extras with twisted prior to 24.0
    twisted25: against the unit test extras with twisted 25.0 or later
    asynctest: against the unit test extras with asynctest
    xdist: with pytest in parallel mode
    under `{basepython}`
    doctesting: including doctests
commands =
    {env:_PYTEST_TOX_COVERAGE_RUN:} pytest {posargs:{env:_PYTEST_TOX_DEFAULT_POSARGS:}}
    doctesting: {env:_PYTEST_TOX_COVERAGE_RUN:} pytest --doctest-modules {env:_PYTEST_TOX_POSARGS_JUNIT:} --pyargs _pytest
    coverage: coverage combine
    coverage: coverage report -m
    # Run `coverage xml` only on CI.
    coverage: python -c 'import os; os.environ.get("CI") and os.execlp("coverage", "coverage", "xml")'
passenv =
    COVERAGE_*
    PYTEST_ADDOPTS
    TERM
    CI
setenv =
    _PYTEST_TOX_DEFAULT_POSARGS={env:_PYTEST_TOX_POSARGS_DOCTESTING:} {env:_PYTEST_TOX_POSARGS_JUNIT:} {env:_PYTEST_TOX_POSARGS_LSOF:} {env:_PYTEST_TOX_POSARGS_XDIST:} {env:_PYTEST_FILES:}

    # See https://docs.python.org/3/library/io.html#io-encoding-warning
    # If we don't enable this, neither can any of our downstream users!
    # pylib is not PYTHONWARNDEFAULTENCODING clean, so don't set for it.
    !pylib: PYTHONWARNDEFAULTENCODING=1

    # Configuration to run with coverage similar to CI, e.g.
    # "tox -e py313-coverage".
    coverage: _PYTEST_TOX_COVERAGE_RUN=coverage run -m

    doctesting: _PYTEST_TOX_POSARGS_DOCTESTING=doc/en

    # The configurations below are related only to standard unittest support.
    # Run only tests from test_unittest.py.
    asynctest: _PYTEST_FILES=testing/test_unittest.py
    twisted24: _PYTEST_FILES=testing/test_unittest.py
    twisted25: _PYTEST_FILES=testing/test_unittest.py

    nobyte: PYTHONDONTWRITEBYTECODE=1

    lsof: _PYTEST_TOX_POSARGS_LSOF=--lsof

    xdist: _PYTEST_TOX_POSARGS_XDIST=-n auto
dependency_groups = dev
deps =
    exceptiongroup: exceptiongroup>=1.2
    pluggymain: pluggy @ git+https://github.com/pytest-dev/pluggy.git
    pylib: py>=1.11
    twisted24: twisted<25
    twisted25: twisted>=25
# Can use the same wheel for all environments.
package = wheel
wheel_build_env = .pkg

[testenv:linting]
description =
    run pre-commit-defined linters under `{basepython}`
skip_install = True
dependency_groups =
deps = pre-commit>=4
commands = pre-commit run --all-files --show-diff-on-failure {posargs:}
setenv =
    # pre-commit and tools it launches are not clean of this warning.
    PYTHONWARNDEFAULTENCODING=

[testenv:docs]
description =
    build the documentation site under \
    `{toxinidir}{/}doc{/}en{/}_build{/}html` with `{basepython}`
basepython = python3.14 # Sync with .readthedocs.yaml to get errors.
usedevelop = True
dependency_groups =
deps =
    -r{toxinidir}/doc/en/requirements.txt
commands =
    sphinx-build \
      -j auto \
      -W --keep-going \
      -b html doc/en doc/en/_build/html \
      {posargs:}
setenv =
    # Sphinx is not clean of this warning.
    PYTHONWARNDEFAULTENCODING=

[testenv:docs-checklinks]
description =
    check the links in the documentation with `{basepython}`
usedevelop = True
changedir = doc/en
dependency_groups =
deps = -r{toxinidir}/doc/en/requirements.txt
commands =
    sphinx-build -W -q --keep-going -b linkcheck . _build
setenv =
    # Sphinx is not clean of this warning.
    PYTHONWARNDEFAULTENCODING=

[testenv:regen]
description =
    regenerate documentation examples under `{basepython}`
changedir = doc/en
dependency_groups =
deps =
    PyYAML
    regendoc>=0.8.1
    sphinx
allowlist_externals =
    make
commands =
    make regen
setenv =
    # We don't want this warning to reach regen output.
    PYTHONWARNDEFAULTENCODING=
    # Remove CI markers: pytest auto-detects those and uses more verbose output, which is undesirable
    # for the example documentation.
    CI=
    BUILD_NUMBER=

[testenv:plugins]
description =
    run reverse dependency testing against pytest plugins under `{basepython}`
# use latest versions of all plugins, including pre-releases
pip_pre=true
changedir = testing/plugins_integration
dependency_groups =
deps = -rtesting/plugins_integration/requirements.txt
allowlist_externals = uv
setenv =
    PYTHONPATH=.
commands =
    uv pip check
    pytest bdd_wallet.py
    pytest --cov=. simple_integration.py
    pytest --ds=django_settings simple_integration.py
    pytest --html=simple.html simple_integration.py
    pytest --reruns 5 simple_integration.py pytest_rerunfailures_integration.py
    pytest pytest_anyio_integration.py
    pytest pytest_asyncio_integration.py
    pytest pytest_mock_integration.py
    pytest pytest_trio_integration.py
    pytest pytest_twisted_integration.py
    pytest simple_integration.py --force-sugar --flakes

[testenv:py310-freeze]
description =
    test pytest frozen with `pyinstaller` under `{basepython}`
changedir = testing/freeze
dependency_groups =
deps =
    pyinstaller
commands =
    {envpython} create_executable.py
    {envpython} tox_run.py

[testenv:release]
description = do a release, required posarg of the version number
usedevelop = True
passenv = *
dependency_groups =
deps =
    colorama
    pre-commit>=2.9.3
    towncrier
commands = python scripts/release.py {posargs}

[testenv:prepare-release-pr]
description = prepare a release PR from a manual trigger in GitHub actions
usedevelop = {[testenv:release]usedevelop}
passenv = {[testenv:release]passenv}
dependency_groups = {[testenv:release]dependency_groups}
deps = {[testenv:release]deps}
commands = python scripts/prepare-release-pr.py {posargs}

[testenv:generate-gh-release-notes]
description = generate release notes that can be published as GitHub Release
usedevelop = True
dependency_groups =
deps =
    pypandoc_binary
commands = python scripts/generate-gh-release-notes.py {posargs}

[testenv:update-plugin-list]
description = update the plugin list
skip_install = True
dependency_groups =
deps =
    packaging
    requests
    tabulate[widechars]
    tqdm
    requests-cache
    platformdirs
commands = python scripts/update-plugin-list.py {posargs}

```
