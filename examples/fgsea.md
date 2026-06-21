# fgsea example

RDS: list (fgsea R package)
Field names differ from enrichit/clusterProfiler!

```bash
Rscript scripts/sniff_platform.R path/to/fgsea.rds
# → fgsea
```

Critical field name differences:
- `ES` (not `enrichmentScore`)
- `pval` (not `pvalue`)
- `padj` (not `p.adjust`)
- `leadingEdge` is a **list** of character vectors (not a string)

Workaround for extract_gsea_capsule.R (which only supports gsealens):

```r
obj <- readRDS("path/to/fgsea.rds")
df  <- obj[["result"]]
le  <- obj[["leadingEdge"]]   # list column
# Convert to readable form
df$leading_edge_genes <- sapply(le, paste, collapse="/")
write.csv(df, "./out/single_Hallmark.csv", row.names=FALSE)
```
