# MSigDB MCP 设置指南

> **目标**: 让外部用户获得与本项目相同的 MSigDB 元数据查询能力。

本项目使用 **MSigDB 官方 SQLite 数据库** 作为核心基础设施，提供 35,361 个基因集的 BRIEF/FULL/PMID/AUTHORS/DOI 等元数据。本文档说明如何自建这套基础设施。

## 推荐路径：使用官方 SQLite 数据库

MSigDB 官方发布了一个完整的 SQLite 数据库（289 MB），包含 18 个规范化表。这是最简单、零维护的自建方式。

### 下载步骤

1. 访问 MSigDB 下载页：[https://www.gsea-msigdb.org/gsea/downloads.jsp](https://www.gsea-msigdb.org/gsea/downloads.jsp)
2. 注册免费账号（学术研究使用免费）
3. 下载 `msigdb_v<version>.Hs.db.zip`（当前最新为 `msigdb_v2026.1.Hs.db.zip`，约 50-80 MB 压缩）
4. 解压得到 `msigdb_v2026.1.Hs.db`（约 289 MB）

### 数据库放置

将 `msigdb_v2026.1.Hs.db` 放到任意位置，然后通过环境变量指定路径：

**Windows (PowerShell)**:
```powershell
$env:MSIGDB_DB_PATH = "D:\path\to\msigdb_v2026.1.Hs.db"
```

**Linux/macOS**:
```bash
export MSIGDB_DB_PATH=/path/to/msigdb_v2026.1.Hs.db
```

### 三层访问方式

本项目支持 3 层访问策略，按优先级降级：

#### Tier 1：MSigDB MCP server（推荐）

[MSigDB MCP](https://github.com/DDL095/msigdb-mcp-builder) 提供 6 个 MCP 工具：

| 工具 | 用途 |
|---|---|
| `get_geneset` | 完整元数据 + 基因成员列表 |
| `get_geneset_brief` | 关键字段（BRIEF/FULL/PMID/DOI/AUTHORS） |
| `get_genesets_by_genes` | 反向查找：包含给定基因的基因集 |
| `get_genesets_by_pattern` | 名称 LIKE 模式搜索 |
| `search_text` | 全文搜索（BRIEF/FULL/EXACT_SOURCE） |
| `list_collections` | 集合统计 |

**安装步骤**：
1. 克隆 [DDL095/msigdb-mcp-builder](https://github.com/DDL095/msigdb-mcp-builder) 仓库
2. 安装依赖：`pip install mcp`
3. 在 `~/.copilot/mcp.json`（或 VS Code settings）添加：
   ```json
   {
     "mcpServers": {
       "msigdb": {
         "command": "python",
         "args": ["path/to/mcp_server.py"],
         "env": {
           "MSIGDB_DB_PATH": "D:/path/to/msigdb_v2026.1.Hs.db"
         }
       }
     }
   }
   ```

#### Tier 2：直接调用 SQLite（无 MCP）

使用本仓库提供的 `scripts/query_msigdb.py`，功能与 MCP 完全一致，但通过 subprocess 调用。

**使用示例**：
```bash
python scripts/query_msigdb.py get_geneset_brief \
  --params '{"name":"KEGG_PARKINSONS_DISEASE"}'

python scripts/query_msigdb.py search_text \
  --params '{"query":"oxidative phosphorylation","limit":10}'
```

**适用场景**：
- 不希望配置 MCP
- CI/CD 测试环境
- 临时调试

#### Tier 3：仅用 RDS 内 `Description` 字段（降级模式）

当 MCP 和 DB 都不可用时，skill 仍能运行，但只能依赖 GSEAlens RDS 内每个通路的 `Description` 字段。

**降级行为**：
- 报告 frontmatter 含 `msigdb_tier: degraded`
- G6 门控标记 `degraded_mode`
- 涌现发现 SOP 跳过 SYNTHESIZE 阶段
- 仅基于通路名相似性给出"假说候选"（不视为最终结论）

## 字段覆盖率（官方 v2026.1.Hs 实测）

| Collection | 数量 | BRIEF | FULL | PMID |
|---|---:|---:|---:|---:|
| H (Hallmark) | 50 | 100% | 0% | 100% |
| C2:CGP | 3,555 | 100% | **100%** | **100%** |
| C2:CP:BIOCARTA | 292 | 100% | 73% | 0% |
| C2:CP:KEGG_LEGACY | 186 | 100% | 61% | 0% |
| C2:CP:KEGG_MEDICUS | 658 | 100% | **100%** | 0% |
| C2:CP:PID | 196 | 100% | 0% | 100% |
| C2:CP:REACTOME | 1,839 | 100% | 0% | 0% |
| C2:CP:WIKIPATHWAYS | 925 | 100% | 0% | 0% |
| C5:GO:BP/CC/MF | ~10,490 | 100% | 0% | 0% |
| C5:HPO | 5,793 | 100% | 90% | 0% |
| C7:IMMUNESIGDB | 4,872 | 100% | **100%** | **99%** |
| C7:VAX | 347 | 100% | **100%** | **100%** |
| C6 (oncogenic) | 189 | 100% | 91% | 96% |

**KEGG 名称误导警告**：
- `KEGG_PARKINSONS_DISEASE` 实为 Complex I 线粒体基因集
- `KEGG_HUNTINGTONS_DISEASE` 实为 Complex II + Complex III
- `KEGG_ALZHEIMERS_DISEASE` 实为 Complex IV + 凋亡

解读这些通路时**必须**先调 `get_geneset_brief` 看 FULL，只引用 FULL 描述中的实际机制。

## 数据库更新

MSigDB 每年发布新版本（v2025.X.Hs / v2026.X.Hs / ...）。升级步骤：

1. 从官网下载最新 `msigdb_v<version>.Hs.db.zip`
2. 解压替换旧文件（或放到新路径）
3. 更新 `MSIGDB_DB_PATH` 环境变量
4. 重启 MCP server 或重新调用脚本

无需迁移数据，无需运行 scraper。

## 旧版 scraper 工具链（已废弃）

> **历史说明**: 在官方 SQLite DB 被发现之前，本项目曾使用自建 scraper 工具链（4 阶段管线：抓取 TSV → 解析 → 入库）。该工具链维护成本高，已于 v0.6 废弃。
>
> 旧版本备份在 `D:\BaiduYunDrive\OneDrive\.backup\msigdb_scraper_20260622_122031\`。
>
> 不推荐使用 scraper 方式重建。直接下载官方 DB 即可获得更完整的数据。

## 验证安装

下载并放置 DB 后，可运行本仓库的验证脚本：

```bash
python tests/msigdb/_test_mcp_functions.py
```

应输出 6 个工具的实测结果，每个工具至少 1 个示例。

## 常见问题

**Q1: 官方 DB 的 schema 与本项目的 `mcp_server.py` 不匹配怎么办？**

A: 本项目 `mcp_server.py` 已经适配官方 v2026.1.Hs schema（18 表规范化）。直接使用即可，不需要额外转换。

**Q2: 我只有旧版 scraper DB（2 表扁平 schema），能继续用吗？**

A: 旧版 DB 已经无法兼容 v0.6 的 `mcp_server.py`。建议下载官方 DB 替换。

**Q3: DB 损坏或下载不完整怎么办？**

A: 重新下载。DB 是单个 SQLite 文件，可以用 `sqlite3 msigdb.db "PRAGMA integrity_check;"` 验证完整性。

**Q4: 公司网络无法访问 MSigDB 官网怎么办？**

A: 可使用我们之前归档的 scraper 工具链（备份目录），但这是 fallback 方案，推荐用官方 DB。