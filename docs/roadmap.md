# 路线图

> 本文档持续更新。所列日期仅为参考，并非承诺。

## 最终目标

让 gsealens-explorer 成为 **GSEAlens Capsule 的专用解读器**，能在多个 agent 平台适配使用。

本项目的解读方法论（|NES| enrichment direction framework、方向反转分类、涌现发现 SOP）平台无关，独立公开在 [`docs/methodology/`](methodology/)，供其他 GSEA 平台用户参考自适配。

## v0.6 —正式可用基础（下一版本）

主题： **测试体系 + 多 SA 架构 POC**。

### v0.6.0 测试框架 + 合成测试数据

- `tests/testdata/synthetic_gsea.rds` —— 脚本生成的 mock GSEAlens Capsule，包含 5 个 contrast × 50 条 Hallmark 通路，并预置若干方向翻转案例（true_flip、p_suppression、p_restoration）。
- `tests/test_skill_structure.py` —— 校验 frontmatter 有效性、GSEAlens profile ↔ script 交叉引用、对 SKILL.md 本身做反模式正则检测。
- `tests/test_quality_gate.py` —— 向 G1/G2/G3 喂入已知的 PASS 与 FAIL 报告，断言判决正确。
- `tests/trigger_consistency.py` —— 校验所有部署位置的 GSEAlens 聚焦关键词触发一致性。
- 接入 GitHub Actions CI，在每个 PR 上跑冒烟测试。

### v0.6.1 — 多 SA 并行架构 POC

这是 v0.6 的差异化特性。不再由单个 SA 顺序完成所有工作，而是拆分为 fan-out / fan-in 模式，共享同一个 R REPL。完整设计见 [`multi_sa_architecture.md`](multi_sa_architecture.md)。

## v0.7 — MSigDB 硬依赖工具链 + 可视化

### MSigDB 硬依赖策略

MSigDB 本地 MCP 是本项目的核心特色基础设施，通过抓取 MSigDB 官方 35,361 个基因集的 BRIEF/FULL/PMID/AUTHORS/GEOID 元数据，最大化增强解读与数据处理能力。

**三层访问策略（S0 自动检测，按优先级降级）**：

| Tier                         | 数据源                                  | 能力                                                                                               | 触发条件                          |
| ---------------------------- | --------------------------------------- | -------------------------------------------------------------------------------------------------- | --------------------------------- |
| **Tier 1**（推荐）     | `mcp__msigdb__*` 6 个工具             | 全部能力，接口最干净                                                                               | 已配置 `msigdb` MCP             |
| **Tier 2**（fallback） | `scripts/query_msigdb.py` 直读 SQLite | 数据等价于 MCP，需 subagent 构造调用                                                               | MCP 不可用但 `msigdb.db` 可访问 |
| **Tier 3**（降级）     | RDS 内 `Description` 字段             | 仅通路名 + NES，**无 BRIEF/FULL/PMID**；涌现 SOP 跳过 SYNTHESIZE 阶段；报告标注 `degraded` | MCP 与 db 都不可用                |

**降级行为明确化**：Tier 3 模式下报告 frontmatter 必须含 `msigdb_tier: degraded`，G6 门控标记为 `degraded_mode`，提醒用户解读深度受限。

### v0.7.0 — MSigDB 自建工具链开源

让外部用户也能复刻 Tier 1 能力。MSigDB 官方提供两种数据获取方式，对应两条自建路径：

#### 路径 A：完整 scrape 管线（忠实复刻）

基于 [`msigdb_scraper`](https://github.com/DDL095/msigdb-mcp-builder) 工具链（计划独立开源），4 阶段管线：

| 阶段           | 脚本                                | 输入                    | 输出                               |
| -------------- | ----------------------------------- | ----------------------- | ---------------------------------- |
| 1. 基因集清单  | `extract_genelist.py`             | MSigDB browse 页面      | `genelist_<route>.tsv` × 26     |
| 2. 清单拆分    | `genelist_extract.py`             | 官方 CSV（可选）        | per-route tsv                      |
| 3. TSV 抓取    | `fetch_one.py` + `parse_tsv.py` | 基因集名 + 限速 4 req/s | `tsv/<route>/*.tsv` + `*.json` |
| 4. SQLite 入库 | `build_sqlite.py`                 | 所有 JSON               | `msigdb.db` (~566 MB)            |

- 抓取速率：4 req/s（MSigDB 官方允许 5 req/s）
- 总耗时：35,361 × 0.25s ≈ 2.5 小时（单进程）；多 route 并行可缩短到 ~30 分钟
- 支持断点续传（已存在文件跳过）

#### 路径 B：官方整包下载（推荐公众用户）

从 MSigDB 官方下载页 [https://www.gsea-msigdb.org/gsea/downloads.jsp](https://www.gsea-msigdb.org/gsea/downloads.jsp) 获取整包 TSV/JSON（需免费注册）：

- `msigdb_v<version>.Hs_files_to_locate_on_our_website.zip` —— 所有基因集的 TSV 单文件合集
- `msigdb_v<version>.Hs.xml` —— 所有基因集的 XML

简化流程：下载 → 格式适配（需要 `normalize_official_dump.py`，从 flat TSV 拆分为 per-geneset JSON） → `build_sqlite.py` 入库。

#### 开源策略

- **`msigdb_scraper` 独立开源**（推荐方案）：作为独立 repo `DDL095/msigdb-mcp-builder`，通用 MSigDB 工具链，任何需要 MSigDB 元数据的 AI 项目都能用。gsealens-explorer 在 `docs/msigdb_mcp_setup.md` 中引用。
- `scripts/query_msigdb.py` —— Tier 2 SQLite 直读 fallback，纯客户端，不依赖 mcp_server.py，与 MCP 6 工具接口一致。
- `docs/msigdb_mcp_setup.md` —— 文档化完整自建流程（两条路径）+ MCP 配置说明。

### v0.7.1 — 可视化代码落地

SKILL.md §5c 目前仅以文字描述 cascade 热图，尚未交付代码。

- `scripts/plot_cascade_heatmap.R` —— §5c 的 ComplexHeatmap 实现。
- `scripts/plot_gsea_dot.R` —— §6d 中 Fig 3 的点图。
- `scripts/plot_leading_edge.R` —— §6d 中 Fig 5 的 UpSet + 热图。
- 这些脚本都是示例脚本，用于在后续生成时让 LLM 能够参考相应脚本进行基础代码的整理与渲染。

## v0.8 — 报告易用性

### v0.8.0 — Quarto 报告

- 从纯 Markdown 升级为 `.qmd`，让用户从同一份源文件渲染出 PDF / HTML / Word。
- 将报告模板参数化，使同一份分析能为「实验室内部评审」和「论文补充材料」渲染出不同形态。

### v0.8.1 — 论文生态交接

- 文档化推荐工作流：用户可使用 [academic-research-skills](https://github.com/Imbad0202/academic-research-skills) 中 `academic-paper` 模式，将 gsealens-explorer 报告转成论文的 Results 章节。
- [academic-research-skills](https://github.com/Imbad0202/academic-research-skills) 是一个公开的 AI skill 仓库，具有高参考度与可信度，可作为下游论文写作的基础设施。
- 交接方向：**单向**（gsealens-explorer → academic-paper），不做双向同步。
- `docs/handoff_to_academic_paper.md` —— 字段映射与格式约定（v0.8.1 实施时编写）。

## 明确推迟的项目

以下内容已经讨论过，但暂列入范围之外：

- **clusterProfiler / fgsea / enrichit 一等支持** —— 本项目聚焦 GSEAlens Capsule。其他平台的字段映射方法论已记录在 [`docs/methodology/`](methodology/)，外部用户可参考自适配。若社区需求强烈，未来可能作为独立兼容层引入。
- **VS Code 扩展（.vsix）** —— skill + agent role 的形态已足够；扩展封装目前只增加维护成本，用户收益尚不明确。
- **单细胞 / 空间 RNA-seq GSEA** —— 输出 schema 不同；待 bulk 场景稳定后再考虑。
- **非 LLM 的纯 R/Python 库形态** —— 对可复现性很有吸引力，但本项目的核心价值在于 agent 循环；待项目稳定后再议（不绑定版本号）。

## 如何影响路线图

欢迎开 `feature_request` issue（见 `.github/ISSUE_TEMPLATE/`）。若 PR 提前实现了方法论变更，同样欢迎——只需在同一 PR 中更新 `SKILL.md` 与 `CHANGELOG.md`。
