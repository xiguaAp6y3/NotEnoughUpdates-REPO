import json
import re
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
items_dir = repo_root / 'items'
mappings_file = repo_root / 'mappings' / 'player_stats_zh_cn.json'

with open(mappings_file, 'r', encoding='utf-8') as f:
    mappings = json.load(f)['mappings']

# keys we care about
keys_to_check = ['Crux Fortune', 'Pristine', 'Fig Fortune', 'Ferocity']
escaped_keys = [re.escape(k) for k in keys_to_check]
pattern = re.compile(r"\b(?:%s)\b" % ("|".join(escaped_keys)))

results = []
for p in items_dir.glob('**/*.json'):
    try:
        data = json.load(p.open('r', encoding='utf-8'))
    except Exception:
        continue

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

    for path_keys, lore_list in lore_sections:
        for idx, entry in enumerate(lore_list):
            if not isinstance(entry, str):
                continue
            for m in pattern.finditer(entry):
                results.append({
                    'file': str(p.relative_to(repo_root)),
                    'lore_path': '/'.join(path_keys),
                    'lore_index': idx,
                    'matched_key': m.group(0),
                    'lore_entry': entry
                })

print(json.dumps({'total_matches': len(results), 'matches': results}, ensure_ascii=False, indent=2))
