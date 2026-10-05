"""Read a rule corpus from a spreadsheet. Layer A -- names no repository, no framework.

The corpus is authored in a spreadsheet, so the harness reads one. Exporting a CSV first
worked but added a step that can be skipped, and a skipped export means the checker scores
yesterday's corpus while the workbook says something else -- silently, and with no error.

Stdlib only: `.xlsx` is a zip of XML, and the checkers are stdlib-only by invariant.

**What is lost, and why it is accepted.** A spreadsheet does not diff in review, so a
changed rule sentence is invisible in a pull request. Two things cover that: the corpus
carries the sentence into `docs/rule-index.md`, which is generated, tracked and *is* the
review artefact; and `tools/corpus.py --check` fails on a corpus that breaks any convention
the harness depends on.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

DEFAULT_SHEET = "Rules"


def _cells(row: ET.Element, shared: list[str]) -> dict[str, str]:
    """One row, keyed by column letter. Handles shared, inline and literal cells."""
    out: dict[str, str] = {}
    for cell in row.iter(NS + "c"):
        column = "".join(ch for ch in cell.get("r", "") if ch.isalpha())
        kind = cell.get("t")
        if kind == "inlineStr":
            node = cell.find(NS + "is")
            out[column] = "".join(t.text or "" for t in node.iter(NS + "t")) if node is not None else ""
            continue
        value = cell.find(NS + "v")
        if value is None:
            out[column] = ""
        elif kind == "s":
            out[column] = shared[int(value.text)]
        else:
            out[column] = value.text or ""
    return out


def read(path: str | Path, sheet: str = DEFAULT_SHEET) -> list[dict[str, str]]:
    """Rows as dicts keyed by the header row, like ``csv.DictReader`` returns.

    Blank rows are dropped: a spreadsheet almost always carries a few, and they would
    otherwise become corpus entries with no ID.
    """
    path = Path(path)
    with zipfile.ZipFile(path) as archive:
        try:
            shared = [
                "".join(t.text or "" for t in item.iter(NS + "t"))
                for item in ET.fromstring(archive.read("xl/sharedStrings.xml"))
            ]
        except KeyError:
            shared = []
        names = [s.get("name") for s in ET.fromstring(archive.read("xl/workbook.xml")).iter(NS + "sheet")]
        if sheet not in names:
            raise ValueError(f"{path.name}: no sheet named {sheet!r} (has: {names})")
        grid = ET.fromstring(archive.read(f"xl/worksheets/sheet{names.index(sheet) + 1}.xml"))

    rows = [_cells(r, shared) for r in grid.iter(NS + "row")]
    if not rows:
        raise ValueError(f"{path.name}: sheet {sheet!r} is empty")
    header = rows[0]
    return [
        {header.get(col, col): val for col, val in row.items()}
        for row in rows[1:]
        if any(v.strip() for v in row.values())
    ]
