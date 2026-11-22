# routes/products.py
from flask import Blueprint, render_template, request, url_for, redirect, flash
from flask_login import current_user
from extensions import mysql
from math import ceil

products_bp = Blueprint("products", __name__, template_folder="../templates")


# ─────────────────────────────────────────────
# List products
# ─────────────────────────────────────────────
@products_bp.route('/')
def list_products():
    q            = request.args.get('q', '').strip()
    cat          = request.args.get('category', '').strip()
    sort         = request.args.get('sort', 'new').strip()
    price_range  = request.args.get('price_range', '').strip()
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1

    per_page = 12
    where, params = [], []

    if q:
        where.append("(name LIKE %s OR description LIKE %s)")
        params.extend([f"%{q}%", f"%{q}%"])
    if cat:
        where.append("category = %s")
        params.append(cat)
    if sort == 'sale':
        where.append("stock > 0")

    # Price range filter  e.g. "0-5000"
    if price_range and '-' in price_range:
        parts = price_range.split('-', 1)
        try:
            min_p = float(parts[0]) if parts[0] else None
            max_p = float(parts[1]) if parts[1] else None
            if min_p is not None:
                where.append("price >= %s"); params.append(min_p)
            if max_p:
                where.append("price <= %s"); params.append(max_p)
        except ValueError:
            pass

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    sort_map = {
        'new':        'created_at DESC',
        'price_asc':  'price ASC',
        'price_desc': 'price DESC',
        'sale':       'created_at DESC',
    }
    order_sql = sort_map.get(sort, 'created_at DESC')

    cur = mysql.connection.cursor()

    cur.execute(f"SELECT COUNT(*) AS cnt FROM products {where_sql}", params)
    total = cur.fetchone()['cnt']
    pages  = ceil(total / per_page) if total else 1
    offset = (page - 1) * per_page

    cur.execute(
        f"""SELECT id, name, description, price, stock, image, category
            FROM products {where_sql}
            ORDER BY {order_sql}
            LIMIT %s OFFSET %s""",
        params + [per_page, offset],
    )
    products = cur.fetchall()

    cur.execute(
        "SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND category <> ''"
    )
    categories = [r['category'] for r in cur.fetchall()]

    # Wishlist ids for the current user so we can mark heart icons
    wishlist_ids = set()
    if current_user.is_authenticated:
        cur.execute(
            "SELECT product_id FROM wishlist WHERE user_id = %s", (current_user.id,)
        )
        wishlist_ids = {row['product_id'] for row in cur.fetchall()}

    cur.close()

    return render_template(
        'products/list.html',
        products=products,
        q=q,
        category=cat,
        sort=sort,
        price_range=price_range,
        categories=categories,
        page=page,
        pages=pages,
        wishlist_ids=wishlist_ids,
    )


# ─────────────────────────────────────────────
# Product detail
# ─────────────────────────────────────────────
@products_bp.route('/<int:product_id>')
def product_detail(product_id):
    cur = mysql.connection.cursor()

    cur.execute('SELECT * FROM products WHERE id = %s', (product_id,))
    product = cur.fetchone()
    if not product:
        flash('Product not found.', 'warning')
        cur.close()
        return redirect(url_for('products.list_products'))

    # Reviews with reviewer name
    cur.execute(
        """SELECT r.id, r.rating, r.title, r.body, r.created_at, u.name AS reviewer
           FROM reviews r
           JOIN users u ON u.id = r.user_id
           WHERE r.product_id = %s
           ORDER BY r.created_at DESC""",
        (product_id,),
    )
    reviews = cur.fetchall()

    # Related products (same category, excluding this one)
    related = []
    if product.get('category'):
        cur.execute(
            """SELECT id, name, price, image FROM products
               WHERE category = %s AND id != %s
               ORDER BY created_at DESC LIMIT 4""",
            (product['category'], product_id),
        )
        related = cur.fetchall()

    # Is this product in the current user's wishlist?
    in_wishlist = False
    if current_user.is_authenticated:
        cur.execute(
            "SELECT id FROM wishlist WHERE user_id = %s AND product_id = %s",
            (current_user.id, product_id),
        )
        in_wishlist = cur.fetchone() is not None

    cur.close()

    return render_template(
        'products/detail.html',
        product=product,
        reviews=reviews,
        related=related,
        in_wishlist=in_wishlist,
    )
