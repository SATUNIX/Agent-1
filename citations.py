"""
Very light citation DB & renumberer.
"""
import json, pathlib, re

REF = pathlib.Path("docs/_references.json")
REF.parent.mkdir(exist_ok=True)
CITE = re.compile(r"\[\^(\d+)]")


def add_refs(pairs: list[tuple[str, str]]):
    db = _load()
    for title, url in pairs:
        db[url] = title
    _save(db)


def reindex_citations(md: str) -> str:
    mapping, nxt = {}, 1

    def sub(m: re.Match) -> str:
        nonlocal nxt
        old = m.group(1)
        if old not in mapping:
            mapping[old] = str(nxt)
            nxt += 1
        return f"[^{mapping[old]}]"

    return CITE.sub(sub, md)


def _load():
    if REF.exists():
        return json.loads(REF.read_text())
    return {}


def _save(data):
    REF.write_text(json.dumps(data, indent=2))
