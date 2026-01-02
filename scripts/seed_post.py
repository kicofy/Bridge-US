import os
import sqlite3


def main() -> None:
    db_path = os.path.join(os.path.dirname(__file__), "..", "instance", "app.db")
    db_path = os.path.abspath(db_path)

    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """
            INSERT INTO posts (title, content, city, section, status, source_lang)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "Welcome to Bridge US",
                "This is a seeded approved post so you can verify Step 2 wiring.",
                "Boston",
                "first_week",
                "approved",
                "en",
            ),
        )
        con.execute(
            "UPDATE posts SET author_name=?, author_handle=? WHERE id = (SELECT id FROM posts ORDER BY id DESC LIMIT 1)",
            ("Bridge Team", "@bridgeus"),
        )
        con.commit()
        print("Seeded 1 approved post.")
    finally:
        con.close()


if __name__ == "__main__":
    main()


