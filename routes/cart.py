from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import mysql

cart_bp = Blueprint("cart", __name__, template_folder="../templates")


@cart_bp.route("/view", endpoint="view_cart")
@login_required
def cart_view():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT ci.id, p.id AS product_id, p.name, p.price, ci.quantity, p.image, p.stock
        FROM cart_items ci
        JOIN products p ON p.id = ci.product_id
        WHERE ci.user_id = %s
    """, (current_user.id,))
    items = cur.fetchall()
    cur.close()

    for it in items:
        it["price"] = float(it["price"] or 0)
        it["quantity"] = int(it["quantity"] or 0)

    total = sum(it["price"] * it["quantity"] for it in items)
    return render_template("cart/view.html", items=items, total=total)


@cart_bp.route("/add/<int:product_id>", methods=["POST"])
@login_required
def cart_add(product_id):
    qty = int(request.form.get("quantity", 1))

    cur = mysql.connection.cursor()
    # Check stock
    cur.execute("SELECT stock FROM products WHERE id=%s", (product_id,))
    product = cur.fetchone()
    if not product:
        flash("Product not found.", "warning")
        cur.close()
        return redirect(url_for("products.list_products"))

    cur.execute(
        "SELECT id, quantity FROM cart_items WHERE user_id=%s AND product_id=%s",
        (current_user.id, product_id),
    )
    row = cur.fetchone()

    if row:
        new_qty = row["quantity"] + qty
        if new_qty > product["stock"]:
            flash("Not enough stock available.", "warning")
            cur.close()
            return redirect(url_for("products.product_detail", product_id=product_id))
        cur.execute(
            "UPDATE cart_items SET quantity=%s WHERE id=%s", (new_qty, row["id"])
        )
    else:
        if qty > product["stock"]:
            flash("Not enough stock available.", "warning")
            cur.close()
            return redirect(url_for("products.product_detail", product_id=product_id))
        cur.execute(
            "INSERT INTO cart_items (user_id, product_id, quantity) VALUES (%s,%s,%s)",
            (current_user.id, product_id, qty),
        )

    mysql.connection.commit()
    cur.close()
    flash("Added to cart.", "success")
    return redirect(url_for("products.product_detail", product_id=product_id))


@cart_bp.route("/update/<int:item_id>", methods=["POST"])
@login_required
def cart_update(item_id):
    qty = int(request.form.get("quantity", 1))
    cur = mysql.connection.cursor()
    if qty < 1:
        cur.execute("DELETE FROM cart_items WHERE id=%s AND user_id=%s", (item_id, current_user.id))
    else:
        cur.execute(
            "UPDATE cart_items SET quantity=%s WHERE id=%s AND user_id=%s",
            (qty, item_id, current_user.id),
        )
    mysql.connection.commit()
    cur.close()
    return redirect(url_for("cart.view_cart"))


@cart_bp.route("/remove/<int:item_id>", methods=["POST"], endpoint="remove")
@login_required
def cart_remove(item_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM cart_items WHERE id=%s AND user_id=%s", (item_id, current_user.id))
    mysql.connection.commit()
    cur.close()
    flash("Item removed.", "info")
    return redirect(url_for("cart.view_cart"))


@cart_bp.route("/count")
@login_required
def cart_count():
    cur = mysql.connection.cursor()
    cur.execute("SELECT COALESCE(SUM(quantity),0) AS cnt FROM cart_items WHERE user_id=%s", (current_user.id,))
    cnt = cur.fetchone()["cnt"]
    cur.close()
    return jsonify({"count": int(cnt)})
