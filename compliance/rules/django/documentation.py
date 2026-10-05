"""Django: Documentation and docstrings -- 15 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

Four things shape this category.

**Django's documentation is reStructuredText in `.txt` files under `docs/`.** Not `.rst`,
not Markdown, not docstrings -- Django's public documentation is narrative reST, and its
docstrings are for developers rather than for the manual. Every rule here therefore targets
the `docs/` tree, and `is_doc_path` in ``tests.py`` is the single place that decides what
counts as one.

**The prose rules must fire on the situation, not on the spelling.** *"Write hypothetical
persons as they/their"* is not a rule about the word "he"; if C106 only selected lines
containing "he" or "she" it could record violations and never a compliant line, so its
antecedent is a line carrying **any** third-person pronoun and the grading asks which. The
same shape gives C109 (a word that could be spelled `-ise` or `-ize`), C116 (a line naming
an RFC or PEP, in either the role form or plain) and C117 (a line naming a MIME type, an
environment variable or a CVE). This is §4.2 applied to lexical rules, and it is the reason
those four preconditions look broader than the rule text sounds.

**Three rules name a tool, and the honest answer is that this bundle does not carry it.**
C103's spelling/lint checks and C104's `blacken-docs` are decided by running them; declaring
``lint_run`` and withholding keeps the row's applicability count while refusing to invent
the verdict. C074 is different and is graded: *"verify documentation builds cleanly with
make html"* is an obligation on the contributor to have run something, and whether they ran
it is in the command log.

**Structural rules read the rebuilt file, not the diff.** Which section a `versionchanged`
note sits at the end of, and how deep a heading is, cannot be answered from three lines of
context. Those rules take the file's whole text and then narrow back to the lines the agent
actually wrote (invariant 5); a file the harness never rebuilt becomes an ``Unreadable``
target rather than a silent absence.
"""

from __future__ import annotations

import re

from compliance.core.models import (
    EvidenceBundle,
    Satisfied,
    Target,
    Undetermined,
    Violated,
)
from compliance.core.registry import rule
from compliance.extractors import rst
from compliance.rules.django.tests import (
    _run_target,
    _target,
    _unreadable,
    doc_file_targets,
    doc_line_targets,
    doc_lines,
    is_doc_path,
    new_public_definitions,
    owned_files,
    ran,
)

CATEGORY = "Documentation and docstrings"

# --- Django vocabulary ---------------------------------------------------------------

# `make html` is what the writing-documentation guide tells contributors to run, from
# inside `docs/`. `make.bat html` is the Windows spelling the same paragraph offers.
MAKE_HTML = re.compile(r"\bmake(?:\.bat)?\b[^\n|;&]*\bhtml\b")
# Positive detection of a failed or noisy build. Searching for a success string instead
# would match unrelated output constantly.
BUILD_NOT_CLEAN = re.compile(
    r"^WARNING:|^ERROR:|\bSphinx error\b|\bExtension error\b|Exception occurred"
    r"|make(?:\.exe)?(?:\[\d+\])?: \*\*\*|\bbuild (?:failed|succeeded, \d+ warning)",
    re.M | re.I)

OPTIPNG = re.compile(r"\boptipng\b")
ADVPNG = re.compile(r"\badvpng\b")

# The Sphinx object directives Django's documentation defines things with -- the Python
# domain's, plus the custom ones its `djangodocs` extension adds.
OBJECT_DIRECTIVES = frozenset("""
class method attribute function data module exception decorator classmethod staticmethod
property currentmodule setting templatetag templatefilter fieldlookup lookup
django-admin django-admin-option admin-option
""".split())

VERSION_DIRECTIVES = ("versionadded", "versionchanged")

# Django's fixed heading hierarchy, from `docs/internals/contributing/writing-documentation`.
# A chapter heading carries an overline as well as an underline; everything below it does
# not, which is why `=` appears at two levels.
HEADING_ORDER = ("=", "-", "~", '"')

INDENT_STEP = 4

# Terms the style guide fixes the capitalization of. Django and Python are proper nouns;
# `model`, `template` and `view` are concepts and stay lowercase even though the classes
# that implement them are capitalized; URLconf has exactly one spelling.
PROPER_TERMS = {"django": "Django", "python": "Python"}
CONCEPT_TERMS = ("Model", "Models", "Template", "Templates", "View", "Views")
URLCONF = "URLconf"
_URLCONF_ANY = re.compile(r"\bURLconf\b|\b[Uu][Rr][Ll][Cc][Oo][Nn][Ff]\b")
_TERM_MENTION = re.compile(
    r"\b(?:[Dd]jango|[Pp]ython|[Mm]odels?|[Tt]emplates?|[Vv]iews?)\b|" + _URLCONF_ANY.pattern)

# Words that end in `-ise` and are not `-ize` words at all. Without this the rule reports
# "otherwise" and "raise" as British spellings, which is a false positive on nearly every
# page of the documentation.
ALLOWED_ISE = frozenset("""
advertise advertised advertises advertising anticlockwise arise arises arising bruise
chastise circumcise clockwise comprise comprised comprises comprising compromise
compromised compromises compromising concise cruise cruises cruising demise despise
devise devised devises devising disguise disguised disguises disguising enterprise
enterprises excise exercise exercised exercises exercising expertise franchise guise
improvise improvised improvises improvising incise likewise merchandise noise otherwise
paradise poise praise precise premise premises promise promised promises promising raise
raised raises raising reprise revise revised revises revising rise rises rising supervise
supervised supervises supervising surmise surprise surprised surprises surprising
televise treatise wise
""".split())

# Proper nouns and acronyms that are capitalized mid-heading without making it title case.
HEADING_PROPER = frozenset("""
Django Python HTTP HTTPS URL URLs URLconf URLconfs SQL JSON XML YAML CSV HTML CSS API APIs
REST ORM WSGI ASGI GIS PostgreSQL MySQL MariaDB SQLite Oracle Unicode ASCII UTC UTF
GeoDjango Sphinx Git GitHub Trac Windows Linux macOS Unix JavaScript AJAX CSRF XSS SMTP
IMAP POP3 TLS SSL UUID PDF PNG JPEG GZip Jinja Trac Python2 Python3 Redis Memcached
January February March April May June July August September October November December
Monday Tuesday Wednesday Thursday Friday Saturday Sunday
""".split())

_ENV_VARS = """
DJANGO_SETTINGS_MODULE DJANGO_COLORS PYTHONPATH PYTHONWARNINGS PYTHONSTARTUP
PYTHONHASHSEED PYTHONIOENCODING PYTHONDONTWRITEBYTECODE PATH HOME LANG LC_ALL LC_CTYPE
TZ VIRTUAL_ENV PGPASSWORD PGHOST PGPORT PGUSER PGDATABASE MYSQL_PWD USER SHELL EDITOR
TMPDIR
""".split()

_ROLE_SPAN = re.compile(r":[a-zA-Z:+-]+:`[^`]*`")
_LITERAL_SPAN = re.compile(r"``[^`]*``")
_URL_SPAN = re.compile(r"https?://\S+")

_PERSON_PRONOUN = re.compile(
    r"\b(?:he|him|his|she|her|hers|himself|herself|they|them|their|theirs|themselves)\b"
    r"|\bs/he\b|\bhe/she\b|\bhis/her\b|\bhim/her\b", re.I)
_GENDERED_PRONOUN = re.compile(
    r"\b(?:he|him|his|she|her|hers|himself|herself)\b"
    r"|\bs/he\b|\bhe/she\b|\bhis/her\b|\bhim/her\b", re.I)

_ISE_WORD = re.compile(r"\b\w+is(?:e|es|ed|er|ers|ing|ation|ations)\b", re.I)
_IZE_WORD = re.compile(r"\b\w+iz(?:e|es|ed|er|ers|ing|ation|ations)\b", re.I)

_RFC_PEP_PLAIN = re.compile(r"\b(RFC|PEP)\s*[-#]?\s*(\d+)\b")
_RFC_PEP_ROLE = re.compile(r":(?:rfc|pep):`", re.I)

_MIME = re.compile(
    r"\b(?:text|application|image|audio|video|multipart|message|font|model)"
    r"/[a-zA-Z0-9][a-zA-Z0-9.+-]*\b")
_CVE = re.compile(r"\bCVE-\d{4}-\d{4,}\b", re.I)
_ENVVAR = re.compile(r"\b(?:" + "|".join(sorted(_ENV_VARS)) + r")\b")

_DIRECTIVE = re.compile(r"^(?P<indent>[ \t]*)\.\.\s+(?P<name>[A-Za-z][\w:-]*)::(?P<arg>.*)$")
_CODE_BLOCK = re.compile(r"^[ \t]*\.\.\s+(?:code-block|sourcecode)::\s*(?:python|pycon|py)\s*$",
                         re.I)
_WORD = re.compile(r"[A-Za-z][A-Za-z'\-]*")


# --- shared documentation plumbing ----------------------------------------------------


def _indent(text: str) -> int:
    return len(text) - len(text.lstrip())


def _strip(text: str, *patterns: re.Pattern) -> str:
    for pattern in patterns:
        text = pattern.sub(" ", text)
    return text


def _prose(text: str) -> str:
    """A documentation line with its markup removed, leaving what a reader reads.

    Roles and inline literals are stripped because a rule about prose has no business
    grading ``Model`` in ```Model``` -- that is a class name, correctly capitalized.
    """
    return _strip(text, _ROLE_SPAN, _LITERAL_SPAN, _URL_SPAN)


def _directives(lines, names) -> list[tuple[int, int, str, str]]:
    """(line number, indent, directive name, argument) for each named directive."""
    out = []
    for lineno, text in lines:
        if match := _DIRECTIVE.match(text):
            if match.group("name").lower() in names:
                out.append((lineno, _indent(text), match.group("name").lower(),
                            match.group("arg").strip()))
    return out


def _section_starts(lines) -> list[int]:
    """The first line of each section: a heading's overline when it has one, else its text."""
    return sorted(h.lineno - 1 if h.overline else h.lineno for h in rst.headings(lines))


def _heading_level(heading: rst.RstHeading):
    char = heading.char
    if char == "=":
        return 0 if heading.overline else 1
    if char in HEADING_ORDER:
        return HEADING_ORDER.index(char) + 1
    return None


def _owns_line(change, lineno: int) -> bool:
    return change.is_new or lineno in change.modified_lines


def _python_blocks(lines) -> list[tuple[int, int]]:
    """(first, last) line of each Python code block: `.. code-block:: python` and `::`.

    The bare `::` form is included because Django's documentation uses it constantly and
    Sphinx highlights it as Python by default, so `blacken-docs` reformats it too.
    """
    out: list[tuple[int, int]] = []
    index, total = 0, len(lines)
    while index < total:
        lineno, text = lines[index]
        stripped = text.strip()
        opens = bool(_CODE_BLOCK.match(text)) or (
            stripped.endswith("::") and not stripped.startswith("..") and stripped != "::")
        if not opens:
            index += 1
            continue
        base, start, end, cursor = _indent(text), None, None, index + 1
        while cursor < total:
            body_lineno, body_text = lines[cursor]
            if not body_text.strip():
                cursor += 1
                continue
            if _indent(body_text) <= base:
                break
            if start is None:
                start = body_lineno
            end = body_lineno
            cursor += 1
        if start is not None:
            out.append((start, end))
        index = max(cursor, index + 1)
    return out


# --- tool-run obligations --------------------------------------------------------------


@rule(id="DJANGO-C074", category=CATEGORY, ownership="touched",
      reads=("files", "commands"))
class DocsBuildVerified:
    """Pre-condition: the contribution changes documentation.
    Pass condition: the agent ran `make html` (or `make.bat html`) over it and the build
    reported no error or warning.

    Graded from the command log rather than withheld, and the distinction matters. C103
    asks whether the docs *pass* a set of checks, which is a property of the artefact and
    needs the checks run. This rule asks whether the contributor *verified* the build,
    which is a property of what they did -- and what they did is exactly what a trajectory
    records. An agent that changed documentation and never built it has not verified
    anything, and that is the violation, not a missing tool.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        docs = [p for p, _ in owned_files(b, is_doc_path)]
        if not docs:
            return []
        return [_run_target(b, "docsbuild", b, f"{len(docs)} documentation file(s) changed")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        runs = ran(bundle, MAKE_HTML)
        if not runs:
            return Violated("documentation changed but `make html` was never run, so the "
                            "build is not shown to be clean")
        noisy = [c for c in runs if BUILD_NOT_CLEAN.search(c.output or "")]
        if noisy:
            first = BUILD_NOT_CLEAN.search(noisy[0].output or "")
            return Violated(f"`make html` did not build cleanly: "
                            f"{first.group(0).strip()[:70]!r}")
        return Satisfied(f"ran `make html` {len(runs)} time(s), no warning or error")


@rule(id="DJANGO-C103", category=CATEGORY, ownership="touched",
      reads=("files", "lint_run"))
class DocsChecksPass:
    """Pre-condition: the contribution changes documentation, which is what a pull request
    must get past the docs checks.
    Pass condition: the spelling, code-block-format and lint checks report nothing new on it.

    Withheld, with the missing input named. Answering *"does the spelling checker pass?"*
    means running `sphinx-build -b spelling`, and invariant 1 forbids a checker from running
    anything. The sandbox that produces `lint_report.json` does not yet cover the
    documentation toolchain, so the rule declares ``lint_run`` and returns
    ``tool_missing`` -- which ``tests/test_check_tier.py`` permits exactly while that stays
    true, and no longer.

    The pre-condition still fires, so the row records how often the rule would have applied
    rather than disappearing from the corpus.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        docs = [p for p, _ in owned_files(b, is_doc_path)]
        if not docs:
            return []
        return [_run_target(b, "docschecks", docs, f"{len(docs)} documentation file(s)")]

    def pass_condition(self, t: Target):
        return Undetermined(
            "tool_missing",
            f"the documentation spelling, code-block-format and lint checks were not run "
            f"over {len(t.payload)} changed file(s); no docs lint result for this run")


@rule(id="DJANGO-C104", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files", "lint_run"))
class DocCodeBlocksAreBlackened:
    """Pre-condition: each Python code block the agent added to a documentation file.
    Pass condition: `blacken-docs` reformats nothing in it.

    Withheld for the same reason as C103: whether a block is black-formatted is decided by
    running black over it, and this checker may not run anything. Lexical proxies were
    considered -- single-quoted strings, spacing inside brackets -- and rejected: they
    recognise a handful of black's rules out of dozens, so a "pass" would mean only that the
    proxy found nothing, which is a vacuous verdict wearing a real one.

    ``heuristic`` describes the pre-condition, not the grading. Finding a Python code block
    in reST is lexical: the bare `::` form carries no language marker and is treated as
    Python because Sphinx's default highlighter does, which over-fires on shell transcripts
    introduced the same way.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path, change in owned_files(b, is_doc_path):
            lines = doc_lines(change)
            for start, end in _python_blocks(lines):
                if any(_owns_line(change, n) for n in range(start, end + 1)):
                    targets.append(_target(f"codeblock:{path}:{start}", path, (start, end),
                                           (path, start, end), f"{path}:{start}-{end}"))
        return targets

    def pass_condition(self, t: Target):
        path, start, end = t.payload
        return Undetermined("tool_missing",
                            f"`blacken-docs` was not run over {path}:{start}-{end}")


@rule(id="DJANGO-C125", category=CATEGORY, ownership="touched",
      reads=("files", "commands"))
class DocImagesAreCompressed:
    """Pre-condition: each PNG image the contribution adds to or changes under `docs/`.
    Pass condition: the agent ran both `optipng` and `advpng` before committing it.

    The corpus files this as ``differential`` and the byte-level question -- *is this PNG
    already as small as optipng would make it?* -- would indeed need the tool. But the rule
    as written is an obligation on the contributor's process, "compress ... prior to
    committing", and the process is in the command log. Graded there, the same way C074 is,
    rather than withheld against evidence the sentence does not actually ask for.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [
            _target(f"png:{path}", path, None, b, path)
            for path, _change in owned_files(
                b, lambda p: p.startswith("docs/") and p.lower().endswith(".png"))
        ]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        missing = [name for name, pattern in (("optipng", OPTIPNG), ("advpng", ADVPNG))
                   if not ran(bundle, pattern)]
        if missing:
            return Violated(f"documentation image committed without running "
                            f"{' and '.join(missing)}")
        return Satisfied("optipng and advpng were both run")


# --- what a new feature owes the documentation -----------------------------------------


@rule(id="DJANGO-C080", category=CATEGORY, ownership="created", heuristic=True,
      reads=("files",))
class VersionDirectiveForNewFeature:
    """Pre-condition: each public top-level function or class the agent newly added to
    library code -- a new feature.
    Pass condition: the contribution adds a `.. versionadded::` or `.. versionchanged::`
    directive carrying a version.

    ``heuristic`` twice over, and both admissions matter. The antecedent is a proxy: a new
    public definition is what a feature looks like in a patch, and so does an extracted
    helper. And *"at the correct Django version"* cannot be decided from a bundle at all --
    knowing which release is in development means reading `django/__init__.py` on the
    branch, which the contribution need not contain. A directive with a version present is
    graded as satisfying; a wrong version passes, and the rule says so rather than pretending
    to a precision it lacks.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [
            _target(f"versiondir:{path}:{span[0]}", path, span, (b, name), f"{name} in {path}")
            for path, _module, name, span in new_public_definitions(b)
        ]

    def pass_condition(self, t: Target):
        bundle, name = t.payload
        for path, change in owned_files(bundle, is_doc_path):
            for lineno, text in change.added_lines:
                if match := _DIRECTIVE.match(text):
                    if match.group("name").lower() in VERSION_DIRECTIVES:
                        if match.group("arg").strip():
                            return Satisfied(f"{text.strip()} in {path}:{lineno}")
                        return Violated(f"{text.strip()!r} in {path}:{lineno} carries no "
                                        f"Django version")
        return Violated(f"{name} is a new public API and the contribution adds no "
                        f"versionadded/versionchanged directive for it")


# --- prose conventions -------------------------------------------------------------------


@rule(id="DJANGO-C106", category=CATEGORY, ownership="created", heuristic=True,
      reads=("files",))
class GenderNeutralPronouns:
    """Pre-condition: each documentation line the agent wrote that refers to a person by
    pronoun, whichever pronoun it uses.
    Pass condition: that pronoun is they, them or their.

    The pre-condition is the whole design of this rule. Selecting lines containing "he" or
    "she" would be selecting the violation: every target would fail, a compliant line would
    never appear, and the rate would be 0% by construction (§4.2). Selecting on *any*
    third-person pronoun makes both outcomes reachable.

    ``heuristic`` because "refers to a hypothetical person" is not what a pronoun search
    finds. "her" is also a possessive about a named contributor, "they" is also plural, and
    a pronoun inside quoted example output is not Django's prose at all.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return doc_line_targets(b, "pronoun", lambda text: _PERSON_PRONOUN.search(_prose(text)))

    def pass_condition(self, t: Target):
        text = _prose(t.payload)
        if match := _GENDERED_PRONOUN.search(text):
            return Violated(f"gendered pronoun {match.group(0)!r} where they/their/them "
                            f"belongs: {t.payload.strip()[:70]!r}")
        return Satisfied()


@rule(id="DJANGO-C108", category=CATEGORY, ownership="created", heuristic=True,
      reads=("files",))
class TermCapitalization:
    """Pre-condition: each documentation line the agent wrote that uses one of the terms
    the style guide fixes the capitalization of, in any casing.
    Pass condition: it spells them Django, Python, model, template, view and URLconf.

    Roles and inline literals are removed before both selection and grading, because
    ```Model``` and :class:`~django.db.models.Model` are the class, correctly capitalized,
    and the rule is about the concept in prose. A sentence-initial "Model" is also allowed:
    English capitalizes the first word regardless.

    ``heuristic`` because the exclusions cannot be complete. A capitalized "View" opening a
    list item, or "Template" inside a quotation, reads as prose to this check and is not.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return doc_line_targets(b, "terms", lambda text: _TERM_MENTION.search(_prose(text)))

    def pass_condition(self, t: Target):
        text = _prose(t.payload)
        for lowered, correct in PROPER_TERMS.items():
            for match in re.finditer(rf"\b{lowered}\b", text):
                after = text[match.end():match.end() + 1]
                before = text[max(0, match.start() - 1):match.start()]
                if after in (".", "-", "/", "_") or before in (".", "/", "-", "_"):
                    continue  # `django.db`, `django-admin`: a module or command, not prose
                return Violated(f"{lowered!r} should be {correct!r}: {t.payload.strip()[:70]!r}")
        for term in CONCEPT_TERMS:
            for match in re.finditer(rf"\b{term}\b", text):
                if _sentence_initial(text, match.start()):
                    continue
                return Violated(f"{term!r} should be lowercase in prose: "
                                f"{t.payload.strip()[:70]!r}")
        for match in _URLCONF_ANY.finditer(text):
            if match.group(0) != URLCONF:
                return Violated(f"{match.group(0)!r} should be {URLCONF!r}: "
                                f"{t.payload.strip()[:70]!r}")
        return Satisfied()


def _sentence_initial(text: str, position: int) -> bool:
    """Whether the word at ``position`` opens the line or a sentence."""
    before = text[:position].rstrip()
    return not before or before[-1] in ".!?:"


@rule(id="DJANGO-C109", category=CATEGORY, ownership="created", heuristic=True,
      reads=("files",))
class AmericanIzeSpelling:
    """Pre-condition: each documentation line the agent wrote containing a word that takes
    the `-ize`/`-ise` alternation, in either spelling.
    Pass condition: it is spelled `-ize`.

    Words that merely end in `-ise` without being `-ize` words -- "otherwise", "raise",
    "precise", "comprise" -- are excluded from the pre-condition, not from the grading:
    they are not instances of the alternation at all, so a line containing only those is
    not a line the rule has anything to say about. The list is necessarily partial, which
    is the ``heuristic`` admission: an `-ise` word missing from it is reported as British
    spelling.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return doc_line_targets(b, "ize", lambda text: bool(_alternating_words(text)))

    def pass_condition(self, t: Target):
        british = [w for w in _alternating_words(t.payload) if _ISE_WORD.fullmatch(w)]
        if british:
            return Violated(f"British `-ise` spelling: {british[0]!r} in "
                            f"{t.payload.strip()[:70]!r}")
        return Satisfied()


def _alternating_words(text: str) -> list[str]:
    prose = _prose(text)
    words = [m.group(0) for m in _ISE_WORD.finditer(prose)
             if m.group(0).lower() not in ALLOWED_ISE]
    words += [m.group(0) for m in _IZE_WORD.finditer(prose)]
    return words


@rule(id="DJANGO-C116", category=CATEGORY, ownership="created", heuristic=True,
      reads=("files",))
class RfcAndPepRoles:
    """Pre-condition: each documentation line the agent wrote that names an RFC or a PEP,
    in the role form or in plain text.
    Pass condition: every such mention is inside a `:rfc:` or `:pep:` role.

    Selecting only plain-text mentions would make the rule unable to record a compliant
    line, so role mentions are targets too and pass. Grading removes the role spans first
    and asks what is left.

    ``heuristic`` for the clause it cannot check: *"with section-level links when
    available"* means `:rfc:`2616#section-14.9`` rather than `:rfc:`2616``, and whether a
    section anchor exists for a given reference is a fact about the RFC, not about the
    patch. A role without an anchor is graded as satisfying.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return doc_line_targets(
            b, "rfcpep",
            lambda text: _RFC_PEP_PLAIN.search(_strip(text, _URL_SPAN))
            or _RFC_PEP_ROLE.search(text))

    def pass_condition(self, t: Target):
        remaining = _strip(t.payload, _ROLE_SPAN, _URL_SPAN)
        if match := _RFC_PEP_PLAIN.search(remaining):
            return Violated(f"{match.group(0)!r} written as plain text instead of a "
                            f":{match.group(1).lower()}: role")
        return Satisfied()


@rule(id="DJANGO-C117", category=CATEGORY, ownership="created", heuristic=True,
      reads=("files",))
class DedicatedSphinxRoles:
    """Pre-condition: each documentation line the agent wrote that names a MIME type, a
    known environment variable or a CVE id, in a role or otherwise.
    Pass condition: each is written with `:mimetype:`, `:envvar:` or `:cve:` respectively.

    Grading strips only the *matching* role, so `:setting:`DJANGO_SETTINGS_MODULE`` is still
    reported: the rule is about using the dedicated role, not about using any role. Inline
    literals are deliberately left in place, since ```text/html``` is precisely the "code
    formatting" the rule says to replace.

    ``heuristic``, and mostly for environment variables. An all-caps identifier is
    indistinguishable from a Django setting, a constant or a shell placeholder, so the check
    matches a curated list of real environment variables instead -- which under-fires by
    construction on any variable not on it.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return doc_line_targets(b, "roles", lambda text: bool(_role_candidates(text)))

    def pass_condition(self, t: Target):
        for kind, role, pattern in _ROLE_KINDS:
            remaining = _strip(t.payload, re.compile(rf":{role}:`[^`]*`"), _URL_SPAN)
            if match := pattern.search(remaining):
                return Violated(f"{kind} {match.group(0)!r} is not written with the "
                                f":{role}: role")
        return Satisfied()


_ROLE_KINDS = (
    ("MIME type", "mimetype", _MIME),
    ("environment variable", "envvar", _ENVVAR),
    ("CVE id", "cve", _CVE),
)


def _role_candidates(text: str) -> list[str]:
    without_urls = _strip(text, _URL_SPAN)
    found = [m.group(0) for _kind, _role, pattern in _ROLE_KINDS
             for m in pattern.finditer(without_urls)]
    found += re.findall(r":(?:mimetype|envvar|cve):`[^`]*`", text)
    return found


# --- reST structure -----------------------------------------------------------------------


@rule(id="DJANGO-C110", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class SentenceCaseHeadings:
    """Pre-condition: each reST section heading the agent wrote or edited.
    Pass condition: it is sentence case rather than title case.

    Decided by counting, not by a rule about every word: a heading is called title case
    when two or more of its non-initial words are capitalized without being proper nouns or
    acronyms. One such word is left alone, because the curated proper-noun list can never be
    complete and a single unfamiliar name is far more likely than a half-title-cased
    heading.

    ``heuristic`` for that list. "Using the Sites framework" is sentence case with a proper
    noun in it; "Using The Sites Framework" is not, and only a dictionary tells them apart.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for target in doc_file_targets(b, "heading"):
            if _unreadable(target) is not None:
                targets.append(target)
                continue
            path, change, lines = target.payload
            for heading in rst.headings(lines):
                if not (_owns_line(change, heading.lineno)
                        or _owns_line(change, heading.underline_lineno)):
                    continue
                targets.append(_target(f"heading:{path}:{heading.lineno}", path,
                                       (heading.lineno, heading.underline_lineno),
                                       heading, heading.text.strip()))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        text = t.payload.text.strip()
        words = _WORD.findall(text)
        offenders = [w for w in words[1:]
                     if w[0].isupper() and not w.isupper() and len(w) > 3
                     and w not in HEADING_PROPER]
        if len(offenders) >= 2:
            return Violated(f"title-case heading {text[:60]!r} (capitalized: {offenders[:3]})")
        return Satisfied(text[:60])


@rule(id="DJANGO-C115", category=CATEGORY, ownership="touched", reads=("files",))
class HeadingUnderlineHierarchy:
    """Pre-condition: each reST section heading the agent wrote or edited.
    Pass condition: its underline character is one of Django's four, and it does not skip a
    level below the heading before it.

    Django fixes the hierarchy: `=` with an overline for the document title, then `=`, `-`,
    `~` and `"` for the levels beneath. Two things are decidable from the rebuilt file and
    both are checked -- an adornment character outside that set, and a jump from a section
    to a sub-sub-section with nothing in between. What is not checked is a heading that is
    at a *shallower* level than its neighbour, which is how a document legitimately returns
    to a higher level.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for target in doc_file_targets(b, "hierarchy"):
            if _unreadable(target) is not None:
                targets.append(target)
                continue
            path, change, lines = target.payload
            previous = None
            for heading in rst.headings(lines):
                level = _heading_level(heading)
                if _owns_line(change, heading.lineno) or _owns_line(change, heading.underline_lineno):
                    targets.append(_target(
                        f"hierarchy:{path}:{heading.lineno}", path,
                        (heading.lineno, heading.underline_lineno), (heading, level, previous),
                        heading.text.strip()))
                if level is not None:
                    previous = level
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        heading, level, previous = t.payload
        if level is None:
            return Violated(f"heading {heading.text.strip()[:40]!r} is underlined with "
                            f"{heading.char!r}, which is not one of Django's "
                            f"{' '.join(HEADING_ORDER)}")
        if previous is not None and level > previous + 1:
            return Violated(f"heading {heading.text.strip()[:40]!r} jumps from level "
                            f"{previous} to level {level}, skipping a level of the hierarchy")
        return Satisfied(f"level {level}")


@rule(id="DJANGO-C118", category=CATEGORY, ownership="created", reads=("files",))
class ObjectDirectiveIndentation:
    """Pre-condition: each Sphinx object directive the agent added to a documentation file.
    Pass condition: it sits at a multiple of four spaces and its description begins exactly
    four spaces further in.

    "Directive flush-left" is checked as "at a multiple of four", because a nested directive
    is by definition not flush-left and the same scheme governs it. The description is the
    first more-indented line after the directive, which is where the four-space step is
    observable; how the rest of the block is laid out belongs to reST, not to this rule.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path, change in owned_files(b, is_doc_path):
            lines = doc_lines(change)
            index = {lineno: position for position, (lineno, _) in enumerate(lines)}
            for lineno, indent, name, _arg in _directives(lines, OBJECT_DIRECTIVES):
                if not _owns_line(change, lineno):
                    continue
                targets.append(_target(f"objdir:{path}:{lineno}", path, (lineno, lineno),
                                       (name, indent, lines, index.get(lineno, 0)),
                                       lines[index.get(lineno, 0)][1].strip()[:100]))
        return targets

    def pass_condition(self, t: Target):
        name, indent, lines, position = t.payload
        if indent % INDENT_STEP:
            return Violated(f".. {name}:: is indented {indent} space(s), not a multiple of "
                            f"{INDENT_STEP}")
        for _lineno, text in lines[position + 1:]:
            if not text.strip():
                continue
            body = _indent(text)
            if body <= indent:
                return Satisfied(f".. {name}:: has no description")
            if body != indent + INDENT_STEP:
                return Violated(f"description of .. {name}:: is indented {body} space(s), "
                                f"not {indent + INDENT_STEP}")
            return Satisfied(f".. {name}:: at {indent}, description at {body}")
        return Satisfied(f".. {name}:: has no description")


@rule(id="DJANGO-C123", category=CATEGORY, ownership="created", reads=("files",))
class VersionchangedAtEndOfSection:
    """Pre-condition: each `.. versionchanged::` directive the agent added to a
    documentation file.
    Pass condition: nothing but its own indented body follows it before the next section
    heading.

    The directive's block -- blank lines and anything indented past it -- belongs to the
    note and is skipped. What must not appear after that is ordinary prose, which is what
    "at the beginning of the section" looks like from below.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path, change in owned_files(b, is_doc_path):
            lines = doc_lines(change)
            if not lines:
                continue
            starts = _section_starts(lines)
            for lineno, indent, _name, _arg in _directives(lines, ("versionchanged",)):
                if not _owns_line(change, lineno):
                    continue
                targets.append(_target(f"vchanged:{path}:{lineno}", path, (lineno, lineno),
                                       (path, lineno, indent, lines, starts),
                                       f"{path}:{lineno}"))
        return targets

    def pass_condition(self, t: Target):
        path, lineno, indent, lines, starts = t.payload
        end_of_section = min((s for s in starts if s > lineno), default=lines[-1][0] + 1)
        trailing = []
        in_block = True
        for line_number, text in lines:
            if line_number <= lineno or line_number >= end_of_section:
                continue
            if not text.strip():
                continue
            if in_block and _indent(text) > indent:
                continue
            in_block = False
            trailing.append((line_number, text.strip()))
        if trailing:
            return Violated(f"versionchanged note at {path}:{lineno} is followed by "
                            f"{len(trailing)} more line(s) in its section, starting "
                            f"{trailing[0][1][:50]!r} -- it belongs at the end")
        return Satisfied(f"versionchanged note closes its section at {path}:{lineno}")


@rule(id="DJANGO-C143", category=CATEGORY, ownership="created", reads=("files",))
class BlankLineAfterVersionDirective:
    """Pre-condition: each `.. versionadded::` or `.. versionchanged::` directive the agent
    added to a documentation file.
    Pass condition: the line immediately after it is blank, or it has no description at all.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path, change in owned_files(b, is_doc_path):
            lines = doc_lines(change)
            index = {lineno: position for position, (lineno, _) in enumerate(lines)}
            for lineno, _indent_, name, _arg in _directives(lines, VERSION_DIRECTIVES):
                if not _owns_line(change, lineno):
                    continue
                position = index.get(lineno, 0)
                following = lines[position + 1][1] if position + 1 < len(lines) else ""
                targets.append(_target(f"blankline:{path}:{lineno}", path, (lineno, lineno),
                                       (path, lineno, name, following),
                                       f".. {name}:: at {path}:{lineno}"))
        return targets

    def pass_condition(self, t: Target):
        path, lineno, name, following = t.payload
        if following.strip():
            return Violated(f".. {name}:: at {path}:{lineno} is followed immediately by "
                            f"{following.strip()[:50]!r} with no blank line between")
        return Satisfied(f".. {name}:: at {path}:{lineno} is followed by a blank line")
