"""Display real BRIEF/FULL samples from official DB for LLM-relevant collections."""
import sqlite3

DB = r'D:\BaiduYunDrive\OneDrive\实验相关文档\AI\msigdb_scraper\msigdb_v2026.1.Hs_官方.db'
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# Pick one example from each collection that has good FULL coverage
SAMPLES = [
    # Hallmark: BRIEF yes, FULL no, PMID yes
    ('H',             'HALLMARK_HYPOXIA'),
    # C2:CGP: full coverage with PMID
    ('C2:CGP',        None),  # pick first
    # KEGG_LEGACY: BRIEF yes, FULL 61%, no PMID
    ('C2:CP:KEGG_LEGACY', None),
    # KEGG_MEDICUS: full BRIEF/FULL, no PMID
    ('C2:CP:KEGG_MEDICUS', None),
    # BIOCARTA: BRIEF yes, FULL 73%, no PMID
    ('C2:CP:BIOCARTA', None),
    # REACTOME: BRIEF yes, FULL no
    ('C2:CP:REACTOME', None),
    # HPO: BRIEF yes, FULL 90%
    ('C5:HPO',        None),
    # IMMUNESIGDB: full coverage
    ('C7:IMMUNESIGDB', None),
    # 3CA: full
    ('C4:3CA',        None),
    # CGN: full BRIEF/FULL
    ('C4:CGN',        None),
]

def fetch_first_with_full(coll):
    c.execute('''
        SELECT gs.standard_name, gsd.description_brief, gsd.description_full,
               gsd.contributor, gsd.contrib_organization, gsd.GEO_id, gsd.exact_source,
               p.PMID, p.title as pub_title
        FROM gene_set gs
        LEFT JOIN gene_set_details gsd ON gsd.gene_set_id = gs.id
        LEFT JOIN publication p ON p.id = gsd.publication_id
        WHERE gs.collection_name = ?
          AND gsd.description_full IS NOT NULL AND gsd.description_full != ''
        LIMIT 1
    ''', (coll,))
    return c.fetchone()

def fetch_any(coll):
    c.execute('''
        SELECT gs.standard_name, gsd.description_brief, gsd.description_full,
               gsd.contributor, gsd.contrib_organization, gsd.GEO_id, gsd.exact_source,
               p.PMID, p.title as pub_title
        FROM gene_set gs
        LEFT JOIN gene_set_details gsd ON gsd.gene_set_id = gs.id
        LEFT JOIN publication p ON p.id = gsd.publication_id
        WHERE gs.collection_name = ?
        LIMIT 1
    ''', (coll,))
    return c.fetchone()

def show(label, name, row):
    print(f'\n{"="*100}')
    print(f'COLLECTION: {label}')
    print(f'NAME:       {name}')
    print(f'{"="*100}')
    print(f'CONTRIBUTOR:       {row["contributor"]}')
    print(f'CONTRIB_ORG:       {row["contrib_organization"]}')
    print(f'EXACT_SOURCE:      {row["exact_source"]}')
    print(f'GEO_ID:            {row["GEO_id"]}')
    print(f'PMID:              {row["PMID"]}')
    print(f'PUB_TITLE:         {(row["pub_title"] or "")[:80] if row["pub_title"] else None}')
    print(f'--- DESCRIPTION_BRIEF ({len(row["description_brief"] or "")} chars) ---')
    print(row['description_brief'])
    print(f'--- DESCRIPTION_FULL ({len(row["description_full"] or "")} chars) ---')
    print(row['description_full'] or '(EMPTY)')

# Hallmark (FULL is empty)
row = fetch_any('H')
show('H', 'HALLMARK_HYPOXIA', row)

# C2:CGP with FULL
row = fetch_first_with_full('C2:CGP')
show('C2:CGP', row['standard_name'], row)

# KEGG_LEGACY (has FULL, no PMID)
row = fetch_first_with_full('C2:CP:KEGG_LEGACY')
show('C2:CP:KEGG_LEGACY', row['standard_name'], row)

# KEGG_MEDICUS (has FULL)
row = fetch_first_with_full('C2:CP:KEGG_MEDICUS')
show('C2:CP:KEGG_MEDICUS', row['standard_name'], row)

# BIOCARTA
row = fetch_first_with_full('C2:CP:BIOCARTA')
show('C2:CP:BIOCARTA', row['standard_name'], row)

# REACTOME (no FULL)
row = fetch_any('C2:CP:REACTOME')
show('C2:CP:REACTOME', row['standard_name'], row)

# HPO (90% FULL)
row = fetch_first_with_full('C5:HPO')
show('C5:HPO', row['standard_name'], row)

# IMMUNESIGDB (99% FULL, 99% PMID)
row = fetch_first_with_full('C7:IMMUNESIGDB')
show('C7:IMMUNESIGDB', row['standard_name'], row)

# CGN (full BRIEF/FULL)
row = fetch_first_with_full('C4:CGN')
show('C4:CGN', row['standard_name'], row)

conn.close()