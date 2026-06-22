# 路线图

> 本文档持续更新。所列日期仅为参考，并非承诺。

## 最终目标

让 gsealens-explorer 成为完美适配GSEAlens的GSEA结果解读器，能在多个agent平台适配使用。

## v0.6 — 公开发布基础（下一版本）

主题： **测试体系 + 多 SA 架构 POC**。

### v0.6.0 测试框架 + 合成测试数据

- `tests/testdata/synthetic_gsea.rds` —— 脚本生成的 mock capsule，包含 5 个 contrast × 50 条 Hallmark 通路，并预置若干方向翻转案例（true_flip、p_suppression、p_restoration）。
- `tests/test_skill_structure.py` —— 校验 frontmatter 有效性、profile ↔ script 交叉引用、对 SKILL.md 本身做反模式正则检测。
- `tests/test_quality_gate.py` —— 向 G1/G2/G3 喂入已知的 PASS 与 FAIL 报告，断言判决正确。
- 接入 GitHub Actions CI，在每个 PR 上跑冒烟测试。

### v0.6.1 — 多 SA 并行架构 POC

这是 v0.6 的差异化特性。不再由单个 SA 顺序完成所有工作，而是拆分为 fan-out / fan-in 模式，共享同一个 R REPL。完整设计见 [`multi_sa_architecture.md`](multi_sa_architecture.md)。

## v0.7 — 可视化

MSigDB 硬链接的说明:

MSigDB 硬链接这方面是作为本项目的特色，是要硬依赖一个私有部署的本地 MSigDB MCP，这样能最大化的增强解读与数据处理的能力与速度

- 将 `get_geneset_brief` / `search_text` 视为**可选**增强能力：在 S0 自动检测可用性，存在则走 MCP，缺失则回退到 `msigdbr` + rds内已有的整理好的描述。因为msigdb的自建MCP可以通过额外的full description来补充相关的内容。

### v0.7.0 — 可视化代码落地

SKILL.md §5c 目前仅以文字描述 cascade 热图，尚未交付代码。

- `scripts/plot_cascade_heatmap.R` —— §5c 的 ComplexHeatmap 实现。
- `scripts/plot_gsea_dot.R` —— §6d 中 Fig 3 的点图。
- `scripts/plot_leading_edge.R` —— §6d 中 Fig 5 的 UpSet + 热图
- 这些脚本都是示例脚本，用于在后续生成时，让LLM能够参考相应脚本进行基础代码的整理与渲染。

## v0.8 — 报告易用性

### v0.8.0 — Quarto 报告

- 从纯 Markdown 并行为 `.qmd`，让用户从同一份源文件渲染出 PDF / HTML / Word。
- 将报告模板参数化，使同一份分析能为「实验室内部评审」和「论文补充材料」渲染出不同形态。

### v0.8.1 — 论文生态

- 文档化向[academic-research-skills](https://github.com/Imbad0202/academic-research-skills)中 `academic-paper` 的交接流程，把报告转成论文的 Results 章节。

## 明确推迟的项目

以下内容已经讨论过，但暂列入范围之外：

- **VS Code 扩展（.vsix）** —— skill + agent role 的形态已足够；扩展封装目前只增加维护成本，用户收益尚不明确。
- **单细胞 / 空间 RNA-seq GSEA** —— 输出 schema 不同；待 bulk 场景稳定后再考虑。
- **非 LLM 的纯 R/Python 库形态** —— 对可复现性很有吸引力，但本项目的核心价值在于 agent 循环；留待 v1.x 再议。

## 如何影响路线图

欢迎开 `feature_request` issue（见 `.github/ISSUE_TEMPLATE/`）。若 PR 提前实现了方法论变更，同样欢迎——只需在同一 PR 中更新 `SKILL.md` 与 `CHANGELOG.md`。
