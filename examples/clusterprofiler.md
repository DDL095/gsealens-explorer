# clusterProfiler example

RDS: single `gseaResult` S4 object (clusterProfiler)
Same class name as enrichit — distinguish by `@organism` field.

```bash
Rscript scripts/sniff_platform.R path/to/clusterprofiler.rds
# → clusterprofiler (when @organism is set, e.g. "hsa")
```

Field differences from enrichit:
- `qvalues` (plural) instead of `qvalue`
- `@organism` field present (e.g. "hsa", "mmu")
- Typically comes with `@setType` and `@geneSets` slots

Same gseaResult S4 dispatch — use `obj@result` to access the data frame.
