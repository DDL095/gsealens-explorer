# Methodology — Platform-Agnostic Interpretation Framework

> gsealens-explorer 是一等公民项目，专精 **GSEAlens Capsule** RDS 解读。
> 但其核心**解读方法论**（|NES| enrichment direction framework、方向反转分类、涌现发现 SOP）平台无关，可以被其他 GSEA 工具（clusterProfiler / fgsea / enrichit）的用户参考并自行适配。
>
> 本目录将这些方法论从项目代码与 RDS 字段绑定中抽象出来，整理成可移植的规范。

## 文档结构

| 文档 | 内容 | 适用对象 |
|---|---|---|
| [nes_direction_framework.md](nes_direction_framework.md) | \|NES\| enrichment direction framework 的核心定义、3 级置信度、绝对禁忌 | 所有 GSEA 解读场景 |
| [flip_classification.md](flip_classification.md) | 跨对比组方向反转的精确分类（P-Suppression / P-Restoration / RTP-Only / True Flip） | 多对比组 GSEA |
| [emergent_discovery_sop.md](emergent_discovery_sop.md) | 涌现发现 4 步法（EXTRACT / CLUSTER / SYNTHESIZE / HYPOTHESIZE） | 任何需要从大量通路中提炼生物学主题的场景 |
| [porting_guide.md](porting_guide.md) | 如何将本方法论适配到其他 GSEA 平台（clusterProfiler / fgsea / enrichit） | 平台开发者、GSEA 用户 |

## 核心原则

### 1. NES 不是"激活/抑制"

NES 衡量的是**基因集成员在排序列表中的位置集中度**，不是基因表达的上调/下调。

- NES > 0：成员集中在 `{left_group}` 排序顶部
- NES < 0：成员集中在 `{right_group}` 排序顶部
- **NES 的符号只表示富集方向，不表示基因表达变化方向**

❌ 错误：
> "NEG 数量大于 POS，提示基因集被抑制"
> "该通路在 treatment 组被激活"
> "上调通路" / "下调通路"

✅ 正确：
> "更多通路富集在 control 组，说明 treatment 组的基因表达谱在某些方面更接近 control"
> "该通路富集在 treatment 组（NES>0），说明其成员在 treatment 组表达更高"
> "POS 通路数: N, NEG 通路数: M"（仅描述数量）

### 2. 富集方向必须绑定对比组角色

富集方向的解读必须**明确对比组的 left/right 角色**：

```
RT_vs_Model:
  - NES > 0 → 富集在 RT
  - NES < 0 → 富集在 Model

RTP_vs_RT:
  - NES > 0 → 富集在 RTP
  - NES < 0 → 富集在 RT
```

不能跨对比组直接说"富集回 Model"——必须先确认每个对比组的 left/right 角色。

### 3. 跨对比组解读需要"轴"概念

| 对比组 | 比较轴 | 含义 |
|---|---|---|
| RT_vs_Model | "RT 损伤轴" | RT 与 Model 的偏离 |
| RTP_vs_RT | "P 药净效应轴" | RTP 与 RT 的差异 = P 药加入的净效应 |

P 压制 vs P 重启 取决于通路在 RT_vs_Model 中的方向：
- 如果通路在 RT_vs_Model 中 NES<0（Model 富集）→ P 药在 RTP 中重新激活 → "P 重启"
- 如果通路在 RT_vs_Model 中 NES>0（RT 富集）→ P 药在 RTP 中压制 → "P 压制"

### 4. 涌现发现需要"证据支撑"

主题命名必须有 BRIEF/FULL 文本支持，**不能**仅凭通路名推断。

每个涌现假说必须引用 ≥3 条基因集 description 作为支撑。

## 跨文档引用

- **本项目使用该方法论的具体实例**：见 [../SKILL.md §2](../SKILL.md)（gsealens-explorer 主 SKILL 文档）
- **方向反转的精确分类 R 代码**：见 [flip_classification.md](flip_classification.md)
- **涌现发现的 GSEA Capsule 集成**：见 [../SKILL.md §3a](../SKILL.md)（三层 MSigDB 访问策略）

## 引用本方法论

如果您在论文或项目中使用了本方法论，请引用：

> gsealens-explorer project. (2026). NES Direction Framework for GSEA Interpretation.
> GitHub: https://github.com/DDL095/gsealens-explorer/tree/main/docs/methodology
> （具体引用信息见 [../../CITATION.cff](../../CITATION.cff)）