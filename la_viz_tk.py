#!/usr/bin/env python3
"""线性代数交互可视化 · 纯 tkinter · 零依赖"""
import tkinter as tk
import math

W, H = 520, 520
CX, CY = 260, 260
SCALE = 60

def eigen2(a,b,c,d):
    tr = a + d
    det = a*d - b*c
    disc = tr*tr - 4*det
    if disc < 0:
        return None
    sqrtD = math.sqrt(disc)
    l1 = (tr + sqrtD) / 2
    l2 = (tr - sqrtD) / 2
    if abs(b) > 1e-9:
        v1 = (l1 - d, b); v2 = (l2 - d, b)
    elif abs(c) > 1e-9:
        v1 = (c, l1 - a); v2 = (c, l2 - a)
    else:
        v1 = (1.0, 0.0); v2 = (0.0, 1.0)
    n1 = math.sqrt(v1[0]**2+v1[1]**2) or 1
    n2 = math.sqrt(v2[0]**2+v2[1]**2) or 1
    return (l1, v1[0]/n1, v1[1]/n1), (l2, v2[0]/n2, v2[1]/n2), det, tr

def draw():
    a = sa.get() / 10.0
    b = sb.get() / 10.0
    c = sc.get() / 10.0
    d = sd.get() / 10.0

    canvas.delete("all")

    # grid
    for i in range(-6, 7):
        x = CX + i*SCALE
        canvas.create_line(x, 0, x, H, fill='#1a1a2e')
        y = CY + i*SCALE
        canvas.create_line(0, y, W, y, fill='#1a1a2e')

    # axes
    canvas.create_line(CX, 0, CX, H, fill='#333', width=1)
    canvas.create_line(0, CY, W, CY, fill='#333', width=1)

    # 原始正方形 (灰色虚线)
    pts = [(CX+x*SCALE, CY-y*SCALE) for x,y in [(-1,-1),(1,-1),(1,1),(-1,1),(-1,-1)]]
    for i in range(4):
        canvas.create_line(pts[i][0],pts[i][1], pts[i+1][0],pts[i+1][1],
                          fill='#4a4', dash=(6,6), width=2)

    # 变形后的平行四边形 (白色)
    tpts = [(CX + (a*x+b*y)*SCALE, CY - (c*x+d*y)*SCALE)
            for x,y in [(-1,-1),(1,-1),(1,1),(-1,1),(-1,-1)]]
    for i in range(4):
        canvas.create_line(tpts[i][0],tpts[i][1], tpts[i+1][0],tpts[i+1][1],
                          fill='white', width=2.5)

    # 特征向量
    eg = eigen2(a,b,c,d)
    if eg:
        (l1,v1x,v1y), (l2,v2x,v2y), det, tr = eg
        # λ₁
        canvas.create_line(CX, CY,
            CX + v1x*l1*SCALE, CY - v1y*l1*SCALE,
            fill='#4fc3f7', width=2.5)
        canvas.create_line(CX, CY,
            CX - v1x*l1*SCALE, CY + v1y*l1*SCALE,
            fill='#4fc3f7', dash=(4,8), width=1)
        # λ₂
        canvas.create_line(CX, CY,
            CX + v2x*l2*SCALE, CY - v2y*l2*SCALE,
            fill='#4fc3f7', width=2)
        canvas.create_line(CX, CY,
            CX - v2x*l2*SCALE, CY + v2y*l2*SCALE,
            fill='#4fc3f7', dash=(4,8), width=1)

        info = (f"[[{a:.1f},{b:.1f}],[{c:.1f},{d:.1f}]]  "
                f"det={det:.2f}  trace={tr:.2f}  "
                f"λ₁={l1:.2f}  λ₂={l2:.2f}")
    else:
        det = a*d - b*c; tr = a + d
        info = (f"[[{a:.1f},{b:.1f}],[{c:.1f},{d:.1f}]]  "
                f"det={det:.2f}  trace={tr:.2f}  "
                f"特征值复数——对角化失败")

    info_label.config(text=info)

root = tk.Tk()
root.title("矩阵 = 空间的变形器 · 拖滑块")
root.configure(bg='#12121a')

canvas = tk.Canvas(root, width=W, height=H, bg='#0a0a14', highlightthickness=0)
canvas.pack()

info_label = tk.Label(root, text="", bg='#12121a', fg='white',
                      font=('Courier New', 11))
info_label.pack(pady=(2,0))

# 滑块
def make_slider(label, v0, lo, hi):
    f = tk.Frame(root, bg='#12121a')
    f.pack(fill='x', padx=20, pady=2)
    tk.Label(f, text=label, bg='#12121a', fg='#888',
             font=('Segoe UI', 9), width=18, anchor='w').pack(side='left')
    s = tk.Scale(f, from_=lo, to=hi, orient='horizontal', resolution=1,
                 length=360, bg='#1a1a2e', fg='#c8b878', highlightthickness=0,
                 troughcolor='#2a2a3e', activebackground='#c8b878',
                 command=lambda v: draw())
    s.set(v0)
    s.pack(side='left', padx=(4,0))
    return s

sa = make_slider('a (x→x)', 20, -30, 30)
sb = make_slider('b (y→x)  剪切', 5, -20, 20)
sc = make_slider('c (x→y)  剪切', 3, -20, 20)
sd = make_slider('d (y→y)', 15, -30, 30)

draw()
root.mainloop()
