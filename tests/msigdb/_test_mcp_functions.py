"""Test all 6 mcp_server query functions against the official DB."""
import sys
sys.path.insert(0, r'D:\BaiduYunDrive\OneDrive\实验相关文档\AI\msigdb_scraper')
from mcp_server import (
    _get_geneset, _get_geneset_brief, _get_genesets_by_genes,
    _get_genesets_by_pattern, _list_collections, _search_text,
)
import json

def show(label, result):
    print(f'\n=== {label} ===')
    if isinstance(result, list):
        print(f'  Type: list, len={len(result)}')
        if result and 'error' in result[0]:
            print(f'  Error: {result[0]}')
        elif result:
            for k in result[0]:
                v = str(result[0][k])[:80]
                print(f'    {k}: {v}')
    elif isinstance(result, dict):
        if 'error' in result:
            print(f'  Error: {result["error"]}')
        else:
            for k, v in result.items():
                sv = str(v)[:100] if not isinstance(v, list) else f'list[{len(v)}]'
                print(f'  {k}: {sv}')

# Test 1: get_geneset_brief
show('1. get_geneset_brief(KEGG_PARKINSONS_DISEASE)',
     _get_geneset_brief('KEGG_PARKINSONS_DISEASE'))

# Test 2: get_geneset_brief with Hallmark (has PMID)
show('2. get_geneset_brief(HALLMARK_HYPOXIA)',
     _get_geneset_brief('HALLMARK_HYPOXIA'))

# Test 3: get_geneset (with genes list, head only)
r = _get_geneset('KEGG_PARKINSONS_DISEASE')
print(f'\n=== 3. get_geneset(KEGG_PARKINSONS_DISEASE) ===')
if 'error' in r:
    print(f'  Error: {r["error"]}')
else:
    print(f'  standard_name: {r["standard_name"]}')
    print(f'  collection/subcollection: {r["collection"]}/{r["subcollection"]}')
    print(f'  gene_count: {r["gene_count"]}')
    print(f'  first 10 genes: {r["genes"][:10]}')

# Test 4: get_genesets_by_genes (AND mode)
r = _get_genesets_by_genes(['STAT1', 'IRF1'], collection='H', limit=5)
show('4. get_genesets_by_genes([STAT1,IRF1], H, AND)',
     r)

# Test 5: get_genesets_by_pattern
r = _get_genesets_by_pattern('FIBROBLAST', limit=5)
show('5. get_genesets_by_pattern(%FIBROBLAST%)', r)

# Test 6: search_text
r = _search_text('oxidative phosphorylation', limit=5)
show('6. search_text(oxidative phosphorylation)', r)

# Test 7: list_collections (head only)
r = _list_collections()
print(f'\n=== 7. list_collections ===')
print(f'  Total collections: {len(r)}')
for c in r[:5]:
    print(f'    {c["collection_name"]}: {c["gene_set_count"]} sets')

print('\n\n=== ALL TESTS DONE ===')