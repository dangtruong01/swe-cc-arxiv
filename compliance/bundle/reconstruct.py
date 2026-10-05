"""base_commit + patch -> the file contents the agent actually left behind.

Phase 3 onward needs this. A diff's three lines of context are not enough to parse
Python: an added block inside a function does not stand alone as a module, so any rule
that reads an AST needs the whole post-patch file.

Two halves, deliberately separated:

* ``base_text`` reads a blob out of a local git cache. This is I/O, and it belongs to
  bundle *building* -- invariant 1 forbids I/O in checkers, not in the builder.
* ``apply_hunks`` is pure: base text plus hunks in, post-patch text out. No repository,
  no subprocess, so it is unit-testable on its own and carries the reconstruction logic.

**One cache per repository, shared by every run.** ``.cache/repos/<slug>`` is cloned once
and read by every instance, condition, model and framework that repository has runs for --
they differ by ``base_commit``, not by repository, and one clone holds every commit. Nothing
is ever checked out and nothing is written to it, so concurrent readers are safe.

The cache is a blobless clone (``--filter=blob:none --no-checkout``) -- roughly 70 MB for a
large project against ~500 MB for a full one.

**Blobs are fetched lazily, so the FIRST read of a file reaches the network.** Measured:
0.60 s for a blob the clone does not have yet, 0.017 s once it does. That is a real
qualification on "scoring is offline" -- it is offline once warm, not offline absolutely.
It is confined to bundle *building*, which is the component allowed I/O; the checkers
themselves never touch it, which is what ``tests/test_purity.py`` pins. A fully offline
cache is one ``git fetch`` away (drop ``--filter``) at roughly seven times the disk.

Reconstruction is optional in the sense that nothing crashes without it: ``head_text`` and
``base_text`` stay ``None`` and the rules that need them report missing evidence rather
than guessing. It is not optional in the sense that matters -- a repository scored with no
cache silently reports an applicability several points low.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Optional

from compliance.core.models import FileChange, Hunk

logger = logging.getLogger("compliance.bundle.reconstruct")

DEFAULT_CACHE = Path(__file__).resolve().parents[2] / ".cache" / "repos"


class ReconstructionError(RuntimeError):
    """The post-patch text could not be rebuilt. Never silently substituted."""


def cache_path(repo: str, root: Optional[Path] = None) -> Path:
    return (root or DEFAULT_CACHE) / repo


def ensure_clone(repo: str, url: Optional[str] = None, root: Optional[Path] = None) -> Path:
    """Create the blobless cache for ``repo`` if it is not already there.

    With no ``url``, it is read from ``rules/<repo>/repo.conf``, so adding a repository
    needs no code change here.
    """
    path = cache_path(repo, root)
    if (path / "HEAD").exists() or (path / ".git").exists():
        return path
    if url is None:
        from compliance.core.registry import repo_conf

        url = repo_conf(repo).get("REPO_URL")
        if not url:
            raise KeyError(f"rules/{repo}/repo.conf does not set REPO_URL")
    path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("cloning %s into %s (blobless)", url, path)
    subprocess.run(
        ["git", "clone", "--filter=blob:none", "--no-checkout", "--quiet", url, str(path)],
        check=True,
        capture_output=True,
    )
    return path


def base_text(repo_dir: Path, commit: str, path: str) -> Optional[str]:
    """The file as it stood at ``commit``, or None if it did not exist there."""
    result = subprocess.run(
        ["git", "-C", str(repo_dir), "show", f"{commit}:{path}"],
        capture_output=True,
        text=True,
        errors="replace",
    )
    return result.stdout if result.returncode == 0 else None


def apply_hunks(base: Optional[str], hunks: tuple[Hunk, ...]) -> str:
    """Rebuild the post-patch text. Pure -- no repository, no subprocess.

    Raises ReconstructionError when a hunk's context does not match the base, which
    means the cache and the run disagree about the base commit. Substituting a
    best-effort result there would put a file the agent never wrote in front of the
    rules.
    """
    base_lines = (base or "").splitlines()
    out: list[str] = []
    cursor = 0  # 0-based index into base_lines

    for hunk in sorted(hunks, key=lambda h: h.old_start):
        # A new file's hunk header is `@@ -0,0 +1,N @@`, so old_start is 0 and the
        # index would be -1. Clamp rather than treat it as an overlap.
        start = max(0, hunk.old_start - 1)
        if start < cursor:
            raise ReconstructionError(f"overlapping hunks at old line {hunk.old_start}")
        out.extend(base_lines[cursor:start])
        cursor = start
        for line in hunk.lines:
            tag, text = line[:1], line[1:]
            if tag == "+":
                out.append(text)
            elif tag == "-":
                if cursor >= len(base_lines) or base_lines[cursor] != text:
                    raise ReconstructionError(
                        f"removed line does not match base at {cursor + 1}: "
                        f"expected {text!r}"
                    )
                cursor += 1
            else:  # context
                if cursor < len(base_lines):
                    # Verify context too, not just removals. Without this a wrong hunk
                    # offset passes silently and produces a file the agent never wrote
                    # -- which would feed a corrupt AST to every rule downstream, and
                    # look like a finding rather than a crash.
                    if text and base_lines[cursor] != text:
                        raise ReconstructionError(
                            f"context does not match base at line {cursor + 1}: "
                            f"expected {text!r}, found {base_lines[cursor]!r}"
                        )
                    out.append(base_lines[cursor])
                    cursor += 1
                else:
                    out.append(text)
    out.extend(base_lines[cursor:])
    return "\n".join(out) + ("\n" if out else "")


def reconstruct_file(
    change: FileChange, repo_dir: Path, commit: str
) -> tuple[Optional[str], Optional[str]]:
    """Return (base_text, head_text) for one changed file."""
    if change.is_binary:
        return None, None
    base = None if change.is_new else base_text(repo_dir, commit, change.old_path or change.path)
    if change.is_deleted:
        return base, None
    if not change.hunks:
        return base, base
    return base, apply_hunks(base, change.hunks)


def reconstruct(
    files: dict[str, FileChange], repo_dir: Path, commit: str
) -> tuple[dict[str, FileChange], list[str]]:
    """Populate head_text/base_text on every changed file.

    Returns the updated mapping and a list of notes describing anything that could not
    be rebuilt, so the bundle records the gap instead of hiding it.
    """
    from dataclasses import replace

    out: dict[str, FileChange] = {}
    notes: list[str] = []
    for path, change in files.items():
        try:
            base, head = reconstruct_file(change, repo_dir, commit)
            out[path] = replace(change, base_text=base, head_text=head)
        except ReconstructionError as exc:
            notes.append(f"could not reconstruct {path}: {exc}")
            out[path] = change
        except (OSError, subprocess.SubprocessError) as exc:  # noqa: PERF203
            notes.append(f"repo cache unusable for {path}: {exc}")
            out[path] = change
    return out, notes
