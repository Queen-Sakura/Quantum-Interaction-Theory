"""
膜渲染原型机 · 三维驻波叠加花
物理: 有限腔 L×L×L → 分立模式 sin(nxπx/L)sin(nyπy/L)sin(nzπz/L)
      取Δν区间模式叠加 → 局域干涉峰 = 光子 = 一朵花
"""

import numpy as np
from scipy.ndimage import zoom

# ============ 参数 ============
L = 1.0          # 腔尺寸
c = 1.0          # 光速
N_GRID = 80      # 体素网格 (降采样用于3D渲染)
N_FINE = 160     # 精细网格用于关键切片
NU_CENTER = 20.0 # 中心频率 ν̄
DELTA_NU = 4.0   # 频率区间半宽 Δν
PHASE_WEIGHT = 'gaussian'  # 权重分布

# ============ 驻波模式 ============
def mode_freq(nx, ny, nz):
    """ν = (c/2L) * sqrt(nx²+ny²+nz²)"""
    return (c / (2*L)) * np.sqrt(nx**2 + ny**2 + nz**2)

def mode_field(nx, ny, nz, X, Y, Z, t=0):
    """三维驻波场: sin(nxπx/L)·sin(nyπy/L)·sin(nzπz/L)·cos(2πν t)"""
    fx = np.sin(nx * np.pi * X / L)
    fy = np.sin(ny * np.pi * Y / L)
    fz = np.sin(nz * np.pi * Z / L)
    return fx * fy * fz * np.cos(2 * np.pi * mode_freq(nx, ny, nz) * t)

def weight(nx, ny, nz, nu_center, delta_nu):
    """频率权重: 在[ν̄-Δν, ν̄+Δν]内的模式参与叠加"""
    nu = mode_freq(nx, ny, nz)
    if PHASE_WEIGHT == 'gaussian':
        sigma = delta_nu / 3
        return np.exp(-0.5 * ((nu - nu_center) / sigma)**2)
    else:
        return 1.0 if abs(nu - nu_center) <= delta_nu else 0.0

# ============ 收集 Δν 区间内的模式 ============
print(f"收集模式: ν̄={NU_CENTER}, Δν={DELTA_NU}...")
modes = []
n_max = int(np.ceil((NU_CENTER + DELTA_NU) * 2 * L / c)) + 2
for nx in range(1, n_max):
    for ny in range(1, n_max):
        for nz in range(1, n_max):
            nu = mode_freq(nx, ny, nz)
            if abs(nu - NU_CENTER) <= DELTA_NU * 2:  # 宽收
                w = weight(nx, ny, nz, NU_CENTER, DELTA_NU)
                if w > 0.01:
                    modes.append((nx, ny, nz, nu, w))

print(f"找到 {len(modes)} 个模式 (n_max={n_max})")
for nx, ny, nz, nu, w in modes[:10]:
    print(f"  ({nx:3d},{ny:3d},{nz:3d}) ν={nu:7.3f} w={w:.4f}")
if len(modes) > 10:
    print(f"  ... 共 {len(modes)} 个")

# ============ 计算叠加场 ============
print(f"\n渲染 3D 场 ({N_FINE}³ → 切片, {N_GRID}³ → 体渲染)...")

# 精细网格做 XY 切片
x_fine = np.linspace(0.01, 0.99, N_FINE)
y_fine = np.linspace(0.01, 0.99, N_FINE)
z_mid = 0.5
X_f, Y_f = np.meshgrid(x_fine, y_fine)
Z_f = np.full_like(X_f, z_mid)

field_xy = np.zeros_like(X_f)
for nx, ny, nz, nu, w in modes:
    field_xy += w * mode_field(nx, ny, nz, X_f, Y_f, Z_f, t=0)

print(f"  切片能量范围: [{np.min(field_xy**2):.4f}, {np.max(field_xy**2):.4f}]")

# 找峰
idx_peak = np.unravel_index(np.argmax(field_xy**2), field_xy.shape)
print(f"  主峰位置: ({x_fine[idx_peak[1]]:.3f}, {y_fine[idx_peak[0]]:.3f}, z={z_mid})")

# ============ 3D 体素数据 (低分辨率) ============
x_3d = np.linspace(0.05, 0.95, N_GRID)
y_3d = np.linspace(0.05, 0.95, N_GRID)
z_3d = np.linspace(0.05, 0.95, N_GRID)
X3, Y3, Z3 = np.meshgrid(x_3d, y_3d, z_3d, indexing='ij')

field_3d = np.zeros((N_GRID, N_GRID, N_GRID))
chunk_size = 5
for i in range(0, len(modes), chunk_size):
    chunk = modes[i:i+chunk_size]
    for nx, ny, nz, nu, w in chunk:
        field_3d += w * mode_field(nx, ny, nz, X3, Y3, Z3, t=0)
    if (i // chunk_size) % 20 == 0:
        print(f"  3D: {i}/{len(modes)}...")

energy_3d = field_3d**2
print(f"  3D 能量范围: [{np.min(energy_3d):.4f}, {np.max(energy_3d):.4f}]")

# ============ 输出 ============
import os
outdir = "/root/ArgoShared/membrane_render"
os.makedirs(outdir, exist_ok=True)

# 保存 3D 数据供 plotly 使用
np.savez_compressed(
    f"{outdir}/field_3d.npz",
    energy=energy_3d, field=field_3d,
    x=x_3d, y=y_3d, z=z_3d,
    NU_CENTER=NU_CENTER, DELTA_NU=DELTA_NU, n_modes=len(modes)
)

# 保存切片数据
np.savez_compressed(
    f"{outdir}/slice_xy.npz",
    field_xy=field_xy, x=x_fine, y=y_fine, z_mid=z_mid,
    energy_xy=field_xy**2
)

# 同时保存单模式对比 (取最大权重模式)
top_mode = max(modes, key=lambda m: m[4])
nx0, ny0, nz0, nu0, w0 = top_mode
field_single = mode_field(nx0, ny0, nz0, X_f, Y_f, Z_f, t=0)
np.savez_compressed(
    f"{outdir}/slice_single_mode.npz",
    field_xy=field_single, x=x_fine, y=y_fine, z_mid=z_mid,
    energy_xy=field_single**2,
    mode=(nx0, ny0, nz0), nu=nu0
)

print(f"\n数据保存到 {outdir}/")
print(f"  3D 体素: {N_GRID}³")
print(f"  XY 切片 (z=0.5): {N_FINE}²")
print(f"  单模式 ({nx0},{ny0},{nz0}) vs {len(modes)} 模式叠加")
print("✅ 数据就绪，运行 membrane_render_html.py 生成可视化")
