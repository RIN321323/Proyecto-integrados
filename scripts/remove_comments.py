import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
exclude_dirs = {'.venv', 'venv', '__pycache__'}
modified = []

for dirpath, dirnames, filenames in os.walk(ROOT):
    # skip excluded dirs
    parts = set(dirpath.replace('\\', '/').split('/'))
    if parts & exclude_dirs:
        continue
    # skip virtualenv site-packages inside project
    if 'site-packages' in dirpath:
        continue
    for fn in filenames:
        if not fn.endswith('.py'):
            continue
        fpath = os.path.join(dirpath, fn)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception:
            continue
        new_lines = []
        changed = False
        for line in lines:
            stripped = line.lstrip()
            if stripped.startswith('#'):
                changed = True
                continue
            new_lines.append(line)
        if changed:
            with open(fpath, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            modified.append(fpath)

print('Modified files:')
for p in modified:
    print(p)
print('\nTotal modified:', len(modified))
