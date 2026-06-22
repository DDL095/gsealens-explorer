"""Inspect official DB schema details."""
import sqlite3

DB = r'D:\BaiduYunDrive\OneDrive\实验相关文档\AI\msigdb_scraper\msigdb_v2026.1.Hs_官方.db'
conn = sqlite3.connect(DB)
c = conn.cursor()

# Schema of every table we care about
for t in ['gene_set', 'gene_set_details', 'publication', 'author', 'publication_author',
          'collection', 'gene_symbol', 'gene_set_gene_symbol', 'namespace']:
    print(f'\n=== {t} ===')
    c.execute(f'PRAGMA table_info("{t}")')
    for r in c.fetchall():
        print(f'  {r[1]:35s} {r[2]}')
    c.execute(f'SELECT * FROM "{t}" LIMIT 1')
    row = c.fetchone()
    if row:
        print(f'  SAMPLE:')
        c.execute(f'PRAGMA table_info("{t}")')
        cols = [r[1] for r in c.fetchall()]
        for col, val in zip(cols, row):
            sv = str(val)[:100] if val is not None else 'NULL'
            print(f'    {col:30s} = {sv}')

# Try joining to get a flat record like scraper's gene_sets row
print('\n=== JOIN TEST: can we reproduce the scraper flat row? ===')
test_name = 'KEGG_PARKINSONS_DISEASE'
c.execute('''
SELECT gs.GENESET_NAME, gs.SYSTEMATIC_NAME, gs.COLLECTION_CODE,
       gs.DESCRIPTION_BRIEF, gs.DESCRIPTION_FULL,
       (SELECT GROUP_CONCAT(PMID, ';') FROM publication p
        JOIN gene_set_publication gsp ON p.PMID=gsp.PMID
        WHERE gsp.GENESET_NAME=?) AS PMIDS
FROM gene_set gs
WHERE gs.GENESET_NAME=?
''', (test_name, test_name))
try:
    row = c.fetchone()
    if row:
        print(f'  JOIN success: {row[:4]}')
    else:
        print(f'  Not found, trying alt schema')
except Exception as e:
    print(f'  JOIN error: {e}')

# Inspect any junction tables for publications
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%publication%'")
print(f'\nPublication-related tables: {[r[0] for r in c.fetchall()]}')

conn.close()
