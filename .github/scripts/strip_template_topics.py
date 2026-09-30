"""从 WinCHM 工程文件中去掉“模板页”目录条目（Kind=2，如 Fixed Top），生成一份仅供网页编译用的临时 .wcp。

用法：python strip_template_topics.py 输入.wcp 输出.wcp
原工程文件不会被修改，WinCHM 里照常使用。
"""
import re
import sys
from collections import OrderedDict
from pathlib import Path

src, dst = Path(sys.argv[1]), Path(sys.argv[2])
raw = src.read_bytes()
encoding = "utf-16" if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-16-le"
text = raw.decode(encoding)
newline = "\r\n" if "\r\n" in text else "\n"
lines = text.split(newline)

start = next(i for i, line in enumerate(lines) if line.strip().upper() == "[TOPICS]")
end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("[")), len(lines))

entry = re.compile(r"^TitleList\.([A-Za-z]+)\.(\d+)=(.*)$")
topics: "OrderedDict[int, list[tuple[str, str]]]" = OrderedDict()
others = []
for line in lines[start + 1:end]:
    match = entry.match(line)
    if match:
        topics.setdefault(int(match.group(2)), []).append((match.group(1), match.group(3)))
    elif not line.startswith("TitleList="):
        others.append(line)

kept = [fields for _, fields in sorted(topics.items()) if dict(fields).get("Kind", "0").strip() != "2"]
removed = len(topics) - len(kept)

section = [f"TitleList={len(kept)}"]
for new_index, fields in enumerate(kept):
    section += [f"TitleList.{name}.{new_index}={value}" for name, value in fields]
section += [line for line in others if line.strip()]
section.append("")

out = lines[:start + 1] + section + lines[end:]
dst.write_bytes(newline.join(out).encode("utf-16"))
print(f"topics: {len(topics)} -> {len(kept)} (removed {removed} template entries)")
