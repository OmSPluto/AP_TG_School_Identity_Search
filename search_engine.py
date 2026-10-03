
import sqlite3, re, json
from pathlib import Path

TOKEN_RE = re.compile(r"[a-z0-9]+")

def norm(s):
    return " ".join(TOKEN_RE.findall(str(s or "").lower()))

class FastSchoolIndex:
    def __init__(self, db_path, columns, semantic, enrichment_path=None):
        self.db_path = str(db_path)
        self.columns = list(columns)
        self.map = semantic
        self.enrichment_path = Path(enrichment_path) if enrichment_path else None

    def conn(self):
        c = sqlite3.connect(
            f"file:{Path(self.db_path).resolve()}?mode=ro", uri=True
        )
        c.row_factory = sqlite3.Row
        return c

    def states(self):
        with self.conn() as c:
            return [r[0] for r in c.execute(
                "SELECT DISTINCT trim(state) FROM school_fts "
                "WHERE trim(state)<>'' ORDER BY trim(state)"
            )]

    def districts(self, state):
        with self.conn() as c:
            return [r[0] for r in c.execute(
                "SELECT DISTINCT trim(district) FROM school_fts "
                "WHERE lower(trim(state))=lower(?) AND trim(district)<>'' "
                "ORDER BY trim(district)", (state,)
            )]

    def villages(self, state, district):
        with self.conn() as c:
            return [r[0] for r in c.execute(
                "SELECT DISTINCT trim(village) FROM school_fts "
                "WHERE lower(trim(state))=lower(?) "
                "AND lower(trim(district))=lower(?) "
                "AND trim(village)<>'' ORDER BY trim(village)",
                (state, district)
            )]

    def search(self, q, state, district="", village="", limit=3):
        q = norm(q)
        if not state:
            return []

        where = ["lower(trim(f.state))=lower(?)"]
        args = [state]

        if district and district != "All Districts":
            where.append("lower(trim(f.district))=lower(?)")
            args.append(district)

        if village and village != "All Villages":
            where.append("lower(trim(f.village))=lower(?)")
            args.append(village)

        filters = " AND ".join(where)

        with self.conn() as c:
            rows = []
            if q:
                toks = TOKEN_RE.findall(q)
                fts = " AND ".join(f'"{t}"*' for t in toks)
                rows = c.execute(
                    f"""SELECT s.row_id,s.data_json,
                               bm25(school_fts,1.0,1.2,.3,.3,.8,.8,2.0) rank
                        FROM school_fts f
                        JOIN schools s ON s.row_id=f.row_id
                        WHERE school_fts MATCH ? AND {filters}
                        ORDER BY rank LIMIT 40""",
                    [fts] + args
                ).fetchall()

                if len(rows) < limit:
                    more = c.execute(
                        f"""SELECT s.row_id,s.data_json,0 rank
                            FROM schools s JOIN school_fts f ON f.row_id=s.row_id
                            WHERE {filters}
                              AND (lower(f.name) LIKE lower(?)
                                   OR lower(f.updated_name) LIKE lower(?)
                                   OR lower(f.udise) LIKE lower(?))
                            LIMIT 20""",
                        args + [f"%{q}%", f"%{q}%", f"%{q}%"]
                    ).fetchall()
                    rows += more
            else:
                rows = c.execute(
                    f"""SELECT s.row_id,s.data_json,0 rank
                        FROM schools s JOIN school_fts f ON f.row_id=s.row_id
                        WHERE {filters} ORDER BY f.name LIMIT 40""",
                    args
                ).fetchall()

        seen, out = set(), []
        for r in rows:
            if r["row_id"] not in seen:
                seen.add(r["row_id"])
                out.append(json.loads(r["data_json"]))
            if len(out) >= limit:
                break
        return out
