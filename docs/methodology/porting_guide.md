# Porting Guide — 将方法论适配到其他 GSEA 平台

## 目标读者

- **平台开发者**：想让自己的工具支持 gsealens-explorer 的方法论
- **GSEA 用户**：想用本方法论解读 clusterProfiler / fgsea / enrichit 的输出

## 方法论的 3 个核心组件

| 组件 | 平台依赖性 | 适配难度 |
|---|---|---|
| **NES 方向框架** (§nes_direction_framework.md) | 低 | 🟢 简单 |
| **反转分类** (§flip_classification.md) | 低 | 🟢 简单 |
| **涌现发现 SOP** (§emergent_discovery_sop.md) | 中 | 🟡 中等 |

## 平台数据契约（最小集）

要让方法论能跑起来，你的 GSEA 工具至少需要输出：

```r
result <- list(
  pathway_id      = "HALLMARK_HYPOXIA",       # 通路唯一标识
  pathway_name    = "Hypoxia",                # 人类可读名字（可选）
  NES             = 1.85,                     # 标准化富集分数
  pvalue          = 0.001,                    # 原始 p 值
  p.adjust        = 0.012,                    # FDR 校正 p 值
  leading_edge    = "VEGFA,LDHA,PGK1,...",    # leading edge 基因
  contrast_id     = "RT_vs_Model",            # 对比组标识
  left_group      = "RT",                     # 左组（treatment）
  right_group     = "Model",                  # 右组（control）
  description     = "Genes up-regulated..."   # 通路描述（如有）
)
```

## 各平台适配指南

### clusterProfiler 适配

clusterProfiler 的 `gseGO` / `gseKEGG` / `gseNES` 返回 `gseaResult` S4 对象。

**字段映射**：

| 通用契约 | clusterProfiler 字段 |
|---|---|
| `pathway_id` | `@result$ID` |
| `pathway_name` | `@result$Description` |
| `NES` | `@result$NES` |
| `pvalue` | `@result$pvalue` |
| `p.adjust` | `@result$p.adjust` |
| `leading_edge` | `@result$core_enrichment` |
| `contrast_id` | （需自备对比组注册表） |
| `left_group` | （需自备对比组注册表） |
| `right_group` | （需自备对比组注册表） |
| `description` | （来自 msigdbr + 自定义元数据） |

**R 适配代码**：
```r
# 将 clusterProfiler 结果转成通用契约
gseaResult_to_canonical <- function(gsea_result, contrast_id, left_g, right_g) {
  df <- gsea_result@result
  data.frame(
    pathway_id   = df$ID,
    pathway_name = df$Description,
    NES          = df$NES,
    pvalue       = df$pvalue,
    p.adjust     = df$p.adjust,
    leading_edge = df$core_enrichment,
    contrast_id  = contrast_id,
    left_group   = left_g,
    right_group  = right_g,
    stringsAsFactors = FALSE
  )
}
```

### fgsea 适配

fgsea 返回一个 data.frame。

**字段映射**：

| 通用契约 | fgsea 字段 |
|---|---|
| `pathway_id` | `pathway` |
| `NES` | `NES` |
| `pvalue` | `pval` |
| `p.adjust` | `padj` |
| `leading_edge` | （从 `leadingEdge` 列提取） |
| `description` | （fgsea 不提供） |

**R 适配代码**：
```r
fgsea_to_canonical <- function(fgsea_res, contrast_id, left_g, right_g,
                                pathway_descriptions = list()) {
  data.frame(
    pathway_id   = fgsea_res$pathway,
    pathway_name = fgsea_res$pathway,  # fgsea 没有 description
    NES          = fgsea_res$NES,
    pvalue       = fgsea_res$pval,
    p.adjust     = fgsea_res$padj,
    leading_edge = sapply(fgsea_res$leadingEdge, paste, collapse=","),
    contrast_id  = contrast_id,
    left_group   = left_g,
    right_group  = right_g,
    description  = sapply(fgsea_res$pathway,
                          function(p) pathway_descriptions[[p]] %||% ""),
    stringsAsFactors = FALSE
  )
}
```

### enrichit 适配

enrichit 行为类似 clusterProfiler（S4 对象，class 也叫 `gseaResult`）。

字段映射与 clusterProfiler 相同，但需注意：
- `qvalue` 字段名是 `qvalues`（复数）
- `setSize` 字段含义相同
- 字段映射代码可与 clusterProfiler 共享

## 反转分类适配

`flip_classification.md` 的 R 代码是平台无关的，只要你的 data.frame 有 `NES` 和 `p.adjust` 列即可：

```r
classify_flip_mode <- function(rt_nes, rtp_nes, threshold = 1.5) {
  # 同 docs/methodology/flip_classification.md 中代码
}
```

## 涌现发现 SOP 适配

涌现发现 SOP 高度依赖**通路描述（description）**的获取：

| 平台 | description 来源 |
|---|---|
| GSEAlens + MSigDB MCP | 官方 DB，含 BRIEF/FULL/PMID |
| clusterProfiler + msigdbr | msigdbr 不提供 description → 需自备映射表 |
| fgsea | 无 description → 仅基于通路名聚类（精度低） |
| enrichit | 同 clusterProfiler |

### 自建 description 映射（无 MSigDB MCP 的场景）

对于 clusterProfiler / fgsea 用户，可以：

1. **下载 MSigDB 官方 SQLite DB**（289 MB）— 与 GSEAlens 用户相同
2. 用 `scripts/query_msigdb.py get_geneset_brief` 查询 description
3. 在脚本内 join 到 GSEA 结果表

**Python 示例**：
```python
import subprocess, json

def get_brief(name):
    result = subprocess.run(
        ['python', 'scripts/query_msigdb.py', 'get_geneset_brief',
         '--params', json.dumps({'name': name})],
        capture_output=True, text=True, encoding='utf-8'
    )
    return json.loads(result.stdout)

# 批量获取 top 通路
top_pathways = gsea_result.nlargest(20, 'NES')['ID']
for pid in top_pathways:
    brief = get_brief(pid)
    print(f'{pid}: {brief.get("description_brief", "")}')
```

## 完整工作流示例（clusterProfiler 用户）

```r
library(clusterProfiler)
library(msigdbr)

# 1. 运行 GSEA
gsea_res <- gseGO(geneList = gene_list, OrgDb = org.Hs.eg.db, ont = "BP")

# 2. 转换为通用契约
canonical <- gseaResult_to_canonical(
  gsea_res,
  contrast_id = "RT_vs_Model",
  left_g = "RT",
  right_g = "Model"
)

# 3. 应用 |NES| 框架（按 confidence 分级）
canonical$absNES <- abs(canonical$NES)
canonical$Enriched_In <- ifelse(canonical$NES > 0, canonical$left_group, canonical$right_group)
canonical$Confidence <- ifelse(
  canonical$absNES >= 1.5 & canonical$p.adjust < 0.05, "High",
  ifelse(canonical$absNES >= 1.0 & canonical$p.adjust < 0.25, "Medium", "Low")
)

# 4. （多对比组时）应用反转分类
if (exists("gsea_res_rtp_vs_rt")) {
  canonical_rtp <- gseaResult_to_canonical(gsea_res_rtp_vs_rt, "RTP_vs_RT", "RTP", "RT")
  merged <- merge(canonical, canonical_rtp, by = "pathway_id", suffixes = c(".rt", ".rtp"))
  merged$flip_mode <- mapply(classify_flip_mode, merged$NES.rt, merged$NES.rtp)
}

# 5. 获取 BRIEF/FULL（如果装了 MSigDB DB）
# 通过 R 调用 Python 或直接读 SQLite
```

## 与本项目 gsealens-explorer 的差异

| 维度 | gsealens-explorer | 其他平台用户 |
|---|---|---|
| **数据格式** | GSEAlens Capsule RDS（含多对比组 + contrast_registry） | 通常每次运行 1 个对比组 |
| **MSigDB 集成** | 三层访问策略（MCP / SQLite / RDS-only） | 通常需自己 join msigdbr |
| **涌现发现** | EXTRACT / CLUSTER / SYNTHESIZE / HYPOTHESIZE 四步法 | 同样的方法论可复用 |
| **报告输出** | 自动生成 Markdown 报告 | 需用户自行实现 |

## 反馈与贡献

如果您实现了本方法论的某个平台适配，欢迎：
1. 在 [Issues](https://github.com/DDL095/gsealens-explorer/issues) 报告您的经验
2. 提交 PR 添加适配代码到 `examples/` 目录
3. 更新本指南，分享您的案例

## 进一步阅读

- NES 方向框架：[nes_direction_framework.md](nes_direction_framework.md)
- 反转分类：[flip_classification.md](flip_classification.md)
- 涌现 SOP：[emergent_discovery_sop.md](emergent_discovery_sop.md)
- MSigDB DB 设置：[../msigdb_mcp_setup.md](../msigdb_mcp_setup.md)