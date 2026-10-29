from flask import Flask, request, render_template_string, redirect, url_for
import requests
import json
import os

app = Flask(__name__)
DATA_FILE = 'store_data.json'

# Default Data Structure
def load_data():
    if not os.path.exists(DATA_FILE):
        default_data = {
            "config": {
                "wa_token": "",
                "phone_id": "",
                "verify_token": "my_secret_token_123",
                "payment_info": "1. Cash on Delivery (COD)\n2. EasyPaisa/JazzCash: 0300-1234567 (Account Title: Ali)"
            },
            "products": [
                {"id": 1, "name": "Wireless Earbuds", "price": 2500, "stock": 10},
                {"id": 2, "name": "Smart Watch", "price": 4500, "stock": 5}
            ],
            "orders": [],
            "sessions": {}
        }
        save_data(default_data)
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# HTML Admin Dashboard (No-Code Interface)
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>WhatsApp Store Admin Panel</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>body { background-color: #f4f7f6; } .card { margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }</style>
</head>
<body class="p-4">
<div class="container">
    <h2 class="mb-4 text-success fw-bold">🟢 WhatsApp E-Commerce Bot Dashboard</h2>
    
    <div class="row">
        <!-- Settings & API Key -->
        <div class="col-md-6">
            <div class="card p-3">
                <h4>⚙️ 1. WhatsApp API & Payment Setup</h4>
                <form method="POST" action="/save_config">
                    <div class="mb-2">
                        <label class="fw-bold">WhatsApp Access Token (API Key):</label>
                        <input type="text" name="wa_token" class="form-control" value="{{ data.config.wa_token }}" placeholder="EAAGm0..." required>
                    </div>
                    <div class="mb-2">
                        <label class="fw-bold">Phone Number ID:</label>
                        <input type="text" name="phone_id" class="form-control" value="{{ data.config.phone_id }}" placeholder="1023456789..." required>
                    </div>
                    <div class="mb-2">
                        <label class="fw-bold">Webhook Verify Token (Meta mein yehi dalein):</label>
                        <input type="text" name="verify_token" class="form-control" value="{{ data.config.verify_token }}" readonly>
                    </div>
                    <div class="mb-3">
                        <label class="fw-bold">Payment Gateway / Method Details:</label>
                        <textarea name="payment_info" class="form-control" rows="3" required>{{ data.config.payment_info }}</textarea>
                        <small class="text-muted">Yeh details customer ko checkout ke waqt nazar aayengi.</small>
                    </div>
                    <button type="submit" class="btn btn-success w-100">Save Settings</button>
                </form>
            </div>
        </div>

        <!-- Add Products -->
        <div class="col-md-6">
            <div class="card p-3">
                <h4>📦 2. Add New Product & Stock</h4>
                <form method="POST" action="/add_product">
                    <div class="mb-2">
                        <label class="fw-bold">Product Name:</label>
                        <input type="text" name="name" class="form-control" placeholder="e.g. Nike Shoes" required>
                    </div>
                    <div class="mb-2">
                        <label class="fw-bold">Price (Rs):</label>
                        <input type="number" name="price" class="form-control" placeholder="e.g. 3000" required>
                    </div>
                    <div class="mb-3">
                        <label class="fw-bold">Available Stock (Quantity):</label>
                        <input type="number" name="stock" class="form-control" placeholder="e.g. 20" required>
                    </div>
                    <button type="submit" class="btn btn-primary w-100">➕ Add Product to WhatsApp</button>
                </form>
            </div>

            <!-- Product List -->
            <div class="card p-3">
                <h5>📋 Current Inventory (Stock)</h5>
                <table class="table table-bordered table-sm mt-2">
                    <thead class="table-light"><tr><th>ID</th><th>Product</th><th>Price</th><th>Stock</th><th>Action</th></tr></thead>
                    <tbody>
                        {% for p in data.products %}
                        <tr>
                            <td>{{ p.id }}</td>
                            <td>{{ p.name }}</td>
                            <td>Rs. {{ p.price }}</td>
                            <td>
                                {% if p.stock > 0 %}<span class="badge bg-success">{{ p.stock }} In Stock</span>
                                {% else %}<span class="badge bg-danger">Out of Stock</span>{% endif %}
                            </td>
                            <td><a href="/delete_product/{{ p.id }}" class="btn btn-danger btn-sm">Delete</a></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- Orders List -->
    <div class="card p-3 mt-2">
        <h4>🛒 3. Received WhatsApp Orders</h4>
        <table class="table table-striped mt-2">
            <thead class="table-dark"><tr><th>Customer Phone</th><th>Product</th><th>Price</th><th>Address & Payment</th></tr></thead>
            <tbody>
                {% for o in data.orders %}
                <tr>
                    <td>{{ o.phone }}</td>
                    <td>{{ o.product }}</td>
                    <td>Rs. {{ o.price }}</td>
                    <td>{{ o.details }}</td>
                </tr>
                {% else %}
                <tr><td colspan="4" class="text-center">Abhi tak koi order nahi aaya.</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
</body>
</html>
"""

# Dashboard Routes
@app.route('/')
def dashboard():
    data = load_data()
    return render_template_string(DASHBOARD_HTML, data=data)

@app.route('/save_config', methods=['POST'])
def save_config():
    data = load_data()
    data['config']['wa_token'] = request.form['wa_token'].strip()
    data['config']['phone_id'] = request.form['phone_id'].strip()
    data['config']['payment_info'] = request.form['payment_info'].strip()
    save_data(data)
    return redirect(url_for('dashboard'))

@app.route('/add_product', methods=['POST'])
def add_product():
    data = load_data()
    new_id = len(data['products']) + 1 if data['products'] else 1
    data['products'].append({
        "id": new_id,
        "name": request.form['name'],
        "price": int(request.form['price']),
        "stock": int(request.form['stock'])
    })
    save_data(data)
    return redirect(url_for('dashboard'))

@app.route('/delete_product/<int:pid>')
def delete_product(pid):
    data = load_data()
    data['products'] = [p for p in data['products'] if p['id'] != pid]
    save_data(data)
    return redirect(url_for('dashboard'))

# Function to Send WhatsApp Message via Official Cloud API
def send_wa_msg(to_phone, text_msg):
    data = load_data()
    token = data['config']['wa_token']
    phone_id = data['config']['phone_id']
    if not token or not phone_id:
        return
    url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"body": text_msg}
    }
    requests.post(url, headers=headers, json=payload)

# WhatsApp Webhook (Bot Brain)
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    data = load_data()
    
    # Meta Verification
    if request.method == 'GET':
        if request.args.get("hub.verify_token") == data['config']['verify_token']:
            return request.args.get("hub.challenge"), 200
        return "Verification Failed", 403

    # Handle Incoming Messages
    if request.method == 'POST':
        body = request.json
        try:
            msg_info = body['entry'][0]['changes'][0]['value']['messages'][0]
            sender = msg_info['from']
            text = msg_info['text']['body'].strip()
        except (KeyError, IndexError):
            return "OK", 200

        sessions = data['sessions']
        user_state = sessions.get(sender, {"step": "MENU"})

        # Reset or Show Catalog
        if text.lower() in ['hi', 'hello', 'menu', 'shop', 'salam', '0']:
            msg = "🛍️ *Welcome to Our WhatsApp Store!* 🛍️\n\nHamare available products:\n\n"
            for p in data['products']:
                if p['stock'] > 0:
                    msg += f"*{p['id']}*. {p['name']} - Rs.{p['price']} _(Stock: {p['stock']})_\n"
                else:
                    msg += f"~*{p['id']}*. {p['name']} (Out of Stock)~\n"
            msg += "\n👉 *Khareedne ke liye Product ka Number likh kar bhejein (maslan: 1)*"
            sessions[sender] = {"step": "SELECT_PRODUCT"}
            send_wa_msg(sender, msg)

        # Product Selection Step
        elif user_state['step'] == "SELECT_PRODUCT":
            if text.isdigit():
                pid = int(text)
                prod = next((p for p in data['products'] if p['id'] == pid), None)
                if prod and prod['stock'] > 0:
                    sessions[sender] = {"step": "CHECKOUT", "product": prod}
                    msg = f"✅ Aapne select kiya hai: *{prod['name']}* (Rs. {prod['price']})\n\n"
                    msg += f"💳 *Payment Methods:*\n{data['config']['payment_info']}\n\n"
                    msg += "📦 *Order Confirm karne ke liye apna Naam, Mukammal Address aur Payment Method likh kar bhejein.*\n_(Cancel karne ke liye 0 likhein)_"
                    send_wa_msg(sender, msg)
                else:
                    send_wa_msg(sender, "❌ Yeh product mojood nahi ya Out of Stock hai. Dobara sahi number likhein ya 'Menu' likhein.")
            else:
                send_wa_msg(sender, "👉 Meharbani farma kar sirf Product ka Number likhein (maslan: 1, 2) ya 'Hi' likhein.")

        # Checkout & Stock Deduction Step
        elif user_state['step'] == "CHECKOUT":
            prod = user_state['product']
            # Deduct Stock
            for p in data['products']:
                if p['id'] == prod['id']:
                    p['stock'] = max(0, p['stock'] - 1)
            
            # Save Order
            data['orders'].append({
                "phone": sender,
                "product": prod['name'],
                "price": prod['price'],
                "details": text
            })
            sessions[sender] = {"step": "MENU"}
            
            confirm_msg = f"🎉 *Order Confirmed!*\n\n📦 *Product:* {prod['name']}\n💰 *Total:* Rs. {prod['price']}\n📍 *Details:* {text}\n\nShukriya! Hamari team jald aap se rabta karegi. Naya order karne ke liye *Hi* likhein."
            send_wa_msg(sender, confirm_msg)

        data['sessions'] = sessions
        save_data(data)
        return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
