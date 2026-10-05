"""R1 -- retrieval metrics, and the separation between probe output and experimental data."""

from __future__ import annotations

from pathlib import Path

from conftest import RUNS, TRAJ_PHASE0, make_bundle

from compliance.bundle.builder import build_bundle
from compliance.core.models import Command
from compliance.core.paths import discover
from compliance.core.registry import corpus_path_for, load_corpus
from compliance.core.retrieval import analyse, source_urls_from_corpus, visible_prose

SOURCES = ["https://docs.example.org/contributing/tests.html",
           "https://docs.example.org/contributing/style.html"]
ENTRY = "https://docs.example.org/contributing/index.html"


def cmds(*pairs):
    return tuple(Command(index=i, command=c, output=o) for i, (c, o) in enumerate(pairs))


def test_no_fetch_at_all_is_not_success():
    r = analyse(make_bundle(commands=cmds(("ls -la", "a b c"))), SOURCES, ENTRY)
    assert r.n_fetch_attempts == 0 and not r.fetch_succeeded and r.coverage == 0.0


def test_reading_only_the_index_is_not_success():
    """The entry page is a table of contents. It is real documentation and contains no
    rules, so an agent that reads only it has retrieved nothing to comply with."""
    r = analyse(make_bundle(commands=cmds((f"curl {ENTRY}", "<p>Contents</p>"))), SOURCES, ENTRY)
    assert r.n_fetch_attempts == 1
    assert r.prose_chars_ingested > 0        # it did read something
    assert not r.fetch_succeeded             # but nothing rule-bearing
    assert not r.followed_beyond_entry


def test_reaching_a_rule_page_is_success():
    r = analyse(make_bundle(commands=cmds((f"curl {SOURCES[0]}", "<p>Tests must pass.</p>"))),
                SOURCES, ENTRY)
    assert r.fetch_succeeded and r.coverage == 0.5
    assert r.followed_beyond_entry


def test_strategy_detection():
    for command, expected in [
        (f"curl {ENTRY}", "raw"),
        (f"curl -s {ENTRY} > /tmp/d.html", "to_file"),
        (f"curl -s {ENTRY} | python -c 'from html.parser import HTMLParser'", "stripped"),
        (f"curl -s {ENTRY} | grep -i contributing", "filtered"),
    ]:
        r = analyse(make_bundle(commands=cmds((command, ""))), SOURCES, ENTRY)
        assert r.strategies == (expected,), f"{command!r} -> {r.strategies}"


def test_visible_prose_ignores_harness_wrapper_and_markup():
    obs = "<returncode>0</returncode><output><p>All new functionality should be tested.</p></output>"
    assert visible_prose(obs) == "0 All new functionality should be tested."


def test_corpus_source_urls_are_the_rule_bearing_pages():
    urls = source_urls_from_corpus(load_corpus(corpus_path_for("sympy")))
    assert len(urls) >= 10 and all(u.startswith("http") for u in urls)


def test_the_live_naive_run_is_flagged_void():
    """The first live naive run fetched once, got a table of contents, and stopped.
    Plan §6: that run is void, not a low compliance score."""
    bundle = build_bundle(TRAJ_PHASE0)
    r = analyse(bundle, source_urls_from_corpus(load_corpus(corpus_path_for("sympy"))))
    assert r.n_fetch_attempts == 1
    assert r.source_pages_reached == ()
    assert not r.fetch_succeeded
    assert not r.followed_beyond_entry


def test_probe_output_never_enters_the_experimental_corpus():
    """E1b is methodology, not data. discover() must not pick it up."""
    probe_dir = Path(__file__).resolve().parents[1] / "experiments" / "retrieval" / "results"
    for run in discover(root=RUNS):
        assert probe_dir not in run.path.parents, f"probe output leaked into runs/: {run.path}"
    assert all("experiments" not in str(run.path) for run in discover(root=RUNS))


# --- guided arm: rules-file access -------------------------------------------------

from compliance.core.retrieval import DEFAULT_RULES_PATH, analyse_rules_file  # noqa: E402

RULES_PROBE = {"rules_file_present": "yes", "rules_file_chars": "17528",
               "rules_file_path": DEFAULT_RULES_PATH}


def obs(payload, truncated=False):
    if truncated:
        half = len(payload) // 2
        return (f"<returncode>0</returncode><output_head>\n{payload[:half]}\n</output_head>"
                f"<elided_chars>999 characters elided</elided_chars>"
                f"<output_tail>\n{payload[half:]}\n</output_tail>")
    return f"<returncode>0</returncode>\n<output>\n{payload}\n</output>"


def test_guided_run_that_never_opens_the_file_is_not_opened():
    """The failure mode that makes a guided run void, exactly as naive was."""
    bundle = make_bundle(condition="guided", probe=RULES_PROBE,
                         commands=cmds(("ls -la /rules/", "CONTRIBUTING_RULES.md"),
                                       ("cat sympy/core/mod.py", "code")))
    g = analyse_rules_file(bundle)
    assert g.present and not g.opened and g.n_reads == 0


def test_listing_the_file_is_not_opening_it():
    """ls/stat/wc touch the file but convey none of its content."""
    for command in (f"ls -l {DEFAULT_RULES_PATH}", f"wc -l {DEFAULT_RULES_PATH}",
                    f"stat {DEFAULT_RULES_PATH}"):
        bundle = make_bundle(condition="guided", probe=RULES_PROBE,
                             commands=cmds((command, "166")))
        assert not analyse_rules_file(bundle).opened, command


def test_reading_the_file_is_detected_with_its_strategy():
    for command, expected in [
        (f"cat {DEFAULT_RULES_PATH}", "cat"),
        (f"head -n 60 {DEFAULT_RULES_PATH}", "head_tail"),
        (f"grep -n '##' {DEFAULT_RULES_PATH}", "grep"),
        (f"sed -n '1,80p' {DEFAULT_RULES_PATH}", "sed_awk"),
        (f"python -c \"print(open('{DEFAULT_RULES_PATH}').read())\"", "python"),
    ]:
        g = analyse_rules_file(make_bundle(condition="guided", probe=RULES_PROBE,
                                           commands=cmds((command, obs("rule text")))))
        assert g.opened and expected in g.strategies, command


def test_coverage_and_truncation_are_measured():
    """The file is 17,528 chars against a 10,000-char window, so a bare cat is truncated."""
    payload = "x" * 10000
    g = analyse_rules_file(make_bundle(
        condition="guided", probe=RULES_PROBE,
        commands=cmds((f"cat {DEFAULT_RULES_PATH}", obs(payload, truncated=True)))))
    assert g.opened and g.truncated_reads == 1
    assert 0.5 < g.coverage < 0.65, g.coverage       # ~57% of the file


def test_re_reading_is_distinguished_from_reading_once():
    once = make_bundle(condition="guided", probe=RULES_PROBE,
                       commands=cmds((f"cat {DEFAULT_RULES_PATH}", obs("a"))))
    twice = make_bundle(condition="guided", probe=RULES_PROBE,
                        commands=cmds((f"cat {DEFAULT_RULES_PATH}", obs("a")),
                                      ("ls", "x"),
                                      (f"grep commit {DEFAULT_RULES_PATH}", obs("b"))))
    assert not analyse_rules_file(once).re_read
    g = analyse_rules_file(twice)
    assert g.re_read and g.n_reads == 2 and g.first_read_step == 0 and g.last_read_step == 2


def test_absent_mount_is_reported_as_not_present():
    g = analyse_rules_file(make_bundle(condition="guided", probe={"rules_file_present": "no"}))
    assert not g.present and not g.opened


def test_a_relative_path_read_still_counts():
    """`cd` then read is a read.

    Matching only the absolute path from the probe reported `n_reads=0` on a run that had
    read the whole file -- one model ran
    `cd /workspace && cat .compliance/rules/CONTRIBUTING_RULES.md` and 19375 chars came
    back. "Never opened it" is indistinguishable from ignoring the treatment, which makes
    this the most damaging false negative the module can produce.
    """
    from compliance.core.retrieval import analyse_rules_file
    from compliance.core.models import Command, EvidenceBundle
    absolute = "/workspace/.compliance/rules/CONTRIBUTING_RULES.md"
    bundle = EvidenceBundle(
        instance_id="sympy__sympy-1", base_commit="", created_at="", condition="guided",
        model="m", files={}, commits=(), pr_text=None,
        commands=(Command(index=0, output="rule text " * 50, returncode=0,
                          command="cd /workspace && cat .compliance/rules/CONTRIBUTING_RULES.md"),),
        probe={"rules_file_path": absolute, "rules_file_present": "yes",
               "rules_file_chars": "500"},
    )
    access = analyse_rules_file(bundle)
    assert access.n_reads == 1, "a relative-path read of the rules file must count"


def test_a_chained_find_then_cat_is_a_read():
    """`METADATA_ONLY` is anchored at the start of the command, and agents chain.

    One stored run did
        find /rules -name "*.md" | head -5 && cat /rules/CONTRIBUTING_RULES.md
    and was discarded on its leading `find` while the `cat` returned 6882 characters of
    the file. A command that conveys the file is a read whatever it did first.
    """
    from compliance.core.retrieval import analyse_rules_file
    from compliance.core.models import Command, EvidenceBundle
    path = "/rules/CONTRIBUTING_RULES.md"
    bundle = EvidenceBundle(
        instance_id="x__x-1", base_commit="", created_at="", condition="guided",
        model="m", files={}, commits=(), pr_text=None,
        commands=(Command(index=0, output="rule text " * 40, returncode=0,
                          command=f'find /rules -name "*.md" | head -5 && cat {path}'),),
        probe={"rules_file_path": path, "rules_file_present": "yes",
               "rules_file_chars": "400"},
    )
    assert analyse_rules_file(bundle).n_reads == 1


def test_a_bare_listing_is_still_not_a_read():
    """The exclusion must survive: naming a path conveys none of it."""
    from compliance.core.retrieval import analyse_rules_file
    from compliance.core.models import Command, EvidenceBundle
    path = "/rules/CONTRIBUTING_RULES.md"
    bundle = EvidenceBundle(
        instance_id="x__x-1", base_commit="", created_at="", condition="guided",
        model="m", files={}, commits=(), pr_text=None,
        commands=(Command(index=0, output="-rw-r--r-- 1 root root 17561", returncode=0,
                          command=f"ls -la {path}"),),
        probe={"rules_file_path": path, "rules_file_present": "yes",
               "rules_file_chars": "400"},
    )
    assert analyse_rules_file(bundle).n_reads == 0
