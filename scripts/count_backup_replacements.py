import re, json
from pathlib import Path
repo=Path('.').resolve()
backup=repo/'items_backup_for_lore_translate'
keys=['Crux Fortune','Pristine','Fig Fortune','Ferocity']
pat=re.compile(r"\b(?:%s)\b"%('|'.join([re.escape(k) for k in keys])))
count=0
per={k:0 for k in keys}
for p in backup.glob('**/*.json'):
    s=p.read_text(encoding='utf-8')
    for m in pat.finditer(s):
        per[m.group(0)]+=1
        count+=1
print(json.dumps({'total_replacements':count,'by_key':per},ensure_ascii=False,indent=2))
