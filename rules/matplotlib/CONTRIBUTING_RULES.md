<!-- CONTRIBUTING-RULES-FILE -->
# Matplotlib contribution rules

Extracted from the Matplotlib contributing documentation (matplotlib-rules). 167 rules. Follow all of them.

## Git and commit conventions

- Do not commit changes to your local main branch.
- Add every new file you create to version control.
- Put a [skip appveyor] marker on the first line of the commit message.
- Use [skip ci] only for changes to which documentation checks and unit tests do not apply.

## PR and release metadata

- Write a deprecation notice when introducing a deprecation.
- Write a deprecation announcement when a deprecation expires.
- Put "pending deprecation" in the title of a pending deprecation notice.
- File the release-note entry in the folder that matches the kind of change.
- Keep cross-references out of release-note section titles and put them in the descriptive text.
- Put an API change note in the next_api_changes subdirectory matching its kind.
- Denote code objects in a release-note title with double backticks.
- Describe every new feature in a What's new entry.
- Write each What's new entry into its own file under doc/release/next_whats_new/.
- Add an api_changes/development note using the given template for a minimum-version bump.

## Tests and test style

- Run the issue's reproducer against your branch and confirm it now gives the desired result.
- Run the test suite with a bare pytest from the repository root.
- Put a test in the file under lib/matplotlib/tests that mirrors the module it tests.
- Name a test module with a ``test_`` prefix.
- Name a test function with a ``test_`` prefix.
- Name a test class with a ``Test`` prefix.
- Fix the random seed in any test that uses random numbers.
- Seed numpy's default random generator with 19680801.
- Create test figures and Axes through the standard pyplot constructors.
- Name the expected baseline images in the image_comparison decorator.
- Commit the new baseline image into the matching baseline_images subdirectory.
- Omit the file extension from the baseline image name when comparing several formats.
- Set ``style='mpl20'`` on a new image-comparison test.
- Give a check_figures_equal test exactly two Figure parameters, one drawn by the tested method and one by the baseline method.
- Set an image-comparison tolerance with the ``tol`` argument rather than by any other means.
- Test new and changed code.

## Specialized changes

- Register a new rcParam with a validator and a _Param entry in rcsetup.py.
- Add a commented-out entry for a new rcParam to matplotlibrc.
- Add a new rcParam key to the RcKeyType Literal in typing.py.
- Run test_pyplot_up_to_date after changing the signature of a pyplot-wrapped method.
- Regenerate the pyplot wrappers with tools/boilerplate.py and commit them.
- Do not modify an existing colormap, color sequence or style.
- Give any new colormap, color sequence or style a BSD compatible license.
- Keep the deprecated API fully functional throughout the deprecation period.
- Ship the replacement for a deprecated API before the deprecation period ends.
- Raise a MatplotlibDeprecationWarning when deprecated API is used.
- Use the matching _api deprecation helper for the kind of API being deprecated.
- Set the deprecation helper's *since* parameter to the next point release.
- Update the .pyi stub so it matches the runtime behaviour after a deprecation.
- Update the stub signature for rename_parameter and make_keyword_only deprecations at introduction.
- Give a delete_parameter-deprecated parameter a default value hint in the stub.
- Remove the deprecation warnings along with the API when a deprecation expires.
- Remove deprecated and privatised items from the stub on expiry.
- Mark a pending deprecation with pending=True and no removal version.
- Set pending=False, since to the next meso release and removal at least two meso releases later when converting a pending deprecation.
- List new files and directories in the meson.build of their directory.
- Modify vendored code under extern/ only where the change cannot be made elsewhere.
- Do not make style fixes to vendored code under extern/.
- Suppress a clang-tidy false positive with a narrowly scoped NOLINT comment that gives the reason.
- Check that any code brought in from another project carries a PSF, BSD, MIT or compatible license.
- Do not add GPL or LGPL code to the main code base.
- Add a copy of a vendored dependency's license to the license directory where its license requires distribution.
- State the license clearly when using non-BSD-compatible code in a toolkit.
- Set requires-python in pyproject.toml to the minimum supported Python version.
- Update all six named files together when raising the minimum Python version.
- Update all six named files together when raising the minimum NumPy version.

## Documentation and docstrings

- Do not edit .rst files under doc/plot_types, doc/gallery, doc/tutorials, doc/users/explain or doc/api, except doc/api/api_changes/.
- Write section titles in sentence case.
- Use the listed reST markup characters for each heading level: * for chapters, = for sections, - for subsections, ^ for subsubsections, and " for paragraphs.
- Reserve the # overline markup for the main title in index.rst and start every other page at chapter level or lower.
- Refer to function arguments and keywords with the *emphasis* role.
- Do not use the default role to mark up a function argument.
- Do not use the literal role to mark up a function argument.
- Mark up inline mathematics with the :math: role.
- Mark up displayed mathematics with the .. math:: directive.
- Use the :doc: role to link to another documentation page.
- Name reference labels with hyphen-separated descriptive words.
- Do not encode the documentation hierarchy in a reference label.
- Place a reference label immediately before a section and link to it with the :ref: role.
- Link to Matplotlib methods, classes and modules with back ticks.
- Qualify an abbreviated reference far enough to disambiguate it when several code elements share the name.
- Point a .. plot:: directive at the Python script that generates the figure, not at a generated image.
- When moving or consolidating a page, add a redirect-from directive to the new page instead of leaving the old URL dead.
- Write a redirect-from path as a full path from the doc root, never as a relative link.
- Write docstrings that conform to the numpydoc docstring guide.
- Put new API reference documentation in the module docstring, not in a doc/api page.
- Put the opening and closing quotes of a single-line docstring on the same line as its text.
- Put the opening and closing quotes of a multi-line docstring on their own lines.
- Give string values with plain quotes and no surrounding literal role.
- Do not use formal type-annotation syntax in a docstring type description.
- Describe a parameter that accepts any number as ``float``.
- Describe a 2D position as ``(float, float)``, parentheses included.
- Describe a homogeneous numeric sequence parameter as ``array-like``.
- Describe a return value that really is a numpy array as ``array``, not ``array-like``.
- Spell out a non-float dtype as ``array-like of <dtype>``.
- Describe a non-numeric homogeneous sequence as ``list of <type>``.
- Write parameter types as full references with a leading tilde.
- Write in-text references to code in the abbreviated dotted form.
- Document a simple default with ``{name} : {type}, default: {val}``.
- Do not document None as a default when it is only a not-specified sentinel.
- Wrap a long parameter list with a backslash continuation and no indent on the continuation line.
- Reference an rcParam with the :rc: role.
- Document a property setter's accepted values in its Parameters block, or in an ``.. ACCEPTS:`` block where that is not possible.
- Mark a deliberately inherited docstring with the comment ``# docstring inherited``.
- Put "sgskip" in the filename of an example that should not have a plot generated.
- Separate blocks of narrative text in an example or tutorial with the ``# %%`` separator.
- Cite the source of any public dataset used as sample data.
- Write sample data out in the example code, falling back to cbook.get_sample_data only where that is not feasible.
- Put sample data too large to inline into lib/matplotlib/mpl-data/sample_data/.
- List the showcased functions in a References admonition at the bottom of the example.
- List both the Axes/Figure and the pyplot reference for a dual-API function, pyplot second.
- List every example in a gallery_order.txt that has no '*' placeholder.
- Add any raw .rst file in a mixed gallery subdirectory to a toctree.
- Do not use the word "demo" in a gallery example title.
- Use the simple present tense in a gallery example title that needs a verb.
- Keep a customised example figure within the 720px (or 896px) rendered width limit.
- Title a plot types entry with the method signature and its required arguments.
- Describe a plot types entry in one sentence and link to the method's API documentation.
- Style a plot types entry with the ``_mpl-gallery`` stylesheet.
- Write a verb-phrase heading in the second-person imperative, not the gerund.
- Write directed instructions as second-person imperative sentences.
- Write explanations in the present simple tense.
- Write in the active voice.
- Put a comment before or on the same line as the code it describes, never after it.
- End an example that produces a visual with a show() call.
- Do not leave Python output lines in documentation examples.
- Use a numbered list only for actions performed in a determined order.
- Write tables as reStructuredText ASCII tables.
- Do not use Markdown tables or the csv-table directive.
- Give every public method an informative docstring.
- Add a new rst file to the API docs when you add a new module.
- Put a small example in the Examples section of a high-level plotting function's docstring.
- Add a versioning directive for a backward-incompatible API change.
- Put a versioning directive at the end of its description block.
- Place a class or function versioning directive before the Parameters section.
- Place a parameter's versioning directive at the end of that parameter's description.
- Omit the micro version from a versioning directive and never apply one to a whole module.
- Mark discouraged API with a Discouraged admonition in its docstring.
- Prefix a discouraged function's summary line with [*Discouraged*].
- Write C/C++ header documentation in Numpydoc format.
- Demonstrate a plotting-related feature in a gallery example.
- Put the tags directive at the bottom of the page with the tags underneath it.
- Give every gallery example at least one content tag.
- Write a tag as ``subcategory: tag``.
- Keep a tag to one or two words.
- Do not create a tag that would apply to only one gallery entry.

## AI-assisted contribution policy

- Do not let external AI tooling interact with the project directly by opening issues or pull requests or commenting.
- Disclose in the PR description whether and how AI was used.

## Code and quality

- Get the prek pre-commit checks passing before opening the pull request.
- Update the mypy type hints when you add or change public API.
- Use logging rather than print for debug output.
- Create the module logger as ``_log = logging.getLogger(__name__)`` right after the imports.
- Pass logging arguments as %-style parameters rather than pre-formatted strings.
- Log expected code paths at debug level only.
- Re-stage and re-commit any file a pre-commit hook modified.

## Language and framework style

- Name an Artist property accessor pair ``set_PROPERTYNAME`` and ``get_PROPERTYNAME``.
- Capitalise Figure when it means the Matplotlib object or class, and lowercase it in general language.
- Capitalise Axes when it means the Matplotlib object or class, and lowercase it in general language.
- Capitalise Artist when it means the Matplotlib object or class, and lowercase it in general language.
- Capitalise Axis when it means the Matplotlib object or class, and lowercase it in general language.
- Call the Axes usage pattern the "Axes interface", not the explicit, object-oriented, OO-style or OOP interface.
- Call the pyplot usage pattern the "pyplot interface", not the implicit or MATLAB-like interface, and do not capitalise Pyplot.
- Prefix helper functions and internal attributes with an underscore.
- Format Python code to PEP8 as enforced by ruff.
- Keep lines to at most 88 characters.
- Use the listed standard aliases when importing numpy, matplotlib and its submodules.
- Access rcParams as mpl.rcParams rather than importing it directly.
- Write C and C++ code to PEP7 style.
- Keep Python/C interface code separate from core C/C++ code.
- Name Python/C interface files FOO_wrap.cpp or FOO_wrapper.cpp.
- Declare keyword arguments explicitly when the function consumes all of them.
- Declare locally consumed arguments as keyword-only instead of popping them off **kwargs.
- Raise user-facing warnings through _api.warn_external rather than warnings.warn directly.
