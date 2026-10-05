<!-- CONTRIBUTING-RULES-FILE -->
# scikit-learn contribution rules

Extracted from the scikit-learn contributing documentation (scikit-learn-rules). 146 rules. Follow all of them.

## Git and commit conventions

- Prefix a documentation PR's title with "DOC".
- Put a CI commit-message marker in the latest commit message for it to take effect.

## PR and release metadata

- Do not use a bare "Fix #<ISSUE NUMBER>" as the PR title.
- Add a changelog fragment describing the change when the PR is likely to affect users.
- Name the changelog fragment <PULL REQUEST>.<TYPE>.rst.
- Use one of the seven documented fragment types in the changelog filename.
- Put the fragment in the folder matching the module the PR changes.
- Write the changelog fragment as a single bullet point.

## Tests and test style

- Add new tests for the bug fix or feature the PR contributes.
- Make a bug-fix's new tests fail on unpatched main and pass with the patch applied.
- Make the test suite pass locally before opening the PR.
- Put tests in the module's tests/ subdirectory as appropriately named functions.
- Add a test asserting the deprecation warning is raised only in the relevant cases.
- Catch the deprecation warning in every other test, e.g. with @pytest.mark.filterwarnings.
- Leave the gallery examples free of the deprecation warning.
- Import the object under test from its public location, as client code would.
- Assert quasi-equality of float arrays with sklearn.utils._testing.assert_allclose.
- Pass a non-zero atol when comparing arrays containing zeros.
- Take the pyplot fixture as the first argument of every test that needs matplotlib.
- Seed each test's own RNG instance instead of relying on the global RNG singletons.
- Make a test using the global_random_seed fixture pass for every seed from 0 to 99.
- Run a new global_random_seed test with SKLEARN_TESTS_GLOBAL_RANDOM_SEED="all" before submitting.
- Keep the Python version of a compiled function in the tests as the reference implementation.
- Run the tests with -Werror::FutureWarning so uncaught FutureWarnings fail locally.

## Specialized changes

- Do not slice memoryviews in Cython code.
- Decorate final Cython classes and methods with @final.
- Release the GIL explicitly with prange(nogil=True) or a with nogil block.
- Guard every direct OpenMP call so the code still builds without OpenMP.
- cimport OpenMP routines from sklearn.utils._openmp_helpers, not from the OpenMP library.
- Declare explicit types in Cython code.
- Do not use {var=} f-string expressions in Cython code.
- Do not set SKLEARN_TESTS_GLOBAL_RANDOM_SEED in the pull-request CI configuration.

## Documentation and docstrings

- Illustrate a new feature with narrative user-guide documentation containing small code snippets.
- State the algorithm's expected time and space complexity and its scalability in the user guide.
- Add a usage example under examples/ for a new feature.
- Keep function, method and class docstrings alongside the code in sklearn/.
- Put gallery examples under examples/.
- Order docstring sections Parameters, Returns, See Also, Notes, Examples.
- Name parameter types with Python basic type names, e.g. bool rather than boolean.
- Write array shapes in parentheses after 'of shape'.
- Write a string parameter's allowed values as a brace-enclosed set.
- Use the term dataframe when a parameter relies on frame-like features such as column names.
- Write a list parameter's element type with 'of', as in 'list of int'.
- Put the dtype after the shape when documenting an ndarray parameter.
- Use integral and floating, not int and float, when documenting arbitrary precision.
- Write a None default once, at the end of the type line, as default=None.
- Write each See Also entry on one line with a colon and an explanation.
- Use the .. rubric:: Note directive when adding a Note to an attribute.
- Put one or two code snippets in a docstring's Example section.
- Make a docstring example runnable as is, including all required imports.
- Include a figure generated from an example in a new user-guide section.
- Include one or two short code examples in a user-guide section.
- Put mathematical equations last in a user-guide section, followed by their references.
- Use single backticks for inline literals in .rst files.
- Do not put an Examples section inside a dropdown.
- Place the Examples section immediately after the main discussion.
- Cite arXiv and DOI references with the :arxiv: and :doi: sphinx roles.
- Link to a documentation section through a reference label and the :ref: role.
- Do not rename or remove an existing sphinx reference label.
- Link glossary terms with the :term: role.
- Link to a function with its full import path in the :func: role.
- Link to a class with its full import path unless a currentmodule directive shortens it.
- Add a .. deprecated:: note to the docstring repeating the warning's information.
- Add a .. versionchanged:: directive to the parameter docstring giving the old and new defaults.
- Document constructor arguments under Parameters, not under Attributes.
- Document trailing-underscore attributes in the docstring's Attributes section.
- Write docstrings in the numpydoc standard.

## AI-assisted contribution policy

- Do not submit a pull request generated by a fully-automated tool.
- Edit the AI usage list to keep only the categories of AI assistance you used.
- Include the AI/agent disclosure in every summary, PR description and work description.
- Use the exact disclosure wording naming AI assistance and the absence of human review.
- Put the disclosure at the end of the generated summary.

## Code and quality

- Format contributed Python code according to PEP8.
- Isolate the profiled bottleneck in a dedicated module-level function before compiling it.

## Language and framework style

- Keep a renamed public name working for two releases and warn when it is used.
- Decorate a renamed function or class with utils.deprecated and delegate to the new name.
- Move the deprecated name to DEPRECATED_API_REFERENCE and add the new name to API_REFERENCE in doc/api_reference.py.
- Deprecate an attribute or method with the utils.deprecated decorator on its property.
- Put the deprecated decorator above the property decorator.
- Raise a FutureWarning manually when a deprecated parameter is passed.
- Validate a deprecated parameter and raise its warning in fit, not in __init__.
- Name both the deprecation version and the removal version in the warning message.
- Quote the release version, not the dev version, and set removal two releases later.
- Replace a changing default with a sentinel value and raise FutureWarning when it is left in place.
- Do not accept training data as an argument to an estimator's __init__.
- Set an instance attribute for every keyword argument __init__ accepts.
- Put no logic and no input validation in an estimator's __init__.
- Copy a mutable constructor argument before modifying it, and do so where it is used.
- Do not set trailing-underscore attributes inside __init__.
- Raise ValueError when X and y have different numbers of samples.
- Accept an ignored y=None keyword in second position on an unsupervised estimator's fit.
- Accept y in second position on fit_predict, fit_transform, score and partial_fit.
- Return self from fit.
- Take any parameter that can be set before seeing the data as an __init__ keyword argument.
- Name every public learned attribute with a trailing underscore.
- Name a learned but non-public attribute with a leading underscore.
- Set n_features_in_ at fit time on an estimator that expects tabular input.
- Set feature_names_in_ when the estimator is fitted on a dataframe.
- Inherit a new estimator from BaseEstimator.
- List mixins before BaseEstimator in a new estimator's bases.
- Return an estimator instance from __sklearn_clone__.
- Make a transformer inherit TransformerMixin and implement transform.
- Keep transform's output aligned one-to-one and in order with its input samples.
- Make a regressor inherit RegressorMixin, implement predict and accept numerical y.
- Make a classifier inherit ClassifierMixin.
- Accept string or integer label sequences as y in a classifier's fit.
- Store the observed labels in classes_ instead of assuming a contiguous integer range.
- Order classes_ to match the column order of predict_proba, predict_log_proba and decision_function.
- Return labels drawn from classes_ out of a classifier's predict.
- Make a clustering algorithm inherit ClusterMixin.
- Set a labels_ attribute holding the per-sample cluster assignment.
- Give every attribute added to a Tags subclass a default value.
- Do not let a super class's __init_subclass__ depend on auto_wrap_output_keys.
- Give __sklearn_is_fitted__ no parameters and a boolean return.
- Override _doc_link_module and _doc_link_template to customize an estimator's doc link.
- Set _doc_link_module to the top-level module name containing the estimator.
- Return a dict of template variables from _doc_link_url_param_generator.
- Separate words with underscores in non-class names.
- Put no more than one statement on a line, and break after if and for.
- Use absolute imports.
- Never use a star import.
- Do not use np.asanyarray or np.atleast_2d for input validation.
- Call check_array on any array-like argument to a public API function.
- Do not call numpy.random.random or similar module-level RNG routines.
- Take a random_state keyword and build a RandomState from it.
- Give an estimator a random_state __init__ argument defaulting to None.
- Store the random_state argument unmodified in an attribute of the same name.
- Store a post-fit generator in the random_state_ attribute.
- Define from_estimator, from_predictions or both on a Display class.
- Accept only the computed data in a Display's __init__.
- Restrict a Display's plot method parameters to visualization concerns.
- Store the matplotlib artists created by plot as attributes on the Display.
- Return the result of plot() from a Display's from_estimator and from_predictions.
- Validate the number of axes when a list of axes is passed to plot.
- Import matplotlib inside the plotting function, never at module level.
- Call check_matplotlib_support before importing matplotlib.
- Inherit from CallbackSupportMixin to give an estimator callback support.
- Call _init_callback_context at the start of fit to create the root callback context.
- Decorate a third-party callback-supporting estimator's fit with with_callbacks.
- Do not use with_callbacks on a built-in scikit-learn estimator.
- Implement the full FitCallback protocol on a callback.
- Declare only the optional hook arguments the callback actually uses.
- Define a hook's optional arguments as keyword-only.
- Do not call predict or transform on the estimator a hook receives; use fitted_estimator.
- Implement the AutoPropagatedCallback protocol on a callback meant to propagate to sub-estimators.
- Do not reset callback state in setup or teardown; accumulate across fits.
