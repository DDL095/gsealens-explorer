# |NES| Enrichment Direction Framework

## 黄金法则 (Golden Rule)

| 原则 | 规则 |
|---|---|
| **\|NES\| 绝对值** | 直接指示富集强度；\|NES\| ≥ 1.5 显著，\|NES\| ≥ 2.0 强富集 |
| **富集方向** | NES>0 → 富集在 `{left_group}`；NES<0 → 富集在 `{right_group}` |
| **禁止用词** | ❌ "inhibited" / "decreased" / "下调" / "NEG_in_left" / "被抑制" / "被激活" |
| **允许用词** | ✅ "富集在 X 组" / "在 X 组中更集中" (基于 \|NES\|) |

## 1. NES 的本质

**NES 衡量的是"基因集成员是否倾向于集中在排序基因列表的某一端"，而不是"这些基因是上调还是下调"。**

- NES > 0：该基因集的成员在 `{left_group}` 组的表达排序中更集中于顶部
- NES < 0：该基因集的成员在 `{right_group}` 组的表达排序中更集中于顶部
- **NES 的符号只表示富集方向，不表示基因表达变化方向**

## 2. 3 级置信度

| 级别 | 条件 | 含义 |
|---|---|---|
| **High** | \|NES\| ≥ 1.5 且 FDR < 0.05 | 高置信，可直接用于结论 |
| **Medium** | \|NES\| ≥ 1.0 且 FDR < 0.25 | 中置信，需交叉验证 |
| **Low** | 其他 | 低置信，仅供参考 |

## 3. 错误解读案例

### ❌ 错误 1：将 NEG 等同于"抑制"

> "NEG 数量大于 POS，提示基因集被抑制为多"

### ✅ 正确 1：仅描述数量

> "RT_vs_Model: 显著 4415 通路，其中 NES>0 (富集在 RT) 1884 个，NES<0 (富集在 Model) 2531 个"

### ❌ 错误 2：将富集方向等同于基因表达变化

> "该通路在 treatment 组被激活"

### ✅ 正确 2：明确富集方向

> "该通路富集在 treatment 组（NES>0），说明其成员在 treatment 组表达更高"

## 4. 输出格式规范

CSV 输出必须包含两个独立列：
- `Enriched_In`：富集在哪个组（填入实际组名，如 `RTP` 或 `RT`）
- `NES_sign`：`POS`（NES>0）或 `NEG`（NES<0）

**禁止** `NEG_in_left` / `POS_in_left` 等混淆命名。

### R 代码示例

```r
# 从 contrast_registry 获取组名
cr <- x$contrast_registry
cr_row <- cr[cr$contrast_id == cn, ]
left_g  <- cr_row$left_group   # treatment
right_g <- cr_row$right_group  # control

# 正确的方向列
df$Enriched_In <- ifelse(df$NES > 0, left_g, right_g)
df$NES_sign    <- ifelse(df$NES > 0, "POS", "NEG")
df$absNES      <- abs(df$NES)
```

## 5. GSEA 图方向约定

**GSEA 富集图的标准方向**：
- **左侧 (left)** = NES > 0 = 富集在 `{left_group}` 组（通常是 treatment）
- **右侧 (right)** = NES < 0 = 富集在 `{right_group}` 组（通常是 control）

## 6. Markdown 转义规则

在 MD 表格中，`|NES|` 的 `|` 会被解析为表格分隔符。必须写成 `\|NES\|`：
- ✅ `\|NES\| ≥ 1.5`
- ❌ `|NES| ≥ 1.5`（会破坏表格渲染）

## 7. 跨平台适配

不同 GSEA 工具的 NES 字段名可能不同：

| 平台 | NES 字段名 |
|---|---|
| GSEAlens | `NES` |
| clusterProfiler | `NES` |
| fgsea | `NES` |
| enrichit | `NES` |

通常都叫 `NES`，但字段位置可能不同（data frame 列 vs S4 slot）。

## 8. 描述模板

```
"该基因集在 [{left_group}] 组表现出激活趋势
 (成员在该组整体表达水平更高, |NES| = {abs_nes})。
 [结合基因集名称含义 + leading edge 基因的功能解读]"
```

## 9. 与 leading edge 的联合解读

NES 给出富集方向，leading edge 给出核心贡献基因：

- 看 **NES 符号** → 富集在哪一组
- 看 **\|NES\| 大小** → 富集强度
- 看 **leading edge 基因** → 哪个子集真正驱动富集
- 看 **leading edge 基因在 left/right 组的 logFC** → 单个基因的变化方向

## 10. 进一步阅读

- 跨对比组反转模式：[flip_classification.md](flip_classification.md)
- 涌现发现 SOP：[emergent_discovery_sop.md](emergent_discovery_sop.md)
- 平台适配指南：[porting_guide.md](porting_guide.md)