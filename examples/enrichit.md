# enrichit example

RDS: single `gseaResult` S4 object (enrichit R package)
Single contrast only — wrap in list if multiple.

```bash
Rscript scripts/sniff_platform.R path/to/enrichit.rds
# → enrichit (when no @organism field)

Rscript scripts/extract_gsea_capsule.R path/to/enrichit.rds ./out
# Note: extract_gsea_capsule.R currently only fully supports gsealens
# For enrichit: see scripts/extract_gsea_capsule.R (will exit 1)
# Workaround: read enrichit result with:
#   obj <- readRDS(path)
#   df  <- obj@result
#   write.csv(df, "./out/single_Hallmark.csv")
```

Field differences from gsealens: same NES/p.adjust; no Collection metadata.
