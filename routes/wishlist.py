# routes/wishlist.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import mysql

wishlist_bp = Blueprint("wishlist", __name__, template_folder="../templates")


@wishlist_bp.route("/")
@login_required
def list_wishlist():
    cur = mysql.connection.cursor()
    cur.execute(
        """SELECT p.id, p.name, p.price, p.image, p.category, p.stock,
                  w.id AS wish_id
           FROM wishlist w
           JOIN products p ON p.id = w.product_id
           WHERE w.user_id = %s
           ORDER BY w.added_at DESC""",
        (current_user.id,),
    )
    items = cur.fetchall()
    cur.close()
    return render_template("wishlist/list.html", items=items)


@wishlist_bp.route("/toggle/<int:product_id>", methods=["POST"])
@login_required
def toggle_wishlist(product_id):
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT id FROM wishlist WHERE user_id = %s AND product_id = %s",
        (current_user.id, product_id),
    )
    existing = cur.fetchone()
    if existing:
        cur.execute("DELETE FROM wishlist WHERE id = %s", (existing["id"],))
        flash("Removed from wishlist.", "info")
    else:
        cur.execute(
            "INSERT INTO wishlist (user_id, product_id) VALUES (%s, %s)",
            (current_user.id, product_id),
        )
        flash("Added to wishlist!", "success")
    mysql.connection.commit()
    cur.close()

    # Redirect back to whichever page triggered the toggle
    next_url = request.form.get("next") or request.referrer or url_for("products.list_products")
    return redirect(next_url)


@wishlist_bp.route("/remove/<int:wish_id>", methods=["POST"])
@login_required
def remove_wishlist(wish_id):
    cur = mysql.connection.cursor()
    cur.execute(
        "DELETE FROM wishlist WHERE id = %s AND user_id = %s",
        (wish_id, current_user.id),
    )
    mysql.connection.commit()
    cur.close()
    flash("Item removed from wishlist.", "info")
    return redirect(url_for("wishlist.list_wishlist"))


@wishlist_bp.route("/move-to-cart/<int:wish_id>", methods=["POST"])
@login_required
def move_to_cart(wish_id):
    """Move a wishlist item into the cart then remove it from the wishlist."""
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT product_id FROM wishlist WHERE id = %s AND user_id = %s",
        (wish_id, current_user.id),
    )
    row = cur.fetchone()
    if not row:
        flash("Item not found.", "warning")
        cur.close()
        return redirect(url_for("wishlist.list_wishlist"))

    product_id = row["product_id"]

    # Check stock
    cur.execute("SELECT stock FROM products WHERE id = %s", (product_id,))
    product = cur.fetchone()
    if not product or product["stock"] < 1:
        flash("This item is out of stock.", "danger")
        cur.close()
        return redirect(url_for("wishlist.list_wishlist"))

    # Upsert into cart
    cur.execute(
        "SELECT id, quantity FROM cart_items WHERE user_id = %s AND product_id = %s",
        (current_user.id, product_id),
    )
    cart_row = cur.fetchone()
    if cart_row:
        new_qty = min(cart_row["quantity"] + 1, product["stock"])
        cur.execute(
            "UPDATE cart_items SET quantity = %s WHERE id = %s",
            (new_qty, cart_row["id"]),
        )
    else:
        cur.execute(
            "INSERT INTO cart_items (user_id, product_id, quantity) VALUES (%s, %s, 1)",
            (current_user.id, product_id),
        )

    # Remove from wishlist
    cur.execute(
        "DELETE FROM wishlist WHERE id = %s AND user_id = %s",
        (wish_id, current_user.id),
    )
    mysql.connection.commit()
    cur.close()
    flash("Moved to cart!", "success")
    return redirect(url_for("cart.view_cart"))
