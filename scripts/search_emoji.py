#!/usr/bin/env python3
"""Return Alfred Script Filter items for the bundled Emoji catalogue."""

import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


ROOT_DIR = Path(__file__).resolve().parents[1]
CATALOGUE_PATH = ROOT_DIR / "resources" / "emoji.json"
MAX_RESULTS = 50
QUESTION_MARKS = ("❓", "❔", "⁉️")

# A small semantic bridge lets a Chinese word search the same catalogue that
# serves English names and aliases. Symbols are deliberately included too.
QUERY_ALIASES: Dict[str, Tuple[str, ...]] = {
    "问号": ("question",),
    "？": ("question",),
    "?": ("question",),
    "感叹号": ("exclamation",),
    "！": ("exclamation",),
    "!": ("exclamation",),
    "笑": ("smile", "laugh"),
    "微笑": ("smile",),
    "开心": ("happy", "smile"),
    "哭": ("cry", "tear"),
    "难过": ("sad",),
    "生气": ("angry", "rage"),
    "爱": ("love", "heart"),
    "心": ("heart",),
    "火": ("fire",),
    "星星": ("star",),
    "太阳": ("sun",),
    "月亮": ("moon",),
    "猫": ("cat",),
    "狗": ("dog",),
    "咖啡": ("coffee",),
    "啤酒": ("beer",),
    "音乐": ("music",),
    "派对": ("party",),
    "庆祝": ("celebration", "party"),
    "火箭": ("rocket",),
    "汽车": ("car",),
    "飞机": ("airplane", "flight"),
    "电话": ("phone", "telephone"),
    "电脑": ("computer", "laptop"),
    "书": ("book",),
    "礼物": ("gift",),
    "花": ("flower",),
    "勾": ("check",),
    "对勾": ("check",),
    "叉": ("cross",),
    "警告": ("warning",),
}


def normalized(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def load_catalogue() -> List[dict]:
    with CATALOGUE_PATH.open(encoding="utf-8") as catalogue_file:
        records = json.load(catalogue_file)["emoji"]

    seen = set()
    unique_records = []
    for record in records:
        symbol = record["s"]
        if symbol not in seen:
            unique_records.append(record)
            seen.add(symbol)
    return unique_records


def search_terms(query: str) -> Tuple[str, ...]:
    query = normalized(query)
    return QUERY_ALIASES.get(query, (query,))


def searchable_fields(record: dict) -> Tuple[str, ...]:
    return tuple(
        normalized(value)
        for value in [record["n"], *record.get("a", []), *record.get("k", [])]
        if value
    )


def score_record(record: dict, terms: Sequence[str]) -> int:
    fields = searchable_fields(record)
    score = 0
    for term in terms:
        if not term:
            continue
        if term == normalized(record["n"]):
            score += 100
        elif term in {normalized(alias) for alias in record.get("a", [])}:
            score += 90
        elif term in fields:
            score += 80
        elif term in normalized(record["n"]):
            score += 60
        elif any(term in field for field in fields):
            score += 40
        else:
            return 0
    return score


def search_catalogue(query: str, records: Iterable[dict]) -> List[dict]:
    records = list(records)
    normalized_query = normalized(query)
    by_symbol = {record["s"]: record for record in records}

    if normalized_query in {"问号", "?", "？"}:
        return [by_symbol[symbol] for symbol in QUESTION_MARKS if symbol in by_symbol]

    terms = search_terms(query)
    ranked = []
    for position, record in enumerate(records):
        score = score_record(record, terms) if normalized_query else 1
        if score:
            ranked.append((-score, position, record))
    ranked.sort()
    return [record for _, _, record in ranked[:MAX_RESULTS]]


def display_item(record: dict) -> dict:
    symbol = record["s"]
    name = record["n"].title()
    return {
        "uid": symbol,
        "title": "{}  {}".format(symbol, name),
        "subtitle": "Press Return to copy {}".format(symbol),
        "arg": symbol,
        "valid": True,
        "text": {"copy": symbol, "largetype": symbol},
    }


def main() -> None:
    query = sys.argv[1] if len(sys.argv) > 1 else ""
    records = load_catalogue()
    payload = {"items": [display_item(record) for record in search_catalogue(query, records)]}
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
