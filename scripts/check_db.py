import os
import sqlite3


def main() -> None:
    db_path = os.path.join(os.path.dirname(__file__), "..", "instance", "app.db")
    db_path = os.path.abspath(db_path)
    print("db_path:", db_path)
    print("db_exists:", os.path.exists(db_path))

    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='posts'"
        ).fetchone()
        print("posts_table:", row)
    finally:
        con.close()


if __name__ == "__main__":
    main()


