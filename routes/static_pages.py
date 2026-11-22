# routes/static_pages.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import current_user
from extensions import mysql

static_pages_bp = Blueprint("static_pages", __name__, template_folder="../templates")


@static_pages_bp.route("/about")
def about():
    return render_template("pages/about.html")


@static_pages_bp.route("/contact")
def contact():
    return render_template("pages/contact.html")


@static_pages_bp.route("/help")
def help():
    return render_template("pages/help.html")


@static_pages_bp.route("/returns")
def returns():
    return render_template("pages/returns.html")


@static_pages_bp.route("/blog")
def blog():
    return render_template("blog/index.html")


@static_pages_bp.route("/blog/<slug>")
def blog_detail(slug):
    return render_template("blog/detail.html", slug=slug)


@static_pages_bp.route("/notifications")
def notifications():
    return render_template("pages/notifications.html")


@static_pages_bp.route("/faq")
def faq():
    return render_template("pages/faq.html")


# ─────────────────────────────────────────────
# Product Comparison  (up to 3 products)
# ─────────────────────────────────────────────
@static_pages_bp.route("/compare")
def compare():
    ids_raw = request.args.getlist("ids")
    # Also read from session basket
    basket = session.get("compare_ids", [])
    ids = list({int(i) for i in ids_raw + basket if str(i).isdigit()})[:3]

    products = []
    if ids:
        cur = mysql.connection.cursor()
        placeholders = ','.join(['%s'] * len(ids))
        cur.execute(
            f"SELECT * FROM products WHERE id IN ({placeholders})",
            ids,
        )
        products = cur.fetchall()
        cur.close()

    return render_template("pages/compare.html", products=products)


@static_pages_bp.route("/compare/add/<int:product_id>", methods=["POST"])
def compare_add(product_id):
    basket = session.get("compare_ids", [])
    if product_id not in basket:
        basket.append(product_id)
    session["compare_ids"] = basket[:3]
    next_url = request.form.get("next") or request.referrer or url_for("products.list_products")
    flash("Added to comparison.", "info")
    return redirect(next_url)


@static_pages_bp.route("/compare/remove/<int:product_id>", methods=["POST"])
def compare_remove(product_id):
    basket = session.get("compare_ids", [])
    basket = [i for i in basket if i != product_id]
    session["compare_ids"] = basket
    return redirect(url_for("static_pages.compare"))


@static_pages_bp.route("/compare/clear", methods=["POST"])
def compare_clear():
    session.pop("compare_ids", None)
    return redirect(url_for("products.list_products"))


# ─────────────────────────────────────────────
# Brand store pages
# ─────────────────────────────────────────────
@static_pages_bp.route("/brands")
def brands():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM brands WHERE active=1 ORDER BY name")
    brands = cur.fetchall()
    cur.close()
    return render_template("pages/brands.html", brands=brands)


@static_pages_bp.route("/brands/<slug>")
def brand_store(slug):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM brands WHERE slug=%s AND active=1", (slug,))
    brand = cur.fetchone()
    if not brand:
        flash("Brand not found.", "warning")
        cur.close()
        return redirect(url_for("static_pages.brands"))

    cur.execute(
        """SELECT id, name, price, image, category, stock
           FROM products WHERE brand_id=%s ORDER BY created_at DESC""",
        (brand['id'],),
    )
    products = cur.fetchall()

    # Wishlist ids
    wishlist_ids = set()
    if current_user.is_authenticated:
        cur.execute("SELECT product_id FROM wishlist WHERE user_id=%s", (current_user.id,))
        wishlist_ids = {r['product_id'] for r in cur.fetchall()}

    cur.close()
    return render_template(
        "pages/brand_store.html",
        brand=brand,
        products=products,
        wishlist_ids=wishlist_ids,
    )
