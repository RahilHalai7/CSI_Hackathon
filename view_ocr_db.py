import argparse
import os
import sqlite3


def connect_db(db_path: str) -> sqlite3.Connection:
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"SQLite database not found: {db_path}")
    return sqlite3.connect(db_path)


def fetch_records(conn: sqlite3.Connection, rec_id: int | None, limit: int, search: str | None):
    if rec_id is not None:
        cur = conn.execute(
            """
            SELECT id, source_pdf_path, output_file_path, page_range, ocr_only, structured,
                   created_at, text
            FROM ocr_texts
            WHERE id = ?
            """,
            (rec_id,),
        )
        row = cur.fetchone()
        return [row] if row else []

    base_sql = (
        "SELECT id, source_pdf_path, output_file_path, page_range, ocr_only, structured, "
        "created_at, text FROM ocr_texts"
    )
    params: list = []
    if search:
        base_sql += " WHERE source_pdf_path LIKE ? OR output_file_path LIKE ?"
        like = f"%{search}%"
        params.extend([like, like])

    base_sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    cur = conn.execute(base_sql, params)
    return cur.fetchall()


def format_bool(i: int | None) -> str:
    return "yes" if i else "no"


def print_record(row: tuple, show_text: bool, full_text: bool):
    if not row:
        return
    rid, src, out, pages, ocr_only, structured, created_at, text = row
    print("=" * 80)
    print(f"ID: {rid} | Created: {created_at}")
    print(f"Source PDF: {src}")
    print(f"Output File: {out}")
    print(f"Page Range: {pages or ''}")
    print(f"OCR Only: {format_bool(ocr_only)} | Structured: {format_bool(structured)}")
    if show_text:
        print("-" * 80)
        if full_text or not text:
            print(text or "")
        else:
            snippet = text[:1200]
            print(snippet)
            if len(text) > len(snippet):
                print("\n[...truncated. Use --full-text to show complete content...]\n")


def main():
    parser = argparse.ArgumentParser(description="View OCR text entries from SQLite database")
    parser.add_argument("--db-path", default=os.path.join("data", "ocr.db"), help="Path to SQLite DB")
    parser.add_argument("--id", type=int, help="Show a single record by ID")
    parser.add_argument("--limit", type=int, default=5, help="Number of records to list when not using --id")
    parser.add_argument("--search", help="Filter records by matching source/output path substring")
    parser.add_argument("--full-text", action="store_true", default=True, help="Print full text (default)")
    parser.add_argument("--truncate", action="store_true", help="Print only first 1200 characters of text")
    parser.add_argument("--no-text", action="store_true", help="Do not print the text content")
    args = parser.parse_args()

    try:
        conn = connect_db(args.db_path)
    except Exception as e:
        print(f"❌ {e}")
        return 1

    try:
        rows = fetch_records(conn, args.id, args.limit, args.search)
        if not rows:
            if args.id is not None:
                print(f"No record found with ID {args.id}")
            else:
                print("No records found.")
            return 0

        for row in rows:
            # Default prints full text; use --truncate to shorten
            print_record(row, show_text=not args.no_text, full_text=(args.full_text or (not args.truncate)))
        print("=" * 80)
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())