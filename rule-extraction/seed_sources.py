#!/usr/bin/env python3
"""
Stage 0 prep. Discovers off-nav rule sources in a repo, pulls them raw, bundles
them into one markdown file to paste into the extraction chat.

Replaces the manual seed list and the curl loop.

    python3 seed_sources.py scikit-learn/scikit-learn
    python3 seed_sources.py django/django --ref main -o django-raw.md
    python3 seed_sources.py sympy/sympy --docs https://docs.sympy.org/dev/

Discovery is by pattern against the real repo tree, so it finds files wherever
they live and catches ones no hardcoded list would have.
"""

import argparse
import base64
import fnmatch
import json
import re
import sys
import urllib.error
import urllib.request

API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"

# Matched against every path in the repo tree.
# role: "rules" produces sheet rows, "context" informs other columns only.
PATTERNS = [
    ("*CONTRIBUTING.md",                    "rules",   "rule source or redirect"),
    ("*CONTRIBUTING.rst",                   "rules",   "rule source or redirect"),
    (".github/PULL_REQUEST_TEMPLATE.md",    "rules",   "obligations hide in HTML comments"),
    (".github/PULL_REQUEST_TEMPLATE/*",     "rules",   "obligations hide in HTML comments"),
    (".github/ISSUE_TEMPLATE/*",            "rules",   "expect X-ISSUE"),
    ("CODE_OF_CONDUCT.md",                  "rules",   "expect X-GOV"),
    ("README.md",                           "context", "check for canonical test invocation"),
    ("README.rst",                          "context", "check for canonical test invocation"),
    (".pre-commit-config.yaml",             "context", "decides the Auto-fix column"),
    (".pre-commit-config.yml",              "context", "decides the Auto-fix column"),
    ("setup.cfg",                           "context", "may hold lint config"),
    ("pyproject.toml",                      "context", "may hold lint config"),
    ("tox.ini",                             "context", "may hold lint config"),
    ("*ai-policy*",                         "rules",   "AI / agent contribution policy"),
    ("*ai_policy*",                         "rules",   "AI / agent contribution policy"),
    ("AGENTS.md",                           "rules",   "agent-directed contribution guidance"),
    ("CLAUDE.md",                           "rules",   "agent-directed contribution guidance"),
    (".github/copilot-instructions.md",     "rules",   "agent-directed contribution guidance"),
    ("*changelog/README*",                  "rules",   "changelog fragment format"),
    ("doc*/whats_new/**README.md",          "rules",   "changelog fragment format"),
    ("doc*/whats_new/*legend*",             "context", "defines fragment types"),
    ("doc*/changes/README*",                "rules",   "changelog fragment format"),
    ("*newsfragments/README*",              "rules",   "changelog fragment format"),
    ("*towncrier*",                         "context", "changelog tooling config"),
]

# Fetched but never bundled. Huge and not rule-bearing.
SKIP = ("*.lock", "*.png", "*.svg", "*.po", "*.mo")

FENCE = {".md": "markdown", ".rst": "rst", ".yml": "yaml", ".yaml": "yaml",
         ".toml": "toml", ".cfg": "ini", ".ini": "ini", ".inc": "rst"}


def get(url, token=None, raw=False):
    req = urllib.request.Request(url, headers={"User-Agent": "seed-sources"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    if not raw:
        req.add_header("Accept", "application/vnd.github+json")
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read()
    return body if raw else json.loads(body)


def resolve_version(docs_url):
    """Read the version the docs alias currently serves.

    Sphinx writes _static/documentation_options.js containing VERSION: '<release>'.
    That is far more reliable than scraping the rendered page, which themes format
    inconsistently or omit entirely.
    """
    root = docs_url if docs_url.endswith("/") else docs_url + "/"
    try:
        js = get(root + "_static/documentation_options.js", raw=True).decode("utf-8", "replace")
        m = re.search(r"VERSION:\s*['\"]([^'\"]+)['\"]", js)
        if m:
            return m.group(1), None
    except Exception:
        pass

    try:
        html = get(docs_url, raw=True).decode("utf-8", "replace")
    except Exception as e:
        return None, f"could not fetch: {e}"
    for pat in (r'"version"\s*:\s*"([^"]+)"',
                r'Version\s*:?\s*</?\w*>?\s*([0-9]+\.[0-9]+[0-9a-z.\-]*)',
                r'version[-_ ]?([0-9]+\.[0-9]+\.[0-9]+(?:\.?dev[0-9]*)?)'):
        m = re.search(pat, html, re.I)
        if m:
            return m.group(1), None
    return None, "no version string in documentation_options.js or page"


# Probed one by one when the tree API is unavailable. Covers GitHub convention
# plus the changelog layouts seen so far. Less thorough than tree discovery:
# it cannot find files in locations nobody anticipated.
PROBE = [
    "CONTRIBUTING.md", "CONTRIBUTING.rst", "docs/CONTRIBUTING.md",
    ".github/CONTRIBUTING.md", ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/bug_report.yml", ".github/ISSUE_TEMPLATE/bug_report.md",
    ".github/ISSUE_TEMPLATE/feature_request.yml", ".github/ISSUE_TEMPLATE/config.yml",
    ".github/ISSUE_TEMPLATE/doc_improvement.yml",
    "CODE_OF_CONDUCT.md", ".github/CODE_OF_CONDUCT.md",
    "AGENTS.md", "CLAUDE.md", ".github/copilot-instructions.md",
    ".github/AI_POLICY.md", "doc/contribute/ai-policy.md", "doc/internals/ai-policy.rst",
    "README.md", "README.rst",
    ".pre-commit-config.yaml", ".pre-commit-config.yml",
    "setup.cfg", "pyproject.toml", "tox.ini",
    "doc/whats_new/upcoming_changes/README.md",
    "doc/whats_new/changelog_legend.inc",
    "docs/releases/README.rst", "doc/changes/README.rst",
    "changelog.d/README.md", "newsfragments/README.rst",
]


def matches(path, pat):
    """Case-insensitive on every OS.

    fnmatch.fnmatch applies os.path.normcase, which lowercases on Windows and not
    on Linux, so the same repo yields different manifests on different machines.
    fnmatchcase on lowered strings pins the behaviour.
    """
    return fnmatch.fnmatchcase(path.lower(), pat.replace("**", "*").lower())


def classify(path):
    for pat, role, why in PATTERNS:
        if matches(path, pat):
            return role, why
    return "context", "matched by probe list"


def discover_by_probe(repo, ref):
    hits = {}
    for path in PROBE:
        req = urllib.request.Request(f"{RAW}/{repo}/{ref}/{path}", method="HEAD",
                                     headers={"User-Agent": "seed-sources"})
        try:
            with urllib.request.urlopen(req, timeout=15):
                hits[path] = classify(path)
        except Exception:
            pass
    return hits


def discover(repo, ref, token):
    try:
        tree = get(f"{API}/repos/{repo}/git/trees/{ref}?recursive=1", token)
    except urllib.error.HTTPError as e:
        if e.code not in (403, 429):
            raise
        print("  ! tree API unavailable (rate limit). Falling back to probe list.",
              file=sys.stderr)
        print("  ! Probe cannot find files in unanticipated locations. Pass --token",
              file=sys.stderr)
        print("  ! for full discovery.", file=sys.stderr)
        return discover_by_probe(repo, ref)

    if tree.get("truncated"):
        print("  ! tree truncated, deep paths may be missed", file=sys.stderr)
    paths = [n["path"] for n in tree["tree"] if n["type"] == "blob"]

    hits = {}
    for path in paths:
        if any(matches(path, s) for s in SKIP):
            continue
        for pat, role, why in PATTERNS:
            # ** should cross directory separators, fnmatch's * already does
            if matches(path, pat):
                if path not in hits:
                    hits[path] = (role, why)
                break
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo", help="org/repo")
    ap.add_argument("--ref", default="main", help="branch or tag, default main")
    ap.add_argument("--docs", help="pinned docs root, checked for version drift")
    ap.add_argument("-o", "--out", help="output file, default <repo>-raw-sources.md")
    ap.add_argument("--token", help="GitHub token, raises the rate limit")
    args = ap.parse_args()

    name = args.repo.split("/")[-1]
    out = args.out or f"{name}-raw-sources.md"

    print(f"Repo:   {args.repo}@{args.ref}")

    version, verr = (None, None)
    if args.docs:
        version, verr = resolve_version(args.docs)
        print(f"Docs:   {args.docs}")
        print(f"Version: {version or 'UNRESOLVED (' + str(verr) + ')'}")
        if args.docs and "/stable/" in args.docs:
            print("  ! /stable/ is a moving alias. Pin /dev/ or an explicit version.",
                  file=sys.stderr)

    ref = args.ref
    try:
        hits = discover(args.repo, ref, args.token)
    except urllib.error.HTTPError as e:
        sys.exit(f"tree fetch failed: {e}. Pass --token.")

    # Repos differ on main vs master. Zero hits almost always means wrong ref,
    # since GitHub convention guarantees at least a README.
    if not hits:
        alt = "master" if ref == "main" else "main"
        print(f"  ! nothing found on '{ref}', retrying '{alt}'", file=sys.stderr)
        try:
            hits = discover(args.repo, alt, args.token)
            if hits:
                ref = alt
        except urllib.error.HTTPError:
            pass

    if not hits:
        sys.exit(f"No sources found on main or master for {args.repo}. Check the repo name.")

    print(f"Ref:    {ref}")
    print(f"Found:  {len(hits)} candidate sources\n")

    blocks, manifest = [], []
    for path, (role, why) in sorted(hits.items()):
        try:
            body = get(f"{RAW}/{args.repo}/{ref}/{path}", raw=True).decode("utf-8", "replace")
        except Exception as e:
            print(f"  FAIL  {path}  ({e})")
            manifest.append((path, role, "FETCH FAILED", why))
            continue

        comments = body.count("<!--")
        flag = ""
        # Only meaningful for markdown templates. In YAML, comments are '#'.
        if path.endswith(".md") and "TEMPLATE" in path.upper() and comments == 0:
            flag = "  <- template with no HTML comments, verify against the raw file"
        print(f"  ok    {path}  ({len(body)} b, {comments} comment blocks){flag}")

        ext = "." + path.rsplit(".", 1)[-1] if "." in path else ""

        # Doc sources under doc/ or docs/ are the input to a rendered page that
        # Stage 0 will also enumerate. Extract from one or the other, never both.
        dup = path.lower().startswith(("doc/", "docs/")) and ext in (".rst", ".md", ".jinja2")
        if dup and "whats_new" not in path.lower() and "changes" not in path.lower():
            why += " | DUPLICATE RISK: source of a rendered doc page, do not extract twice"

        blocks.append(
            f"---\n\n## `{path}`\n\n"
            f"Role: **{role}**. {why}\n\n"
            f"```{FENCE.get(ext, '')}\n{body}\n```\n"
        )
        manifest.append((path, role, "ok", why))

    hdr = [
        f"# {args.repo}: off-nav rule sources (raw, verbatim)",
        "",
        f"Repo: `{args.repo}` @ `{ref}`",
    ]
    if args.docs:
        hdr.append(f"Docs: {args.docs}")
        hdr.append(f"Docs version at pull time: **{version or 'UNRESOLVED'}**")
        hdr.append("")
        hdr.append("Any doc page served on a different version is a fetch failure, not a row.")
    hdr += [
        "",
        "Raw source, HTML comments intact. The rendered GitHub view strips comments,",
        "and in template files the comments carry the actual obligations. Extract from",
        "this text, not from a rendered page.",
        "",
        "Role `context` means the file informs Section context and Auto-fix but never",
        "produces sheet rows.",
        "",
        "| Path | Role | Status | Note |",
        "|---|---|---|---|",
    ]
    hdr += [f"| `{p}` | {r} | {s} | {w} |" for p, r, s, w in manifest]
    hdr.append("")

    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(hdr) + "\n" + "\n".join(blocks))

    print(f"\nWrote {out}")
    print("Paste it into the extraction chat as an attachment before Stage 1.")


if __name__ == "__main__":
    main()
