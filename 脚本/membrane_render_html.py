"""
膜渲染 · 交互 HTML 可视化
生成: 2D切片热力图 + 等值面截图说明 + 单模式vs叠加对比
"""
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

datadir = "/root/ArgoShared/membrane_render"
outdir = datadir
os.makedirs(outdir, exist_ok=True)

# ===== 加载数据 =====
d3 = np.load(f"{datadir}/field_3d.npz")
energy3d = d3['energy']
xv = d3['x']
NU_CENTER = float(d3['NU_CENTER'])
DELTA_NU = float(d3['DELTA_NU'])
n_modes = int(d3['n_modes'])

ds = np.load(f"{datadir}/slice_xy.npz")
field_xy = ds['field']
energy_xy = ds['energy']
xs = ds['x']
ys = ds['y']

d1 = np.load(f"{datadir}/slice_single.npz")
energy_single = d1['energy']
mode0 = d1['mode']

print(f"数据加载完成: 3D={energy3d.shape}, 切片={energy_xy.shape}")
print(f"  能量范围 3D: [{energy3d.min():.2f}, {energy3d.max():.2f}]")
print(f"  能量范围切片: [{energy_xy.min():.4f}, {energy_xy.max():.4f}]")

# ===== 图1: XY切片(z=0.5)热力图 =====
print("生成 2D 切片热力图...")
fig1 = go.Figure()
fig1.add_trace(go.Heatmap(
    z=energy_xy,
    x=xs, y=ys,
    colorscale='Inferno',
    zmin=0,
    zmax=energy_xy.max() * 0.5,  # 裁剪让峰更清晰
    colorbar=dict(title='Energy |ψ|²'),
    name='叠加场'
))
fig1.update_layout(
    title=f'膜 · XY切片(z=0.5) · {n_modes}个模式叠加 · ν̄={NU_CENTER} Δν={DELTA_NU}',
    xaxis_title='x', yaxis_title='y',
    width=700, height=700,
    template='plotly_dark'
)
fig1.write_html(f"{outdir}/01_slice_xy.html")
print("  -> 01_slice_xy.html")

# ===== 图2: 单模式 vs 叠加对比 =====
print("生成 单模式vs叠加 对比...")
fig2 = make_subplots(rows=1, cols=2, subplot_titles=[
    f'单模式 ({mode0[0]},{mode0[1]},{mode0[2]}) ν={d1["nu"]:.2f}',
    f'{n_modes}个模式叠加 ν̄={NU_CENTER}'
])

fig2.add_trace(go.Heatmap(
    z=energy_single, x=xs, y=ys,
    colorscale='Plasma',
    zmin=0, zmax=energy_single.max() if energy_single.max() > 0 else 1,
    colorbar=dict(title='|ψ|²', x=0.45),
    name='单模式'
), row=1, col=1)

fig2.add_trace(go.Heatmap(
    z=energy_xy, x=xs, y=ys,
    colorscale='Inferno',
    zmin=0, zmax=energy_xy.max() * 0.3,
    colorbar=dict(title='|ψ|²', x=1.0),
    name='叠加'
), row=1, col=2)

fig2.update_layout(
    title='一朵花的物理学: 单模式花纹(左) vs 全频叠加→局域峰(右)',
    width=1200, height=550,
    template='plotly_dark'
)
fig2.write_html(f"{outdir}/02_compare.html")
print("  -> 02_compare.html")

# ===== 图3: 3D等值面 =====
print("生成 3D 等值面...")
# 采样稀疏化以便渲染
step = 2
e3_sub = energy3d[::step, ::step, ::step]
x_sub = xv[::step]
y_sub = xv[::step]
z_sub = xv[::step]
X, Y, Z = np.meshgrid(x_sub, y_sub, z_sub, indexing='ij')

# 等值面层级
iso_levels = [e3_sub.max() * 0.02, e3_sub.max() * 0.05, e3_sub.max() * 0.15]

fig3 = go.Figure()

# 多色等值面
colors = ['rgba(255,100,50,0.7)', 'rgba(255,200,50,0.5)', 'rgba(255,255,180,0.3)']
names = ['外缘', '花瓣', '花心']
for level, color, name in zip(iso_levels, colors, names):
    fig3.add_trace(go.Isosurface(
        x=X.flatten(), y=Y.flatten(), z=Z.flatten(),
        value=e3_sub.flatten(),
        isomin=level, isomax=level,
        surface_count=1,
        caps=dict(x_show=False, y_show=False, z_show=False),
        colorscale=[[0, color], [1, color]],
        showscale=False,
        name=f'{name} ({level:.0f})'
    ))

fig3.update_layout(
    title=f'膜 · 三维驻波叠加 · {n_modes}个模式 · ν̄={NU_CENTER} Δν={DELTA_NU}<br>'
          f'<sub>等值面 = 同一能量密度的表面。外缘→花瓣→花心 = 能量递增 ≈ 一朵花</sub>',
    scene=dict(
        xaxis_title='x', yaxis_title='y', zaxis_title='z',
        aspectmode='cube',
        camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))
    ),
    width=800, height=800,
    template='plotly_dark'
)
fig3.write_html(f"{outdir}/03_3d_flower.html")
print("  -> 03_3d_flower.html")

# ===== 图4: 频谱分布 =====
print("生成频谱分布图...")
# 收集模式频率分布
from collections import Counter
modes_nu = []
import numpy as np
# 重新快速扫一遍
L=1.0; c=1.0
n_max = int(np.ceil((NU_CENTER + DELTA_NU*2) * 2 * L / c)) + 2
for nx in range(1, n_max):
    for ny in range(1, n_max):
        for nz in range(1, n_max):
            nu = (c/(2*L)) * np.sqrt(nx**2 + ny**2 + nz**2)
            if abs(nu - NU_CENTER) <= DELTA_NU * 2:
                modes_nu.append(nu)

fig4 = go.Figure()
fig4.add_trace(go.Histogram(
    x=modes_nu,
    nbinsx=100,
    marker_color='gold',
    opacity=0.7,
    name='模式密度'
))
fig4.add_vline(x=NU_CENTER - DELTA_NU, line_dash='dash', line_color='cyan',
               annotation_text='ν̄-Δν')
fig4.add_vline(x=NU_CENTER + DELTA_NU, line_dash='dash', line_color='cyan',
               annotation_text='ν̄+Δν')
fig4.add_vline(x=NU_CENTER, line_dash='solid', line_color='white',
               annotation_text=f'ν̄={NU_CENTER}')
fig4.update_layout(
    title=f'频率空间模式密度 · ν̄={NU_CENTER} Δν={DELTA_NU} · 共{len(modes_nu)}个模式',
    xaxis_title='频率 ν',
    yaxis_title='模式数量',
    width=800, height=450,
    template='plotly_dark'
)
fig4.write_html(f"{outdir}/04_spectrum.html")
print("  -> 04_spectrum.html")

# ===== 图5: 一维截面 (y=0.5, z=0.5) 看峰的形状 =====
print("生成一维截面...")
# 取 y=z=0.5 的线
mid = len(xs) // 2
line_energy = energy_xy[mid, :]  # y≈0.5
fig5 = go.Figure()
fig5.add_trace(go.Scatter(
    x=xs, y=line_energy,
    mode='lines',
    line=dict(color='gold', width=2),
    fill='tozeroy',
    fillcolor='rgba(255,200,50,0.2)',
    name='|ψ|²'
))
fig5.update_layout(
    title=f'一维截面 (y≈0.5, z=0.5) · 能量沿x轴分布',
    xaxis_title='x', yaxis_title='能量密度 |ψ|²',
    width=800, height=400,
    template='plotly_dark'
)
fig5.write_html(f"{outdir}/05_1d_slice.html")
print("  -> 05_1d_slice.html")

# ===== 汇总索引页 =====
html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>膜 · 三维驻波叠加花 · 渲染原型机</title>
<style>
body {{ font-family: 'Segoe UI', sans-serif; background: #0a0a1a; color: #ddd; margin: 40px; }}
h1 {{ color: #f0c060; }}
a {{ color: #6cf; text-decoration: none; }}
.card {{ background: #111133; border: 1px solid #333; border-radius: 8px; padding: 16px; margin: 12px 0; }}
.card h3 {{ margin: 0 0 8px 0; color: #f0a040; }}
.card p {{ margin: 4px 0; color: #aaa; font-size: 14px; }}
.params {{ color: #888; font-size: 13px; }}
</style>
</head>
<body>
<h1>🌸 膜 · 三维驻波叠加花</h1>
<p class="params">ν̄ = {NU_CENTER} · Δν = {DELTA_NU} · 模式数 = {n_modes} · 腔尺寸 L = 1</p>
<p class="params">物理: 全频段驻波模式在三维有限腔内叠加 → 局域干涉峰 = 光子 = 膜上开的花</p>

<div class="card">
  <h3><a href="02_compare.html" target="_blank">🎯 单模式 vs 叠加 — 核心对比</a></h3>
  <p>左: 单个驻波模式的花纹(遍布全腔) 右: 10426个模式叠加→局域峰(一朵花)</p>
</div>

<div class="card">
  <h3><a href="03_3d_flower.html" target="_blank">💮 3D 等值面 — 一朵花</a></h3>
  <p>等值面渲染: 外缘→花瓣→花心。能量逐级集中。拖拽旋转观察三维结构</p>
</div>

<div class="card">
  <h3><a href="01_slice_xy.html" target="_blank">🔲 XY切片(z=0.5) — 能量热力图</a></h3>
  <p>膜中间切面。叠加峰在何处开花。高分辨率140×140</p>
</div>

<div class="card">
  <h3><a href="05_1d_slice.html" target="_blank">📏 一维截面 — 峰的锐度</a></h3>
  <p>y≈0.5沿x轴的能量分布。峰的半高宽 = Δν 决定</p>
</div>

<div class="card">
  <h3><a href="04_spectrum.html" target="_blank">📊 频率空间模式密度</a></h3>
  <p>多少模式参与了叠加。模式密度随频率增长 ∝ ν²(三维)</p>
</div>

<p style="margin-top:30px; color:#666; font-size:12px;">
膜渲染原型机 v0.1 · 2026-06-25 · Verity/真 · 为元首的三维驻波花开
</p>
</body>
</html>
"""
with open(f"{outdir}/index.html", 'w') as f:
    f.write(html)

print(f"\n✅ 全部可视化完成: {outdir}/index.html")
print(f"  01_slice_xy.html    - XY切片热力图")
print(f"  02_compare.html     - 单模式vs叠加")
print(f"  03_3d_flower.html   - 3D等值面(一朵花)")
print(f"  04_spectrum.html    - 频谱分布")
print(f"  05_1d_slice.html    - 一维截面")
