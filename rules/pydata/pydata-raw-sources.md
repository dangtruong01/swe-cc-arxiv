# pydata/xarray: off-nav rule sources (raw, verbatim)

Repo: `pydata/xarray` @ `main`
Docs: https://docs.xarray.dev/en/latest/
Docs version at pull time: **UNRESOLVED**

Any doc page served on a different version is a fetch failure, not a row.

Raw source, HTML comments intact. The rendered GitHub view strips comments,
and in template files the comments carry the actual obligations. Extract from
this text, not from a rendered page.

Role `context` means the file informs Section context and Auto-fix but never
produces sheet rows.

| Path | Role | Status | Note |
|---|---|---|---|
| `.github/ISSUE_TEMPLATE/bugreport.yml` | rules | ok | expect X-ISSUE |
| `.github/ISSUE_TEMPLATE/config.yml` | rules | ok | expect X-ISSUE |
| `.github/ISSUE_TEMPLATE/misc.yml` | rules | ok | expect X-ISSUE |
| `.github/ISSUE_TEMPLATE/newfeature.yml` | rules | ok | expect X-ISSUE |
| `.github/PULL_REQUEST_TEMPLATE.md` | rules | ok | obligations hide in HTML comments |
| `.pre-commit-config.yaml` | context | ok | decides the Auto-fix column |
| `CODE_OF_CONDUCT.md` | rules | ok | expect X-GOV |
| `CONTRIBUTING.md` | rules | ok | rule source or redirect |
| `README.md` | context | ok | check for canonical test invocation |
| `doc/contribute/contributing.rst` | rules | ok | rule source or redirect | DUPLICATE RISK: source of a rendered doc page, do not extract twice |
| `pyproject.toml` | context | ok | may hold lint config |
| `CLAUDE.md` | rules | ok | ADDED IN THE v1 APPEND: agent-instruction file at the repo root, outside the docs nav and unmatched by `seed_sources.py` PATTERNS |
| `xarray/tests/CLAUDE.md` | rules | ok | ADDED IN THE v1 APPEND: per-directory agent-instruction file governing test style, outside the docs nav |

---

## `.github/ISSUE_TEMPLATE/bugreport.yml`

Role: **rules**. expect X-ISSUE

```yaml
name: 🐛 Bug Report
description: File a bug report to help us improve
labels: [bug, "needs triage"]
body:
  - type: textarea
    id: what-happened
    attributes:
      label: What happened?
      description: |
        Thanks for reporting a bug! Please describe what you were trying to get done.
        Tell us what happened, what went wrong.
    validations:
      required: true

  - type: textarea
    id: what-did-you-expect-to-happen
    attributes:
      label: What did you expect to happen?
      description: |
        Describe what you expected to happen.
    validations:
      required: false

  - type: textarea
    id: sample-code
    attributes:
      label: Minimal Complete Verifiable Example
      description: |
        Minimal, self-contained copy-pastable example that demonstrates the issue.

        Consider listing additional or specific dependencies in [inline script metadata](https://packaging.python.org/en/latest/specifications/inline-script-metadata/#example)
        so that calling `uv run issue.py` shows the issue when copied into `issue.py`. (not strictly required)

        This will be automatically formatted into code, so no need for markdown backticks.
      render: Python
      value: |
        # /// script
        # requires-python = ">=3.11"
        # dependencies = [
        #   "xarray[complete]@git+https://github.com/pydata/xarray.git@main",
        # ]
        # ///
        #
        # This script automatically imports the development branch of xarray to check for issues.
        # Please delete this header if you have _not_ tested this script with `uv run`!

        import xarray as xr
        xr.show_versions()
        # your reproducer code ...

  - type: textarea
    id: reproduce
    attributes:
      label: Steps to reproduce
      description:
    validations:
      required: false

  - type: checkboxes
    id: mvce-checkboxes
    attributes:
      label: MVCE confirmation
      description: |
        Please confirm that the bug report is in an excellent state, so we can understand & fix it quickly & efficiently. For more details, check out:

        - [Minimal Complete Verifiable Examples](https://stackoverflow.com/help/mcve)
        - [Craft Minimal Bug Reports](https://matthewrocklin.com/minimal-bug-reports)

      options:
        - label: Minimal example — the example is as focused as reasonably possible to demonstrate the underlying issue in xarray.
        - label: Complete example — the example is self-contained, including all data and the text of any traceback.
        - label: Verifiable example — the example copy & pastes into an IPython prompt or [Binder notebook](https://mybinder.org/v2/gh/pydata/xarray/main?urlpath=lab/tree/doc/examples/blank_template.ipynb), returning the result.
        - label: New issue — a search of GitHub Issues suggests this is not a duplicate.
        - label: Recent environment — the issue occurs with the latest version of xarray and its dependencies.

  - type: textarea
    id: log-output
    attributes:
      label: Relevant log output
      description: Please copy and paste any relevant output. This will be automatically formatted into code, so no need for markdown backticks.
      render: Python

  - type: textarea
    id: extra
    attributes:
      label: Anything else we need to know?
      description: |
        Please describe any other information you want to share.

  - type: textarea
    id: show-versions
    attributes:
      label: Environment
      description: |
        Paste the output of `xr.show_versions()` between the `<details>` tags, leaving an empty line following the opening tag.
      value: |
        <details>



        </details>
    validations:
      required: true

```

---

## `.github/ISSUE_TEMPLATE/config.yml`

Role: **rules**. expect X-ISSUE

```yaml
blank_issues_enabled: false
contact_links:
  - name: ❓ Usage question
    url: https://github.com/pydata/xarray/discussions
    about: |
      Ask questions and discuss with other community members here.
      If you have a question like "How do I concatenate a list of datasets?" then
      please include a self-contained reproducible example if possible.
  - name: 🗺️ Raster analysis usage question
    url: https://github.com/corteva/rioxarray/discussions
    about: |
      If you are using the rioxarray extension (engine='rasterio'), or have questions about
      raster analysis such as geospatial formats, coordinate reprojection, etc.,
      please use the rioxarray discussion forum.

```

---

## `.github/ISSUE_TEMPLATE/misc.yml`

Role: **rules**. expect X-ISSUE

```yaml
name: 📝 Issue
description: General issue, that's not a bug report.
labels: ["needs triage"]
body:
  - type: markdown
    attributes:
      value: |
        Please describe your issue here.
  - type: textarea
    id: issue-description
    attributes:
      label: What is your issue?
      description: |
        Thank you for filing an issue! Please give us further information on how we can help you.
      placeholder: Please describe your issue.
    validations:
      required: true

```

---

## `.github/ISSUE_TEMPLATE/newfeature.yml`

Role: **rules**. expect X-ISSUE

```yaml
name: 💡 Feature Request
description: Suggest an idea for xarray
labels: [enhancement]
body:
  - type: textarea
    id: description
    attributes:
      label: Is your feature request related to a problem?
      description: |
        Please do a quick search of existing issues to make sure that this has not been asked before.
        Please provide a clear and concise description of what the problem is. Ex. I'm always frustrated when [...]
    validations:
      required: true
  - type: textarea
    id: solution
    attributes:
      label: Describe the solution you'd like
      description: |
        A clear and concise description of what you want to happen.
  - type: textarea
    id: alternatives
    attributes:
      label: Describe alternatives you've considered
      description: |
        A clear and concise description of any alternative solutions or features you've considered.
    validations:
      required: false
  - type: textarea
    id: additional-context
    attributes:
      label: Additional context
      description: |
        Add any other context about the feature request here.
    validations:
      required: false

```

---

## `.github/PULL_REQUEST_TEMPLATE.md`

Role: **rules**. obligations hide in HTML comments

```markdown
### Description

### Checklist

<!-- Feel free to remove check-list items aren't relevant to your change -->

- [ ] Closes #xxxx
- [ ] Tests added
- [ ] User visible changes (including notable bug fixes) are documented in `whats-new.rst`
- [ ] New functions/methods are listed in `api.rst`

### AI Disclosure

<!--- Please review our AI & contribution guidelines: https://docs.xarray.dev/en/stable/contribute/ai-policy.html. Remove this section if your PR does not contain AI-generated content. --->

- [ ] This PR contains AI-generated content.
  - [ ] I have tested any AI-generated content in my PR.
  - [ ] I take responsibility for any AI-generated content in my PR.
    <!--- If you used AI to generate code, please specify the tool used and the prompt below. --->
    Tools: {e.g., Claude, Codex, GitHub Copilot, ChatGPT, etc.}

```

---

## `.pre-commit-config.yaml`

Role: **context**. decides the Auto-fix column

```yaml
# https://pre-commit.com/
ci:
  autoupdate_schedule: monthly
  autoupdate_commit_msg: "Update pre-commit hooks"
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: debug-statements
      - id: mixed-line-ending
  - repo: https://github.com/pre-commit/pygrep-hooks
    rev: v1.10.0
    hooks:
      # - id: python-check-blanket-noqa  # checked by ruff
      # - id: python-check-blanket-type-ignore  # checked by ruff
      # - id: python-check-mock-methods  # checked by ruff
      - id: python-no-log-warn
      # - id: python-use-type-annotations  # too many false positives
      - id: rst-backticks
      - id: rst-directive-colons
      - id: rst-inline-touching-normal
      - id: text-unicode-replacement-char
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.20
    hooks:
      - id: ruff-check
        args: ["--fix", "--show-fixes"]
      - id: ruff-format
  - repo: https://github.com/keewis/blackdoc
    rev: v0.4.6
    hooks:
      - id: blackdoc
        exclude: "generate_aggregations.py"
        # make sure this is the most recent version of black
        additional_dependencies: ["black==25.11.0"]
  - repo: https://github.com/rbubley/mirrors-prettier
    rev: v3.9.4
    hooks:
      - id: prettier
        args: ["--cache-location=.prettier_cache/cache"]
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v2.1.0
    hooks:
      - id: mypy
        # Copied from setup.cfg
        exclude: "properties|asv_bench"
        # This is slow and so we take it out of the fast-path; requires passing
        # `--hook-stage manual` to pre-commit
        stages: [manual]
        additional_dependencies: [
            # Type stubs
            types-python-dateutil,
            types-setuptools,
            types-PyYAML,
            types-pytz,
            typing-extensions>=4.1.0,
            numpy,
          ]
  - repo: https://github.com/citation-file-format/cff-converter-python
    rev: 5295f87c0e261da61a7b919fc754e3a77edd98a7
    hooks:
      - id: validate-cff
  - repo: https://github.com/ComPWA/taplo-pre-commit
    rev: v0.9.3
    hooks:
      - id: taplo-format
        args: ["--option", "array_auto_collapse=false"]
      - id: taplo-lint
        args: ["--no-schema"]
  - repo: https://github.com/abravalheri/validate-pyproject
    rev: v0.25
    hooks:
      - id: validate-pyproject
        additional_dependencies: ["validate-pyproject-schema-store[all]"]
  - repo: https://github.com/adhtruong/mirrors-typos
    rev: v1.48.0
    hooks:
      - id: typos
  - repo: https://github.com/zizmorcore/zizmor-pre-commit
    rev: v1.26.1
    hooks:
      - id: zizmor
        args: ["--offline"]

```

---

## `CODE_OF_CONDUCT.md`

Role: **rules**. expect X-GOV

```markdown
# NUMFOCUS CODE OF CONDUCT

You can find the full Code of Conduct on the NumFOCUS website: https://numfocus.org/code-of-conduct

## THE SHORT VERSION

NumFOCUS is dedicated to providing a harassment-free community for everyone, regardless of gender, sexual orientation, gender identity and expression, disability, physical appearance, body size, race, or religion. We do not tolerate harassment of community members in any form.

Be kind to others. Do not insult or put down others. Behave professionally. Remember that harassment and sexist, racist, or exclusionary jokes are not appropriate for NumFOCUS.

All communication should be appropriate for a professional audience including people of many different backgrounds. Sexual language and imagery is not appropriate.

Thank you for helping make this a welcoming, friendly community for all.

## HOW TO REPORT

If you feel that the Code of Conduct has been violated, feel free to submit a report, by using the form: [NumFOCUS Code of Conduct Reporting Form](https://numfocus.typeform.com/to/ynjGdT?typeform-source=numfocus.org)

## WHO WILL RECEIVE YOUR REPORT

Your report will be received and handled by NumFOCUS Code of Conduct Working Group; trained, and experienced contributors with diverse backgrounds. The group is making decisions independently from the project, PyData, NumFOCUS or any other organization.

You can learn more about the current group members, as well as the reporting procedure here: https://numfocus.org/code-of-conduct

```

---

## `CONTRIBUTING.md`

Role: **rules**. rule source or redirect

```markdown
Xarray's contributor guidelines [can be found in our online documentation](https://docs.xarray.dev/en/stable/contribute/contributing.html)

```

---

## `README.md`

Role: **context**. check for canonical test invocation

```markdown
# xarray: N-D labeled arrays and datasets

[![Xarray](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydata/xarray/refs/heads/main/doc/badge.json)](https://xarray.dev)
[![Powered by Pixi](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/prefix-dev/pixi/main/assets/badge/v0.json)](https://pixi.sh)
[![CI](https://github.com/pydata/xarray/actions/workflows/ci.yaml/badge.svg?branch=main)](https://github.com/pydata/xarray/actions/workflows/ci.yaml?query=branch%3Amain)
[![Code coverage](https://codecov.io/gh/pydata/xarray/branch/main/graph/badge.svg?flag=unittests)](https://codecov.io/gh/pydata/xarray)
[![Docs](https://readthedocs.org/projects/xray/badge/?version=latest)](https://docs.xarray.dev/)
[![Benchmarked with asv](https://img.shields.io/badge/benchmarked%20by-asv-green.svg?style=flat)](https://asv-runner.github.io/asv-collection/xarray/)
[![Formatted with black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![Available on pypi](https://img.shields.io/pypi/v/xarray.svg)](https://pypi.python.org/pypi/xarray/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/xarray)](https://pypistats.org/packages/xarray)
[![Conda - Downloads](https://img.shields.io/conda/dn/anaconda/xarray?label=conda%7Cdownloads)](https://anaconda.org/anaconda/xarray)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.598201.svg)](https://doi.org/10.5281/zenodo.598201)
[![Examples on binder](https://img.shields.io/badge/launch-binder-579ACA.svg?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFkAAABZCAMAAABi1XidAAAB8lBMVEX///9XmsrmZYH1olJXmsr1olJXmsrmZYH1olJXmsr1olJXmsrmZYH1olL1olJXmsr1olJXmsrmZYH1olL1olJXmsrmZYH1olJXmsr1olL1olJXmsrmZYH1olL1olJXmsrmZYH1olL1olL0nFf1olJXmsrmZYH1olJXmsq8dZb1olJXmsrmZYH1olJXmspXmspXmsr1olL1olJXmsrmZYH1olJXmsr1olL1olJXmsrmZYH1olL1olLeaIVXmsrmZYH1olL1olL1olJXmsrmZYH1olLna31Xmsr1olJXmsr1olJXmsrmZYH1olLqoVr1olJXmsr1olJXmsrmZYH1olL1olKkfaPobXvviGabgadXmsqThKuofKHmZ4Dobnr1olJXmsr1olJXmspXmsr1olJXmsrfZ4TuhWn1olL1olJXmsqBi7X1olJXmspZmslbmMhbmsdemsVfl8ZgmsNim8Jpk8F0m7R4m7F5nLB6jbh7jbiDirOEibOGnKaMhq+PnaCVg6qWg6qegKaff6WhnpKofKGtnomxeZy3noG6dZi+n3vCcpPDcpPGn3bLb4/Mb47UbIrVa4rYoGjdaIbeaIXhoWHmZYHobXvpcHjqdHXreHLroVrsfG/uhGnuh2bwj2Hxk17yl1vzmljzm1j0nlX1olL3AJXWAAAAbXRSTlMAEBAQHx8gICAuLjAwMDw9PUBAQEpQUFBXV1hgYGBkcHBwcXl8gICAgoiIkJCQlJicnJ2goKCmqK+wsLC4usDAwMjP0NDQ1NbW3Nzg4ODi5+3v8PDw8/T09PX29vb39/f5+fr7+/z8/Pz9/v7+zczCxgAABC5JREFUeAHN1ul3k0UUBvCb1CTVpmpaitAGSLSpSuKCLWpbTKNJFGlcSMAFF63iUmRccNG6gLbuxkXU66JAUef/9LSpmXnyLr3T5AO/rzl5zj137p136BISy44fKJXuGN/d19PUfYeO67Znqtf2KH33Id1psXoFdW30sPZ1sMvs2D060AHqws4FHeJojLZqnw53cmfvg+XR8mC0OEjuxrXEkX5ydeVJLVIlV0e10PXk5k7dYeHu7Cj1j+49uKg7uLU61tGLw1lq27ugQYlclHC4bgv7VQ+TAyj5Zc/UjsPvs1sd5cWryWObtvWT2EPa4rtnWW3JkpjggEpbOsPr7F7EyNewtpBIslA7p43HCsnwooXTEc3UmPmCNn5lrqTJxy6nRmcavGZVt/3Da2pD5NHvsOHJCrdc1G2r3DITpU7yic7w/7Rxnjc0kt5GC4djiv2Sz3Fb2iEZg41/ddsFDoyuYrIkmFehz0HR2thPgQqMyQYb2OtB0WxsZ3BeG3+wpRb1vzl2UYBog8FfGhttFKjtAclnZYrRo9ryG9uG/FZQU4AEg8ZE9LjGMzTmqKXPLnlWVnIlQQTvxJf8ip7VgjZjyVPrjw1te5otM7RmP7xm+sK2Gv9I8Gi++BRbEkR9EBw8zRUcKxwp73xkaLiqQb+kGduJTNHG72zcW9LoJgqQxpP3/Tj//c3yB0tqzaml05/+orHLksVO+95kX7/7qgJvnjlrfr2Ggsyx0eoy9uPzN5SPd86aXggOsEKW2Prz7du3VID3/tzs/sSRs2w7ovVHKtjrX2pd7ZMlTxAYfBAL9jiDwfLkq55Tm7ifhMlTGPyCAs7RFRhn47JnlcB9RM5T97ASuZXIcVNuUDIndpDbdsfrqsOppeXl5Y+XVKdjFCTh+zGaVuj0d9zy05PPK3QzBamxdwtTCrzyg/2Rvf2EstUjordGwa/kx9mSJLr8mLLtCW8HHGJc2R5hS219IiF6PnTusOqcMl57gm0Z8kanKMAQg0qSyuZfn7zItsbGyO9QlnxY0eCuD1XL2ys/MsrQhltE7Ug0uFOzufJFE2PxBo/YAx8XPPdDwWN0MrDRYIZF0mSMKCNHgaIVFoBbNoLJ7tEQDKxGF0kcLQimojCZopv0OkNOyWCCg9XMVAi7ARJzQdM2QUh0gmBozjc3Skg6dSBRqDGYSUOu66Zg+I2fNZs/M3/f/Grl/XnyF1Gw3VKCez0PN5IUfFLqvgUN4C0qNqYs5YhPL+aVZYDE4IpUk57oSFnJm4FyCqqOE0jhY2SMyLFoo56zyo6becOS5UVDdj7Vih0zp+tcMhwRpBeLyqtIjlJKAIZSbI8SGSF3k0pA3mR5tHuwPFoa7N7reoq2bqCsAk1HqCu5uvI1n6JuRXI+S1Mco54YmYTwcn6Aeic+kssXi8XpXC4V3t7/ADuTNKaQJdScAAAAAElFTkSuQmCC)](https://mybinder.org/v2/gh/pydata/xarray/main?urlpath=lab/tree/doc/examples/weather-data.ipynb)
[![Twitter](https://img.shields.io/twitter/follow/xarray_dev?style=social)](https://x.com/xarray_dev)

**xarray** (pronounced "ex-array", formerly known as **xray**) is an open source project and Python
package that makes working with labelled multi-dimensional arrays
simple, efficient, and fun!

Xarray introduces labels in the form of dimensions, coordinates and
attributes on top of raw [NumPy](https://www.numpy.org)-like arrays,
which allows for a more intuitive, more concise, and less error-prone
developer experience. The package includes a large and growing library
of domain-agnostic functions for advanced analytics and visualization
with these data structures.

Xarray was inspired by and borrows heavily from
[pandas](https://pandas.pydata.org), the popular data analysis package
focused on labelled tabular data. It is particularly tailored to working
with [netCDF](https://www.unidata.ucar.edu/software/netcdf) files, which
were the source of xarray\'s data model, and integrates tightly with
[dask](https://dask.org) for parallel computing.

## Why xarray?

Multi-dimensional (a.k.a. N-dimensional, ND) arrays (sometimes called
"tensors") are an essential part of computational science. They are
encountered in a wide range of fields, including physics, astronomy,
geoscience, bioinformatics, engineering, finance, and deep learning. In
Python, [NumPy](https://www.numpy.org) provides the fundamental data
structure and API for working with raw ND arrays. However, real-world
datasets are usually more than just raw numbers; they have labels which
encode information about how the array values map to locations in space,
time, etc.

Xarray doesn\'t just keep track of labels on arrays \-- it uses them to
provide a powerful and concise interface. For example:

- Apply operations over dimensions by name: `x.sum('time')`.
- Select values by label instead of integer location:
  `x.loc['2014-01-01']` or `x.sel(time='2014-01-01')`.
- Mathematical operations (e.g., `x - y`) vectorize across multiple
  dimensions (array broadcasting) based on dimension names, not shape.
- Flexible split-apply-combine operations with groupby:
  `x.groupby('time.dayofyear').mean()`.
- Database like alignment based on coordinate labels that smoothly
  handles missing values: `x, y = xr.align(x, y, join='outer')`.
- Keep track of arbitrary metadata in the form of a Python dictionary:
  `x.attrs`.

## Documentation

Learn more about xarray in its official documentation at
<https://docs.xarray.dev/>.

Try out an [interactive Jupyter
notebook](https://mybinder.org/v2/gh/pydata/xarray/main?urlpath=lab/tree/doc/examples/weather-data.ipynb).

## Contributing

You can find information about contributing to xarray at our
[Contributing
page](https://docs.xarray.dev/en/stable/contributing.html).

## Get in touch

- Ask usage questions ("How do I?") on
  [GitHub Discussions](https://github.com/pydata/xarray/discussions).
- Report bugs, suggest features or view the source code [on
  GitHub](https://github.com/pydata/xarray).
- For less well defined questions or ideas, or to announce other
  projects of interest to xarray users, use the [mailing
  list](https://groups.google.com/forum/#!forum/xarray).

## NumFOCUS

<img src="https://numfocus.org/wp-content/uploads/2017/07/NumFocus_LRG.png" width="200" href="https://numfocus.org/">

Xarray is a fiscally sponsored project of
[NumFOCUS](https://numfocus.org), a nonprofit dedicated to supporting
the open source scientific computing community. If you like Xarray and
want to support our mission, please consider making a
[donation](https://numfocus.org/donate-to-xarray) to support
our efforts.

## History

Xarray is an evolution of an internal tool developed at [The Climate
Corporation](https://climate.com/). It was originally written by Climate
Corp researchers Stephan Hoyer, Alex Kleeman and Eugene Brevdo and was
released as open source in May 2014. The project was renamed from
"xray" in January 2016. Xarray became a fiscally sponsored project of
[NumFOCUS](https://numfocus.org) in August 2018.

## Contributors

Thanks to our many contributors!

[![Contributors](https://contrib.rocks/image?repo=pydata/xarray)](https://github.com/pydata/xarray/graphs/contributors)

## License

Copyright 2014-2024, xarray Developers

Licensed under the Apache License, Version 2.0 (the "License"); you
may not use this file except in compliance with the License. You may
obtain a copy of the License at

<https://www.apache.org/licenses/LICENSE-2.0>

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Xarray bundles portions of pandas, NumPy and Seaborn, all of which are
available under a "3-clause BSD" license:

- pandas: `setup.py`, `xarray/util/print_versions.py`
- NumPy: `xarray/compat/npcompat.py`
- Seaborn: `_determine_cmap_params` in `xarray/plot/utils.py`

Xarray also bundles portions of CPython, which is available under the
"Python Software Foundation License" in `xarray/namedarray/pycompat.py`.

Xarray uses icons from the icomoon package (free version), which is
available under the "CC BY 4.0" license.

The full text of these licenses are included in the licenses directory.

```

---

## `doc/contribute/contributing.rst`

Role: **rules**. rule source or redirect | DUPLICATE RISK: source of a rendered doc page, do not extract twice

```rst
.. _contributing:

**********************
Contributing to xarray
**********************

.. note::

  Large parts of this document came from the `Pandas Contributing
  Guide <https://pandas.pydata.org/pandas-docs/stable/development/contributing.html>`_.

Overview
========

We welcome your skills and enthusiasm at the xarray project!. There are numerous opportunities to
contribute beyond just writing code.
All contributions, including bug reports, bug fixes, documentation improvements, enhancement suggestions,
and other ideas are welcome. LLM generated contributions are welcome, but they must follow :doc:`our AI policy <ai-policy>`.

If you have any questions on the process or how to fix something feel free to ask us!
The recommended places to ask questions are `GitHub Discussions <https://github.com/pydata/xarray/discussions>`_
or the Xarray channel in the `OSSci Zulip <https://ossci.zulipchat.com/#narrow/channel/582428-Xarray>`_.

In the past, we had a `Discord <https://discord.com/invite/wEKPCt4PDu>`_ and a
`mailing list <https://groups.google.com/g/xarray>`_. Feel free to browse historical conversations there.

We also have a biweekly community call, details of which are announced on the
`Developers meeting <https://docs.xarray.dev/en/stable/developers-meeting.html>`_.
You are very welcome to join! Though we would love to hear from you, there is no expectation to
contribute during the meeting either - you are always welcome to just sit in and listen.

This project is a community effort, and everyone is welcome to contribute. Everyone within the community
is expected to abide by our `code of conduct <https://github.com/pydata/xarray/blob/main/CODE_OF_CONDUCT.md>`_.

Where to start?
===============

If you are brand new to *xarray* or open-source development, we recommend going
through the `GitHub "issues" tab <https://github.com/pydata/xarray/issues>`_
to find issues that interest you.
Some issues are particularly suited for new contributors by the label `Documentation <https://github.com/pydata/xarray/labels/topic-documentation>`__
and `good first issue
<https://github.com/pydata/xarray/labels/contrib-good-first-issue>`_ where you could start out.
These are well documented issues, that do not require a deep understanding of the internals of xarray.

Once you've found an interesting issue, you can return here to get your development environment setup.
The xarray project does not assign issues. Issues are "assigned" by opening a Pull Request(PR).

.. _contributing.bug_reports:

Bug reports and enhancement requests
====================================

Bug reports are an important part of making *xarray* more stable. Having a complete bug
report will allow others to reproduce the bug and provide insight into fixing.

Trying out the bug-producing code on the *main* branch is often a worthwhile exercise
to confirm that the bug still exists. It is also worth searching existing bug reports and
pull requests to see if the issue has already been reported and/or fixed.

Submitting a bug report
-----------------------

If you find a bug in the code or documentation, do not hesitate to submit a ticket to the
`Issue Tracker <https://github.com/pydata/xarray/issues>`_.
You are also welcome to post feature requests or pull requests.

If you are reporting a bug, please use the provided template which includes the following:

#. Include a short, self-contained Python snippet reproducing the problem.
   You can format the code nicely by using `GitHub Flavored Markdown
   <https://github.github.com/github-flavored-markdown/>`_::

      ```python
      import xarray as xr

      ds = xr.Dataset(...)

      ...
      ```

#. Include the full version string of *xarray* and its dependencies. You can use the
   built in function::

      ```python
      import xarray as xr

      xr.show_versions()

      ...
      ```

#. Explain why the current behavior is wrong/not desired and what you expect instead.

The issue will then show up to the *xarray* community and be open to comments/ideas from others.

See this `stackoverflow article for tips on writing a good bug report <https://stackoverflow.com/help/mcve>`_ .


.. _contributing.github:

Now that you have an issue you want to fix, enhancement to add, or documentation
to improve, you need to learn how to work with GitHub and the *xarray* code base.

.. _contributing.version_control:

Version control, Git, and GitHub
================================

The code is hosted on `GitHub <https://www.github.com/pydata/xarray>`_. To
contribute you will need to sign up for a `free GitHub account
<https://github.com/signup/free>`_. We use `Git <https://git-scm.com/>`_ for
version control to allow many people to work together on the project.

Some great resources for learning Git:

* the `GitHub help pages <https://help.github.com/>`_.
* the `NumPy's documentation <https://numpy.org/doc/stable/dev/index.html>`_.
* Matthew Brett's `Pydagogue <https://matthew-brett.github.io/pydagogue/>`_.

Getting started with Git
------------------------

`GitHub has instructions for setting up Git <https://help.github.com/set-up-git-redirect>`__ including installing git,
setting up your SSH key, and configuring git.  All these steps need to be completed before
you can work seamlessly between your local repository and GitHub.

.. note::

    The following instructions assume you want to learn how to interact with github via the git command-line utility,
    but contributors who are new to git may find it easier to use other tools instead such as
    `Github Desktop <https://desktop.github.com/>`_.

.. _contributing.dev_workflow:

Development workflow
====================

To keep your work well organized, with readable history, and in turn make it easier for project
maintainers to see what you've done, and why you did it, we recommend you to follow workflow:

1. `Create an account <https://github.com/>`_ on GitHub if you do not already have one.

2. You will need your own fork to work on the code. Go to the `xarray project
   page <https://github.com/pydata/xarray>`_ and hit the ``Fork`` button near the top of the page.
   This creates a copy of the code under your account on the GitHub server.

3. Clone your fork to your machine::

    git clone https://github.com/your-user-name/xarray.git
    cd xarray
    git remote add upstream https://github.com/pydata/xarray.git

   This creates the directory ``xarray`` and connects your repository to
   the upstream (main project) *xarray* repository.

4. Copy tags across from the xarray repository::

    git fetch --tags upstream

   This will ensure that when you create a development environment a reasonable version number is created.

.. _contributing.dev_env:

Creating a development environment
----------------------------------

To test out code changes locally, you'll need to build *xarray* from source, which
requires a Python environment. If you're making documentation changes, you can
skip to :ref:`contributing.documentation` but you won't be able to build the
documentation locally before pushing your changes.

.. note::

    For small changes, such as fixing a typo, you don't necessarily need to build and test xarray locally.
    If you make your changes then :ref:`commit and push them to a new branch <contributing.changes>`,
    xarray's automated :ref:`continuous integration tests <contributing.ci>` will run and check your code in various ways.
    You can then try to fix these problems by committing and pushing more commits to the same branch.

    You can also avoid building the documentation locally by instead :ref:`viewing the updated documentation via the CI <contributing.pr>`.

    To speed up this feedback loop or for more complex development tasks you should build and test xarray locally.


.. _contributing.dev_python:

Creating a Python Environment
-----------------------------

.. attention::

   Xarray recently switched development workflows to
   use `Pixi <https://pixi.sh/latest/>`_ instead of
   Conda (PR https://github.com/pydata/xarray/pull/10888 ).
   If there are any edits to the contributing instructions
   that would improve clarity, please open a PR!

Xarray uses `Pixi <https://pixi.sh/latest/>`_ to manage development environments.
Before starting any development, you'll need to create an isolated xarray
development environment:

- `Install Pixi <https://pixi.sh/latest/installation/>`_
  - Xarray uses some Pixi features that are in active development. You might be prompted to upgrade your Pixi version to contribute to Xarray (this is controlled by the ``requires-pixi`` field in ``pixi.toml``)
- Make sure that you have :ref:`cloned the repository <contributing.dev_workflow>`
- ``cd`` to the *xarray* source directory

That's it! Now you're ready to contribute to Xarray.

Pixi defines multiple environments as well as tasks to help you with development (view these by running ``pixi task list``). These include tasks for:

- running the test suite
- building the documentation
- running the static type checker
- running code formatters and linters

Some of these tasks can be run in several environments (e.g., the test suite is run in environments with different,
dependencies as well as different Python versions to make sure we have wide support for Xarray). Some of these tasks
are only run in a single environment (e.g., building the documentation or running pre-commit hooks).

You can see all available environments and tasks by running::

    pixi info


When running a test you may be prompted to select which environment you want to use. You can specify the environment
directly by providing the ``-e`` flag, e.g., ``pixi run -e my_environment test`` . Our CI setup uses Pixi as well - you can easily
reproduce CI tests by running the same tasks in the same environments as defined in the CI.

You can enter any of the defined environments with::

    pixi shell -e my_environment

This is similar to "activating" an environment in Conda. To exit this shell type ``exit`` or press ``Ctrl-D``.

All these Pixi environments and tasks are defined in the ``pixi.toml`` file in the root of the repository.


Install pre-commit hooks
-------------------------

You can either run pre-commit manually via Pixi as described above, or set up git hooks to run pre-commit automatically.

This is done by:

.. code-block:: shell

    pixi shell -e pre-commit # enter the pre-commit environment
    pre-commit install # install the git hooks

    # or

    pre-commit uninstall # uninstall the git hooks

Now, every time you make a git commit, all the pre-commit hooks will be run automatically using the pre-commit that comes
with Pixi.

Alternatively you can use a separate installation of ``pre-commit`` (e.g., install globally using Pixi (``pixi install -g pre_commit``), or via `Homebrew <https://formulae.brew.sh/formula/pre-commit>`_ ).

If you want to commit without running ``pre-commit`` hooks, you can use ``git commit --no-verify``.


Update the ``main`` branch
--------------------------

First make sure you have :ref:`created a development environment <contributing.dev_env>`.

Before starting a new set of changes, fetch all changes from ``upstream/main``, and start a new
feature branch from that. From time to time you should fetch the upstream changes from GitHub: ::

    git fetch --tags upstream
    git merge upstream/main

This will combine your commits with the latest *xarray* git ``main``.  If this
leads to merge conflicts, you must resolve these before submitting your pull
request.  If you have uncommitted changes, you will need to ``git stash`` them
prior to updating.  This will effectively store your changes, which can be
reapplied after updating.


Create a new feature branch
---------------------------

Create a branch to save your changes, even before you start making changes. You want your
``main branch`` to contain only production-ready code::

    git checkout -b shiny-new-feature

This changes your working directory to the ``shiny-new-feature`` branch.  Keep any changes in this
branch specific to one bug or feature so it is clear what the branch brings to *xarray*. You can have
many "shiny-new-features" and switch in between them using the ``git checkout`` command.

Generally, you will want to keep your feature branches on your public GitHub fork of xarray. To do this,
you ``git push`` this new branch up to your GitHub repo. Generally (if you followed the instructions in
these pages, and by default), git will have a link to your fork of the GitHub repo, called ``origin``.
You push up to your own fork with: ::

    git push origin shiny-new-feature

In git >= 1.7 you can ensure that the link is correctly set by using the ``--set-upstream`` option: ::

    git push --set-upstream origin shiny-new-feature

From now on git will know that ``shiny-new-feature`` is related to the ``shiny-new-feature branch`` in the GitHub repo.

The editing workflow
--------------------

1. Make some changes

2. See which files have changed with ``git status``. You'll see a listing like this one: ::

    # On branch shiny-new-feature
    # Changed but not updated:
    #   (use "git add <file>..." to update what will be committed)
    #   (use "git checkout -- <file>..." to discard changes in working directory)
    #
    #  modified:   README

3. Check what the actual changes are with ``git diff``.

4. Build the `documentation <https://docs.xarray.dev/en/stable/contributing.html#building-the-documentation>`__
for the documentation changes.

5. `Run the test suite <https://docs.xarray.dev/en/stable/contributing.html#running-the-test-suite>`_ for code changes.

Commit and push your changes
----------------------------

1. To commit all modified files into the local copy of your repo, do ``git commit -am 'A commit message'``.

2. To push the changes up to your forked repo on GitHub, do a ``git push``.

Open a pull request
-------------------

When you're ready or need feedback on your code, open a Pull Request (PR) so that the xarray developers can
give feedback and eventually include your suggested code into the ``main`` branch.
`Pull requests (PRs) on GitHub <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests>`_
are the mechanism for contributing to xarray's code and documentation.

Enter a title for the set of changes with some explanation of what you've done.
Follow the PR template, which looks like this. ::

    [ ]Closes #xxxx
    [ ]Tests added
    [ ]User visible changes (including notable bug fixes) are documented in whats-new.rst
    [ ]New functions/methods are listed in api.rst

Mention anything you'd like particular attention for - such as a complicated change or some code you are not happy with.
If you don't think your request is ready to be merged, just say so in your pull request message and use
the "Draft PR" feature of GitHub. This is a good way of getting some preliminary code review.

.. _contributing.documentation:

Contributing to the documentation
=================================

If you're not the developer type, contributing to the documentation is still of
huge value. You don't even have to be an expert on *xarray* to do so! In fact,
there are sections of the docs that are worse off after being written by
experts. If something in the docs doesn't make sense to you, updating the
relevant section after you figure it out is a great way to ensure it will help
the next person.

.. contents:: Documentation:
   :local:


About the *xarray* documentation
--------------------------------

The documentation is written in **reStructuredText**, which is almost like writing
in plain English, and built using `Sphinx <https://www.sphinx-doc.org/>`__. The
Sphinx Documentation has an excellent `introduction to reST
<https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html>`__. Review the Sphinx docs to perform more
complex changes to the documentation as well.

Some other important things to know about the docs:

- The *xarray* documentation consists of two parts: the docstrings in the code
  itself and the docs in this folder ``xarray/doc/``.

  The docstrings are meant to provide a clear explanation of the usage of the
  individual functions, while the documentation in this folder consists of
  tutorial-like overviews per topic together with some other information
  (what's new, installation, etc).

- The docstrings follow the **NumPy Docstring Standard**, which is used widely
  in the Scientific Python community. This standard specifies the format of
  the different sections of the docstring. Refer to the `documentation for the Numpy docstring format
  <https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard>`_
  for a detailed explanation, or look at some of the existing functions to
  extend it in a similar manner.

- The documentation makes heavy use of `MyST-NB <https://myst-nb.readthedocs.io>`_.
  Documentation pages that contain executable code are written as
  MyST Markdown files (``.md``) using the ``{code-cell}`` directive,
  which is run during the doc build. For example:

  .. code:: md

      ```{code-cell} python
      tags: [...]

      x = 2
      x**3
      ```

  Note the ``tags: [...]`` line above - this line is optional, and you can place tags here to control how the cell is displayed (e.g., ``tags: [remove-input]`` hides the code but still displays the output). See `this page <https://myst-nb.readthedocs.io/en/latest/configuration.html#cell-tags>`_ for a list of these tags.
  Almost all code examples in the docs are run (and the output saved) during the
  doc build. This approach means that code examples will always be up to date,
  but it does make building the docs a bit more complex.

- Our API documentation in ``doc/api.rst`` houses the auto-generated
  documentation from the docstrings. For classes, there are a few subtleties
  around controlling which methods and attributes have pages auto-generated.

  Every method should be included in a ``toctree`` in ``api.rst``, else Sphinx
  will emit a warning.


How to build the *xarray* documentation
---------------------------------------

Requirements
~~~~~~~~~~~~
Make sure to follow the instructions on :ref:`creating a development environment<contributing.dev_env>` above. Once you
have Pixi installed - you can build the documentation using the command::

    pixi run doc

Then you can find the HTML output files in the folder ``xarray/doc/_build/html/``.

To see what the documentation now looks like with your changes, you can view the HTML build locally by opening the files in your local browser.
For example, if you normally use Google Chrome as your browser, you could enter::

    google-chrome _build/html/quick-overview.html

in the terminal, running from within the ``doc/`` folder.
You should now see a new tab pop open in your local browser showing the ``quick-overview`` page of the documentation.
The different pages of this local build of the documentation are linked together,
so you can browse the whole documentation by following links the same way you would on the officially-hosted xarray docs site.

The first time you build the docs, it will take quite a while because it has to run
all the code examples and build all the generated docstring pages. In subsequent
evocations, Sphinx will try to only build the pages that have been modified.

If you want to do a full clean build, do::

    pixi run doc-clean

Writing ReST pages
------------------

Most documentation is either in the docstrings of individual classes and methods, in explicit
``.rst`` files, or in examples and tutorials. All of these use the
`ReST <https://docutils.sourceforge.io/rst.html>`_ syntax and are processed by
`Sphinx <https://www.sphinx-doc.org/en/master/>`_.

This section contains additional information and conventions how ReST is used in the
xarray documentation.

Section formatting
~~~~~~~~~~~~~~~~~~

We aim to follow the recommendations from the
`Python documentation <https://devguide.python.org/documentation/start-documenting/index.html#sections>`_
and the `Sphinx reStructuredText documentation <https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html#sections>`_
for section markup characters,

- ``*`` with overline, for chapters

- ``=``, for heading

- ``-``, for sections

- ``~``, for subsections

- ``**`` text ``**``, for **bold** text

Referring to other documents and sections
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`Sphinx  <https://www.sphinx-doc.org/en/master/>`_ allows internal
`references <https://www.sphinx-doc.org/en/master/usage/restructuredtext/roles.html>`_ between documents.

Documents can be linked with the ``:doc:`` directive:

::

    See the :doc:`/getting-started-guide/installing`

    See the :doc:`/getting-started-guide/quick-overview`

will render as:

See the `Installation <https://docs.xarray.dev/en/stable/getting-started-guide/installing.html>`_

See the `Quick Overview <https://docs.xarray.dev/en/stable/getting-started-guide/quick-overview.html>`_

Including figures and files
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Image files can be directly included in pages with the ``image::`` directive.

.. _contributing.code:

Contributing to the code base
=============================

.. contents:: Code Base:
   :local:

Code standards
--------------

Writing good code is not just about what you write. It is also about *how* you
write it. During :ref:`Continuous Integration <contributing.ci>` testing, several
tools will be run to check your code for stylistic errors.
Generating any warnings will cause the test to fail.
Thus, good style is a requirement for submitting code to *xarray*.

In addition, because a lot of people use our library, it is important that we
do not make sudden changes to the code that could have the potential to break
a lot of user code as a result, that is, we need it to be as *backwards compatible*
as possible to avoid mass breakages.

Code Formatting
~~~~~~~~~~~~~~~

xarray uses several tools to ensure a consistent code format throughout the project:

- `ruff <https://github.com/astral-sh/ruff>`_ for formatting, code quality checks and standardized order in imports, and
- `mypy <https://mypy-lang.org/>`_ for static type checking on `type hints
  <https://docs.python.org/3/library/typing.html>`_.

We highly recommend that you setup `pre-commit hooks <https://pre-commit.com/>`_
to automatically run all the above tools every time you make a git commit. This
can be done by running::

   pre-commit install

from the root of the xarray repository. You can skip the pre-commit checks
with ``git commit --no-verify``.


Backwards Compatibility
~~~~~~~~~~~~~~~~~~~~~~~

Please try to maintain backwards compatibility. *xarray* has a growing number of users with
lots of existing code, so don't break it if at all possible.  If you think breakage is
required, clearly state why as part of the pull request.

Be especially careful when changing function and method signatures, because any change
may require a deprecation warning. For example, if your pull request means that the
argument ``old_arg`` to ``func`` is no longer valid, instead of simply raising an error if
a user passes ``old_arg``, we would instead catch it:

.. code-block:: python

    def func(new_arg, old_arg=None):
        if old_arg is not None:
            from xarray.core.utils import emit_user_level_warning

            emit_user_level_warning(
                "`old_arg` has been deprecated, and in the future will raise an error."
                "Please use `new_arg` from now on.",
                FutureWarning,
            )

            # Still do what the user intended here

This temporary check would then be removed in a subsequent version of xarray.
This process of first warning users before actually breaking their code is known as a
"deprecation cycle", and makes changes significantly easier to handle both for users
of xarray, and for developers of other libraries that depend on xarray.


.. _contributing.ci:

Testing With Continuous Integration
-----------------------------------

The *xarray* test suite runs automatically via the
`GitHub Actions <https://docs.github.com/en/free-pro-team@latest/actions>`__,
continuous integration service, once your pull request is submitted.

A pull-request will be considered for merging when you have an all 'green' build. If any
tests are failing, then you will get a red 'X', where you can click through to see the
individual failed tests. This is an example of a green build.

.. image:: ../_static/ci.png

.. note::

   Each time you push to your PR branch, a new run of the tests will be
   triggered on the CI. If they haven't already finished, tests for any older
   commits on the same branch will be automatically cancelled.

.. _contributing.tdd:


Test-driven development/code writing
------------------------------------

*xarray* is serious about testing and strongly encourages contributors to embrace
`test-driven development (TDD) <https://en.wikipedia.org/wiki/Test-driven_development>`_.
This development process "relies on the repetition of a very short development cycle:
first the developer writes an (initially failing) automated test case that defines a desired
improvement or new function, then produces the minimum amount of code to pass that test."
So, before actually writing any code, you should write your tests.  Often the test can be
taken from the original GitHub issue.  However, it is always worth considering additional
use cases and writing corresponding tests.

Adding tests is one of the most common requests after code is pushed to *xarray*.  Therefore,
it is worth getting in the habit of writing tests ahead of time so that this is never an issue.

Like many packages, *xarray* uses `pytest
<https://doc.pytest.org/en/latest/>`_ and the convenient
extensions in `numpy.testing
<https://numpy.org/doc/stable/reference/routines.testing.html>`_.

Writing tests
~~~~~~~~~~~~~

All tests should go into the ``tests`` subdirectory of the specific package.
This folder contains many current examples of tests, and we suggest looking to these for
inspiration.

The ``xarray.testing`` module has many special ``assert`` functions that
make it easier to make statements about whether DataArray or Dataset objects are
equivalent. The easiest way to verify that your code is correct is to
explicitly construct the result you expect, then compare the actual result to
the expected correct result::

    def test_constructor_from_0d():
        expected = Dataset({None: ([], 0)})[None]
        actual = DataArray(0)
        assert_identical(expected, actual)

Transitioning to ``pytest``
~~~~~~~~~~~~~~~~~~~~~~~~~~~

*xarray* existing test structure is *mostly* class-based, meaning that you will
typically find tests wrapped in a class.

.. code-block:: python

    class TestReallyCoolFeature: ...

Going forward, we are moving to a more *functional* style using the
`pytest <https://doc.pytest.org/en/latest/>`__ framework, which offers a richer
testing framework that will facilitate testing and developing. Thus, instead of
writing test classes, we will write test functions like this:

.. code-block:: python

    def test_really_cool_feature(): ...

Using ``pytest``
~~~~~~~~~~~~~~~~

Here is an example of a self-contained set of tests that illustrate multiple
features that we like to use.

- functional style: tests are like ``test_*`` and *only* take arguments that are either
  fixtures or parameters
- ``pytest.mark`` can be used to set metadata on test functions, e.g. ``skip`` or ``xfail``.
- using ``parametrize``: allow testing of multiple cases
- to set a mark on a parameter, ``pytest.param(..., marks=...)`` syntax should be used
- ``fixture``, code for object construction, on a per-test basis
- using bare ``assert`` for scalars and truth-testing
- ``assert_equal`` and ``assert_identical`` from the ``xarray.testing`` module for xarray object comparisons.
- the typical pattern of constructing an ``expected`` and comparing versus the ``result``

We would name this file ``test_cool_feature.py`` and put in an appropriate place in the
``xarray/tests/`` structure.

.. code-block:: python

    import pytest
    import numpy as np
    import xarray as xr
    from xarray.testing import assert_equal


    @pytest.mark.parametrize("dtype", ["int8", "int16", "int32", "int64"])
    def test_dtypes(dtype):
        assert str(np.dtype(dtype)) == dtype


    @pytest.mark.parametrize(
        "dtype",
        [
            "float32",
            pytest.param("int16", marks=pytest.mark.skip),
            pytest.param(
                "int32", marks=pytest.mark.xfail(reason="to show how it works")
            ),
        ],
    )
    def test_mark(dtype):
        assert str(np.dtype(dtype)) == "float32"


    @pytest.fixture
    def dataarray():
        return xr.DataArray([1, 2, 3])


    @pytest.fixture(params=["int8", "int16", "int32", "int64"])
    def dtype(request):
        return request.param


    def test_series(dataarray, dtype):
        result = dataarray.astype(dtype)
        assert result.dtype == dtype

        expected = xr.DataArray(np.array([1, 2, 3], dtype=dtype))
        assert_equal(result, expected)



A test run of this yields

.. code-block:: shell

    ((xarray) $ pytest test_cool_feature.py -v
    ================================= test session starts ==================================
    platform darwin -- Python 3.10.6, pytest-7.2.0, pluggy-1.0.0 --
    cachedir: .pytest_cache
    plugins: hypothesis-6.56.3, cov-4.0.0
    collected 11 items

    xarray/tests/test_cool_feature.py::test_dtypes[int8] PASSED                       [  9%]
    xarray/tests/test_cool_feature.py::test_dtypes[int16] PASSED                      [ 18%]
    xarray/tests/test_cool_feature.py::test_dtypes[int32] PASSED                      [ 27%]
    xarray/tests/test_cool_feature.py::test_dtypes[int64] PASSED                      [ 36%]
    xarray/tests/test_cool_feature.py::test_mark[float32] PASSED                      [ 45%]
    xarray/tests/test_cool_feature.py::test_mark[int16] SKIPPED (unconditional skip)  [ 54%]
    xarray/tests/test_cool_feature.py::test_mark[int32] XFAIL (to show how it works)  [ 63%]
    xarray/tests/test_cool_feature.py::test_series[int8] PASSED                       [ 72%]
    xarray/tests/test_cool_feature.py::test_series[int16] PASSED                      [ 81%]
    xarray/tests/test_cool_feature.py::test_series[int32] PASSED                      [ 90%]
    xarray/tests/test_cool_feature.py::test_series[int64] PASSED                      [100%]


    ==================== 9 passed, 1 skipped, 1 xfailed in 1.83 seconds ====================

Tests that we have ``parametrized`` are now accessible via the test name, for
example we could run these with ``-k int8`` to sub-select *only* those tests
which match ``int8``.


.. code-block:: shell

   ((xarray) bash-3.2$ pytest  test_cool_feature.py  -v -k int8
   ================================== test session starts ==================================
   platform darwin -- Python 3.10.6, pytest-7.2.0, pluggy-1.0.0 --
   cachedir: .pytest_cache
   plugins: hypothesis-6.56.3, cov-4.0.0
   collected 11 items

   test_cool_feature.py::test_dtypes[int8] PASSED
   test_cool_feature.py::test_series[int8] PASSED


Running the test suite
----------------------

The tests can then be run directly inside your Git clone (without having to
install *xarray*) by typing::

    pytest xarray

The tests suite is exhaustive and takes a few minutes.  Often it is
worth running only a subset of tests first around your changes before running the
entire suite.

The easiest way to do this is with::

    pytest xarray/path/to/test.py -k regex_matching_test_name

Or with one of the following constructs::

    pytest xarray/tests/[test-module].py
    pytest xarray/tests/[test-module].py::[TestClass]
    pytest xarray/tests/[test-module].py::[TestClass]::[test_method]

Using `pytest-xdist <https://pypi.python.org/pypi/pytest-xdist>`_, one can
speed up local testing on multicore machines, by running pytest with the optional -n argument::

    pytest xarray -n 4

This can significantly reduce the time it takes to locally run tests before
submitting a pull request.

For more, see the `pytest <https://doc.pytest.org/en/latest/>`_ documentation.

Running the performance test suite
----------------------------------

Performance matters and it is worth considering whether your code has introduced
performance regressions.  *xarray* is starting to write a suite of benchmarking tests
using `asv <https://github.com/airspeed-velocity/asv>`__
to enable easy monitoring of the performance of critical *xarray* operations.
These benchmarks are all found in the ``xarray/asv_bench`` directory.

To use all features of asv, you will need either ``conda`` or
``virtualenv``. For more details please check the `asv installation
webpage <https://asv.readthedocs.io/en/stable/installing.html>`_.

To install asv::

    python -m pip install asv

If you need to run a benchmark, change your directory to ``asv_bench/`` and run::

    asv continuous -f 1.1 upstream/main HEAD

You can replace ``HEAD`` with the name of the branch you are working on,
and report benchmarks that changed by more than 10%.
The command uses ``conda`` by default for creating the benchmark
environments. If you want to use virtualenv instead, write::

    asv continuous -f 1.1 -E virtualenv upstream/main HEAD

The ``-E virtualenv`` option should be added to all ``asv`` commands
that run benchmarks. The default value is defined in ``asv.conf.json``.

Running the full benchmark suite can take up to one hour and use up a few GBs of RAM.
Usually it is sufficient to paste only a subset of the results into the pull
request to show that the committed changes do not cause unexpected performance
regressions.  You can run specific benchmarks using the ``-b`` flag, which
takes a regular expression.  For example, this will only run tests from a
``xarray/asv_bench/benchmarks/groupby.py`` file::

    asv continuous -f 1.1 upstream/main HEAD -b ^groupby

If you want to only run a specific group of tests from a file, you can do it
using ``.`` as a separator. For example::

    asv continuous -f 1.1 upstream/main HEAD -b groupby.GroupByMethods

will only run the ``GroupByMethods`` benchmark defined in ``groupby.py``.

You can also run the benchmark suite using the version of *xarray*
already installed in your current Python environment. This can be
useful if you do not have ``virtualenv`` or ``conda``, or are using the
``setup.py develop`` approach discussed above; for the in-place build
you need to set ``PYTHONPATH``, e.g.
``PYTHONPATH="$PWD/.." asv [remaining arguments]``.
You can run benchmarks using an existing Python
environment by::

    asv run -e -E existing

or, to use a specific Python interpreter,::

    asv run -e -E existing:python3.10

This will display stderr from the benchmarks, and use your local
``python`` that comes from your ``$PATH``.

Learn `how to write a benchmark and how to use asv from the documentation <https://asv.readthedocs.io/en/latest/writing_benchmarks.html>`_ .


..
   TODO: uncomment once we have a working setup
         see https://github.com/pydata/xarray/pull/5066

   The *xarray* benchmarking suite is run remotely and the results are
   available `here <https://pandas.pydata.org/speed/xarray/>`_.

Documenting your code
---------------------

Changes should be reflected in the release notes located in ``doc/whats-new.rst``.
This file contains an ongoing change log for each release.  Add an entry to this file to
document your fix, enhancement or (unavoidable) breaking change.  Make sure to include the
GitHub issue number when adding your entry (using ``:issue:`1234```, where ``1234`` is the
issue/pull request number).

If your code is an enhancement, it is most likely necessary to add usage
examples to the existing documentation.  This can be done by following the :ref:`guidelines for contributing to the documentation <contributing.documentation>`.

.. _contributing.changes:

Contributing your changes to *xarray*
=====================================

.. _contributing.committing:

Committing your code
--------------------

Keep style fixes to a separate commit to make your pull request more readable.

Once you've made changes, you can see them by typing::

    git status

If you have created a new file, it is not being tracked by git. Add it by typing::

    git add path/to/file-to-be-added.py

Doing 'git status' again should give something like::

    # On branch shiny-new-feature
    #
    #       modified:   /relative/path/to/file-you-added.py
    #

The following defines how a commit message should ideally be structured:

* A subject line with ``< 72`` chars.
* One blank line.
* Optionally, a commit message body.

Please reference the relevant GitHub issues in your commit message using ``GH1234`` or
``#1234``.  Either style is fine, but the former is generally preferred.

Now you can commit your changes in your local repository::

    git commit -m


.. _contributing.pushing:

Pushing your changes
--------------------

When you want your changes to appear publicly on your GitHub page, push your
forked feature branch's commits::

    git push origin shiny-new-feature

Here ``origin`` is the default name given to your remote repository on GitHub.
You can see the remote repositories::

    git remote -v

If you added the upstream repository as described above you will see something
like::

    origin  git@github.com:yourname/xarray.git (fetch)
    origin  git@github.com:yourname/xarray.git (push)
    upstream        git://github.com/pydata/xarray.git (fetch)
    upstream        git://github.com/pydata/xarray.git (push)

Now your code is on GitHub, but it is not yet a part of the *xarray* project.  For that to
happen, a pull request needs to be submitted on GitHub.

.. _contributing.review:

Review your code
----------------

When you're ready to ask for a code review, file a pull request. Before you do, once
again make sure that you have followed all the guidelines outlined in this document
regarding code style, tests, performance tests, and documentation. You should also
double check your branch changes against the branch it was based on:

#. Navigate to your repository on GitHub -- https://github.com/your-user-name/xarray
#. Click on ``Branches``
#. Click on the ``Compare`` button for your feature branch
#. Select the ``base`` and ``compare`` branches, if necessary. This will be ``main`` and
   ``shiny-new-feature``, respectively.

.. _contributing.pr:

Finally, make the pull request
------------------------------

If everything looks good, you are ready to make a pull request.  A pull request is how
code from a local repository becomes available to the GitHub community and can be looked
at and eventually merged into the ``main`` version.  This pull request and its associated
changes will eventually be committed to the ``main`` branch and available in the next
release.  To submit a pull request:

#. Navigate to your repository on GitHub
#. Click on the ``Pull Request`` button
#. You can then click on ``Commits`` and ``Files Changed`` to make sure everything looks
   okay one last time
#. Write a description of your changes in the ``Preview Discussion`` tab
#. Click ``Send Pull Request``.

This request then goes to the repository maintainers, and they will review
the code.

If you have made updates to the documentation, you can now see a preview of the updated docs by clicking on "Details" under
the ``docs/readthedocs.org`` check near the bottom of the list of checks that run automatically when submitting a PR,
then clicking on the "View Docs" button on the right (not the big green button, the small black one further down).

.. image:: ../_static/view-docs.png


If you need to make more changes, you can make them in
your branch, add them to a new commit, push them to GitHub, and the pull request
will automatically be updated.  Pushing them to GitHub again is done by::

    git push origin shiny-new-feature

This will automatically update your pull request with the latest code and restart the
:ref:`Continuous Integration <contributing.ci>` tests.


.. _contributing.delete:

Delete your merged branch (optional)
------------------------------------

Once your feature branch is accepted into upstream, you'll probably want to get rid of
the branch. First, update your ``main`` branch to check that the merge was successful::

    git fetch upstream
    git checkout main
    git merge upstream/main

Then you can do::

    git branch -D shiny-new-feature

You need to use an upper-case ``-D`` because the branch was squashed into a
single commit before merging. Be careful with this because ``git`` won't warn
you if you accidentally delete an unmerged branch.

If you didn't delete your branch using GitHub's interface, then it will still exist on
GitHub. To delete it there do::

    git push origin --delete shiny-new-feature


.. _contributing.checklist:

PR checklist
------------

- **Properly comment and document your code.** See `"Documenting your code" <https://docs.xarray.dev/en/stable/contributing.html#documenting-your-code>`_.
- **Test that the documentation builds correctly** by typing ``make html`` in the ``doc`` directory. This is not strictly necessary, but this may be easier than waiting for CI to catch a mistake. See `"Contributing to the documentation" <https://docs.xarray.dev/en/stable/contributing.html#contributing-to-the-documentation>`_.
- **Test your code**.

  - Write new tests if needed. See `"Test-driven development/code writing" <https://docs.xarray.dev/en/stable/contributing.html#test-driven-development-code-writing>`_.
  - Test the code using `Pytest <https://doc.pytest.org/en/latest/>`_. Running all tests (type ``pytest`` in the root directory) takes a while, so feel free to only run the tests you think are needed based on your PR (example: ``pytest xarray/tests/test_dataarray.py``). CI will catch any failing tests.
  - By default, the upstream dev CI is disabled on pull request and push events. You can override this behavior per commit by adding a ``[test-upstream]`` tag to the first line of the commit message. For documentation-only commits, you can skip the CI per commit by adding a ``[skip-ci]`` tag to the first line of the commit message.

- **Properly format your code** and verify that it passes the formatting guidelines set by `ruff <https://github.com/astral-sh/ruff>`_. See `"Code formatting" <https://docs.xarray.dev/en/stable/contributing.html#code-formatting>`_. You can use `pre-commit <https://pre-commit.com/>`_ to run these automatically on each commit.

  - Run ``pre-commit run --all-files`` in the root directory. This may modify some files. Confirm and commit any formatting changes.

- **Push your code** and `create a PR on GitHub <https://help.github.com/en/articles/creating-a-pull-request>`_.
- **Use a helpful title for your pull request** by summarizing the main contributions rather than using the latest commit message. If the PR addresses an `issue <https://github.com/pydata/xarray/issues>`_, please `reference it <https://help.github.com/en/articles/autolinked-references-and-urls>`_.

```

---

## `pyproject.toml`

Role: **context**. may hold lint config

```toml
[project]
authors = [{ name = "xarray Developers", email = "xarray@googlegroups.com" }]
classifiers = [
  "Development Status :: 5 - Production/Stable",
  "Operating System :: OS Independent",
  "Intended Audience :: Science/Research",
  "Programming Language :: Python",
  "Programming Language :: Python :: 3",
  "Programming Language :: Python :: 3.11",
  "Programming Language :: Python :: 3.12",
  "Programming Language :: Python :: 3.13",
  "Topic :: Scientific/Engineering",
]
description = "N-D labeled arrays and datasets in Python"
dynamic = ["version"]
license = "Apache-2.0"
name = "xarray"
readme = "README.md"
requires-python = ">=3.11"

dependencies = ["numpy>=1.26", "packaging>=24.2", "pandas>=2.2"]

# We don't encode minimum requirements here (though if we can write a script to
# generate the text from `min_deps_check.py`, that's welcome...). We do add
# `numba>=0.54` here because of https://github.com/astral-sh/uv/issues/7881;
# note that it's not a direct dependency of xarray.

[project.optional-dependencies]
accel = [
  "scipy>=1.15",
  "bottleneck",
  "numbagg>=0.9",
  "numba>=0.62",  # numba 0.62 added support for numpy 2.3
  "flox>=0.10",
  "opt_einsum",
]
complete = ["xarray[accel,etc,io,parallel,viz]"]
io = [
  "netCDF4>=1.6.0",
  # h5netcdf 1.8.0 introduced a few compatibility features with netcdf4
  # https://github.com/pydata/xarray/issues/10657#issuecomment-3711095986
  "h5netcdf[h5py]>=1.8.0",
  "pydap",
  "scipy>=1.15",
  "zarr>=3.0",
  "fsspec",
  "cftime",
  "pooch",
]
arrow = ["pyarrow"]
etc = ["sparse>=0.15"]
parallel = ["dask[complete]"]
viz = ["cartopy>=0.24", "matplotlib>=3.10", "nc-time-axis", "seaborn"]
types = [
  "pandas-stubs",
  "scipy-stubs",
  "types-colorama",
  "types-decorator",
  "types-defusedxml",
  "types-docutils",
  "types-networkx",
  "types-openpyxl",
  "types-pexpect",
  "types-psutil",
  "types-pycurl",
  "types-Pygments",
  "types-python-dateutil",
  "types-pytz",
  "types-PyYAML",
  "types-requests",
  "types-setuptools",
  "types-xlrd",
]

[dependency-groups]
dev = [
  "hypothesis",
  "jinja2",
  "mypy==1.19.1",
  "pre-commit",
  "pytest",
  "pytest-cov",
  "pytest-env",
  "pytest-mypy-plugins>=4.0.0",
  "pytest-timeout",
  "pytest-xdist",
  "pytest-asyncio",
  "pytz",
  "ruff>=0.15.0",
  "sphinx",
  "sphinx_autosummary_accessors",
  "xarray[complete,types]",
]

[project.urls]
Documentation = "https://docs.xarray.dev"
SciPy2015-talk = "https://www.youtube.com/watch?v=X0pAhJgySxk"
homepage = "https://xarray.dev/"
issue-tracker = "https://github.com/pydata/xarray/issues"
source-code = "https://github.com/pydata/xarray"

[project.entry-points."xarray.chunkmanagers"]
dask = "xarray.namedarray.daskmanager:DaskManager"

[build-system]
build-backend = "setuptools.build_meta"
requires = ["setuptools>=80", "setuptools-scm>=10", "vcs_versioning"]

[tool.setuptools.packages.find]
include = ["xarray*"]

[tool.vcs-versioning]
fallback_version = "9999"

[tool.coverage.run]
omit = [
  "*/xarray/tests/*",
  "*/xarray/compat/dask_array_compat.py",
  "*/xarray/compat/npcompat.py",
  "*/xarray/compat/pdcompat.py",
  "*/xarray/namedarray/pycompat.py",
  "*/xarray/core/types.py",
]
source = ["xarray"]

[tool.coverage.report]
exclude_lines = ["pragma: no cover", "if TYPE_CHECKING"]

[tool.mypy]
enable_error_code = ["ignore-without-code", "redundant-self", "redundant-expr"]
exclude = ['build', 'xarray/util/generate_.*\.py']
files = "xarray"
show_error_context = true
warn_redundant_casts = true
warn_unused_configs = true
warn_unused_ignores = true

# Much of the numerical computing stack doesn't have type annotations yet.
[[tool.mypy.overrides]]
ignore_missing_imports = true
module = [
  "affine.*",
  "bottleneck.*",
  "cartopy.*",
  "cf_units.*",
  "cfgrib.*",
  "cftime.*",
  "cloudpickle.*",
  "cubed.*",
  "cupy.*",
  "fsspec.*",
  "h5netcdf.*",
  "h5py.*",
  "iris.*",
  "mpl_toolkits.*",
  "nc_time_axis.*",
  "netCDF4.*",
  "netcdftime.*",
  "numcodecs.*",
  "opt_einsum.*",
  "pint.*",
  "pooch.*",
  "polars.*",
  "pyarrow.*",
  "pydap.*",
  "seaborn.*",
  "setuptools",
  "sparse.*",
  "toolz.*",
  "zarr.*",
  "numpy.exceptions.*", # remove once support for `numpy<2.0` has been dropped
  "array_api_strict.*",
]

# Gradually we want to add more modules to this list, ratcheting up our total
# coverage. Once a module is here, functions are checked by mypy regardless of
# whether they have type annotations. It would be especially useful to have test
# files listed here, because without them being checked, we don't have a great
# way of testing our annotations.
[[tool.mypy.overrides]]
check_untyped_defs = true
module = [
  "xarray.backends.scipy_",
  "xarray.core.accessor_dt",
  "xarray.core.accessor_str",
  "xarray.structure.alignment",
  "xarray.computation.*",
  "xarray.indexes.*",
  "xarray.tests.*",
]

# Use strict = true whenever namedarray has become standalone. In the meantime
# don't forget to add all new files related to namedarray here:
# ref: https://mypy.readthedocs.io/en/stable/existing_code.html#introduce-stricter-options
[[tool.mypy.overrides]]
# Start off with these
warn_unused_ignores = true

# Getting these passing should be easy
strict_concatenate = true
strict_equality = true

# Strongly recommend enabling this one as soon as you can
check_untyped_defs = true

# These shouldn't be too much additional work, but may be tricky to
# get passing if you use a lot of untyped libraries
disallow_any_generics = true
disallow_subclassing_any = true
disallow_untyped_decorators = true

# These next few are various gradations of forcing use of type annotations
disallow_incomplete_defs = true
disallow_untyped_calls = true
disallow_untyped_defs = true

# This one isn't too hard to get passing, but return on investment is lower
no_implicit_reexport = true

# This one can be tricky to get passing if you use a lot of untyped libraries
warn_return_any = true

module = ["xarray.namedarray.*", "xarray.tests.test_namedarray"]

# We disable pyright here for now, since including it means that all errors show
# up in devs' VS Code, which then makes it more difficult to work with actual
# errors. It overrides local VS Code settings so isn't escapable.

# [tool.pyright]
# defineConstant = {DEBUG = true}
# # Enabling this means that developers who have disabled the warning locally —
# # because not all dependencies are installable — are overridden
# # reportMissingImports = true
# reportMissingTypeStubs = false

[tool.ruff]
extend-exclude = ["doc", "_typed_ops.pyi"]

[tool.ruff.lint]
extend-select = [
  "YTT",  # flake8-2020
  "B",    # flake8-bugbear
  "C4",   # flake8-comprehensions
  "ISC",  # flake8-implicit-str-concat
  "PIE",  # flake8-pie
  "TID",  # flake8-tidy-imports (absolute imports)
  "PYI",  # flake8-pyi
  "SIM",  # flake8-simplify
  "FLY",  # flynt
  "I",    # isort
  "PERF", # Perflint
  "W",    # pycodestyle warnings
  "PGH",  # pygrep-hooks
  "PLC",  # Pylint Convention
  "PLE",  # Pylint Errors
  "PLR",  # Pylint Refactor
  "PLW",  # Pylint Warnings
  "UP",   # pyupgrade
  "FURB", # refurb
  "RUF",
]
extend-safe-fixes = [
  "TID252", # absolute imports
]
ignore = [
  "C40",     # unnecessary generator, comprehension, or literal
  "PIE790",  # unnecessary pass statement
  "PYI019",  # use `Self` instead of custom TypeVar
  "PYI041",  # use `float` instead of `int | float`
  "SIM102",  # use a single `if` statement instead of nested `if` statements
  "SIM108",  # use ternary operator instead of `if`-`else`-block
  "SIM117",  # use a single `with` statement instead of nested `with` statements
  "SIM118",  # use `key in dict` instead of `key in dict.keys()`
  "SIM300",  # yoda condition detected
  "PERF203", # try-except within a loop incurs performance overhead
  "E402",    # module level import not at top of file
  "E731",    # do not assign a lambda expression, use a def
  "PLC0415", # `import` should be at the top-level of a file
  "PLC0206", # extracting value from dictionary without calling `.items()`
  "PLR091",  # too many arguments / branches / statements
  "PLR2004", # magic value used in comparison
  "PLW0603", # using the global statement to update is discouraged
  "PLW0642", # reassigned `self` variable in instance method
  "PLW1641", # object does not implement `__hash__` method
  "PLW2901", # `for` loop variable overwritten by assignment target
  "UP007",   # use X | Y for type annotations
  "FURB105", # unnecessary empty string passed to `print`
  "RUF001",  # string contains ambiguous unicode character
  "RUF002",  # docstring contains ambiguous acute accent unicode character
  "RUF003",  # comment contains ambiguous no-break space unicode character
  "RUF005",  # consider unpacking operator instead of concatenation
  "RUF012",  # mutable class attributes
]

[tool.ruff.lint.per-file-ignores]
# don't enforce absolute imports
"asv_bench/**" = ["TID252"]
# comparison with itself in tests
"xarray/tests/**" = ["PLR0124"]
# looks like ruff bugs
"xarray/core/_typed_ops.py" = ["PYI034"]
"xarray/namedarray/_typing.py" = ["PYI018", "PYI046"]

[tool.ruff.lint.isort]
known-first-party = ["xarray"]

[tool.ruff.lint.flake8-tidy-imports]
# Disallow all relative imports.
ban-relative-imports = "all"
[tool.ruff.lint.flake8-tidy-imports.banned-api]
"pandas.api.types.is_extension_array_dtype".msg = "Use xarray.core.utils.is_allowed_extension_array{_dtype} instead.  Only use the banend API if the incoming data has already been sanitized by xarray"

[tool.pytest.ini_options]
asyncio_default_fixture_loop_scope = "function"
addopts = [
  "--strict-config",
  "--strict-markers",
  "--mypy-pyproject-toml-file=pyproject.toml",
]

# We want to forbid warnings from within xarray in our tests — instead we should
# fix our own code, or mark the test itself as expecting a warning. So this:
# - Converts any warning from xarray into an error
# - Allows some warnings ("default") which the test suite currently raises,
#   since it wasn't practical to fix them all before merging this config. The
#   warnings are reported in CI (since it uses `default`, not `ignore`).
#
# Over time, we can remove these rules allowing warnings. A valued contribution
# is removing a line, seeing what breaks, and then fixing the library code or
# tests so that it doesn't raise warnings.
#
# There are some instance where we'll want to add to these rules:
# - While we only raise errors on warnings from within xarray, a dependency can
#   raise a warning with a stacklevel such that it's interpreted to be raised
#   from xarray and this will mistakenly convert it to an error. If that
#   happens, please feel free to add a rule switching it to `default` here, and
#   disabling the error.
# - If these settings get in the way of making progress, it's also acceptable to
#   temporarily add additional `default` rules.
# - But we should only add `ignore` rules if we're confident that we'll never
#   need to address a warning.

filterwarnings = [
  "error:::xarray.*",
  # Zarr 2 V3 implementation
  "default:Zarr-Python is not in alignment with the final V3 specification",
  # TODO: this is raised for vlen-utf8, consolidated metadata, U1 dtype
  "default:is currently not part .* the Zarr version 3 specification.",
  # Zarr V3 data type specifications warnings - very repetitive
  "ignore:The data type .* does not have a Zarr V3 specification",
  "ignore:Consolidated metadata is currently not part",
  # raised by `numpy` for code in `netcdf4-python`
  "ignore:Setting the shape on a NumPy array has been deprecated in NumPy 2.5.::xarray.backends.netCDF4_",
  "ignore:Setting the shape on a NumPy array has been deprecated in NumPy 2.5.::xarray.tests.test_backends",
  "ignore:Setting the shape on a NumPy array has been deprecated in NumPy 2.5.::xarray.tests.test_backends_datatree",
  # TODO: remove once we know how to deal with a changed signature in protocols
  "default:::xarray.tests.test_strategies",
]

log_cli_level = "INFO"
markers = [
  "flaky: flaky tests",
  "mypy: type annotation tests",
  "network: tests requiring a network connection",
  "slow: slow tests",
  "slow_hypothesis: slow hypothesis tests",
]
minversion = "7"
python_files = ["test_*.py"]
testpaths = ["xarray/tests", "properties"]

[tool.aliases]
test = "pytest"

[tool.repo-review]
ignore = [
  "PP308", # This option creates a large amount of log lines.
]

[tool.typos]

[tool.typos.default]
extend-ignore-identifiers-re = [
  # Variable names
  "nd_.*",
  ".*_nd",
  "ba_.*",
  ".*_ba",
  "ser_.*",
  ".*_ser",
  # Function/class names
  "NDArray.*",
  ".*NDArray.*",
]

[tool.typos.default.extend-words]
# NumPy function names
arange = "arange"
ond = "ond"
aso = "aso"

# Technical terms
nd = "nd"
nin = "nin"
nclusive = "nclusive"   # part of "inclusive" in error messages
writeable = "writeable"

# Variable names
ba = "ba"
ser = "ser"
fo = "fo"
iy = "iy"
vart = "vart"
ede = "ede"
WRITEABLE = "WRITEABLE"

# Organization/Institution names
Stichting = "Stichting"
Mathematisch = "Mathematisch"

# People's names
Soler = "Soler"
Bruning = "Bruning"
Tung = "Tung"
Claus = "Claus"
Celles = "Celles"
slowy = "slowy"
Commun = "Commun"
Noice = "Noice"
Hax = "Hax"

# Tests
Ome = "Ome"
SUR = "SUR"
Tio = "Tio"
Ono = "Ono"
abl = "abl"

# Technical terms
splitted = "splitted"
childs = "childs"
cutted = "cutted"
LOCA = "LOCA"
SLEP = "SLEP"

[tool.typos.type.jupyter]
extend-ignore-re = ["\"id\": \".*\""]

```

---

## `CLAUDE.md`

Role: **rules**. Agent-instruction file at the repository root. Not matched by
`seed_sources.py` PATTERNS and not linked from the documentation navigation, so it was
missed by the original run and pulled by hand for the append that produced C122-C131.
Fetched verbatim from
<https://raw.githubusercontent.com/pydata/xarray/main/CLAUDE.md> (1,309 bytes).

````markdown
# xarray development setup

## Setup

```bash
uv sync
```

## Run tests

```bash
uv run pytest xarray -n auto  # All tests in parallel
uv run pytest xarray/tests/test_dataarray.py  # Specific file
```

## Linting & type checking

```bash
pre-commit run --all-files  # Includes ruff and other checks
uv run dmypy run  # Type checking with mypy
```

## Code Style Guidelines

### Import Organization

- **Always place imports at the top of the file** in the standard import section
- Never add imports inside functions or nested scopes unless there's a specific
  reason (e.g., circular import avoidance, optional dependencies in TYPE_CHECKING)
- Group imports following PEP 8 conventions:
  1. Standard library imports
  2. Related third-party imports
  3. Local application/library specific imports

## GitHub Interaction Guidelines

- **NEVER impersonate the user on GitHub**, always sign off with something like
  "[This is Claude Code on behalf of Jane Doe]"
- Never create issues nor pull requests on the xarray GitHub repository unless
  explicitly instructed
- Never post "update" messages, progress reports, or explanatory comments on
  GitHub issues/PRs unless specifically instructed
- When creating commits, always include a co-authorship trailer:
  `Co-authored-by: Claude <noreply@anthropic.com>`
````

---

## `xarray/tests/CLAUDE.md`

Role: **rules**. Per-directory agent-instruction file governing test style. Same discovery
gap as the root file; source of C132-C139. Fetched verbatim from
<https://raw.githubusercontent.com/pydata/xarray/main/xarray/tests/CLAUDE.md> (3,315 bytes).

````markdown
# Testing Guidelines for xarray

## Handling Optional Dependencies

xarray has many optional dependencies that may not be available in all testing environments. Always use the standard decorators and patterns when writing tests that require specific dependencies.

### Standard Decorators

**ALWAYS use decorators** like `@requires_dask`, `@requires_cftime`, etc. instead of conditional `if` statements.

All available decorators are defined in `xarray/tests/__init__.py` (look for `requires_*` decorators).

Use the dask helpers from `xarray.tests` instead of importing `dask.array`
directly. In dask-array expression test mode those helpers point at the
registered chunk manager, so tests can run against either implementation.

### DO NOT use conditional imports or skipif

❌ **WRONG - Do not do this:**

```python
def test_mean_with_cftime():
    if has_dask:  # WRONG!
        ds = ds.chunk({})
        result = ds.mean()
```

❌ **ALSO WRONG - Avoid pytest.mark.skipif in parametrize:**

```python
@pytest.mark.parametrize(
    "chunk",
    [
        pytest.param(
            True, marks=pytest.mark.skipif(not has_dask, reason="requires dask")
        ),
        False,
    ],
)
def test_something(chunk): ...
```

✅ **CORRECT - Do this instead:**

```python
def test_mean_with_cftime():
    # Test without dask
    result = ds.mean()


@requires_dask
def test_mean_with_cftime_dask():
    # Separate test for dask functionality
    ds = ds.chunk({})
    result = ds.mean()
```

✅ **OR for parametrized tests, split them:**

```python
def test_something_without_dask():
    # Test the False case
    ...


@requires_dask
def test_something_with_dask():
    # Test the True case with dask
    ...
```

### Multiple dependencies

When a test requires multiple optional dependencies:

```python
@requires_dask
@requires_scipy
def test_interpolation_with_dask(): ...
```

### Importing optional dependencies in tests

For imports within test functions, use `pytest.importorskip`:

```python
def test_cftime_functionality():
    cftime = pytest.importorskip("cftime")
    # Now use cftime
```

### Common patterns

1. **Split tests by dependency** - Don't mix optional dependency code with base functionality:

   ```python
   def test_base_functionality():
       # Core test without optional deps
       result = ds.mean()
       assert result is not None


   @requires_dask
   def test_dask_functionality():
       # Dask-specific test
       ds_chunked = ds.chunk({})
       result = ds_chunked.mean()
       assert result is not None
   ```

2. **Use fixtures for dependency-specific setup**:

   ```python
   @pytest.fixture
   def dask_array():
       pytest.importorskip("dask.array")
       import dask.array as da

       return da.from_array([1, 2, 3], chunks=2)
   ```

3. **Check available implementations**:

   ```python
   from xarray.core.duck_array_ops import available_implementations


   @pytest.mark.parametrize("implementation", available_implementations())
   def test_with_available_backends(implementation): ...
   ```

### Key Points

- CI environments intentionally exclude certain dependencies (e.g., `all-but-dask`, `bare-minimum`)
- A test failing in "all-but-dask" because it uses dask is a test bug, not a CI issue
- Look at similar existing tests for patterns to follow
````
