"""Per-collection coverage check: BRIEF/FULL/PMID for each subcollection."""
import sqlite3

DB = r'D:\BaiduYunDrive\OneDrive\实验相关文档\AI\msigdb_scraper\msigdb_v2026.1.Hs_官方.db'
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# Map of collection -> sample gene set names
SAMPLES = {
    'H':              ['HALLMARK_HYPOXIA', 'HALLMARK_INFLAMMATORY_RESPONSE'],
    'C1':             ['chr10p11', 'chr1p12'],
    'C2:CGP':         ['BARRIER_CANCER_RELAPSE_NORMAL_SAMPLE_UP', 'YOSHIMURA_JAK2_TARGETS_UP'],
    'C2:CP:BIOCARTA': ['BIOCARTA_P38MAPK_PATHWAY', 'BIOCARTA_WNT_PATHWAY'],
    'C2:CP:KEGG_LEGACY': ['KEGG_PARKINSONS_DISEASE', 'KEGG_HUNTINGTONS_DISEASE'],
    'C2:CP:KEGG_MEDICUS': ['KEGG_MEDICUS_PARKINSONS_DISEASE_REF'],
    'C2:CP:PID':      ['PID_AMB2_NEUTROPHILS_PATHWAY', 'PID_HNF3B_PATHWAY'],
    'C2:CP:REACTOME': ['REACTOME_INTERFERON_GAMMA_SIGNALING', 'REACTOME_OXIDATIVE_PHOSPHORYLATION'],
    'C2:CP:WIKIPATHWAYS': ['WP_PI3K_AKT_SIGNALING_PATHWAY'],
    'C3:MIR:MIRDB':   ['AAACCAC_MIR140', 'AACGGTT_MIR451'],
    'C3:MIR:MIR_LEGACY': ['AAACCAC_MIR140', 'AACGGTT_MIR451'],
    'C3:TFT:GTRD':    ['AACTTT_UNKNOWN', 'AAAYRNCTG_UNKNOWN'],
    'C3:TFT:TFT_LEGACY': ['AACTTT_UNKNOWN', 'AAAYRNCTG_UNKNOWN'],
    'C4:3CA':         ['3CA_NUTLIN_VS_DMSO_DN', '3CA_NUTLIN_VS_DMSO_UP'],
    'C4:CGN':         ['CGN_NEUTROPHIL_UP', 'CGN_MONOCYTE_UP'],
    'C4:CM':          ['CM_GASTRIC_CANCER_VS_NORMAL_UP', 'CM_OVARIAN_CANCER_VS_NORMAL_DN'],
    'C5:GO:BP':       ['GOBP_HYPOXIA_RESPONSE', 'GOBP_T_CELL_ACTIVATION'],
    'C5:GO:CC':       ['GOCC_MITOCHONDRION', 'GOCC_NUCLEUS'],
    'C5:GO:MF':       ['GOMF_DNA_BINDING', 'GOMF_ATP_BINDING'],
    'C5:HPO':         ['HP_ABNORMAL_HEART_MORPHOLOGY', 'HP_ABNORMAL_KIDNEY_MORPHOLOGY'],
    'C6':             ['GSE12345_SOMETHING_UP'],
    'C7:IMMUNESIGDB': ['GSE22886_NAIVE_BCELL_VS_MEMORY_BCELL_UP'],
    'C7:VAX':         ['VX_ASTRAZENECA_SERONEGATIVES_VS_SEROPOSITIVES_2ND_INJECTION_UP'],
    'C8':             ['C8_FOO_BAR'],
    'C9':             ['C9_FOO_BAR'],
}

print(f'{"Collection":<22} {"Sample":<45} {"BRIEF":<6} {"FULL":<6} {"PMID":<6} {"Authors":<8}')
print('=' * 110)

total_checked = 0
brief_hits = full_hits = pmid_hits = authors_hits = 0

for coll, names in SAMPLES.items():
    for name in names:
        c.execute('''
            SELECT gs.collection_name, gsd.description_brief, gsd.description_full,
                   p.PMID, gsd.GEO_id, gsd.contributor
            FROM gene_set gs
            LEFT JOIN gene_set_details gsd ON gsd.gene_set_id = gs.id
            LEFT JOIN publication p ON p.id = gsd.publication_id
            WHERE gs.standard_name = ?
        ''', (name,))
        row = c.fetchone()
        if not row:
            print(f'{coll:<22} {name:<45} (NOT FOUND)')
            continue
        total_checked += 1
        brief = '✓' if row['description_brief'] and row['description_brief'].strip() else '✗'
        full  = '✓' if row['description_full']  and row['description_full'].strip()  else '✗'
        pmid  = '✓' if row['PMID'] else '✗'
        # Count authors
        auth_count = 0
        if row['PMID']:
            c2 = conn.cursor()
            c2.execute('''
                SELECT COUNT(*) FROM publication_author pa
                JOIN publication p ON p.id = pa.publication_id
                WHERE p.PMID = ?
            ''', (row['PMID'],))
            auth_count = c2.fetchone()[0]
        auth = f'{auth_count}' if auth_count else '✗'

        if brief == '✓': brief_hits += 1
        if full  == '✓': full_hits  += 1
        if pmid  == '✓': pmid_hits  += 1
        if auth_count:   authors_hits += 1

        print(f'{coll:<22} {name:<45} {brief:<6} {full:<6} {pmid:<6} {auth:<8}')

print('=' * 110)
print(f'\nTOTAL checked: {total_checked}')
print(f'  BRIEF:    {brief_hits}/{total_checked} ({brief_hits/total_checked*100:.0f}%)')
print(f'  FULL:     {full_hits}/{total_checked} ({full_hits/total_checked*100:.0f}%)')
print(f'  PMID:     {pmid_hits}/{total_checked} ({pmid_hits/total_checked*100:.0f}%)')
print(f'  Authors:  {authors_hits}/{total_checked} (when PMID exists)')

# Overall stats: how many gene sets in each collection have BRIEF/FULL/PMID?
print('\n=== AGGREGATE STATS PER COLLECTION ===')
c.execute('''
SELECT gs.collection_name,
       COUNT(*) AS total,
       SUM(CASE WHEN gsd.description_brief IS NOT NULL AND gsd.description_brief != '' THEN 1 ELSE 0 END) AS with_brief,
       SUM(CASE WHEN gsd.description_full IS NOT NULL AND gsd.description_full != '' THEN 1 ELSE 0 END) AS with_full,
       SUM(CASE WHEN gsd.publication_id IS NOT NULL THEN 1 ELSE 0 END) AS with_pmid
FROM gene_set gs
LEFT JOIN gene_set_details gsd ON gsd.gene_set_id = gs.id
GROUP BY gs.collection_name
ORDER BY gs.collection_name
''')
print(f'{"Collection":<25} {"Total":<7} {"BRIEF":<8} {"FULL":<8} {"PMID":<8}')
print('-' * 60)
for r in c.fetchall():
    name = r[0] or 'NULL'
    tot, br, fu, pm = r[1], r[2], r[3], r[4]
    br_pct = br/tot*100 if tot else 0
    fu_pct = fu/tot*100 if tot else 0
    pm_pct = pm/tot*100 if tot else 0
    print(f'{name:<25} {tot:<7} {br}/{tot} ({br_pct:>3.0f}%) {fu}/{tot} ({fu_pct:>3.0f}%) {pm}/{tot} ({pm_pct:>3.0f}%)')

conn.close()