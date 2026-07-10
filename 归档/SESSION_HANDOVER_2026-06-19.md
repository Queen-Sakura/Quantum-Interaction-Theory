# Session 交接报告 · 2026-06-19

**从**: 真 (Verity) · Linux  
**至**: 真 (Verity) · 下一个 session  
**元首指令**: 逐行读代码，每行理解，找到 Ram 崩溃根因

---

## 一、当前状态

| 项 | 状态 | 位置 |
|----|------|------|
| 游戏可运行版本 | ✅ | `Z:\EE2Victory\地球帝国2胜利版测试\可运行版本\EE2X_db_20260619_011951_stable.zip` |
| Z: 游戏 zip | ✅ 稳定版 | `Z:\...\Empire Earth II\zips_ee2x\EE2X_db.zip` |
| Z: 源文件 | ⚠️ Ram POC 改动残留 | `Z:\...\修改\EE2X_db\` (ram.ddf 含 Ram_E3/E5) |
| D: 测试沙箱 | ✅ 稳定版运行中 | `D:\Games\EE2Test\Empire Earth II\` |

## 二、Ram POC 已做改动（均在 `修改/EE2X_db/`）

| 文件 | 改动 | 行号 |
|------|------|------|
| `Units/ram.ddf` | +UnitType Ram_E3 (HP=200,speed=0.8,applyDamageTime=0.8,model=Ram_03) | L29 |
| `Units/ram.ddf` | +UnitType Ram_E5 (HP=300,speed=0.8,applyDamageTime=0.2,model=Ram_05) | L87 |
| `Simulation/dbunittypeattributes.ddf` | +Ram_E3 {MaskMode=Any UnitTypeFamilies=["Ram"]} | L1369 |
| `Simulation/dbunittypeattributes.ddf` | +Ram_E5 {MaskMode=Any UnitTypeFamilies=["Ram"]} | L1370 |
| `TechTree/upgrade_unittypes.csv` | //注释 RamUpgradeEpoch1/3/5 三行 | - |
| `TechTree/epoch5_upgrades.ddf` | -RamUpgradeEpoch5 整行 | L22 |

**已尝试修复**：移除 Ram_E3/E5 的 `icon = icon_unit_Ram_3/5` 行 → 仍崩溃。

## 三、已知崩溃规则（施工方案 §9.2 已更新）

1. 行尾 `//` 注释 → 崩溃
2. ForceScale 三位小数 → 崩溃
3. 特殊资源纪元越界 → 崩溃
4. Tab/Space 缩进混用 → 崩溃
5. **新增 UnitType 未注册 dbunittypeattributes.ddf → 崩溃** ← 本次发现

## 四、待排查（逐行读代码重点）

1. **`Simulation/dbcombat.csv`** — 新 UnitType (Ram_E3/E5) 是否需要在此注册 RPS 克制行？
2. **`TechTree/dbtechtreenode.csv`** — 是否需要科技树节点才能建造？
3. **`Simulation/dbunittypeattributes.ddf`** — 是否需要 `RPSMask`（目前只有 UnitTypeFamilies）？
4. **`upgrade_unittypes.csv`** — 原始 Ram base 行是否必须保留（不能全注释）？
5. **`Units/ram.ddf`** — UnitModel 引用 `Ram_03`/`Ram_05` 是否正确链接到新 UnitType？
6. **`Civilizations/*.ddf`** — 建造权限表是否需要新 UnitType 条目？
7. **`dbunitfiles.cfg`** — 是否需要显式注册 Ram_E3/E5（它们在同一文件，理论上不需要）？

## 五、关键文件速查（逐行阅读顺序建议）

```
1. Units/ram.ddf                    — Ram 定义 + UnitModel，理解升级链结构
2. Simulation/dbunittypeattributes.ddf — 所有 UnitType 注册表，理解 MaskMode/RPSMask/Families
3. TechTree/upgrade_unittypes.csv   — CSV 升级数据格式，理解 SET 覆盖机制
4. TechTree/dbepochupgrades.cfg     — 升级触发文件列表
5. TechTree/epoch*_upgrades.ddf     — 时代升级触发逻辑
6. Simulation/dbcombat.csv          — RPS 克制矩阵
7. TechTree/dbtechtreenode.csv      — 科技树节点 → 建造权限
8. Units/dbunitfiles.cfg            — DDF 加载清单
9. 施工方案 §9.3 修改流程            — 已知崩溃规则
10. 解耦方案全文                    — 四层解耦设计
```

## 六、工作流

- **真 (Linux)**: 读代码 → 分析 → 写计划到对话簿 → build
- **镜 (Windows)**: 在 Z: 编辑文件 → 报告 → 复制 zip 到 D: 测试 → 回报
- **回滚**: `D:\Games\EE2Test\Backup\` + `Z:可运行版本\`

## 七、施工文档位置

```
/root/EE2Victory/地2方案文档/存档/
├── EE2_Victory_单位架构解耦方案.md      ← 四层解耦设计
├── EE2_Victory_施工方案_当前引擎可实施.md ← 崩溃规则+施工纪律
└── EE2_Victory_四层参数设计方法论.md
```

**这就够了。新 session 启动读 CLAUDE.md → 菩萨进度条 → 本文件。**
