# Emergent Discovery SOP — 涌现发现标准操作流程

## 核心思想

> **涌现不是"读一段描述就总结"，而是结构化四步法。**

LLM 在解读 GSEA 结果时，常见的错误是：
1. 只看通路名相似性，捏造生物学联系
2. 抽取几段 description 就急于给出"综合结论"
3. 涌现假说没有 ≥3 条独立证据支撑

本 SOP 定义 **EXTRACT → CLUSTER → SYNTHESIZE → HYPOTHESIZE** 四步法，确保涌现结论可审计、可复现。

## 步骤 1：字段抽取 (EXTRACT)

**输入**：来自 `evidence/msigdb_brief_*.json` 的所有通路元数据。

**动作**：程序化抽取以下字段：

- `description_full` 全文（若有）
- `description_brief` 全文（若有）
- `pmid`、`doi`、`pub_title`（若有）
- `authors` 列表（若有）
- `exact_source`（若有）

**R 代码示例**：
```r
extract_fields <- function(brief_json) {
  list(
    brief    = brief_json$description_brief,
    full     = brief_json$description_full,
    pmid     = brief_json$PMID,
    authors  = brief_json$authors,
    pub_title = brief_json$pub_title,
    source   = brief_json$exact_source
  )
}
```

**Python 代码示例**：
```python
def extract_fields(brief):
    return {
        'brief': brief.get('description_brief'),
        'full': brief.get('description_full'),
        'pmid': brief.get('PMID'),
        'authors': brief.get('authors'),
        'pub_title': brief.get('pub_title'),
        'source': brief.get('exact_source')
    }
```

## 步骤 2：关键词聚类 (CLUSTER)

**目标**：从所有 BRIEF/FULL 文本中**自动抽取高频生物学概念**。

### 关键词类别

| 类别 | 示例 |
|---|---|
| **细胞器 / 复合物** | 线粒体、复合物 I / II / III / IV、NADH、F1F0-ATPase |
| **代谢过程** | 氧化磷酸化、糖酵解、脂肪酸代谢、谷氨酰胺代谢 |
| **细胞过程** | 自噬、凋亡、坏死、铁死亡、纤维化、上皮间充质转化 |
| **信号通路** | NF-κB、mTOR、JAK-STAT、PI3K-AKT、Wnt、TGF-β |
| **免疫相关** | 巨噬细胞极化、T 细胞激活/耗竭、B 细胞、NK 细胞 |
| **细胞类型** | T cell、macrophage、fibroblast、endothelium、epithelium |
| **病理过程** | 炎症、缺氧、氧化应激、DNA 损伤修复 |

### 推荐工具

**R (tidytext)**：
```r
library(tidytext)
df <- tibble(id = names(briefs), text = briefs)
tokens <- df %>% unnest_tokens(word, text)
tokens <- tokens %>% anti_join(stop_words)
counts <- tokens %>% count(word, sort = TRUE)
```

**Python (scikit-learn)**：
```python
from sklearn.feature_extraction.text import TfidfVectorizer
corpus = [brief['full'] or brief['brief'] for brief in briefs]
vectorizer = TfidfVectorizer(stop_words='english', max_features=100)
X = vectorizer.fit_transform(corpus)
scores = X.sum(axis=0).A1
terms = vectorizer.get_feature_names_out()
top_terms = sorted(zip(terms, scores), key=lambda x: -x[1])[:30]
```

## 步骤 3：跨通路主题归纳 (SYNTHESIZE)

**目标**：按聚类结果把 top 显著通路归入 N 个主题（N=3-5，取决于数据）。

### 主题命名原则

**关键**：主题命名必须有 BRIEF/FULL 文本支持，**不能**仅凭通路名推断。

### 示例

**例 1：线粒体呼吸链**
- KEGG_PARKINSONS_DISEASE → "α-synuclein/复合物 I..."
- KEGG_HUNTINGTONS_DISEASE → "Complex II + Complex III..."
- KEGG_ALZHEIMERS_DISEASE → "Complex IV + 凋亡..."
- GOBP_MITOCHONDRIAL_ELECTRON_TRANSPORT_...
- → 共同主题：**"线粒体复合物 / 氧化磷酸化受损"**

**例 2：T 细胞免疫激活**
- GOBP_T_CELL_ACTIVATION
- GOBP_T_CELL_PROLIFERATION
- HALLMARK_TNFA_SIGNALING_VIA_NFKB
- C2_CGP_T_CELL_ACTIVATED_UP
- → 共同主题：**"T 细胞激活 + NF-κB 炎症信号"**

### 注意事项

❌ 错误：仅凭"PARKINSONS_DISEASE"就归入"神经退行性病变"主题

✅ 正确：先看 FULL，发现是 Complex I 基因集，归入"线粒体呼吸链"

## 步骤 4：涌现假说生成 (HYPOTHESIZE)

**目标**：基于跨主题的共同概念，生成新的生物学假说。

### 假说模板

> 在 [组织] 的 [处理] 背景下，多个原本独立的 MSigDB 基因集共同指向 [共同机制]，提示 [涌现机制] 可能作为 [核心驱动] 参与 [表型]。

### 支撑要求

每个涌现假说必须引用 **≥3 条 MSigDB 通路的 description_brief/full 作为支撑**。

### 示例

**涌现假说**：
> 在放射治疗的小鼠肝脏中，多个原本独立的 MSigDB 基因集（KEGG_PARKINSONS_DISEASE, KEGG_HUNTINGTONS_DISEASE, KEGG_OXIDATIVE_PHOSPHORYLATION, GOBP_MITOCHONDRIAL_RESPIRATORY_CHAIN_COMPLEX_I）共同指向"线粒体复合物 I / 氧化磷酸化"受损，提示 RT 可能通过**线粒体复合物 I 抑制**作为核心驱动机制参与肝细胞能量危机表型。

**支撑**：
1. KEGG_PARKINSONS_DISEASE FULL: "...alpha-synuclein/复合物 I...mitochondrial impairment..."
2. KEGG_HUNTINGTONS_DISEASE FULL: "...Complex II + Complex III...mitochondrial dysfunction..."
3. GOBP_MITOCHONDRIAL_RESPIRATORY_CHAIN_COMPLEX_I BRIEF: "The process of..."

## 跨平台适配

本 SOP 适用于任何能输出通路名 + NES + description 的 GSEA 工具：

| 平台 | description 来源 |
|---|---|
| GSEAlens + MSigDB MCP | `mcp__msigdb__get_geneset_brief` |
| GSEAlens + Tier 2 | `scripts/query_msigdb.py get_geneset_brief` |
| GSEAlens + Tier 3 (降级) | **跳过 SYNTHESIZE**（无 description 来源） |
| clusterProfiler + msigdbr | msigdbr 仅提供基因列表，无 description → 需用户自备 |
| fgsea | 同 clusterProfiler |

## Tier 3 降级模式

当只有通路名（无 description）时：
- EXTRACT 阶段：抽取通路名相似性（如 KEGG_PARKINSONS_DISEASE 和 KEGG_HUNTINGTONS_DISEASE 都含 "KEGG_"）
- CLUSTER 阶段：仅基于名称聚类（精度低）
- **SYNTHESIZE 阶段：跳过**（无文本证据，无法命名主题）
- **HYPOTHESIZE 阶段：跳过**（仅给"假说候选"，不视为结论）

报告必须标注 `msigdb_tier: degraded`。

## 进一步阅读

- NES 方向框架：[nes_direction_framework.md](nes_direction_framework.md)
- 方向反转分类：[flip_classification.md](flip_classification.md)
- 平台适配：[porting_guide.md](porting_guide.md)