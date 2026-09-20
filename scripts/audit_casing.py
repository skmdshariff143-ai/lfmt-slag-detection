import os
import re
from pathlib import Path

web_src = Path("web/src")
import_re = re.compile(r'from\s+[\'"]([^\'"]+)[\'"]')

errors = []
for p in web_src.rglob("*.ts*"):
    content = p.read_text(encoding="utf-8")
    for m in import_re.finditer(content):
        imp = m.group(1)
        if imp.startswith("@/"):
            rel = imp[2:]
            target_ts = web_src / (rel + ".ts")
            target_tsx = web_src / (rel + ".tsx")
            target_dir = web_src / rel
            matched = False
            for cand in [target_ts, target_tsx, target_dir]:
                if cand.exists():
                    curr = web_src
                    parts = rel.split("/")
                    if cand != target_dir:
                        parts[-1] += cand.suffix
                    case_ok = True
                    for part in parts:
                        entries = os.listdir(curr)
                        if part not in entries:
                            case_ok = False
                            break
                        curr = curr / part
                    if case_ok:
                        matched = True
                        break
            if not matched:
                errors.append(f"{p}: import '{imp}' not found or casing mismatch")

print(f"Case-sensitivity audit completed. Errors found: {len(errors)}")
for err in errors:
    print(" ", err)

if errors:
    exit(1)
else:
    print("ALL IMPORTS HAVE EXACT CASE-SENSITIVITY MATCH.")
