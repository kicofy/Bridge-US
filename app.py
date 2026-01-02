import os
from typing import Optional

from flask import Flask, flash, redirect, render_template, request, session, url_for
try:
    from flask_babel import Babel, get_locale as babel_get_locale
except ImportError as e:
    raise SystemExit(
        "Flask-Babel failed to import. This usually means you're running the app with the wrong Python\n"
        "environment (e.g. global/base Python instead of this project's .venv).\n\n"
        "Fix:\n"
        "  .\\.venv\\Scripts\\python -m pip install -r requirements.txt\n"
        "  .\\.venv\\Scripts\\python app.py\n"
    ) from e

from db import (
    SUPPORTED_LANGS,
    close_db,
    create_user,
    create_post,
    get_post_by_id,
    get_user_by_email,
    get_user_by_id,
    init_db,
    list_approved_posts,
    list_pending_posts,
    list_user_posts_in_section,
    review_post,
    set_admin_by_email,
    verify_user_password,
)


def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    # Minimal config for early MVP
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev-only-change-me")
    app.config["BABEL_DEFAULT_LOCALE"] = "en"
    app.config["BABEL_SUPPORTED_LOCALES"] = ["en", "zh"]

    def get_locale() -> str:
        # Priority: user-chosen lang -> query param -> browser -> default
        chosen = session.get("lang")
        if chosen in app.config["BABEL_SUPPORTED_LOCALES"]:
            return chosen

        # If logged in, fall back to user's preferred language
        user_id = session.get("user_id")
        if isinstance(user_id, int):
            user = get_user_by_id(user_id)
            if user and user.get("lang") in app.config["BABEL_SUPPORTED_LOCALES"]:
                return user["lang"]

        q = request.args.get("lang")
        if q in app.config["BABEL_SUPPORTED_LOCALES"]:
            return q

        return request.accept_languages.best_match(app.config["BABEL_SUPPORTED_LOCALES"]) or "en"

    Babel(app, locale_selector=get_locale)

    @app.context_processor
    def inject_i18n_helpers():
        # Make locale available to Jinja templates (e.g., base.html <html lang="...">)
        locale_obj = babel_get_locale()
        # Flask-Babel may return a babel Locale object; normalize to "en"/"zh"
        if locale_obj is None:
            lang = "en"
        else:
            lang = getattr(locale_obj, "language", None) or str(locale_obj).split("_")[0]

        sections = [
            {"code": "first_week", "label": "First week" if lang == "en" else "落地第一周"},
            {
                "code": "housing_move_in",
                "label": "Housing & move-in" if lang == "en" else "找房与入住",
            },
            {
                "code": "food_groceries",
                "label": "Food & groceries" if lang == "en" else "食物与超市",
            },
            {
                "code": "transportation",
                "label": "Transportation" if lang == "en" else "交通出行",
            },
            {"code": "life_admin", "label": "Life admin" if lang == "en" else "办事与生活"},
            {
                "code": "safety_scams",
                "label": "Safety & scams" if lang == "en" else "安全与诈骗",
            },
        ]

        section_label_map = {s["code"]: s["label"] for s in sections}
        current_user = None
        user_id = session.get("user_id")
        if isinstance(user_id, int):
            current_user = get_user_by_id(user_id)
        return {
            "get_locale": babel_get_locale,
            "sections": sections,
            "section_label": lambda code: section_label_map.get(code, code),
            "current_user": current_user,
        }

    # SQLite (Step 2)
    app.config["DATABASE_PATH"] = os.path.join(app.instance_path, "app.db")
    with app.app_context():
        init_db()
    app.teardown_appcontext(close_db)

    # Optional: bootstrap an admin user by email (early MVP)
    admin_email = os.environ.get("ADMIN_EMAIL")
    if admin_email:
        with app.app_context():
            try:
                set_admin_by_email(admin_email)
            except Exception:
                pass

    @app.get("/")
    def index():
        # Home = recommended posts (simple: latest approved)
        posts = list_approved_posts(limit=10)
        return render_template("index.html", posts=posts)

    @app.get("/sections")
    def sections_page():
        return render_template("sections.html")

    @app.get("/sections/<section_code>")
    def section_posts(section_code: str):
        allowed = {s["code"] for s in inject_i18n_helpers()["sections"]}
        if section_code not in allowed:
            return ("Not found", 404)

        posts = list_approved_posts(limit=50, section=section_code)
        return render_template(
            "section_posts.html",
            posts=posts,
            section_code=section_code,
        )

    @app.get("/submit")
    def submit_page():
        user_id = session.get("user_id")
        if not isinstance(user_id, int):
            flash("Please log in to submit a post.", "error")
            return redirect(url_for("login_page"))

        user = get_user_by_id(user_id)
        default_lang = (user.get("lang") if user else "en") or "en"
        if default_lang not in SUPPORTED_LANGS:
            default_lang = "en"

        return render_template("submit.html", supported_langs=sorted(SUPPORTED_LANGS), default_lang=default_lang)

    @app.post("/submit")
    def submit_post():
        user_id = session.get("user_id")
        if not isinstance(user_id, int):
            flash("Please log in to submit a post.", "error")
            return redirect(url_for("login_page"))

        user = get_user_by_id(user_id)

        title = (request.form.get("title") or "").strip()
        content = (request.form.get("content") or "").strip()
        city = (request.form.get("city") or "").strip()
        section = (request.form.get("section") or "").strip()
        source_lang = (request.form.get("source_lang") or "en").strip()

        allowed_sections = {s["code"] for s in inject_i18n_helpers()["sections"]}
        if section not in allowed_sections:
            flash("Please choose a valid section.", "error")
            return redirect(url_for("submit_page"))
        if not title:
            flash("Title is required.", "error")
            return redirect(url_for("submit_page"))
        if not content:
            flash("Content is required.", "error")
            return redirect(url_for("submit_page"))
        if source_lang not in SUPPORTED_LANGS:
            source_lang = (user.get("lang") if user else "en") or "en"
            if source_lang not in SUPPORTED_LANGS:
                source_lang = "en"

        author_name = user["username"] if user else "Anonymous"
        author_handle = f"@{user['username']}" if user else None

        post_id = create_post(
            title=title,
            content=content,
            section=section,
            city=city or None,
            source_lang=source_lang,
            author_name=author_name,
            author_handle=author_handle,
            author_user_id=user_id,
            status="approved",
        )

        flash("Published. Your post is now live.", "success")
        return redirect(url_for("post_detail", post_id=post_id))

    @app.get("/posts/<int:post_id>")
    def post_detail(post_id: int):
        post = get_post_by_id(post_id)
        if not post:
            return ("Not found", 404)
        return render_template("post_detail.html", post=post)

    @app.get("/set-lang/<lang>")
    def set_lang(lang: str):
        if lang in app.config["BABEL_SUPPORTED_LOCALES"]:
            session["lang"] = lang
        return redirect(request.referrer or url_for("index"))

    @app.get("/register")
    def register_page():
        return render_template("register.html", supported_langs=sorted(SUPPORTED_LANGS))

    @app.post("/register")
    def register_submit():
        email = (request.form.get("email") or "").strip().lower()
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        lang = (request.form.get("lang") or "en").strip()

        if not email or "@" not in email:
            flash("Please enter a valid email.", "error")
            return redirect(url_for("register_page"))
        if not username:
            flash("Please enter a username.", "error")
            return redirect(url_for("register_page"))
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return redirect(url_for("register_page"))
        if lang not in SUPPORTED_LANGS:
            lang = "en"

        if get_user_by_email(email):
            flash("This email is already registered. Please log in.", "error")
            return redirect(url_for("login_page"))

        user = create_user(email=email, username=username, password=password, lang=lang)
        session["user_id"] = user["id"]
        session["lang"] = user.get("lang", "en")
        flash("Account created.", "success")
        return redirect(url_for("index"))

    @app.get("/login")
    def login_page():
        return render_template("login.html")

    @app.post("/login")
    def login_submit():
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        user = verify_user_password(email=email, password=password)
        if not user:
            flash("Invalid email or password.", "error")
            return redirect(url_for("login_page"))

        session["user_id"] = user["id"]
        session["lang"] = user.get("lang", "en")
        flash("Logged in.", "success")
        return redirect(url_for("index"))

    @app.post("/logout")
    def logout():
        session.pop("user_id", None)
        # Keep session lang as user-chosen global, or clear it; we keep it.
        flash("Logged out.", "success")
        return redirect(url_for("index"))

    def require_admin() -> Optional[tuple[str, int]]:
        user_id = session.get("user_id")
        if not isinstance(user_id, int):
            return ("Not found", 404)
        user = get_user_by_id(user_id)
        if not user or int(user.get("is_admin") or 0) != 1:
            return ("Not found", 404)
        return None

    @app.get("/admin/queue")
    def admin_queue():
        denied = require_admin()
        if denied:
            return denied
        pending = list_pending_posts(limit=200)
        return render_template("admin_queue.html", pending=pending)

    @app.post("/admin/review/<int:post_id>")
    def admin_review(post_id: int):
        denied = require_admin()
        if denied:
            return denied
        user_id = session.get("user_id")
        assert isinstance(user_id, int)

        decision = (request.form.get("decision") or "").strip()
        note = (request.form.get("note") or "").strip()
        try:
            review_post(post_id=post_id, decision=decision, reviewer_user_id=user_id, note=note)
        except Exception:
            flash("Review failed.", "error")
            return redirect(url_for("admin_queue"))

        flash(f"Post {post_id} -> {decision}", "success")
        return redirect(url_for("admin_queue"))

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=True)


