# gsealens example

RDS: `GSEA_Capsule_*.rds` (ZYH team's GSEALENS pipeline)
Class: `GseaRes` (S3 list, 7 slots: metadata, backend_info, contrast_registry, de_store, expr_bundle, geneset_info, results)

```bash
# 1. Sniff
Rscript scripts/sniff_platform.R path/to/GSEA_Capsule.rds
# → gsealens

# 2. Extract
Rscript scripts/extract_gsea_capsule.R \
    path/to/GSEA_Capsule.rds \
    ./out \
    AduCre_vs_Con AgeCre_vs_Con AgeCre_vs_AduCre
# → ./out/{AduCre_vs_Con,AgeCre_vs_Con,AgeCre_vs_AduCre}_{Hallmark,GOBP_top30,ReactKEGG_top30,leading_edge}.csv
# → ./out/summary.md
# → exit 0 on success

# 3. Audit + Gates
python -c "from audit_logger import AuditLogger; log = AuditLogger('./out'); log.start(); log.s0_rds_found('...', 141504055); log.end()"
python scripts/quality_gate_check.py ./out/01_exploratory_analysis_report.md ./out
```

Output schema uses `/` to separate `core_enrichment` genes; leading_edge is a string `tags=48%, list=12%, signal=43%`.

ZYH 实战: 4 CSV + summary.md in 9 seconds, all validated.
