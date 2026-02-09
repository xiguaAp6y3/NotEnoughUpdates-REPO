import json
import re
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
items_dir = repo_root / 'items'
mappings_file = repo_root / 'mappings' / 'player_stats_zh_cn.json'

with open(mappings_file, 'r', encoding='utf-8') as f:
    mappings = json.load(f)['mappings']

# prepare regex pattern for whole-word matches for each key
keys = sorted(mappings.keys(), key=lambda x: -len(x))  # longer first to avoid partial overlaps
escaped_keys = [re.escape(k) for k in keys]
pattern = re.compile(r"\b(?:%s)\b" % ("|".join(escaped_keys)))

results = []

for p in items_dir.glob('**/*.json'):
    try:
        data = json.load(p.open('r', encoding='utf-8'))
    except Exception:
        # skip files that aren't valid json
        continue

    # function to recursively find lore lists or display->Lore
    def find_lore(obj, path=[]):
        found = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k.lower() == 'lore' and isinstance(v, list):
                    found.append((path + [k], v))
                elif k == 'display' and isinstance(v, dict) and 'Lore' in v and isinstance(v['Lore'], list):
                    found.append((path + [k, 'Lore'], v['Lore']))
                else:
                    found.extend(find_lore(v, path + [k]))
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                found.extend(find_lore(item, path + [str(i)]))
        return found

    lore_sections = find_lore(data)
    if not lore_sections:
        continue

    # load raw text for line context
    raw_text = p.read_text(encoding='utf-8')

    for path_keys, lore_list in lore_sections:
        for idx, entry in enumerate(lore_list):
            if not isinstance(entry, str):
                continue
            for m in pattern.finditer(entry):
                key = m.group(0)
                # find line number in raw_text (best-effort)
                # find entry string in raw_text
                snippet = entry
                lineno = None
                try:
                    # naive search for the entry content
                    loc = raw_text.find(json.dumps(entry, ensure_ascii=False))
                    if loc != -1:
                        lineno = raw_text[:loc].count('\n') + 1
                except Exception:
                    lineno = None

                results.append({
                    'file': str(p.relative_to(repo_root)),
                    'lore_path': '/'.join(path_keys),
                    'lore_index': idx,
                    'matched_key': key,
                    'lore_entry': entry,
                    'line': lineno
                })

# output a summary
summary = {}
for r in results:
    summary.setdefault(r['matched_key'], []).append(r)

print(json.dumps({'total_matches': len(results), 'by_key': {k: len(v) for k, v in summary.items()}, 'matches': results}, ensure_ascii=False, indent=2))
