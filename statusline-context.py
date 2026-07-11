#!/usr/bin/env python3
"""衡 · Context 进度条 · 直接读 API 百分比"""
import sys, json

try:
    data = json.load(sys.stdin)
except:
    print("ctx: …")
    sys.exit(0)

cw = data.get("context_window", {})
pct = cw.get("used_percentage")

if pct is None:
    print("ctx: …")
    sys.exit(0)

pct = min(pct, 100)
w = 20
f = int(pct * w / 100)
f = max(0, min(f, w))
bar = "█" * f + "░" * (w - f)

if pct > 80:    c = "31"
elif pct > 50:  c = "33"
else:           c = "32"

print(f"ctx:[\033[{c}m{bar}\033[0m] {int(pct)}%")
