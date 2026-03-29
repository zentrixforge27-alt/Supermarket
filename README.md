# 🛒 SuperMart — Supermarket Management System

A full-stack supermarket management application built with **Flask** (Python) + **SQLite** + **Vanilla JS**.

---

## 📁 Project Structure

```
supermarket/
├── backend/
│   ├── app.py              # Flask application (all API routes)
│   ├── schema.sql          # Database schema + seed categories
│   ├── requirements.txt    # Python dependencies
│   └── supermarket.db      # SQLite database (auto-created)
├── frontend/
│   └── index.html          # Single-page application (HTML + CSS + JS)
├── run.sh                  # Quick start script (Linux/Mac)
└── README.md
```

---

## 🚀 Quick Start

### Option 1 — Shell Script (Linux/Mac)
```bash
chmod +x run.sh
./run.sh
```

### Option 2 — Manual Setup
```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

# 2. Install dependencies
pip install Flask Werkzeug

# 3. Run the server
cd backend
python3 app.py
```

### Option 3 — Windows
```cmd
python -m venv venv
venv\Scripts\activate
pip install Flask Werkzeug
cd backend
python app.py
```

Open your browser: **http://localhost:5000**

---

## 🔑 Default Login
| Field | Value |
|-------|-------|
| Username | `admin` |
| Password | `admin123` |

---

## 🌱 Load Sample Data
After logging in, click the **"Load Sample Data"** button on the Dashboard to populate:
- 12 sample products across categories
- 4 sample customers

---

## 📊 Features

### Dashboard
- Real-time stats: today's revenue, orders, total products, low-stock alerts
- 7-day sales bar chart
- Top products by units sold
- Revenue by category (pie chart)

### Products
- Add / Edit / Delete products
- Search by name or barcode
- Filter by category
- Low-stock filter (≤10 units)
- Stock badge indicators (green/yellow/red)

### Customers
- Full CRUD operations
- Search by name, phone, or email
- Purchase history per customer

### Billing / POS
- Visual product tile grid
- Click to add products to cart
- Adjust quantities inline
- Apply discounts
- Auto-calculated 5% tax
- Multiple payment methods (Cash, Card, UPI)
- Instant invoice generation

### Orders
- Full order history
- Date range filter
- Printable invoice for each order

### Reports
- **Sales Report**: Revenue trend (7/14/30 days)
- **Product Report**: Top 10 best-selling products table
- **Inventory Report**: Stock status + inventory value

---

## 🗄️ Database Schema

### Tables
| Table | Key Columns |
|-------|-------------|
| `users` | id, username, password_hash |
| `categories` | id, name |
| `products` | id, name, category_id, price, stock, barcode |
| `customers` | id, name, phone, email |
| `orders` | id, customer_id, total_amount, discount, tax, payment_method |
| `order_items` | id, order_id, product_id, quantity, price |

---

## 🔌 REST API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/logout` | Logout |
| GET | `/api/auth/status` | Check session |

### Products
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/products` | List products (search, filter) |
| GET | `/api/products/:id` | Get single product |
| POST | `/api/products` | Create product |
| PUT | `/api/products/:id` | Update product |
| DELETE | `/api/products/:id` | Delete product |

### Customers
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/customers` | List customers |
| GET | `/api/customers/:id` | Get customer |
| POST | `/api/customers` | Create customer |
| PUT | `/api/customers/:id` | Update customer |
| DELETE | `/api/customers/:id` | Delete customer |
| GET | `/api/customers/:id/orders` | Customer order history |

### Orders
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/orders` | List orders (date filter) |
| GET | `/api/orders/:id` | Get order with items |
| POST | `/api/orders` | Create order (checkout) |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analytics/dashboard` | Dashboard stats |
| GET | `/api/analytics/sales?days=7` | Sales by day |
| GET | `/api/analytics/top-products` | Top selling products |
| GET | `/api/analytics/category-sales` | Revenue by category |

---

## 🛡️ Security Notes
- Passwords are hashed with **PBKDF2-SHA256** via Werkzeug
- All routes (except login) require session authentication
- Input validation on all write endpoints
- SQLite parameterized queries (SQL injection protection)
- Foreign key constraints enforced

---

## 🔧 Configuration
Edit `backend/app.py` to change:
- `SECRET_KEY` — Flask session secret (use env variable in production)
- `DATABASE` — SQLite file path
- Tax rate (default: 5% — change in checkout logic)
- Port (default: 5000)
