"""
WriterAgent – drafts Markdown, fills TODOs, renumbers citations.
Retries once (300-s timeout) on Ollama calls.
"""
import pathlib, re, os, requests, time
from search_tool import ddg_search
from citations import add_refs, reindex_citations
import git_helper

DOCS = pathlib.Path("docs")
DOCS.mkdir(exist_ok=True)


class WriterAgent:
    model = os.getenv("WRITER_MODEL", "deepseek-r1:7b")
    api = os.getenv("OLLAMA_API", "http://localhost:11434/api/generate")

    # ──────────────────────────────────────────────────────────────────────
    def generate_document(self, instruction: str) -> str:
        md = self._llm_with_retry(f"Write a thorough Markdown document:\n{instruction}")
        md = self._fill_todos(md)
        self._save(md)
        git_helper.commit_all(f"docs: {instruction[:60]}")
        return md

    # ──────────────────────────────────────────────────────────────────────
    def _llm_with_retry(self, prompt: str) -> str:
        body = {"model": self.model, "prompt": prompt, "stream": False}
        for attempt in (1, 2):
            try:
                r = requests.post(self.api, json=body, timeout=300)
                r.raise_for_status()
                return r.json()["response"]
            except requests.Timeout:
                if attempt == 1:
                    print("Writer LLM timed out – retrying once…")
                    time.sleep(1)
                    continue
                raise

    # ──────────────────────────────────────────────────────────────────────
    def _fill_todos(self, md: str) -> str:
        if "TODO:" not in md:
            return md
        for q in re.findall(r"TODO:\s*(.+)", md):
            bullets = ddg_search(q, 5)
            md = md.replace(f"TODO: {q}", bullets)
            add_refs(re.findall(r"\[([^\]]+)]\((http[^\)]+)\)", bullets))
        return reindex_citations(md)

    def _save(self, md: str):
        h1 = next((l for l in md.splitlines() if l.startswith("# ")), "# index")
        slug = re.sub(r"\W+", "_", h1[2:].strip()).lower() or "index"
        (DOCS / f"{slug}.md").write_text(md, encoding="utf-8")
