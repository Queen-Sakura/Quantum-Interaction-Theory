#!/usr/bin/env python3
"""线性代数交互可视化 · 拖滑块看正方形变形"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from matplotlib.patches import Polygon

# 初始矩阵
A0 = np.array([[2.0, 0.5],
               [0.3, 1.5]])

# 单位正方形四点
sq = np.array([[-1,-1],[1,-1],[1,1],[-1,1]])

def eigen2(a,b,c,d):
    tr = a + d; det = a*d - b*c; disc = tr*tr - 4*det
    if disc < 0:
        return None, None, None
    sqrtD = np.sqrt(disc)
    l1 = (tr + sqrtD) / 2
    l2 = (tr - sqrtD) / 2
    if abs(b) > 1e-9:
        v1 = np.array([l1 - d, b]); v2 = np.array([l2 - d, b])
    elif abs(c) > 1e-9:
        v1 = np.array([c, l1 - a]); v2 = np.array([c, l2 - a])
    else:
        v1 = np.array([1.0, 0.0]); v2 = np.array([0.0, 1.0])
    return l1, v1/np.linalg.norm(v1), l2, v2/np.linalg.norm(v2)

# === 画布 ===
fig, (ax, ax_info) = plt.subplots(2, 1, figsize=(7, 9),
    gridspec_kw={'height_ratios': [5, 1]})
plt.subplots_adjust(bottom=0.35)

ax.set_xlim(-5, 5); ax.set_ylim(-5, 5)
ax.set_aspect('equal')
ax.grid(True, alpha=0.3, linestyle='--')
ax.axhline(y=0, color='#444', linewidth=0.8)
ax.axvline(x=0, color='#444', linewidth=0.8)
ax.set_title("矩阵 = 空间的变形器 · 拖下方滑块", fontsize=12, color='white')
ax.set_facecolor('#0a0a14')
fig.patch.set_facecolor('#12121a')

# 原始正方形
poly_orig = None
poly_trans = None
ev_lines = []

def draw(a,b,c,d):
    global poly_orig, poly_trans, ev_lines

    # clear old
    for ln in ev_lines:
        try: ln.remove()
        except: pass
    ev_lines.clear()
    if poly_orig:
        try: poly_orig.remove()
        except: pass
    if poly_trans:
        try: poly_trans.remove()
        except: pass

    A = np.array([[a,b],[c,d]])
    det = a*d - b*c
    tr = a + d

    # 原始正方形
    orig = Polygon(sq, fill=False, edgecolor='#4a4', linewidth=2,
                   linestyle='--', alpha=0.6, label='原始正方形')
    ax.add_patch(orig)
    poly_orig = orig

    # 变形后的平行四边形
    trans_pts = sq @ A.T
    trans = Polygon(trans_pts, fill=False, edgecolor='white', linewidth=2.5,
                    alpha=0.9, label='变形后')
    ax.add_patch(trans)
    poly_trans = trans

    # 特征向量
    l1, v1, l2, v2 = None, None, None, None
    disc = tr*tr - 4*det
    if disc >= 0:
        sqrtD = np.sqrt(disc)
        l1 = (tr + sqrtD) / 2
        l2 = (tr - sqrtD) / 2
        if abs(b) > 1e-9:
            v1 = np.array([l1 - d, b]); v2 = np.array([l2 - d, b])
        elif abs(c) > 1e-9:
            v1 = np.array([c, l1 - a]); v2 = np.array([c, l2 - a])
        else:
            v1 = np.array([1.0, 0.0]); v2 = np.array([0.0, 1.0])
        v1 = v1 / np.linalg.norm(v1)
        v2 = v2 / np.linalg.norm(v2)

        # 画特征向量（实线和虚线）
        scale = max(abs(l1), abs(l2), 2) + 1
        for v, lam, color in [(v1, l1, '#4fc3f7'), (v2, l2, '#4fc3f7')]:
            # 正向
            lh, = ax.plot([0, v[0]*lam], [0, v[1]*lam], color=color,
                          linewidth=2.5, alpha=0.8)
            ev_lines.append(lh)
            # 反向 虚线
            lh2, = ax.plot([0, -v[0]*lam], [0, -v[1]*lam], color=color,
                           linewidth=1, linestyle=':', alpha=0.4)
            ev_lines.append(lh2)

        info = f"M=[[{a:.1f},{b:.1f}],[{c:.1f},{d:.1f}]] | det={det:.2f} | trace={tr:.2f} | λ₁={l1:.2f} λ₂={l2:.2f}"
    else:
        info = f"M=[[{a:.1f},{b:.1f}],[{c:.1f},{d:.1f}]] | det={det:.2f} | trace={tr:.2f} | 特征值复数——对角化失败"

    # info panel
    ax_info.clear()
    ax_info.set_facecolor('#12121a')
    ax_info.text(0.5, 0.6, info, transform=ax_info.transAxes,
                fontsize=11, color='white', ha='center', va='center',
                fontfamily='monospace')
    ax_info.axis('off')
    fig.canvas.draw_idle()

# === 滑块 ===
slider_color = '#c8b878'
ax_a = plt.axes([0.15, 0.26, 0.7, 0.03])
ax_b = plt.axes([0.15, 0.20, 0.7, 0.03])
ax_c = plt.axes([0.15, 0.14, 0.7, 0.03])
ax_d = plt.axes([0.15, 0.08, 0.7, 0.03])

s_a = Slider(ax_a, 'a (x→x)', -3.0, 3.0, valinit=A0[0,0], color=slider_color)
s_b = Slider(ax_b, 'b (y→x) 剪切', -2.0, 2.0, valinit=A0[0,1], color=slider_color)
s_c = Slider(ax_c, 'c (x→y) 剪切', -2.0, 2.0, valinit=A0[1,0], color=slider_color)
s_d = Slider(ax_d, 'd (y→y)', -3.0, 3.0, valinit=A0[1,1], color=slider_color)

def update(val):
    draw(s_a.val, s_b.val, s_c.val, s_d.val)

s_a.on_changed(update)
s_b.on_changed(update)
s_c.on_changed(update)
s_d.on_changed(update)

draw(A0[0,0], A0[0,1], A0[1,0], A0[1,1])
plt.show()
