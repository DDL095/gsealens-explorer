"""Compare official MSigDB DB vs scraper-built DB."""
import sqlite3
from pathlib import Path

DBS = [
    ('OFFICIAL', r'D:\BaiduYunDrive\OneDrive\实验相关文档\AI\msigdb_scraper\msigdb_v2026.1.Hs_官方.db'),
    ('SCRAPER',  r'D:\BaiduYunDrive\OneDrive\实验相关文档\AI\msigdb_scraper\msigdb.db'),
]

for label, path in DBS:
    print(f'\n===== {label}: {path} =====')
    if not Path(path).exists():
        print('  NOT FOUND')
        continue
    sz = Path(path).stat().st_size / (1024*1024)
    print(f'  Size: {sz:.1f} MB')
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in c.fetchall()]
    print(f'  Tables: {tables}')
    for t in tables:
        try:
            c.execute(f'SELECT COUNT(*) FROM "{t}"')
            n = c.fetchone()[0]
            print(f'    {t}: {n:,} rows')
        except Exception as e:
            print(f'    {t}: ERR {e}')
    # schema of main tables
    for guess in ['gene_sets', 'GENE_SETS', 'genesets', 'geneset']:
        if guess in tables:
            c.execute(f'PRAGMA table_info("{guess}")')
            cols = [(r[1], r[2]) for r in c.fetchall()]
            print(f'  Schema of {guess}:')
            for name, typ in cols:
                print(f'    {name}: {typ}')
            # Sample one row
            c.execute(f'SELECT * FROM "{guess}" LIMIT 1')
            row = c.fetchone()
            if row:
                print(f'  Sample row (first 5 cols): {row[:5]}')
            break
    conn.close()
