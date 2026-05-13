from __future__ import annotations

import re

import requests
from bs4 import BeautifulSoup


def search_company_news(company_name: str, max_results: int = 5) -> list[dict]:
    try:
        url = f"https://www.baidu.com/s?wd={requests.utils.quote(company_name)}&rn={max_results}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        for item in soup.select(".result, .c-container")[:max_results]:
            title_el = item.select_one("h3 a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            link = title_el.get("href", "")
            abstract_el = item.select_one(".c-abstract, .content-right_8Zs40")
            abstract = abstract_el.get_text(strip=True) if abstract_el else ""
            results.append({"title": title, "url": link, "abstract": abstract})
        return results
    except Exception:
        return []


def format_news_for_prompt(company_name: str, news: list[dict]) -> str:
    if not news:
        return f"未能找到{company_name}的相关公开信息。"
    lines = [f"关于{company_name}的最新公开信息：\n"]
    for i, item in enumerate(news, 1):
        lines.append(f"{i}. {item['title']}")
        if item.get("abstract"):
            lines.append(f"   {item['abstract']}")
    return "\n".join(lines)
