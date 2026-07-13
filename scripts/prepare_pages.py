#!/usr/bin/env python3
"""ページ生成の下ごしらえスクリプト（汎用ローダー）。

画像は生成しません。指定ページについて、
  - 登場キャラ／場所に対応する「参照画像の候補」を名簿から探す
  - 完成画像の保存先パスを表示する
だけを行います。最終判断（どの画像を使うか）はAIが名簿とYAML本文を見て決めます。

対応表（誰がどの画像か）はコードに書かず、すべて characters.yaml / locations.yaml に置きます。
新しい作品でも、このスクリプトは編集不要です。

使い方:
    python3 scripts/prepare_pages.py "step6_yaml生成/第1章_〇〇/作品名_step6_ch1_p01-05.yaml" p01-03
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    yaml = None

# このファイルは scripts/ にあるので、親が作品フォルダのルート
ROOT = Path(__file__).resolve().parents[1]

# 参照画像が無くてよい注記（影・声・画面外など）
SKIP_NOTES = ("声のみ", "画面外", "気配のみ", "影のみ", "後ろ姿のみ", "手のみ", "シルエット", "モノローグのみ")


def load_yaml(path: Path) -> Any:
    if yaml is None:
        raise SystemExit("PyYAML が必要です。Codex から実行してください。")
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_config() -> dict[str, Any]:
    cfg_path = ROOT / "config.yaml"
    return load_yaml(cfg_path) if cfg_path.exists() else {}


def load_roster(filename: str, top_key: str) -> list[dict[str, Any]]:
    path = ROOT / filename
    if not path.exists():
        return []
    data = load_yaml(path) or {}
    return data.get(top_key, []) or []


def parse_page_spec(spec: str) -> set[int]:
    spec = spec.lower().replace("〜", "-").replace("～", "-").replace(" ", "").replace("p", "")
    pages: set[int] = set()
    for part in spec.split(","):
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            pages.update(range(int(a), int(b) + 1))
        else:
            pages.add(int(part))
    return pages


def entry_terms(entry: dict[str, Any]) -> list[str]:
    """名簿1件の照合語（key / name / aliases）を集める。"""
    terms: list[str] = []
    for field in ("name", "key"):
        val = entry.get(field)
        if val:
            terms.append(str(val))
    terms.extend(str(a) for a in entry.get("aliases", []) if a)
    return [t for t in terms if t]


def match_entry(text: str, roster: list[dict[str, Any]]) -> dict[str, Any] | None:
    """テキストに名簿の照合語が含まれていれば、その名簿エントリを返す。"""
    for entry in roster:
        for term in entry_terms(entry):
            if term and term in text:
                return entry
    return None


def pick_sheets(entry: dict[str, Any], tone: str, locations: str) -> list[str]:
    """基本シート＋（あれば）文脈に合う variants のシートを候補として返す。"""
    sheets: list[str] = list(entry.get("sheets", []) or [])
    variants = entry.get("variants") or []
    matched: list[str] = []
    for v in variants:
        tone_hit = any(t in tone for t in v.get("when_tone", []))
        loc_hit = any(l in locations for l in v.get("when_location", []))
        if tone_hit or loc_hit:
            matched.extend(v.get("sheets", []) or [])
    if matched:
        sheets = sheets + matched
    else:
        # 文脈で絞れない場合は variants の全候補を提示し、判断はAIに委ねる
        for v in variants:
            sheets.extend(v.get("sheets", []) or [])
    # 重複除去（順序維持）
    seen: set[str] = set()
    return [s for s in sheets if not (s in seen or seen.add(s))]


def page_chars_and_locs(page: dict[str, Any]) -> tuple[list[str], str]:
    char_names: list[str] = []
    loc_parts: list[str] = []
    for panel in page.get("panels", []):
        for char in panel.get("characters_in_panel", []):
            name = str(char.get("name", ""))
            if name and not any(skip in name for skip in SKIP_NOTES):
                char_names.append(name)
        for key in ("location", "background_details", "scene_description"):
            if panel.get(key):
                loc_parts.append(str(panel[key]))
    return char_names, "\n".join(loc_parts)


def chapter_folder_and_key(yaml_path: Path) -> tuple[str, str]:
    folder = yaml_path.parent.name
    m = re.search(r"第(\d+)章", folder)
    return folder, (f"ch{int(m.group(1))}" if m else "ch")


def extract_page_number(page: dict[str, Any]) -> int:
    """page_number は本来プレーンな整数だが、AI生成YAMLで `1章-1` や `page_id: ch1_p01`
    のような表記ゆれが起きることがあるため、数字を頑健に拾う。"""
    raw_id = page.get("page_id")
    if raw_id:
        m = re.search(r"p0*(\d+)", str(raw_id), re.IGNORECASE)
        if m:
            return int(m.group(1))

    raw = page.get("page_number")
    if isinstance(raw, int):
        return raw
    if isinstance(raw, str):
        m = re.search(r"章[-_ー－]?0*(\d+)", raw)
        if m:
            return int(m.group(1))
        numbers = re.findall(r"\d+", raw)
        if len(numbers) == 1:
            return int(numbers[0])
        if len(numbers) > 1:
            return int(numbers[-1])
    if raw is not None:
        m = re.search(r"p0*(\d+)", str(raw), re.IGNORECASE)
        if m:
            return int(m.group(1))
    return -1


def grid_field(page: dict[str, Any], key: str) -> Any:
    """grid_rows/grid_cols/aspect_ratio はページ直下が既定だが、
    `layout:` の下にネストされている場合もフォールバックで読む。"""
    if key in page:
        return page[key]
    return (page.get("layout") or {}).get(key)


def summarize_page(page: dict[str, Any], yaml_path: Path, cfg: dict[str, Any],
                   characters: list[dict[str, Any]], locations: list[dict[str, Any]]) -> dict[str, Any]:
    page_num = extract_page_number(page)
    folder, chapter_key = chapter_folder_and_key(yaml_path)
    tone = page.get("page_context", {}).get("emotional_tone", "")
    char_names, loc_text = page_chars_and_locs(page)

    char_refs: dict[str, list[str]] = {}
    for name in dict.fromkeys(char_names):  # 重複除去
        entry = match_entry(name, characters)
        if entry is None:
            char_refs[name] = []  # 名簿未登録 → 要登録のサイン
        else:
            char_refs[name] = pick_sheets(entry, tone, loc_text)

    loc_refs: dict[str, list[str]] = {}
    prompt_only: list[str] = []
    seen_keys: set[str] = set()
    for entry in locations:
        if not any(term in loc_text for term in entry_terms(entry)):
            continue
        key = entry.get("key") or entry.get("name") or ""
        if key in seen_keys:
            continue
        seen_keys.add(key)
        label = entry.get("name") or key
        if entry.get("prompt_only"):
            prompt_only.append(label)
        else:
            loc_refs[label] = pick_sheets(entry, tone, loc_text)

    size = cfg.get("page_size", {"width": 1000, "height": 1414})
    out_dir = cfg.get("output_dir", "step7_完成画像")
    out_name = f"{chapter_key}_p{page_num:02d}_{size['width']}x{size['height']}.png"

    return {
        "page_number": page_num,
        "tone": tone,
        "grid": {"rows": grid_field(page, "grid_rows"), "cols": grid_field(page, "grid_cols"),
                 "aspect_ratio": grid_field(page, "aspect_ratio")},
        "references": {"characters": char_refs, "locations": loc_refs,
                       "prompt_only_locations": prompt_only},
        "output_path": str(Path(out_dir) / folder / out_name),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="指定ページの参照画像候補と保存先を表示する")
    parser.add_argument("yaml_path", type=Path)
    parser.add_argument("pages", help="例: p01 / p01-03 / 1,3,5")
    args = parser.parse_args()

    yaml_path = args.yaml_path if args.yaml_path.is_absolute() else ROOT / args.yaml_path
    cfg = load_config()
    characters = load_roster("characters.yaml", "characters")
    locations = load_roster("locations.yaml", "locations")

    data = load_yaml(yaml_path)
    if not isinstance(data, dict) or "pages" not in data:
        raise SystemExit(f"pages を含むStep6 YAMLではありません: {yaml_path}")

    wanted = parse_page_spec(args.pages)
    pages = [p for p in data.get("pages", []) if extract_page_number(p) in wanted]
    if not pages:
        raise SystemExit(f"指定ページが見つかりません: {args.pages}")

    result = {
        "yaml": str(yaml_path),
        "pages": [summarize_page(p, yaml_path, cfg, characters, locations) for p in pages],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
