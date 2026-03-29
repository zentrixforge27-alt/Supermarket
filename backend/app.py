"""
SUPERMARKET MANAGEMENT SYSTEM - Flask Backend
=============================================
Flask serves BOTH the frontend HTML AND the API.
Since they share the same origin (localhost:5000),
there are NO CORS issues and sessions work perfectly.

Run: python app.py
Open: http://localhost:5000
Login: admin / admin123
"""

import os
import sqlite3
import mimetypes
from datetime import date
from functools import wraps
from flask import Flask, request, jsonify, session, g, Response
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'supermarket-secret-key-change-in-production-2024'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'supermarket.db')
SCHEMA   = os.path.join(BASE_DIR, 'schema.sql')
FRONTEND = os.path.join(BASE_DIR, '..', 'frontend')

# ─── DATABASE ─────────────────────────────────────────────────────────────────

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

@app.teardown_appcontext
def close_db(_):
    db = g.pop('db', None)
    if db:
        db.close()

def qry(sql, args=(), one=False):
    cur  = get_db().execute(sql, args)
    rows = cur.fetchall()
    return (rows[0] if rows else None) if one else rows

def row2dict(row):
    return dict(zip(row.keys(), row)) if row else None

def init_db():
    with app.app_context():
        db = get_db()
        with open(SCHEMA, 'r', encoding='utf-8') as f:
            db.executescript(f.read())
        db.execute("DELETE FROM users WHERE username='admin'")
        db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?,?)",
            ('admin', generate_password_hash('admin123'))
        )
        db.commit()

# ─── AUTH DECORATOR ───────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized — please log in'}), 401
        return f(*args, **kwargs)
    return decorated

def ok(data, code=200):
    return jsonify(data), code

def err(msg, code=400):
    return jsonify({'error': msg}), code

# ─── FRONTEND ─────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    path = os.path.join(FRONTEND, 'index.html')
    with open(path, 'r', encoding='utf-8') as f:
        return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}

# ─── AUTH ─────────────────────────────────────────────────────────────────────

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()
    if not username or not password:
        return err('Username and password are required')
    user = qry("SELECT * FROM users WHERE username=?", [username], one=True)
    if user and check_password_hash(user['password_hash'], password):
        session.clear()
        session['user_id']  = user['id']
        session['username'] = user['username']
        return ok({'success': True, 'username': user['username']})
    return err('Invalid username or password', 401)

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return ok({'success': True})

@app.route('/api/auth/status')
def auth_status():
    if 'user_id' in session:
        return ok({'authenticated': True, 'username': session['username']})
    return ok({'authenticated': False})

# ─── CATEGORIES ───────────────────────────────────────────────────────────────

@app.route('/api/categories')
@login_required
def get_categories():
    return ok([row2dict(r) for r in qry("SELECT * FROM categories ORDER BY name")])

# ─── PRODUCTS ─────────────────────────────────────────────────────────────────

@app.route('/api/products')
@login_required
def get_products():
    search    = request.args.get('search', '').strip()
    category  = request.args.get('category', '').strip()
    low_stock = request.args.get('low_stock', '').strip()
    sql  = "SELECT p.*, c.name AS category_name FROM products p LEFT JOIN categories c ON p.category_id=c.id WHERE 1=1"
    args = []
    if search:
        sql += " AND (p.name LIKE ? OR p.barcode LIKE ?)"
        args += [f'%{search}%', f'%{search}%']
    if category:
        sql += " AND p.category_id=?"
        args.append(category)
    if low_stock:
        sql += " AND p.stock <= 10"
    sql += " ORDER BY p.name"
    return ok([row2dict(r) for r in qry(sql, args)])

@app.route('/api/products/<int:pid>')
@login_required
def get_product(pid):
    row = qry("SELECT p.*, c.name AS category_name FROM products p LEFT JOIN categories c ON p.category_id=c.id WHERE p.id=?", [pid], one=True)
    return ok(row2dict(row)) if row else err('Product not found', 404)

@app.route('/api/products', methods=['POST'])
@login_required
def create_product():
    data  = request.get_json(silent=True) or {}
    name  = (data.get('name') or '').strip()
    price = data.get('price')
    if not name:      return err('Product name is required')
    if price is None: return err('Price is required')
    try:
        db  = get_db()
        cur = db.execute(
            "INSERT INTO products (name, category_id, price, stock, barcode) VALUES (?,?,?,?,?)",
            (name, data.get('category_id') or None, float(price),
             int(data.get('stock') or 0), data.get('barcode') or None)
        )
        db.commit()
        return ok({'id': cur.lastrowid, 'message': 'Product created'}, 201)
    except sqlite3.IntegrityError as e:
        return err(str(e))

@app.route('/api/products/<int:pid>', methods=['PUT'])
@login_required
def update_product(pid):
    data  = request.get_json(silent=True) or {}
    name  = (data.get('name') or '').strip()
    price = data.get('price')
    if not name:      return err('Product name is required')
    if price is None: return err('Price is required')
    db = get_db()
    db.execute(
        "UPDATE products SET name=?, category_id=?, price=?, stock=?, barcode=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (name, data.get('category_id') or None, float(price),
         int(data.get('stock') or 0), data.get('barcode') or None, pid)
    )
    db.commit()
    return ok({'message': 'Product updated'})

@app.route('/api/products/<int:pid>', methods=['DELETE'])
@login_required
def delete_product(pid):
    db = get_db()
    db.execute("DELETE FROM products WHERE id=?", [pid])
    db.commit()
    return ok({'message': 'Product deleted'})

# ─── CUSTOMERS ────────────────────────────────────────────────────────────────

@app.route('/api/customers')
@login_required
def get_customers():
    search = request.args.get('search', '').strip()
    sql, args = "SELECT * FROM customers WHERE 1=1", []
    if search:
        sql += " AND (name LIKE ? OR phone LIKE ? OR email LIKE ?)"
        args += [f'%{search}%', f'%{search}%', f'%{search}%']
    sql += " ORDER BY name"
    return ok([row2dict(r) for r in qry(sql, args)])

@app.route('/api/customers/<int:cid>')
@login_required
def get_customer(cid):
    row = qry("SELECT * FROM customers WHERE id=?", [cid], one=True)
    return ok(row2dict(row)) if row else err('Customer not found', 404)

@app.route('/api/customers', methods=['POST'])
@login_required
def create_customer():
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    if not name: return err('Customer name is required')
    db  = get_db()
    cur = db.execute(
        "INSERT INTO customers (name, phone, email) VALUES (?,?,?)",
        (name, data.get('phone') or None, data.get('email') or None)
    )
    db.commit()
    return ok({'id': cur.lastrowid, 'message': 'Customer created'}, 201)

@app.route('/api/customers/<int:cid>', methods=['PUT'])
@login_required
def update_customer(cid):
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    if not name: return err('Customer name is required')
    db = get_db()
    db.execute("UPDATE customers SET name=?, phone=?, email=? WHERE id=?",
               (name, data.get('phone') or None, data.get('email') or None, cid))
    db.commit()
    return ok({'message': 'Customer updated'})

@app.route('/api/customers/<int:cid>', methods=['DELETE'])
@login_required
def delete_customer(cid):
    db = get_db()
    db.execute("DELETE FROM customers WHERE id=?", [cid])
    db.commit()
    return ok({'message': 'Customer deleted'})

@app.route('/api/customers/<int:cid>/orders')
@login_required
def customer_orders(cid):
    rows = qry("SELECT * FROM orders WHERE customer_id=? ORDER BY created_at DESC", [cid])
    return ok([row2dict(r) for r in rows])

# ─── ORDERS ───────────────────────────────────────────────────────────────────

@app.route('/api/orders')
@login_required
def get_orders():
    date_from = request.args.get('from', '').strip()
    date_to   = request.args.get('to',   '').strip()
    sql  = "SELECT o.*, c.name AS customer_name FROM orders o LEFT JOIN customers c ON o.customer_id=c.id WHERE 1=1"
    args = []
    if date_from:
        sql += " AND DATE(o.created_at) >= ?"; args.append(date_from)
    if date_to:
        sql += " AND DATE(o.created_at) <= ?"; args.append(date_to)
    sql += " ORDER BY o.created_at DESC LIMIT 200"
    return ok([row2dict(r) for r in qry(sql, args)])

@app.route('/api/orders/<int:oid>')
@login_required
def get_order(oid):
    order = qry(
        "SELECT o.*, c.name AS customer_name, c.phone AS customer_phone FROM orders o LEFT JOIN customers c ON o.customer_id=c.id WHERE o.id=?",
        [oid], one=True
    )
    if not order: return err('Order not found', 404)
    items          = qry("SELECT oi.*, p.name AS product_name FROM order_items oi JOIN products p ON oi.product_id=p.id WHERE oi.order_id=?", [oid])
    result         = row2dict(order)
    result['items'] = [row2dict(i) for i in items]
    return ok(result)

@app.route('/api/orders', methods=['POST'])
@login_required
def create_order():
    data  = request.get_json(silent=True) or {}
    items = data.get('items', [])
    if not items: return err('Cart is empty')
    db = get_db()
    try:
        for item in items:
            prod = db.execute("SELECT * FROM products WHERE id=?", [item['product_id']]).fetchone()
            if not prod:                             return err(f"Product ID {item['product_id']} not found")
            if prod['stock'] < int(item['quantity']): return err(f"Not enough stock for '{prod['name']}' (available: {prod['stock']})")

        subtotal = sum(float(i['price']) * int(i['quantity']) for i in items)
        discount = float(data.get('discount') or 0)
        tax_rate = float(data.get('tax_rate') or 5)
        tax      = round(max(subtotal - discount, 0) * tax_rate / 100, 2)
        total    = round(max(subtotal - discount, 0) + tax, 2)

        cur = db.execute(
            "INSERT INTO orders (customer_id, total_amount, discount, tax, payment_method) VALUES (?,?,?,?,?)",
            (data.get('customer_id') or None, total, discount, tax, data.get('payment_method', 'cash'))
        )
        order_id = cur.lastrowid
        for item in items:
            db.execute("INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?,?,?,?)",
                       (order_id, item['product_id'], int(item['quantity']), float(item['price'])))
            db.execute("UPDATE products SET stock = stock - ? WHERE id=?",
                       (int(item['quantity']), item['product_id']))
        db.commit()
        return ok({'order_id': order_id, 'total': total, 'tax': tax, 'discount': discount}, 201)
    except Exception as e:
        db.rollback()
        return err(str(e), 500)

# ─── ANALYTICS ────────────────────────────────────────────────────────────────

@app.route('/api/analytics/dashboard')
@login_required
def dashboard_stats():
    db    = get_db()
    today = date.today().isoformat()
    return ok({
        'total_products':  db.execute("SELECT COUNT(*) FROM products").fetchone()[0],
        'total_customers': db.execute("SELECT COUNT(*) FROM customers").fetchone()[0],
        'today_sales':     round(db.execute("SELECT COALESCE(SUM(total_amount),0) FROM orders WHERE DATE(created_at)=?", [today]).fetchone()[0], 2),
        'today_orders':    db.execute("SELECT COUNT(*) FROM orders WHERE DATE(created_at)=?", [today]).fetchone()[0],
        'low_stock_items': db.execute("SELECT COUNT(*) FROM products WHERE stock <= 10").fetchone()[0],
        'total_revenue':   round(db.execute("SELECT COALESCE(SUM(total_amount),0) FROM orders").fetchone()[0], 2),
    })

@app.route('/api/analytics/sales')
@login_required
def sales_analytics():
    days = int(request.args.get('days', 7))
    rows = qry(
        "SELECT DATE(created_at) AS date, COUNT(*) AS orders, ROUND(SUM(total_amount),2) AS revenue FROM orders WHERE created_at >= DATE('now', ?) GROUP BY DATE(created_at) ORDER BY date",
        [f'-{days} days']
    )
    return ok([row2dict(r) for r in rows])

@app.route('/api/analytics/top-products')
@login_required
def top_products():
    rows = qry(
        "SELECT p.name, SUM(oi.quantity) AS total_sold, ROUND(SUM(oi.quantity*oi.price),2) AS revenue FROM order_items oi JOIN products p ON oi.product_id=p.id GROUP BY oi.product_id ORDER BY total_sold DESC LIMIT 10"
    )
    return ok([row2dict(r) for r in rows])

@app.route('/api/analytics/category-sales')
@login_required
def category_sales():
    rows = qry(
        "SELECT COALESCE(c.name,'Uncategorised') AS category, ROUND(SUM(oi.quantity*oi.price),2) AS revenue FROM order_items oi JOIN products p ON oi.product_id=p.id LEFT JOIN categories c ON p.category_id=c.id GROUP BY p.category_id ORDER BY revenue DESC"
    )
    return ok([row2dict(r) for r in rows])

# ─── SEED ─────────────────────────────────────────────────────────────────────

@app.route('/api/seed', methods=['POST'])
@login_required
def seed_data():
    db = get_db()
    products = [
        ('Fresh Apples',        1,  2.99, 150, 'BAR001'),
        ('Whole Milk 1L',       2,  1.49,  80, 'BAR002'),
        ('Chicken Breast 500g', 3,  5.99,  45, 'BAR003'),
        ('Sourdough Bread',     4,  3.49,  30, 'BAR004'),
        ('Orange Juice 1L',     5,  2.99,  60, 'BAR005'),
        ('Potato Chips',        6,  1.99, 120, 'BAR006'),
        ('Frozen Pizza',        7,  4.99,  40, 'BAR007'),
        ('Shampoo 200ml',       8,  3.99,  55, 'BAR008'),
        ('Dish Soap',           9,  1.79,  90, 'BAR009'),
        ('Banana Bunch',        1,  1.29, 200, 'BAR010'),
        ('Cheddar Cheese',      2,  4.49,   8, 'BAR011'),
        ('Sparkling Water',     5,  0.99, 150, 'BAR012'),
        ('Tomatoes 500g',       1,  1.99,  60, 'BAR013'),
        ('Yoghurt 400g',        2,  2.49,  35, 'BAR014'),
        ('Biscuits Pack',       6,  1.49,   6, 'BAR015'),
    ]
    for p in products:
        db.execute("INSERT OR IGNORE INTO products (name, category_id, price, stock, barcode) VALUES (?,?,?,?,?)", p)
    customers = [
        ('Alice Johnson', '555-0101', 'alice@email.com'),
        ('Bob Smith',     '555-0102', 'bob@email.com'),
        ('Carol White',   '555-0103', 'carol@email.com'),
        ('David Brown',   '555-0104', 'david@email.com'),
    ]
    for c in customers:
        db.execute("INSERT OR IGNORE INTO customers (name, phone, email) VALUES (?,?,?)", c)
    db.commit()
    return ok({'message': 'Sample data loaded successfully'})

# ─── RUN ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    print("\n" + "="*50)
    print("  SuperMart Management System")
    print("="*50)
    print("  URL   : http://localhost:5000")
    print("  Login : admin / admin123")
    print("="*50 + "\n")
    app.run(debug=True, port=5000, host='0.0.0.0')
