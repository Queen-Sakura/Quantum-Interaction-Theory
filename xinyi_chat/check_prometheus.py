#!/usr/bin/env python3
"""检查 prometheus.su 是否可注册"""
import urllib.request
try:
    req = urllib.request.Request('http://prometheus.su', headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=5)
    content = resp.read().decode('utf-8', errors='ignore')
    if 'истек' in content or 'истёк' in content:
        print(f"EXPIRED — still in redemption/delete cycle")
    elif 'не найден' in content.lower() or 'not found' in content.lower() or resp.status == 404:
        print(f"AVAILABLE! prometheus.su is free!")
    else:
        # Could be parked or active
        import re
        title = re.search(r'<title>(.*?)</title>', content, re.I)
        print(f"STATUS: {title.group(1) if title else 'unknown'} — {resp.url}")
except Exception as e:
    # Connection refused might mean no web server = possibly available
    if 'Connection refused' in str(e) or 'Name or service not known' in str(e):
        print(f"POSSIBLY AVAILABLE — no web server: {e}")
    else:
        print(f"CHECK FAILED: {e}")
