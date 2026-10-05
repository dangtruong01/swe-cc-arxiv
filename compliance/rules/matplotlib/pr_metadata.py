"""matplotlib: PR and release metadata -- 10 rules.

Layer C. Every rule is two layers (`docs/checker-authoring.md` §2): ``precondition``
selects on the rule's ANTECEDENT, ``pass_condition`` grades.

**None of these reads ``pr_text``**, which is the category prior. Matplotlib does not put
release notes in the pull request body: every one of these ten sentences is about a *file*
-- a note under :file:`doc/api/next_api_changes/` or under the What's new directory -- so
the correct declaration is ``("files",)`` throughout. This is the §5 worked example
almost verbatim.

**C220 and C230 are kept apart deliberately** (§7.5). Both could be read as covering an
entry written straight into the aggregated :file:`doc/users/whats_new.rst`. C220 grades the
*routing between* the two per-kind trees and selects only entries already filed in one of
them; C230 grades *being its own file in the named directory* and is the rule that catches
the aggregate. Each docstring names the other, and a test pins that C220 finds no target
on an aggregate edit.

The corpus's What's new directory is :file:`doc/release/next_whats_new/` and every
benchmark instance has :file:`doc/users/next_whats_new/`; both are accepted and the
mismatch is recorded in ``_common.py`` rather than corrected in the workbook (§0).
"""

from __future__ import annotations

import re

from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.rules.matplotlib._common import (API_CHANGE_KINDS, API_CHANGE_ROOT,
                                                 DOUBLE_BACKTICK, MIN_PYTHON_FILES,
                                                 RELEASE_AGGREGATE_PREFIXES,
                                                 RELEASE_AGGREGATES, WHATS_NEW_DIRS, XREF,
                                                 added_lines, api_change_notes_added,
                                                 expires_deprecation, head_lines,
                                                 introduces_deprecation,
                                                 introduces_pending_deprecation,
                                                 is_whats_new, new_public_defs,
                                                 new_rcparams, note_kind,
                                                 raises_min_numpy, raises_min_python,
                                                 release_notes_added, target, titles_of,
                                                 whats_new_added)

CATEGORY = "PR and release metadata"

#: Words that put a release-note entry on the API-change side of the routing table.
_API_KIND_WORDS = re.compile(r"\bdeprecat|\bremov|\bapi change|\bbehaviou?r change"
                             r"\bno longer\b|\brenamed\b", re.I)
#: A bare code object in a title: a call, a dotted path, or a dunder/underscored name.
_CODE_TOKEN = re.compile(r"(?<![`\w.])((?:[A-Za-z_][\w]*\.)+[A-Za-z_]\w*"
                         r"|[A-Za-z_]\w*\s*\(\s*\)"
                         r"|_[A-Za-z]\w*)")
#: The template C289 supplies opens with this heading.
_MIN_VERSION_TEMPLATE = re.compile(r"increase to minimum supported versions of "
                                   r"dependencies", re.I)


def _entry_text(bundle: EvidenceBundle, path: str) -> str:
    return "\n".join(text for _, text in added_lines(bundle, path))


def _lines_of(bundle: EvidenceBundle, path: str):
    """Whole-file lines when the patch reconstructs, else the added ones.

    A note the agent created reconstructs; a note it extended may not, and the added
    lines are then the part it is answerable for anyway.
    """
    return head_lines(bundle, path) or added_lines(bundle, path)


@rule(
    id="MATPLOTLIB-C205",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- "when introducing" is a newness qualifier; the
                          # target is the deprecation the agent added
    reads=("files",),  # spec §5: both the deprecation and the notice are in the patch
    heuristic=True,
)
class DeprecationNoticeWhenIntroducingADeprecation:
    """Pre-condition: each package file where the agent added a call to an ``_api``
    deprecation helper.
    Pass condition: the contribution also files an API change note under
    :file:`doc/api/next_api_changes/`.

    Heuristic on the **pre-condition** (§6.3): *introducing a deprecation* is approximated
    by one of the six named ``_api`` helpers appearing on a line the agent wrote, so a
    deprecation announced only in prose, or made by hand-rolled warning, is not seen.
    The pass condition is exact -- the note is a file in a named folder, so it is either
    in the diff or it is not.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"deprecation-notice:{path}", path, None, (path, b),
                       f"{path} introduces a deprecation")
                for path in introduces_deprecation(b)]

    def pass_condition(self, t: Target):
        path, bundle = t.payload
        if notes := api_change_notes_added(bundle):
            return Satisfied(f"{path} deprecates API and the change files {notes[0]}")
        return Violated(f"{path} introduces a deprecation with no API change note under "
                        f"{API_CHANGE_ROOT}")


@rule(
    id="MATPLOTLIB-C212",
    category=CATEGORY,
    ownership="touched",  # spec §4.1 -- expiring a deprecation edits (and deletes from)
                          # code that was already there
    reads=("files",),  # spec §5
    heuristic=True,
)
class DeprecationAnnouncementWhenADeprecationExpires:
    """Pre-condition: each package file where the agent removed a call to an ``_api``
    deprecation helper.
    Pass condition: the contribution files an API change note under
    :file:`doc/api/next_api_changes/`.

    Heuristic on the **pre-condition** (§6.3): *a deprecation expiring* is approximated by
    the helper call disappearing from the file, which is what expiry looks like in a diff
    but also what moving the helper elsewhere looks like. Deletion is an edit, so the
    evidence is the minus side of the patch and the ownership is ``touched``, not an
    absence of evidence.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"expiry-notice:{path}", path, None, (path, b),
                       f"{path} removes a deprecation helper")
                for path in expires_deprecation(b)]

    def pass_condition(self, t: Target):
        path, bundle = t.payload
        if notes := api_change_notes_added(bundle):
            return Satisfied(f"{path} expires a deprecation and the change files "
                             f"{notes[0]}")
        return Violated(f"{path} expires a deprecation with no announcement under "
                        f"{API_CHANGE_ROOT}")


@rule(
    id="MATPLOTLIB-C218",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- the pending deprecation is what the agent added
    reads=("files",),  # spec §5
    heuristic=True,
)
class PendingDeprecationNoticeSaysPending:
    """Pre-condition: the contribution introduces a pending deprecation -- an ``_api``
    helper added with ``pending=True``.
    Pass condition: one of the release-note entries it files has "pending deprecation" in
    its title.

    Heuristic on the **pre-condition** (§6.3), for the same reason as C205, and on the
    title match, which reads the note's reST section titles rather than a field the
    project declares. Note the direction: the pre-condition is the *pending deprecation*,
    not the notice, so a contribution that files no notice at all fails rather than
    escaping (§7.1).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        pending = introduces_pending_deprecation(b)
        if not pending:
            return []
        return [target(f"pending-title:{b.instance_id}", pending[0], None, (pending, b),
                       f"{pending[0]} introduces a pending deprecation")]

    def pass_condition(self, t: Target):
        pending, bundle = t.payload
        notes = release_notes_added(bundle)
        if not notes:
            return Violated(f"{pending[0]} introduces a pending deprecation and the "
                            f"contribution files no release note at all")
        for path in notes:
            for _, title in titles_of(_lines_of(bundle, path)):
                if "pending deprecation" in title.lower():
                    return Satisfied(f"{path} titles the notice {title!r}")
        return Violated(f"no release-note title says 'pending deprecation'; "
                        f"{notes[0]} is titled "
                        f"{(titles_of(_lines_of(bundle, notes[0])) or [(0, '(no title)')])[0][1]!r}")


@rule(
    id="MATPLOTLIB-C220",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- a release-note entry is a file the agent wrote
    reads=("files",),  # spec §5: the note and its folder are both in the patch
    heuristic=True,
)
class ReleaseNoteFiledInTheFolderForItsKind:
    """Pre-condition: each release-note entry the agent filed in one of the two per-kind
    trees.
    Pass condition: the tree matches the kind of change the entry describes -- API changes
    under :file:`doc/api/next_api_changes/`, everything else under the What's new
    directory.

    Heuristic on the **pass condition** (§6.2): the *kind* of a change is read off the
    entry's own words -- "deprecated", "removed", "behaviour change" and their relatives
    -- and a differently worded API change reads as a new feature.

    Deliberately narrower than its sentence, to keep it off C230's ground (§7.5): an entry
    written straight into :file:`doc/users/whats_new.rst` finds no target here, because a
    note that is in no per-kind folder has no routing to grade. C230 is the rule that
    catches it.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"note-folder:{path}", path, None, (path, b), path)
                for path in release_notes_added(b)]

    def pass_condition(self, t: Target):
        path, bundle = t.payload
        text = _entry_text(bundle, path)
        api_kind = bool(_API_KIND_WORDS.search(text))
        if api_kind and is_whats_new(path):
            return Violated(f"{path} describes an API change but is filed under the "
                            f"What's new directory, not {API_CHANGE_ROOT}")
        if not api_kind and path.startswith(API_CHANGE_ROOT):
            return Violated(f"{path} describes no API change but is filed under "
                            f"{API_CHANGE_ROOT} rather than the What's new directory")
        return Satisfied(f"{path} is filed in the folder for "
                         f"{'an API change' if api_kind else 'a new feature'}")


@rule(
    id="MATPLOTLIB-C225",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- no newness qualifier: a title the agent wrote or
                          # rewrote is one it is answerable for
    reads=("files",),  # spec §5
)
class NoCrossReferencesInReleaseNoteTitles:
    """Pre-condition: each section title in a release-note entry the agent wrote or edited.
    Pass condition: the title carries no reST cross-reference.

    Not a heuristic. A cross-reference has an exact written form -- an explicit role such
    as ``:func:`x``` or a trailing-underscore hyperlink -- and section titles are exactly
    the lines an underline follows. The sentence's second half ("ensure a cross-reference
    is included in the descriptive text") is a placement instruction for the reference the
    title must not carry, not a requirement that every note contain one, so it is not
    graded as a separate obligation.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in sorted(b.files):
            if not (path.startswith(WHATS_NEW_DIRS) or path.startswith(API_CHANGE_ROOT)):
                continue
            authored = {n for n, _ in added_lines(b, path)}
            for number, title in titles_of(_lines_of(b, path)):
                if b.files[path].is_new or number in authored:
                    out.append(target(f"title-xref:{path}:{number}", path,
                                      (number, number), (path, number, title), title))
        return out

    def pass_condition(self, t: Target):
        path, number, title = t.payload
        if match := XREF.search(title):
            return Violated(f"{path}:{number} puts the cross-reference "
                            f"{match.group(0)} in a section title")
        return Satisfied(f"{path}:{number} titles the section {title!r} with no "
                         f"cross-reference")


@rule(
    id="MATPLOTLIB-C226",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the note is a file the agent brought into being
    reads=("files",),  # spec §5
)
class ApiChangeNoteInAKindSubdirectory:
    """Pre-condition: each API change note the agent added under
    :file:`doc/api/next_api_changes/`.
    Pass condition: it sits in one of the four named subdirectories.

    Not a heuristic: the four subdirectories are published by name, and which one a path
    is in is a fact about the path. This grades only the *placement in a subdirectory*;
    which of the four is the right one for a given change is a judgement the corpus does
    not make mechanical, and the docstring says so rather than the flag implying more
    precision than there is.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"note-kind:{path}", path, None, path, path)
                for path in api_change_notes_added(b)]

    def pass_condition(self, t: Target):
        path: str = t.payload
        kind = note_kind(path)
        if kind in API_CHANGE_KINDS:
            return Satisfied(f"{path} is filed under {kind}/")
        return Violated(f"{path} is not in one of {', '.join(API_CHANGE_KINDS)}: "
                        f"the note sits at {kind or 'the root'} of {API_CHANGE_ROOT}")


@rule(
    id="MATPLOTLIB-C228",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- no newness qualifier on the title
    reads=("files",),  # spec §5
    heuristic=True,
)
class CodeObjectsInReleaseNoteTitlesUseDoubleBackticks:
    """Pre-condition: each section title in a release-note entry the agent wrote or edited.
    Pass condition: any code object in it is wrapped in double backticks.

    Heuristic on the **pass condition** (§6.2), and graded one-sidedly: *is this word a
    code object* cannot be decided from the title, so what is detected is the wrong form
    -- a dotted path, a call with parentheses, or an underscored identifier standing bare
    outside ``literal`` markup. A title naming a code object in plain prose that matches
    none of those patterns passes, and one containing an ordinary sentence with a full
    stop between two words could read as a dotted path.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in release_notes_added(b) + [p for p in sorted(b.files)
                                              if p.startswith(API_CHANGE_ROOT)
                                              and not b.files[p].is_new]:
            for number, title in titles_of(_lines_of(b, path)):
                out.append(target(f"title-literal:{path}:{number}", path,
                                  (number, number), (path, number, title), title))
        return out

    def pass_condition(self, t: Target):
        path, number, title = t.payload
        outside = DOUBLE_BACKTICK.sub(" ", title)
        if match := _CODE_TOKEN.search(outside):
            return Violated(f"{path}:{number} names the code object {match.group(1)!r} "
                            f"in the title without double backticks")
        return Satisfied(f"{path}:{number} leaves no code object unmarked in {title!r}")


@rule(
    id="MATPLOTLIB-C229",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- "every new feature": the target is API the agent
                          # added
    reads=("files",),  # spec §5
    heuristic=True,
)
class NewFeatureDescribedInAWhatsNewEntry:
    """Pre-condition: the contribution adds a new public feature -- a public function or
    class, or an rcParam.
    Pass condition: it also files a What's new entry.

    Heuristic on the **pre-condition** (§6.3). The corpus's own list of what counts as a
    feature is open ("function, parameter, rcParam, config value, behavior, ..."), so the
    antecedent is approximated by the two members of it that are decidable from the patch:
    a new public definition, and a new key in ``rcsetup._validators``. A new *parameter* or
    a changed *behaviour* is a feature by the same sentence and is not selected, so this
    under-fires -- the direction §4.5 prefers to the reverse.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        features = [f"{path}:{name}" for path, name, _ in new_public_defs(b)]
        features += [f"rcParam {key}" for key in new_rcparams(b)]
        if not features:
            return []
        return [target(f"whats-new:{b.instance_id}", None, None, (features, b),
                       f"{len(features)} new feature(s), e.g. {features[0]}")]

    def pass_condition(self, t: Target):
        features, bundle = t.payload
        if entries := whats_new_added(bundle):
            return Satisfied(f"{len(features)} new feature(s) described in {entries[0]}")
        return Violated(f"adds {features[0]} with no What's new entry under "
                        f"{' or '.join(WHATS_NEW_DIRS)}")


@rule(
    id="MATPLOTLIB-C230",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the entry is an artefact the agent wrote
    reads=("files",),  # spec §5
    heuristic=True,
)
class WhatsNewEntryIsItsOwnFile:
    """Pre-condition: each What's new entry the contribution writes, wherever it put it.
    Pass condition: the entry is its own new file under the What's new directory.

    Heuristic on the **pre-condition** (§6.3): *an entry* is recognised as either a new
    file in the What's new directory or added text in one of the aggregated release-note
    pages the release process would otherwise generate, and prose added to some third
    place is not seen as an entry at all.

    This is the rule that catches an entry written into :file:`doc/users/whats_new.rst`;
    C220, which grades the routing between the two per-kind trees, deliberately does not
    (§7.5). Accepting :file:`doc/users/next_whats_new/` alongside the corpus's
    :file:`doc/release/next_whats_new/` is the second reason for the flag -- see
    ``_common.py``.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = [target(f"whats-new-file:{path}", path, None, (path, b), path)
               for path in whats_new_added(b)]
        for path in sorted(b.files):
            if path in RELEASE_AGGREGATES or path.startswith(RELEASE_AGGREGATE_PREFIXES):
                if added_lines(b, path):
                    out.append(target(f"whats-new-file:{path}", path, None, (path, b),
                                      f"{len(added_lines(b, path))} line(s) added"))
        return out

    def pass_condition(self, t: Target):
        path, bundle = t.payload
        if is_whats_new(path) and bundle.files[path].is_new:
            return Satisfied(f"{path} is a separate file in the What's new directory")
        if is_whats_new(path):
            return Violated(f"{path} extends an existing What's new file instead of "
                            f"being written as its own")
        return Violated(f"the entry was written into {path} instead of its own file "
                        f"under {WHATS_NEW_DIRS[0]}")


@rule(
    id="MATPLOTLIB-C289",
    category=CATEGORY,
    ownership="touched",  # spec §4.2 -- the antecedent is the version bump, which edits
                          # files that were already there
    reads=("files",),  # spec §5
    heuristic=True,
)
class MinimumVersionBumpCarriesADevelopmentNote:
    """Pre-condition: the contribution raises the minimum supported Python or NumPy
    version.
    Pass condition: it adds a note under :file:`doc/api/next_api_changes/development/`
    using the supplied template.

    Heuristic on **both layers** (§6.3, §6.2). The pre-condition approximates *a minimum
    version bump* by the policy page's own fields appearing among the added lines of the
    files that carry them, which also fires on an unrelated edit to those fields. The pass
    condition checks the template by its heading -- "Increase to minimum supported
    versions of dependencies" -- and not by the comparison table beneath it, so a note
    with the right heading and none of the body passes.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        which = [name for name, bumped in (("Python", raises_min_python(b)),
                                           ("NumPy", raises_min_numpy(b))) if bumped]
        if not which:
            return []
        return [target(f"min-version-note:{b.instance_id}", None, None, (which, b),
                       f"raises the minimum {' and '.join(which)} version")]

    def pass_condition(self, t: Target):
        which, bundle = t.payload
        development = f"{API_CHANGE_ROOT}development/"
        notes = [p for p in api_change_notes_added(bundle) if p.startswith(development)]
        if not notes:
            return Violated(f"raises the minimum {which[0]} version with no note under "
                            f"{development}")
        for path in notes:
            if _MIN_VERSION_TEMPLATE.search(_entry_text(bundle, path)):
                return Satisfied(f"{path} uses the supplied template")
        return Violated(f"{notes[0]} does not use the supplied template, whose heading "
                        f"is 'Increase to minimum supported versions of dependencies'")


#: Named so the module states the file list C286 and C287 share with `specialized.py`;
#: the six-file rules themselves live there because their category is Specialized changes.
_SHARED_WITH_SPECIALIZED = MIN_PYTHON_FILES
