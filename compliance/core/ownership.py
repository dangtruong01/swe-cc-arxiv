"""created | touched | enclosing -- implemented once, so no rule reinvents it.

Invariant 5: targets come only from agent-authored content. A rule never gets credit for
code that was already compliant before the agent arrived.

``touched`` and ``enclosing`` reduce to the same predicate -- *some line the agent's edit
reaches falls inside this span* -- and that is deliberate. What separates them is the span the rule
hands over, not the arithmetic: ``touched`` is given the target's own span, ``enclosing``
the span of the definition the target belongs to. Edit one line of a function body and
you own that function's doctest under ``enclosing`` while owning none of its lines under
``touched``.
"""

from __future__ import annotations

from compliance.core.models import EvidenceBundle, FileChange


def owns_file(bundle: EvidenceBundle, path: str, mode: str) -> bool:
    change = bundle.files.get(path)
    if change is None:
        return False
    if mode == "created":
        return change.is_new
    if mode == "touched":
        return bool(change.modified_lines) or change.is_new or change.is_binary
    if mode == "enclosing":
        return bool(change.modified_lines) or change.is_new
    raise ValueError(f"unknown ownership mode: {mode!r}")


def owned_files(bundle: EvidenceBundle, mode: str) -> list[FileChange]:
    """Every changed file the agent owns under ``mode``, in stable path order."""
    return [bundle.files[p] for p in sorted(bundle.files) if owns_file(bundle, p, mode)]


def owns_span(bundle: EvidenceBundle, path: str, span: tuple[int, int], mode: str) -> bool:
    """Whether the agent owns a post-patch line span within ``path``."""
    change = bundle.files.get(path)
    if change is None:
        return False
    start, end = span
    covered = set(range(start, end + 1)) & change.modified_lines
    if mode == "created":
        # A deletion never creates anything, so `created` reads authored lines only.
        authored = set(range(start, end + 1)) & change.authored_lines
        return change.is_new or len(authored) == (end - start + 1)
    if mode == "touched":
        return bool(covered)
    if mode == "enclosing":
        return bool(covered)
    raise ValueError(f"unknown ownership mode: {mode!r}")


def authored_lines_of(bundle: EvidenceBundle, path: str) -> tuple[tuple[int, str], ...]:
    """The (line number, text) pairs the agent added to ``path``."""
    change = bundle.files.get(path)
    return change.added_lines if change else ()


def owned_span(
    bundle: EvidenceBundle,
    path: str,
    span: tuple[int, int],
    mode: str,
    *,
    enclosing_span: tuple[int, int] | None = None,
) -> bool:
    """``owns_span`` with the ``enclosing`` span supplied separately.

    A doctest is owned under ``enclosing`` when the agent edited any line of the
    function that carries it, which is a different span from the doctest's own.
    """
    if mode == "enclosing" and enclosing_span is not None:
        return owns_span(bundle, path, enclosing_span, "enclosing")
    return owns_span(bundle, path, span, mode)


def modified_lines_of(bundle: EvidenceBundle, path: str) -> frozenset[int]:
    """Every post-patch line the agent's edit reaches in ``path``, written or deleted from."""
    change = bundle.files.get(path)
    return change.modified_lines if change else frozenset()
