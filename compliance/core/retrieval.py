"""What did the agent actually retrieve?

Layer A: no repository is named here. The set of rule-bearing URLs is passed in, and
comes from the corpus's own Source column, so a second repository needs no code change.

This exists because the report's alerts require it:

    fetch_succeeded = False on a naive run  ->  the run is void, not a low score

Without these metrics a naive run that never read the guidelines is indistinguishable
from one that read them and ignored them, and the two mean opposite things.

Derived purely from ``bundle.commands`` -- the command text and the observation each
one produced -- so it needs no extra capture and works on runs already collected.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Iterable, Optional

from compliance.adapters import load as load_adapter
from compliance.core.models import Command, EvidenceBundle

# `_FETCH` moved to the adapter: which actions reach the network is a property of the
# scaffold. Everything below -- what a URL looks like, what counts as reaching a page --
# is ours and stays here.
_URL = re.compile(r"https?://[^\s'\"|>);]+")
_TO_FILE = re.compile(r">\s*\S+|--output\s+\S+|-o\s+\S+|tee\s+\S+")
_STRIPPER = re.compile(r"HTMLParser|html\.parser|html2text|w3m|lynx|BeautifulSoup|bs4|sed\s+.*<", re.I)
_FILTER = re.compile(r"\b(grep|rg|ag)\b")


@dataclass(frozen=True)
class Retrieval:
    """Everything the bundle can say about the agent's attempt to read the guidelines."""

    n_fetch_attempts: int = 0
    urls_fetched: tuple[str, ...] = ()
    #: rule-bearing pages the agent ASKED for -- read from the command, so a 404 counts
    source_pages_attempted: tuple[str, ...] = ()
    #: rule-bearing pages whose fetch actually returned normative prose
    source_pages_obtained: tuple[str, ...] = ()
    n_source_pages_total: int = 0
    entry_url: Optional[str] = None
    followed_beyond_entry: bool = False
    strategies: tuple[str, ...] = ()
    prose_chars_ingested: int = 0
    step_first_fetch: Optional[int] = None
    step_last_fetch: Optional[int] = None
    n_commands: int = 0

    @property
    def source_pages_reached(self) -> tuple[str, ...]:
        """Deprecated alias for `source_pages_attempted`.

        The old name claimed more than the measurement supported -- it is derived from
        the command string, so it says the agent asked, never that anything came back.
        Kept so stored analyses and older callers keep resolving.
        """
        return self.source_pages_attempted

    @property
    def fetch_succeeded(self) -> bool:
        """Did the agent ATTEMPT a page the rules are drawn from?

        Structural, not a byte threshold. Necessary but nowhere near sufficient: use
        `rules_obtained` for whether the guidelines actually arrived.
        """
        return bool(self.source_pages_attempted)

    @property
    def rules_obtained(self) -> bool:
        """Did the agent end up HOLDING rule-bearing prose?

        This is the measure the open question needs. `fetch_succeeded` counts an agent
        that fired five URLs and collected five 404s; this one does not.
        """
        return bool(self.source_pages_obtained)

    @property
    def coverage(self) -> float:
        """Share of rule-bearing pages ATTEMPTED. See `coverage_obtained`."""
        if not self.n_source_pages_total:
            return 0.0
        return len(self.source_pages_attempted) / self.n_source_pages_total

    @property
    def coverage_obtained(self) -> float:
        """Share of rule-bearing pages whose content actually arrived."""
        if not self.n_source_pages_total:
            return 0.0
        return len(self.source_pages_obtained) / self.n_source_pages_total

    def as_dict(self) -> dict:
        return {
            "n_fetch_attempts": self.n_fetch_attempts,
            "urls_fetched": list(self.urls_fetched),
            "source_pages_attempted": list(self.source_pages_attempted),
            "source_pages_obtained": list(self.source_pages_obtained),
            # legacy key, still emitted so stored analyses and alerts keep resolving
            "source_pages_reached": list(self.source_pages_attempted),
            "rules_obtained": self.rules_obtained,
            "coverage_obtained": round(self.coverage_obtained, 4),
            "n_source_pages_total": self.n_source_pages_total,
            "coverage": round(self.coverage, 4),
            "entry_url": self.entry_url,
            "followed_beyond_entry": self.followed_beyond_entry,
            "strategies": list(self.strategies),
            "prose_chars_ingested": self.prose_chars_ingested,
            "fetch_succeeded": self.fetch_succeeded,
            "step_first_fetch": self.step_first_fetch,
            "step_last_fetch": self.step_last_fetch,
            "n_commands": self.n_commands,
        }


class _Text(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.out: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        self.skip += tag in ("script", "style")

    def handle_endtag(self, tag):
        self.skip -= tag in ("script", "style")

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.out.append(data.strip())


def visible_prose(text: str, adapter: Optional[object] = None) -> str:
    """The part of an observation a reader would actually take meaning from.

    Strips the harness's own wrapper tags first, then any HTML the command returned.
    Which tags those are is the scaffold's business, so the pattern comes from the
    adapter; stripping HTML afterwards is ours and stays here.
    """
    adapter = adapter or load_adapter()
    text = adapter.WRAPPER_TAGS.sub(" ", text)
    parser = _Text()
    parser.feed(text)
    return re.sub(r"\s+", " ", " ".join(parser.out)).strip()


# --- did a fetch actually come back with rules? --------------------------------------
#
# `source_pages_attempted` says the agent ASKED for a rule-bearing URL. It cannot say the
# request succeeded: the URL is read out of the command string, so a 404, a DNS failure and
# a full page all score identically. Measured across one repository's corpus, 27 of 57
# attempts returned nothing but navigation chrome, page titles or "Page Not Found" -- so
# reporting attempts as though they were acquisitions overstated retrieval by roughly 2x.
#
# The distinction matters because the open question (findings F1/F13) is whether agents END
# UP HOLDING the guidelines, not whether they typed a URL. An agent that fires five
# candidate URLs and eats five 404s must not outrank one that fetches a single page.

# Chrome a generated documentation page carries whether or not the fetch returned content.
_CHROME = re.compile(
    r"Contents Menu Expand|Light mode|Dark mode|Auto light/dark|Skip to content|"
    r"Page Not Found|Table of Contents|Back to top|Toggle .{0,20}navigation|"
    r"On this page|previous\s+next", re.I)

# Language that only appears in normative prose, never in a title or a nav bar.
_NORMATIVE = re.compile(
    r"\b(must|should|do not|don't|never|always|required?|requires|ensure|"
    r"pull request|docstring|doctest|commit message|test suite)\b", re.I)

# A page counts as OBTAINED when its own fetch returned this much prose after chrome is
# removed, carrying at least this many normative markers. Both thresholds are deliberately
# conservative: the cost of a false positive here is reporting retrieval that did not
# happen, which is the exact error this measure exists to remove. The entry page's table of
# contents -- 644 chars of real documentation containing no rules -- must not pass.
_OBTAINED_MIN_CHARS = 1500
_OBTAINED_MIN_NORMATIVE = 5


def _carries_rules(prose: str) -> bool:
    """Is this observation normative documentation, rather than chrome or a title?"""
    if not prose:
        return False
    clean = _CHROME.sub(" ", prose)
    return (len(clean) >= _OBTAINED_MIN_CHARS
            and len(_NORMATIVE.findall(clean)) >= _OBTAINED_MIN_NORMATIVE)


# `curl -o file` puts the page on disk and NOTHING in the observation, so pairing a fetch
# with its own output would score a competent agent zero. The path it wrote is recoverable
# from the command, and whatever later command reads that path carries the prose.
_OUT_PATH = re.compile(r"(?:-o|--output|>)\s+([^\s;|&<>]+)")


def _strategy(command: str) -> str:
    if _STRIPPER.search(command):
        return "stripped"
    if _FILTER.search(command):
        return "filtered"
    if _TO_FILE.search(command):
        return "to_file"
    return "raw"


# Names too generic to identify a page on their own.
_GENERIC = {"index.html", "index", "index.htm", "", "docs", "contributing"}


def _page_keys(url: str) -> tuple[str, ...]:
    """Distinctive tails of a URL path, longest first.

    Matching on these rather than the whole URL is what lets us see pages an agent
    assembled at runtime. A bash array of basenames looped over a $URL_BASE never puts
    a full URL in the command text, so a competent agent that scripts its retrieval
    would otherwise score zero -- the metric would be biased against exactly the
    behaviour we are trying to detect.

    The bare basename is included only when it is distinctive: `docstring.html` names
    one page, `index.html` names dozens.
    """
    path = re.sub(r"^https?://[^/]+/", "", url.rstrip("/"))
    parts = [p for p in path.split("/") if p]
    if not parts:
        return ()
    keys = ["/".join(parts[-2:])] if len(parts) >= 2 else []
    if parts[-1].lower() not in _GENERIC:
        keys.append(parts[-1])
    return tuple(dict.fromkeys(keys))


def analyse(
    bundle: EvidenceBundle,
    source_urls: Iterable[str] = (),
    entry_url: Optional[str] = None,
    adapter: Optional[object] = None,
) -> Retrieval:
    """Summarise the agent's retrieval behaviour.

    ``source_urls`` are the pages the corpus draws its rules from, so "coverage" means
    the fraction of rule-bearing pages the agent actually opened -- not the fraction of
    the web it visited.

    ``adapter`` supplies which actions reach the network. Defaults to the framework the
    bundle itself records, so a run scored straight out of ``runs/`` reads its own
    scaffold's vocabulary without the caller having to know one was involved. Under a
    scaffold with a browser tool "fetching" is not a shell verb at all, and the default
    that once said "the framework every stored run used" silently became wrong the moment
    a second framework existed.
    """
    adapter = adapter or load_adapter(bundle.framework)
    sources = {u.rstrip("/") for u in source_urls}
    # page-key -> canonical url, so a page counts however the agent addressed it
    by_key = {k: u.rstrip("/") for u in sources for k in _page_keys(u)}
    entry = entry_url or bundle.probe.get("docs_url") or None

    urls: list[str] = []
    strategies: list[str] = []
    attempted: set[str] = set()
    obtained: set[str] = set()
    prose = 0
    first = last = None

    # Text an agent parked on disk with `curl -o`, keyed by the path it wrote. Whatever
    # later command reads that path supplies the prose the fetch itself never showed.
    deferred: dict[str, set[str]] = {}
    commands = list(bundle.commands)

    for position, command in enumerate(commands):
        if not adapter.FETCH_ACTIONS.search(command.command):
            continue
        first = command.index if first is None else first
        last = command.index
        strategies.append(_strategy(command.command))

        # Which rule-bearing pages did THIS command ask for?
        here: set[str] = set()
        for url in _URL.findall(command.command):
            url = url.rstrip("/")
            urls.append(url)
            if url in sources:
                here.add(url)
        # Also credit pages named without a full URL: path fragments assembled at
        # runtime, bash arrays, loops over a base URL.
        for key, canonical in by_key.items():
            if key and key in command.command:
                here.add(canonical)
        attempted |= here

        # ...and did THIS command's own output bring rules back? Pairing the request with
        # its own observation is the whole point: summing prose across the cell cannot
        # tell a page that answered from one that 404'd beside a page that answered.
        body = visible_prose(command.output, adapter)
        prose += len(body)
        if here and _carries_rules(body):
            obtained |= here

        # A fetch that wrote to disk shows nothing now. Remember the path so a later read
        # of it can settle the question.
        if here and not _carries_rules(body):
            for path in _OUT_PATH.findall(command.command):
                deferred.setdefault(path.strip("\"'"), set()).update(here)

    # Second pass: any command naming a deferred path, whose output carries rules, closes
    # out the pages that fetch wrote there.
    if deferred:
        for command in commands:
            for path, pages in deferred.items():
                if path and path in command.command and pages - obtained:
                    if _carries_rules(visible_prose(command.output, adapter)):
                        obtained |= pages

    return Retrieval(
        n_fetch_attempts=len(strategies),
        urls_fetched=tuple(dict.fromkeys(urls)),
        source_pages_attempted=tuple(sorted(attempted)),
        source_pages_obtained=tuple(sorted(obtained)),
        n_source_pages_total=len(sources),
        entry_url=entry,
        followed_beyond_entry=any(u != (entry or "").rstrip("/") for u in urls),
        strategies=tuple(dict.fromkeys(strategies)),
        prose_chars_ingested=prose,
        step_first_fetch=first,
        step_last_fetch=last,
        n_commands=len(bundle.commands),
    )


def source_urls_from_corpus(corpus: dict) -> list[str]:
    """The distinct pages a repo's rules were extracted from, in stable order."""
    urls = []
    for rule in corpus.values():
        url = (getattr(rule, "source", "") or "").split(" | ")[0].strip()
        if url.startswith("http") and url not in urls:
            urls.append(url)
    return sorted(urls)


# --- guided arm: was the mounted rules file actually opened? ------------------------
#
# The naive arm's failure was that the treatment was available but never consumed. The
# guided arm can fail the same way: the rules are mounted as a file, and the agent still
# has to open it. Without this, "had the rules and ignored them" and "never looked at the
# rules" produce the same compliance score and support opposite conclusions.

DEFAULT_RULES_PATH = "/rules/CONTRIBUTING_RULES.md"

# Which actions count as *reading* a file is a property of the scaffold, not of this
# module: a bash agent runs `cat`, a tool-using agent opens an editor view. The vocabulary
# therefore lives in the framework's adapter (Layer D) and is looked up per bundle.
#
# This is the subtlest framework coupling in the codebase, because getting it wrong does
# not raise -- it reports `opened=False`, and "had the rules and ignored them" becomes
# indistinguishable from "never looked at the rules", which is the exact confusion this
# module exists to prevent.


@dataclass(frozen=True)
class RulesFileAccess:
    """Whether the guided treatment was consumed, and how much of it."""

    path: str = DEFAULT_RULES_PATH
    present: bool = False
    n_reads: int = 0
    first_read_step: Optional[int] = None
    last_read_step: Optional[int] = None
    chars_ingested: int = 0
    max_single_read: int = 0
    truncated_reads: int = 0
    file_chars: int = 0
    strategies: tuple[str, ...] = ()
    read_commands: tuple[str, ...] = ()
    n_commands: int = 0

    @property
    def opened(self) -> bool:
        """Did any of the file's content reach the agent's context?"""
        return self.n_reads > 0 and self.chars_ingested > 0

    @property
    def re_read(self) -> bool:
        """Did the agent come back to it, or read once and move on?"""
        return self.n_reads > 1

    @property
    def coverage(self) -> float:
        """Fraction of the file that reached the context.

        Summed across reads, so re-reads of the same section can overlap; treat it as an
        upper bound on how much was seen, not an exact figure.
        """
        if not self.file_chars:
            return 0.0
        return min(1.0, self.chars_ingested / self.file_chars)

    def as_dict(self) -> dict:
        return {
            "path": self.path,
            "present": self.present,
            "opened": self.opened,
            "n_reads": self.n_reads,
            "re_read": self.re_read,
            "first_read_step": self.first_read_step,
            "last_read_step": self.last_read_step,
            "chars_ingested": self.chars_ingested,
            "max_single_read": self.max_single_read,
            "truncated_reads": self.truncated_reads,
            "file_chars": self.file_chars,
            "coverage": round(self.coverage, 4),
            "strategies": list(self.strategies),
            "read_commands": list(self.read_commands),
            "n_commands": self.n_commands,
        }


def analyse_rules_file(
    bundle: EvidenceBundle,
    path: Optional[str] = None,
    adapter: Optional[object] = None,
) -> RulesFileAccess:
    """Did the agent open the mounted rules file, when, how much, and more than once?

    ``adapter`` supplies the framework's read vocabulary and its observation wrapper.
    Defaults to the framework the bundle records; pass it explicitly only for a
    trajectory being read outside ``runs/``, where nothing knows which scaffold wrote it.
    """
    adapter = adapter or load_adapter(bundle.framework)
    path = path or bundle.probe.get("rules_file_path") or DEFAULT_RULES_PATH
    # Matched on the FILENAME as well as the full path. An agent that `cd`s first and then
    # reads a relative path has read the file just as surely as one that spelled it out,
    # and matching only the absolute path reports `n_reads=0` on a run that read the whole
    # thing -- "never opened it", which is indistinguishable from ignoring the treatment
    # and is the single most damaging false negative this module can produce.
    #
    # Observed: one model ran
    #     cd /workspace && ... && cat .compliance/rules/CONTRIBUTING_RULES.md
    # and was recorded as never having opened a file it read in full, 19375 chars of it.
    #
    # The filename is distinctive enough to carry the match on its own -- it is ours, not
    # the repository's, and nothing else in a run is called CONTRIBUTING_RULES.md.
    basename = path.rsplit("/", 1)[-1]
    present = (bundle.probe.get("rules_file_present") or "").lower() == "yes"
    try:
        file_chars = int(bundle.probe.get("rules_file_chars") or 0)
    except ValueError:
        file_chars = 0

    reads, strategies, commands = [], [], []
    ingested = biggest = truncated = 0
    for command in bundle.commands:
        names = (path, basename) if basename else (path,)
        if not any(n in command.command for n in names):
            continue
        matched = [name for name, pattern in adapter.READ_STRATEGIES
                   if pattern.search(command.command)]
        # METADATA_ONLY suppresses `ls`/`stat`/`find` -- actions that name a path without
        # conveying it -- but it is anchored at the START of the command, and agents chain.
        # Checking it BEFORE the read verbs meant
        #     find /rules -name "*.md" | head -5 && cat /rules/CONTRIBUTING_RULES.md
        # was discarded on its leading `find` while its `cat` returned 6882 characters of
        # the file. A command that conveys the file is a read whatever it did first, so
        # the metadata rule now only applies when nothing in it reads.
        if not matched:
            continue
        payload = adapter.observation_payload(command.output)
        reads.append(command.index)
        strategies.extend(matched)
        commands.append(command.command.strip()[:160])
        ingested += len(payload)
        biggest = max(biggest, len(payload))
        truncated += adapter.was_truncated(command.output)

    return RulesFileAccess(
        path=path,
        present=present,
        n_reads=len(reads),
        first_read_step=reads[0] if reads else None,
        last_read_step=reads[-1] if reads else None,
        chars_ingested=ingested,
        max_single_read=biggest,
        truncated_reads=truncated,
        file_chars=file_chars,
        strategies=tuple(dict.fromkeys(strategies)),
        read_commands=tuple(commands),
        n_commands=len(bundle.commands),
    )
