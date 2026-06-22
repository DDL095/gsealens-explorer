"""
query_msigdb.py — Tier 2 SQLite fallback for MSigDB MCP.

When the `mcp__msigdb__*` tools are not available, this script provides the
same 6 query interfaces by reading the MSigDB official SQLite DB directly.
Subagents can call this script via subprocess (no MCP setup required).

Data source: MSigDB official v2026.1.Hs SQLite DB (~289 MB).
Download URL: https://www.gsea-msigdb.org/gsea/downloads.jsp
After download, extract to a path and set MSIGDB_DB_PATH env var, or place
the file at the default location shown below.

Usage:
  python scripts/query_msigdb.py get_geneset_brief --params '{"name":"KEGG_PARKINSONS_DISEASE"}'
  python scripts/query_msigdb.py search_text --params '{"query":"oxidative phosphorylation","limit":10}'

Environment:
  MSIGDB_DB_PATH — path to msigdb_v<version>.Hs.db (default: ./msigdb_v2026.1.Hs.db)

Output: JSON to stdout. Compatible with `mcp__msigdb__*` responses
(get_geneset_brief returns flat dict; list queries return list of dicts).
"""
import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

# Default DB location is empty unless MSIGDB_DB_PATH is set.
# Users must either:
#   1. Set MSIGDB_DB_PATH environment variable to point to msigdb_v<version>.Hs.db
#   2. Place the DB file at one of the well-known locations listed in
#      docs/msigdb_mcp_setup.md and update this default accordingly.
DEFAULT_DB_CANDIDATES = [
    './msigdb_v2026.1.Hs.db',                       # current working dir
    './data/msigdb_v2026.1.Hs.db',                  # ./data subdir
    str(Path.home() / 'msigdb_v2026.1.Hs.db'),     # home dir
]


def _resolve_db_path():
    env = os.environ.get('MSIGDB_DB_PATH')
    if env:
        return Path(env)
    for cand in DEFAULT_DB_CANDIDATES:
        if Path(cand).exists():
            return Path(cand)
    return Path(DEFAULT_DB_CANDIDATES[0])


DB_PATH = _resolve_db_path()


def get_conn():
    if not DB_PATH.exists():
        return None
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _split_collection(coll):
    if not coll:
        return ('', '')
    parts = coll.split(':', 1)
    return (parts[0], parts[1] if len(parts) > 1 else '')


def get_geneset(name):
    conn = get_conn()
    if not conn:
        return {'error': f'Database not found: {DB_PATH}'}
    cur = conn.cursor()
    cur.execute('''
        SELECT gs.id, gs.standard_name, gs.collection_name, gs.tags, gs.license_code,
               gsd.description_brief, gsd.description_full,
               gsd.systematic_name, gsd.exact_source, gsd.GEO_id,
               gsd.contributor, gsd.contrib_organization,
               gsd.external_details_URL,
               p.PMID, p.DOI, p.title as pub_title,
               n.label as namespace
        FROM gene_set gs
        LEFT JOIN gene_set_details gsd ON gsd.gene_set_id = gs.id
        LEFT JOIN publication p ON p.id = gsd.publication_id
        LEFT JOIN namespace n ON n.id = gsd.primary_namespace_id
        WHERE gs.standard_name = ? OR gsd.systematic_name = ?
    ''', (name, name))
    row = cur.fetchone()
    if not row:
        conn.close()
        return {'error': f'Gene set not found: {name}'}
    result = dict(row)
    gs_id = result['id']

    if result.get('PMID'):
        cur.execute('''
            SELECT a.display_name, a.full_name, pa.author_order
            FROM publication p JOIN publication_author pa ON pa.publication_id = p.id
            JOIN author a ON a.id = pa.author_id
            WHERE p.PMID = ? ORDER BY pa.author_order
        ''', (result['PMID'],))
        result['authors'] = [
            {'display_name': r['display_name'], 'full_name': r['full_name'],
             'order': r['author_order']}
            for r in cur.fetchall()
        ]
    else:
        result['authors'] = []

    cur.execute('''
        SELECT gs.symbol FROM gene_set_gene_symbol gsgs
        JOIN gene_symbol gs ON gs.id = gsgs.gene_symbol_id
        WHERE gsgs.gene_set_id = ? ORDER BY gs.symbol
    ''', (gs_id,))
    result['genes'] = [r['symbol'] for r in cur.fetchall()]
    result['gene_count'] = len(result['genes'])

    cat, subcat = _split_collection(result.get('collection_name', ''))
    result['collection'] = cat
    result['subcollection'] = subcat
    conn.close()
    return result


def get_geneset_brief(name):
    conn = get_conn()
    if not conn:
        return {'error': f'Database not found: {DB_PATH}'}
    cur = conn.cursor()
    cur.execute('''
        SELECT gs.standard_name, gs.collection_name,
               gsd.description_brief, gsd.description_full,
               gsd.systematic_name, gsd.exact_source, gsd.GEO_id,
               gsd.contributor, gsd.contrib_organization,
               p.PMID, p.DOI, p.title as pub_title,
               n.label as namespace
        FROM gene_set gs
        LEFT JOIN gene_set_details gsd ON gsd.gene_set_id = gs.id
        LEFT JOIN publication p ON p.id = gsd.publication_id
        LEFT JOIN namespace n ON n.id = gsd.primary_namespace_id
        WHERE gs.standard_name = ? OR gsd.systematic_name = ?
    ''', (name, name))
    row = cur.fetchone()
    if not row:
        conn.close()
        return {'error': f'Gene set not found: {name}'}
    result = dict(row)
    if result.get('PMID'):
        cur.execute('''
            SELECT a.display_name FROM publication_author pa
            JOIN publication p ON p.id = pa.publication_id
            JOIN author a ON a.id = pa.author_id
            WHERE p.PMID = ? ORDER BY pa.author_order
        ''', (result['PMID'],))
        result['authors'] = '; '.join(r['display_name'] for r in cur.fetchall())
    else:
        result['authors'] = None
    cat, subcat = _split_collection(result.get('collection_name', ''))
    result['collection'] = cat
    result['subcollection'] = subcat
    conn.close()
    return result


def get_genesets_by_genes(genes, collection=None, require_all=True, limit=20):
    conn = get_conn()
    if not conn:
        return [{'error': f'Database not found: {DB_PATH}'}]
    cur = conn.cursor()
    placeholders = ','.join('?' * len(genes))
    sql = f'''
        SELECT gs.standard_name, gs.collection_name,
               gsd.description_brief, p.PMID,
               COUNT(DISTINCT gsym.symbol) AS match_count,
               (SELECT COUNT(*) FROM gene_set_gene_symbol WHERE gene_set_id = gs.id) AS gene_count
        FROM gene_set_gene_symbol gsgs
        JOIN gene_set gs ON gs.id = gsgs.gene_set_id
        JOIN gene_symbol gsym ON gsym.id = gsgs.gene_symbol_id
        LEFT JOIN gene_set_details gsd ON gsd.gene_set_id = gs.id
        LEFT JOIN publication p ON p.id = gsd.publication_id
        WHERE gsym.symbol IN ({placeholders})
    '''
    params = list(genes)
    if collection:
        sql += ' AND gs.collection_name LIKE ?'
        params.append(f'{collection}%')
    if require_all:
        sql += ' GROUP BY gs.id HAVING COUNT(DISTINCT gsym.symbol) = ?'
        params.append(len(genes))
        sql += ' ORDER BY gene_count ASC'
    else:
        sql += ' GROUP BY gs.id ORDER BY match_count DESC, gene_count ASC'
    sql += ' LIMIT ?'
    params.append(limit)
    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    for r in rows:
        cat, subcat = _split_collection(r.get('collection_name', ''))
        r['collection'] = cat
        r['subcollection'] = subcat
    conn.close()
    return rows


def get_genesets_by_pattern(pattern, collection=None, limit=20):
    conn = get_conn()
    if not conn:
        return [{'error': f'Database not found: {DB_PATH}'}]
    cur = conn.cursor()
    sql = '''
        SELECT gs.standard_name, gs.collection_name,
               gsd.description_brief, p.PMID,
               (SELECT COUNT(*) FROM gene_set_gene_symbol WHERE gene_set_id = gs.id) AS gene_count
        FROM gene_set gs
        LEFT JOIN gene_set_details gsd ON gsd.gene_set_id = gs.id
        LEFT JOIN publication p ON p.id = gsd.publication_id
        WHERE gs.standard_name LIKE ?
    '''
    params = [f'%{pattern}%']
    if collection:
        sql += ' AND gs.collection_name LIKE ?'
        params.append(f'{collection}%')
    sql += ' ORDER BY gs.standard_name LIMIT ?'
    params.append(limit)
    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    for r in rows:
        cat, subcat = _split_collection(r.get('collection_name', ''))
        r['collection'] = cat
        r['subcollection'] = subcat
    conn.close()
    return rows


def search_text(query, limit=10):
    conn = get_conn()
    if not conn:
        return [{'error': f'Database not found: {DB_PATH}'}]
    cur = conn.cursor()
    pat = f'%{query}%'
    cur.execute('''
        SELECT gs.standard_name, gs.collection_name,
               gsd.description_brief, gsd.description_full,
               gsd.exact_source, p.PMID,
               (SELECT COUNT(*) FROM gene_set_gene_symbol WHERE gene_set_id = gs.id) AS gene_count
        FROM gene_set gs
        LEFT JOIN gene_set_details gsd ON gsd.gene_set_id = gs.id
        LEFT JOIN publication p ON p.id = gsd.publication_id
        WHERE gsd.description_brief LIKE ?
           OR gsd.description_full LIKE ?
           OR gsd.exact_source LIKE ?
        ORDER BY gene_count ASC LIMIT ?
    ''', (pat, pat, pat, limit))
    rows = [dict(r) for r in cur.fetchall()]
    for r in rows:
        cat, subcat = _split_collection(r.get('collection_name', ''))
        r['collection'] = cat
        r['subcollection'] = subcat
    conn.close()
    return rows


def list_collections():
    conn = get_conn()
    if not conn:
        return [{'error': f'Database not found: {DB_PATH}'}]
    cur = conn.cursor()
    cur.execute('''
        SELECT gs.collection_name,
               COUNT(*) AS gene_set_count,
               SUM((SELECT COUNT(*) FROM gene_set_gene_symbol WHERE gene_set_id = gs.id)) AS total_gene_set_members
        FROM gene_set gs
        GROUP BY gs.collection_name
        ORDER BY gene_set_count DESC
    ''')
    rows = [dict(r) for r in cur.fetchall()]
    for r in rows:
        cat, subcat = _split_collection(r.get('collection_name', ''))
        r['collection'] = cat
        r['subcollection'] = subcat
    conn.close()
    return rows


TOOLS = {
    'get_geneset': get_geneset,
    'get_geneset_brief': get_geneset_brief,
    'get_genesets_by_genes': get_genesets_by_genes,
    'get_genesets_by_pattern': get_genesets_by_pattern,
    'search_text': search_text,
    'list_collections': list_collections,
}


def main():
    ap = argparse.ArgumentParser(description='MSigDB Tier 2 SQLite fallback')
    ap.add_argument('tool', choices=list(TOOLS.keys()))
    ap.add_argument('--params', type=json.loads, default='{}',
                    help="JSON params, e.g. '{\"name\":\"KEGG_PARKINSONS_DISEASE\"}'")
    args = ap.parse_args()
    result = TOOLS[args.tool](**args.params)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()