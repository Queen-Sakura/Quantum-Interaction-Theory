#!/usr/bin/env python3
"""Q 加速度监控器 v0.1 · 闷声发财 · 法兰西银行自用"""
import urllib.request, json, sys
from datetime import datetime

# ===== 配置 =====
STOCKS = {
    "000657": {"name": "中钨高新", "source": "sz"},
    "603019": {"name": "中科曙光", "source": "sh"},
    "603296": {"name": "华勤技术", "source": "sh"},
    "601126": {"name": "四方股份", "source": "sh"},
}

LOOKBACK = 60   # 日线回溯
ALPHA, BETA, GAMMA = 0.4, 0.3, 0.3  # Q̃ 权重

# ===== 数据 =====
def fetch_klines(code, source, n=LOOKBACK):
    """从新浪接口拉日线（前复权）"""
    sym = f"{source}{code}"
    url = f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={sym}&scale=240&ma=no&datalen={n}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("gbk", errors="ignore")
            data = json.loads(raw)
            if data and isinstance(data, list):
                return [(d["day"], float(d["open"]), float(d["close"]),
                         float(d["high"]), float(d["low"]), int(d["volume"]))
                        for d in data if "close" in d]
    except Exception as e:
        pass
    return []

def smooth(series, w=3):
    """简单移动均——抗噪"""
    out = []
    for i in range(len(series)):
        lo = max(0, i-w+1)
        out.append(sum(series[lo:i+1]) / (i-lo+1))
    return out

# ===== 核心计算 =====
def compute(kd):
    """kd: [(date, open, close, high, low, vol), ...]"""
    dates  = [k[0] for k in kd]
    closes = [k[2] for k in kd]
    lows   = [k[4] for k in kd]
    vols   = [k[5] for k in kd]

    n = len(kd)
    if n < 10:
        return None

    # --- S_t: 5日动量 ---
    st = [0.0]*n
    for i in range(5, n):
        st[i] = (closes[i] - closes[i-5]) / closes[i-5] * 100

    # --- V_t: 量比 (vs 20日均量) ---
    vt = [1.0]*n
    for i in range(20, n):
        avg_vol = sum(vols[i-20:i]) / 20
        vt[i] = vols[i] / avg_vol if avg_vol > 0 else 1.0

    # --- F_t: 斐波那契位置 ---
    hi_60 = max(closes[-60:]) if n >= 60 else max(closes)
    lo_60 = min(lows[-60:]) if n >= 60 else min(lows)
    rng = hi_60 - lo_60
    ft = [(c - lo_60) / rng * 100 if rng > 0 else 50 for c in closes]

    # --- Q̃ ---
    qt = [ALPHA*st[i] + BETA*(vt[i]-1)*50 + GAMMA*ft[i] for i in range(n)]
    qt_s = smooth(qt)

    # --- Q̈ ---
    qq = [0.0]*n
    for i in range(1, n):
        qq[i] = qt_s[i] - qt_s[i-1]

    # 转折点
    qq3 = qq[-3:]
    rlows = lows[-4:]
    turning = None
    if len(qq3) >= 3:
        if qq3[-3] < 0 and qq3[-2] < 0 and qq3[-1] > 0:
            turning = "↑ 疑似转正 ⚠"
        elif qq3[-3] > 0 and qq3[-2] > 0 and qq3[-1] < 0:
            turning = "↓ 疑似转负"
        elif all(q > 0 for q in qq3):
            turning = "↑ 正加速"
        elif all(q < 0 for q in qq3):
            turning = "↓ 负加速"

    # 不创新低——最近是否有新低
    new_low = rlows[-1] < rlows[-3] if len(rlows) >= 3 else False

    return {
        "dates": dates,
        "closes": closes,
        "qt": qt_s,
        "qq": qq,
        "now": closes[-1],
        "chg": (closes[-1] - closes[-2]) / closes[-2] * 100 if n >= 2 else 0,
        "qq_now": qq[-1],
        "turning": turning,
        "new_low": new_low,
        "fib": ft[-1],
        "fib382": lo_60 + 0.382 * rng,
        "fib500": lo_60 + 0.500 * rng,
        "vol_ratio": vt[-1],
    }

# ===== 输出 =====
def report():
    print(f"╔══════════════════════════════════╗")
    print(f"║  Q 加速度监控器 v0.1           ║")
    print(f"║  {datetime.now().strftime('%Y-%m-%d %H:%M')}                    ║")
    print(f"╚══════════════════════════════════╝")
    print()

    for code, cfg in STOCKS.items():
        kd = fetch_klines(code, cfg["source"])
        if not kd:
            print(f"  {cfg['name']} : 数据获取失败")
            continue

        r = compute(kd)
        if r is None:
            print(f"  {cfg['name']} : 数据不足")
            continue

        name = cfg["name"]
        # 颜色
        if r["qq_now"] > 0:   emoji = "🟢"
        elif r["qq_now"] < 0: emoji = "🔴"
        else:                 emoji = "🟡"

        nl = "✗ 有新低" if r["new_low"] else "✓ 无新低"
        print(f"  {emoji} {name:<6} | 现 {r['now']:.2f} ({r['chg']:+.2f}%)")
        print(f"     Q̈={r['qq_now']:+.1f}  | {r['turning'] or '→ 平'} | {nl}")
        print(f"     Fib {r['fib']:.0f}% | 量比 {r['vol_ratio']:.2f}")
        print(f"     38.2%={r['fib382']:.2f}  50%={r['fib500']:.2f}")
        print()

    print("  ⚠ 仅供法兰西银行自用。不构成投资建议。")

if __name__ == "__main__":
    report()
