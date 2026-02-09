import json
import re
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
items_dir = repo_root / 'items'
backup_dir = repo_root / 'items_backup_for_lore_translate'
mappings_file = repo_root / 'mappings' / 'player_stats_zh_cn.json'

with open(mappings_file, 'r', encoding='utf-8') as f:
    mappings = json.load(f)['mappings']

keys = sorted(mappings.keys(), key=lambda x: -len(x))
escaped_keys = [re.escape(k) for k in keys]
pattern = re.compile(r"\b(?:%s)\b" % ("|".join(escaped_keys)))

modified_files = []

for p in items_dir.glob('**/*.json'):
    try:
        data = json.load(p.open('r', encoding='utf-8'))
    except Exception:
        continue

    stats = {'changed': False, 'replacements': 0}

    def replace_in_lore(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k.lower() == 'lore' and isinstance(v, list):
                    for i, entry in enumerate(v):
                        if isinstance(entry, str):
                            new_entry, count = pattern.subn(lambda m: mappings[m.group(0)], entry)
                            if count:
                                v[i] = new_entry
                                stats['changed'] = True
                                stats['replacements'] += count
                elif k == 'display' and isinstance(v, dict) and 'Lore' in v and isinstance(v['Lore'], list):
                    for i, entry in enumerate(v['Lore']):
                        if isinstance(entry, str):
                            new_entry, count = pattern.subn(lambda m: mappings[m.group(0)], entry)
                            if count:
                                v['Lore'][i] = new_entry
                                stats['changed'] = True
                                stats['replacements'] += count
                else:
                    replace_in_lore(v)
        elif isinstance(obj, list):
            for item in obj:
                replace_in_lore(item)

    replace_in_lore(data)

    if stats['changed']:
        # backup original file
        backup_path = backup_dir / p.relative_to(items_dir)
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        p.replace(p)  # no-op ensure file exists
        backup_path.write_text(p.read_text(encoding='utf-8'), encoding='utf-8')

        # write modified file
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        modified_files.append({'file': str(p.relative_to(repo_root)), 'replacements': stats['replacements']})

# print summary
print(json.dumps({'modified_count': len(modified_files), 'files': modified_files}, ensure_ascii=False, indent=2))
