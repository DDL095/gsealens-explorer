"""Test if we can reconstruct scraper's flat row from official DB."""
import sqlite3

DB = r'D:\BaiduYunDrive\OneDrive\实验相关文档\AI\msigdb_scraper\msigdb_v2026.1.Hs_官方.db'
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# Try a known KEGG pathway that should have a PMID
for name in ['KEGG_PARKINSONS_DISEASE', 'HALLMARK_HYPOXIA']:
    print(f'\n=== {name} ===')
    c.execute('''
        SELECT gs.id, gs.standard_name, gs.collection_name,
               gsd.description_brief, gsd.description_full,
               gsd.systematic_name, gsd.exact_source, gsd.GEO_id,
               gsd.contributor, gsd.contrib_organization,
               p.PMID, p.title as pub_title, p.DOI
        FROM gene_set gs
        LEFT JOIN gene_set_details gsd ON gsd.gene_set_id = gs.id
        LEFT JOIN publication p ON p.id = gsd.publication_id
        WHERE gs.standard_name = ?
    ''', (name,))
    row = c.fetchone()
    if row:
        for k in row.keys():
            v = row[k]
            sv = str(v)[:120] if v is not None else 'NULL'
            print(f'  {k:25s} = {sv}')
    else:
        print('  NOT FOUND')

    # Authors for this publication
    c.execute('''
        SELECT a.display_name, a.full_name, pa.author_order
        FROM gene_set gs
        JOIN gene_set_details gsd ON gsd.gene_set_id = gs.id
        JOIN publication p ON p.id = gsd.publication_id
        JOIN publication_author pa ON pa.publication_id = p.id
        JOIN author a ON a.id = pa.author_id
        WHERE gs.standard_name = ?
        ORDER BY pa.author_order
        LIMIT 5
    ''', (name,))
    authors = [(r[0], r[1], r[2]) for r in c.fetchall()]
    print(f'  Authors (first 5): {authors}')

    # Gene members count + first 5
    c.execute('''
        SELECT gs.symbol
        FROM gene_set_gene_symbol gsgs
        JOIN gene_symbol gs ON gs.id = gsgs.gene_symbol_id
        JOIN gene_set gset ON gset.id = gsgs.gene_set_id
        WHERE gset.standard_name = ?
        LIMIT 5
    ''', (name,))
    syms = [r[0] for r in c.fetchall()]
    print(f'  Gene symbols (first 5): {syms}')

# Cross-check counts between official and scraper
print('\n=== Cross-check: scraper DB has what fields? ===')
conn2 = sqlite3.connect(r'D:\BaiduYunDrive\OneDrive\实验相关文档\AI\msigdb_scraper\msigdb.db')
c2 = conn2.cursor()
c2.execute("SELECT * FROM gene_sets WHERE name = 'KEGG_PARKINSONS_DISEASE'")
row = c2.fetchone()
cols = [d[0] for d in c2.description]
for col, val in zip(cols, row):
    sv = str(val)[:120] if val else 'NULL/empty'
    print(f'  {col:25s} = {sv}')

conn.close()
conn2.close()
