<!-- CONTRIBUTING-RULES-FILE -->
# Django contribution rules

Extracted from the Django contributing documentation (django-rules). 78 rules. Follow all of them.

## Git and commit conventions

- Do not force-push to rewrite published history on django/django branches without team discussion.
- Phrase commit subject lines in past tense and end them with a period.

## PR and release metadata

- Start the commit message with 'Fixed #xxxxx' when the commit closes ticket xxxxx.
- Include 'Refs #xxxxx' in the commit message when referencing but not closing ticket xxxxx.
- If a contribution adds a feature or changes existing behavior, it should include documentation.
- Add a release-note entry in docs/releases/A.B.txt for new features.

## Tests and test style

- Write a regression test for a bug fix that fails on the pre-fix code and passes after.
- Write tests that exercise all newly added feature code.
- Wrap test-local model definitions with @isolate_apps() to avoid polluting the global apps registry.

## Specialized changes

- Raise a RemovedInDjangoXXWarning at the point the deprecated feature is used, in the deprecating release.
- Ensure `python -Wa runtests.py` produces no unintended warnings after adding a RemovedInDjangoXXWarning.
- Mark unreferenced deprecation-linked code with a RemovedInDjangoXXWarning comment so it's found when the deprecation completes.
- Annotate deprecated documentation entries with .. deprecated:: A.B, a description, and an upgrade path.
- Document the deprecation and its upgrade path under the 'Features deprecated in A.B' release-notes heading.
- Record the deprecation in docs/internals/deprecation.txt under the version it will be removed.

## Documentation and docstrings

- Verify documentation builds cleanly with make html (or make.bat html).
- Document new features with a versionadded/versionchanged directive at the correct Django version.
- Ensure documentation passes the spelling, code-block-format, and lint checks before a PR can be merged.
- Format Python code blocks in documentation with blacken-docs.
- Write hypothetical-person references with they/their/them rather than he/she constructions.
- Follow Django's term-capitalization conventions (Django/Python capitalized; model/template/view lowercase; URLconf as shown).
- Spell '-ize' words in American English style, not British '-ise'.
- Use sentence-case (not title-case) for reST section headings.
- Follow Django's fixed reST heading-underline hierarchy for section levels.
- Reference RFCs/PEPs via the :rfc:/:pep: Sphinx roles with section-level links when available.
- Use the dedicated Sphinx roles for MIME types, env vars, and CVE IDs rather than plain text/code formatting.
- Follow the fixed indentation scheme for Sphinx object directives: directive flush-left, description indented 4 spaces, nested directives +4 spaces further.
- Place versionchanged notes at the end of the relevant section rather than the beginning.
- Compress documentation PNG images using optipng and advpng prior to committing.
- Follow the versionadded/versionchanged directive with a mandatory blank line before any description.

## AI-assisted contribution policy

- Disclose any AI tools used in preparing a contribution and what each was used for.
- Verify AI-assisted contributions against the documented contribution checklist before submission.
- An AI agent must avoid fabricating nonexistent APIs, features, or citations in a contribution.
- An AI agent must self-report any output that may violate contribution requirements, with an explanation.

## Code and quality

- Ensure code passes black, blacken-docs, flake8, isort, and zizmor checks cleanly.
- Ensure the full test suite passes before submission.
- Ensure the test suite passes and docs build warning-free before opening a pull request.

## Language and framework style

- Format all Python files with black.
- Indent Python files with 4 spaces and HTML files with 2 spaces.
- Follow PEP 8 style conventions except where Django's .flake8 config excludes specific errors.
- Keep code lines to at most 88 characters.
- Wrap documentation, comments, and docstrings at 79 characters.
- Do not use f-strings for any string that may require translation, including error/logging messages.
- Avoid using 'we' in code comments.
- Name variables, functions, and methods with snake_case, not camelCase.
- Name classes (and class-returning factory functions) in PascalCase.
- In tests, prefer assertRaisesMessage() and assertWarnsMessage() over assertRaises() and assertWarns().
- Use assertRaisesRegex() and assertWarnsRegex() only if regex matching is required.
- For boolean checks, use assertIs(x, True/False) instead of assertTrue()/assertFalse().
- Write test docstrings as direct statements of expected behavior; omit 'Tests that'/'Ensures that' preambles.
- Sort imports using isort according to Django's import-grouping rules.
- Order import groups as future / stdlib / third-party / other Django / local Django / try-except, sorted alphabetically within each group.
- Within each import group, put plain 'import x' lines before 'from x import y' lines.
- Use absolute imports across Django components and single-dot relative imports locally; never use multi-dot relative imports.
- Alphabetize items on a single import line, listing uppercase names before lowercase names.
- Wrap long import statements using parentheses, 4-space continuation indent, a trailing comma, and a closing parenthesis on its own line.
- Leave one blank line between imports and module-level code, and two blank lines before the first function or class.
- Prefer documented convenience imports (e.g. from django.views import View) over internal module paths.
- Place {% extends %} as the first non-comment line in a template.
- Use exactly one space inside {{ }} variable tags.
- Alphabetize library names within a {% load %} tag.
- Use exactly one space inside {% %} tag delimiters.
- Name the block in {% endblock %} whenever it is on a different line from {% block %}.
- Space tokens inside {{ }}/{% %} singly, but keep '.' (attribute access) and '|' (filter) unspaced.
- Do not indent top-level {% block %} tags in an extending template.
- Name a view function's first parameter 'request'.
- Name model fields in lowercase snake_case.
- Place class Meta after model fields, with one blank line before it.
- Order model class members as: fields, manager attributes, Meta, dunder methods, save(), get_absolute_url(), then custom methods.
- Represent field choices via all-uppercase class attributes mapped to labels, or via a TextChoices/IntegerChoices enum.
- Avoid accessing django.conf.settings at module import time; use lazy indirection instead.
- Delete unused imports on edit; keep only backwards-compatibility imports, marked with # NOQA.
- Strip trailing whitespace from all changed lines.
- Do not sign contributed code with your name; contributor credit belongs in the AUTHORS file instead.
- Follow the .editorconfig-defined indentation for JavaScript files (typically 4 spaces).
- Name JavaScript variables in camelCase.
- Run Biome against JavaScript changes; it is also run via pre-commit.
- Prefer event delegation over direct element binding in JavaScript so behavior survives DOM structure changes.
