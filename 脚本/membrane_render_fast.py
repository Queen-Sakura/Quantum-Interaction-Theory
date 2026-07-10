"""
膜渲染原型机 · 三维驻波叠加花 (快速版)
"""
import numpy as np
import os, time

L = 1.0; c = 1.0
NU_CENTER = 12.0
DELTA_NU = 3.0
N_GRID = 50   # 3D
N_SLICE = 140 # 切片

# ===== 收集模式 =====
n_max = int(np.ceil((NU_CENTER + DELTA_NU*2) * 2 * L / c)) + 2
print(f"n_max={n_max}, 扫描模式空间...")
modes = []
for nx in range(1, n_max):
    for ny in range(1, n_max):
        nz2_max = int((NU_CENTER + DELTA_NU*2)**2 * 4*L**2 / c**2 - nx**2 - ny**2)
        for nz in range(1, min(n_max, int(np.sqrt(max(0, nz2_max))) + 2)):
            nu = (c/(2*L)) * np.sqrt(nx**2 + ny**2 + nz**2)
            if abs(nu - NU_CENTER) <= DELTA_NU:
                w = np.exp(-0.5 * ((nu - NU_CENTER)/(DELTA_NU/3))**2)
                if w > 0.001:
                    modes.append((nx, ny, nz, nu, w))

print(f"找到 {len(modes)} 个模式")

# ===== XY切片 (z=0.5) =====
print("计算 XY 切片...")
t0 = time.time()
xv = np.linspace(0.02, 0.98, N_SLICE)
yv = np.linspace(0.02, 0.98, N_SLICE)
X, Y = np.meshgrid(xv, yv)
Z = np.full_like(X, 0.5)

field = np.zeros_like(X)
for nx, ny, nz, nu, w in modes:
    fx = np.sin(nx * np.pi * X / L)
    fy = np.sin(ny * np.pi * Y / L)
    fz = np.sin(nz * np.pi * Z / L)
    field += w * fx * fy * fz

energy = field**2
print(f"  切片完成 {time.time()-t0:.1f}s, 能量峰值={energy.max():.4f}, 最小值={energy.min():.6f}")

# 找峰
ipeak = np.unravel_index(np.argmax(energy), energy.shape)
py, px = ipeak
print(f"  主峰位置: x={xv[px]:.3f}, y={yv[py]:.3f}, z=0.5")

# ===== 3D体素 (低分辨率) =====
print(f"计算 3D 体素 ({N_GRID}³)...")
t0 = time.time()
xv3 = np.linspace(0.05, 0.95, N_GRID)
X3, Y3, Z3 = np.meshgrid(xv3, xv3, xv3, indexing='ij')
field3 = np.zeros((N_GRID, N_GRID, N_GRID), dtype=np.float32)

for i, (nx, ny, nz, nu, w) in enumerate(modes):
    fx = np.sin(nx * np.pi * X3 / L).astype(np.float32)
    fy = np.sin(ny * np.pi * Y3 / L).astype(np.float32)
    fz = np.sin(nz * np.pi * Z3 / L).astype(np.float32)
    field3 += w * fx * fy * fz
    if (i+1) % 50 == 0:
        print(f"  3D: {i+1}/{len(modes)} ({time.time()-t0:.0f}s)")

energy3 = (field3**2).astype(np.float32)
print(f"  3D 完成 {time.time()-t0:.1f}s, 能量峰值={energy3.max():.4f}")

# ===== 单模式对比 =====
top = max(modes, key=lambda m: m[4])
nx0, ny0, nz0, nu0, w0 = top
field_single = np.sin(nx0*np.pi*X/L) * np.sin(ny0*np.pi*Y/L) * np.sin(nz0*np.pi*Z/L)
energy_single = field_single**2
print(f"  单模式({nx0},{ny0},{nz0}) ν={nu0:.3f} 切片峰值={energy_single.max():.4f}")

# ===== 保存 =====
outdir = "/root/ArgoShared/membrane_render"
os.makedirs(outdir, exist_ok=True)
np.savez_compressed(f"{outdir}/field_3d.npz",
    energy=energy3, field=field3, x=xv3,
    NU_CENTER=NU_CENTER, DELTA_NU=DELTA_NU, n_modes=len(modes))
np.savez_compressed(f"{outdir}/slice_xy.npz",
    field=field, energy=energy, x=xv, y=yv,
    z_mid=0.5, n_modes=len(modes))
np.savez_compressed(f"{outdir}/slice_single.npz",
    field=field_single, energy=energy_single, x=xv, y=yv,
    mode=(nx0,ny0,nz0), nu=nu0)

print(f"\n✅ 全部数据保存到 {outdir}/")
print(f"   3D: {N_GRID}³ = {N_GRID**3} 体素")
print(f"   切片: {N_SLICE}² = {N_SLICE**2} 像素")
print(f"   模式数: {len(modes)}")
