"""
DuckDuckGo search helper – returns Markdown bullet list.
"""
from duckduckgo_search import DDGS


def ddg_search(query: str, num: int = 5) -> str:
    out = []
    with DDGS() as d:
        for r in d.text(query, max_results=num):
            out.append(f"- [{r['title']}]({r['href']})\n  {r['body']}")
    return "\n".join(out)
