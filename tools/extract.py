import re
import os

base = r'C:\Users\wuergou\Desktop\WuJaw.github.io\tools'

for entry in os.scandir(base):
    if not entry.name.endswith('.html'):
        continue
    # entry.path is bytes-safe
    with open(entry.path, 'r', encoding='utf-8') as f:
        content = f.read()
    m = re.search(r'<script>const component = "(.*?)"</script>', content, re.DOTALL)
    if m:
        code = m.group(1)
        code = code.replace('\\n', '\n').replace('\\"', '"')
        out = entry.path.replace('.html', '_component.js')
        with open(out, 'w', encoding='utf-8') as o:
            o.write(code)
        # log via repr so it doesn't break the terminal
        sys_msg = f"OK: {entry.name!r} -> {len(code)} chars"
        print(sys_msg)
    else:
        print(f"NO MATCH: {entry.name!r}")
