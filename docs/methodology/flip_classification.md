# Flip Classification — 跨对比组方向反转的精确分类

## 背景问题

多对比组 GSEA 解读时（如 RT_vs_Model + RTP_vs_RT），常见的错误是把不同对比组的 right_group 混为一谈：

> ❌ 错误："在 RTP_vs_RT 中 NES<0，即富集回 Model 方向"
>
> 这句话是错的，因为 RTP_vs_RT 的 right_group=RT 而非 Model。

本规范定义 5 种精确的反转模式，避免这类错误。

## 5 种反转模式

### 模式总览

| 模式 | RT_vs_Model NES | RTP_vs_RT NES | 中文含义 | 典型例子 |
|---|---|---|---|---|
| **P 重启 (P-Restoration)** | **< 0** (富集 Model) | **> 0** (富集 RTP) | RT 损伤下沉的程序，P 药在 RTP 中**重新激活** | HYPOXIA, EMT, GLYCOLYSIS, COLLAGEN_FORMATION, MYC_TARGETS |
| **P 压制 (P-Suppression)** | **> 0** (富集 RT) | **< 0** (富集 RT，因为 right_group=RT) | RT 富集的程序，P 药让 RT 端相对富集强度**下降** | IFN-γ, ALLOGRAFT, OXPHOS, JAK-STAT, TCR, KRAS_UP |
| **RTP 独有 (RTP-Only)** | NS | **> 0** (富集 RTP) | RT 不驱动，P 药特有贡献 | HEME_METABOLISM, E2F_TARGETS, G2M_CHECKPOINT |
| **RT 独有 (RT-Only)** | **任意显著** | NS | 仅 RT 驱动，P 药无显著效应 | (需根据具体通路看) |
| **不变 (Stable)** | **任意** | **同向** | P 药未改变富集方向 | (需根据具体通路看) |
| **真反转 (True Flip)** | **> 0** (富集 RT) | **< 0** (富集 RT) | 同符号变化但 \|NES\| 反转 | (少见) |

### 关键：跨轴解读需要"轴"概念

每对对比组构成一条独立的"比较轴"(axis)：

| 对比组 | 比较轴 | 典型含义 |
|---|---|---|
| RT_vs_Model | "RT 损伤轴" | RT 与 Model 的偏离 |
| RTP_vs_Model | "联合治疗轴" | RTP 与 Model 的偏离 |
| RTP_vs_RT | "P 药净效应轴" | RTP 与 RT 的差异 = P 药加入的净效应 |

**P 压制 vs P 重启 取决于通路在 RT_vs_Model 中的方向**：
- 通路在 RT_vs_Model 中 NES<0（Model 富集）→ P 药在 RTP 中重新激活 → "P 重启"
- 通路在 RT_vs_Model 中 NES>0（RT 富集）→ P 药在 RTP 中压制 → "P 压制"

## 分类算法（R 代码）

```r
classify_flip_mode <- function(rt_nes, rtp_nes, threshold = 1.5) {
  # rt_nes: NES in RT_vs_Model
  # rtp_nes: NES in RTP_vs_RT
  # Returns: one of "p_restoration", "p_suppression", "rtp_only",
  #          "rt_only", "stable", "true_flip", "ambiguous"

  rt_sig  <- !is.na(rt_nes)  && abs(rt_nes)  >= threshold
  rtp_sig <- !is.na(rtp_nes) && abs(rtp_nes) >= threshold

  if (!rt_sig && !rtp_sig) return("stable")
  if (rt_sig && !rtp_sig)  return("rt_only")
  if (!rt_sig && rtp_sig)  return("rtp_only")

  # Both significant
  if (sign(rt_nes) != sign(rtp_nes)) {
    if (rt_nes < 0 && rtp_nes > 0) {
      # RT 富集 Model → RTP 富集 RTP (P 重启)
      return("p_restoration")
    } else {
      # RT 富集 RT → RTP 富集 Model (少见, 真反转)
      return("true_flip")
    }
  } else {
    # Same sign
    if (sign(rt_nes) > 0) {
      return("p_suppression")
    } else {
      return("ambiguous")
    }
  }
}
```

## 文本表述规范

| 错误措辞 ❌ | 正确措辞 ✅ |
|---|---|
| "在 RTP_vs_RT 中 NES<0，即富集回 Model 方向" | "在 RTP_vs_RT 中 NES<0，意味着该通路在 RT 端仍相对富集（因为 right_group=RT），P 药压制了 RT 端的相对富集强度" |
| "通路从 RT 端回到 Model 端" | "P 药压制了 RT 端的相对富集（在 RT↔Model 这条轴上，RTP 端表型更接近 Model）" |
| "在 RTP_vs_RT 中，Model 富集" | "在 RTP_vs_RT 中，富集在 RT 端" |
| "通路在 RTP 中下调" | "通路在 RTP 端的相对富集强度下降（NES 减小）" |

## 关键警示："接近 Model" ≠ "回到 Model"

- "P 药使 RTP 端的转录表型**更接近** Model 端" — 这句话**对**（在 RT↔Model 这条轴上，RTP 端的偏离幅度减小）
- "P 药使 RTP 端**回到** Model 端的基线水平" — 这句话**错**（RTP 端与 Model 端仍有显著差异，RTP_vs_Model 中仍有大量显著通路）

推荐用"更接近"（比较距离减小）替代"回到"（完全重合）。

## 跨平台适配

本分类方法适用于任何能输出 NES + FDR 的 GSEA 工具：

| 平台 | NES 字段位置 |
|---|---|
| GSEAlens | `x$results[[cn]]$data@result$NES` |
| clusterProfiler | `gseaResult@result$NES` |
| fgsea | `fgseaRes$NES` |
| enrichit | `enrichit_result$NES` |

所有平台都有 NES + padj，分类逻辑不变。

## 应用案例

### 案例 1：放射治疗 + 增敏药（RT + P）

| 对比组 | NES>0 富集在 | NES<0 富集在 |
|---|---|---|
| RT_vs_Model | RT | Model |
| RTP_vs_RT | RTP | RT |
| RTP_vs_Model | RTP | Model |

| 通路 | RT_vs_Model NES | RTP_vs_RT NES | 模式 |
|---|---|---|---|
| HYPOXIA | -1.8 (Model) | +1.6 (RTP) | **P 重启** |
| OXPHOS | +2.0 (RT) | -1.4 (RT) | **P 压制** |
| HEME_METABOLISM | NS | +1.7 (RTP) | **RTP 独有** |
| INTERFERON_GAMMA_RESPONSE | +1.9 (RT) | NS | RT 独有 |

## 进一步阅读

- NES 方向框架：[nes_direction_framework.md](nes_direction_framework.md)
- 涌现发现 SOP：[emergent_discovery_sop.md](emergent_discovery_sop.md)
- 平台适配：[porting_guide.md](porting_guide.md)