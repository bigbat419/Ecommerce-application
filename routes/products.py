# routes/products.py
from flask import Blueprint, jsonify, render_template, request, url_for, redirect, flash
from extensions import mysql
from math import ceil
from flask import Blueprint, request, jsonify

products_bp = Blueprint("products", __name__, template_folder="../templates")

# -------------------------
# List products with search, category filter, and pagination
# -------------------------

product_bp = Blueprint("product", __name__)
@product_bp.route("/products", methods=["POST"])
def add_product():
    data = request.json
    (
        "INSERT INTO products (name, price, image) VALUES (%s, %s, %s)",
        (data["name"], data["price"], data["image"])
    )
    return jsonify({"message": "Product added"})

@products_bp.route('/products')
def list_products():
    q = request.args.get('q', '').strip()
    cat = request.args.get('category', '').strip()
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1

    per_page = 8
    where = []
    params = []

    # Search filter
    if q:
        where.append("(name LIKE %s OR description LIKE %s)")
        params.extend([f"%{q}%", f"%{q}%"])

    # Category filter
    if cat:
        where.append("category = %s")
        params.append(cat)

    where_sql = "WHERE " + " AND ".join(where) if where else ""

    # Cursor (DictCursor already set globally in extensions.py)
    cur = mysql.connection.cursor()

    # Count total
    count_q = f"SELECT COUNT(*) as cnt FROM products {where_sql}"
    cur.execute(count_q, params)
    total = cur.fetchone()['cnt']

    pages = ceil(total / per_page) if total else 1
    offset = (page - 1) * per_page

    # Fetch products
    q_sql = f"""
        SELECT id, name, description, price, stock, image, category
        FROM products {where_sql}
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
    """
    cur.execute(q_sql, params + [per_page, offset])
    products = cur.fetchall()

    # Fetch categories
    cur.execute("SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND category <> ''")
    categories = [r['category'] for r in cur.fetchall()]
    cur.close()


    return render_template(
        'products/list.html',
        products=products,
        q=q,
        category=cat,
        categories=categories,
        page=page,
        pages=pages
    )


# -------------------------
# Product detail
# -------------------------
@products_bp.route('/product/<int:product_id>')
def product_detail(product_id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM products WHERE id=%s', (product_id,))
    product = cur.fetchone()
    cur.close()

    if not product:
        flash('Product not found', 'warning')
        return redirect(url_for('products/list.html'))

    return render_template('products/detail.html', product=product)
