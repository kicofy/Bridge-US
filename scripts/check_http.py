import os
import sqlite3
import urllib.request


def get_latest_approved_post_id(db_path: str) -> int:
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT id FROM posts WHERE status='approved' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if not row:
            raise RuntimeError("No approved posts found.")
        return int(row[0])
    finally:
        con.close()


def main() -> None:
    base = "http://127.0.0.1:5000"
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "instance", "app.db"))

    print("GET /", urllib.request.urlopen(f"{base}/").status)
    print("GET /?city=Boston&section=first_week", urllib.request.urlopen(f"{base}/?city=Boston&section=first_week").status)

    pid = get_latest_approved_post_id(db_path)
    print("latest_approved_post_id", pid)
    print("GET /posts/<id>", urllib.request.urlopen(f"{base}/posts/{pid}").status)


if __name__ == "__main__":
    main()


