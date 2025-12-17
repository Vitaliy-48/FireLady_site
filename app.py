from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response
from datetime import datetime
from configsite import MY_BOT_TOKEN, MY_CHAT_ID, MY_SECRET_KEY
import requests
import os
import json
import csv

app = Flask(__name__, static_folder="static")
app.secret_key = MY_SECRET_KEY  # Для збереження даних у сесії


colors = {
    1: {"hex": "#FFFFFF", "name": "Білий"},
    2: {"hex": "#228B22", "name": "Смарагдовий"},
    3: {"hex": "#9370DB", "name": "Лавандовий"},
    4: {"hex": "#FFDAB9", "name": "Персиковий"},
    5: {"hex": "#4169E1", "name": "Сапфіровий"},
    6: {"hex": "#DAA520", "name": "Золотистий"},
    7: {"hex": "#708090", "name": "Темно-сірий"},
    8: {"hex": "#FF4500", "name": "Червоний"},
    9: {"hex": "#008080", "name": "Бірюзовий"}
}


products = []

with open("products.csv", mode="r", encoding="utf-8-sig") as file:
    reader = csv.reader(file, delimiter=",")
    next(reader)
    for row in reader:
        products.append({
            "id": row[0],
            "name": row[1],
            "image": row[2],
            "price": row[3] if len(row) > 3 else ""
        })

@app.route("/")
def home():
    compositions_folder = os.path.join(app.static_folder, "compositions")
    compositions = [
        f for f in os.listdir(compositions_folder)
        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))
    ]
    return render_template("index.html", compositions=compositions)


@app.route("/catalog")
def catalog():
    default_color = next(iter(colors))  # Перший ключ із словника
    return render_template("catalog.html", products=products, colors=colors, default_color=default_color)


@app.route("/add-to-cart", methods=["POST"])
def add_to_cart():
    data = request.json
    product = next((p for p in products if p["id"] == data["id"]), None)
    if not product:
        return json.dumps({"error": "Товар не знайдено"}), 400

    color_id = data.get("color_id")
    if color_id is None:
        return json.dumps({"error": "Колір не вибрано"}), 400  # Запобігаємо помилці

    color_name = colors.get(int(color_id), {}).get("name", "Невідомий колір")
    color_hex = data.get("color_hex")

    cart_item = {
        "id": product["id"],
        "name": product["name"],
        "price": product["price"],
        "image": product["image"],
        "color_id": color_id,
        "color_name": color_name,
        "color_hex": color_hex,
        "quantity": int(data["quantity"]),
        "selected": data.get("selected", False)
}
    if "cart" not in session:
        session["cart"] = []
    session["cart"].append(cart_item)
    session.modified = True
    return json.dumps(session["cart"])

@app.route("/checkout")
def checkout():
    cart = session.get("cart", [])
    total = sum(int(item["price"]) * int(item.get("quantity", 1)) for item in cart)
    selected_items = [item for item in cart if item.get("selected", False)]
    return render_template("checkout.html", cart=cart, selected_items=selected_items, total=total)

@app.route("/remove-item", methods=["POST"])
def remove_item():
    product_id = request.form.get("id")
    color_id = request.form.get("color_id")

    if "cart" in session:
        session["cart"] = [
            item for item in session["cart"]
            if not (item["id"] == product_id and str(item["color_id"]) == str(color_id))
        ]
        session.modified = True

    return redirect(url_for("checkout"))


@app.route("/reviews", methods=["GET", "POST"])
def reviews():
    reviews_file = "reviews.json"

    if request.method == "POST":
        review = request.form["review"]
        with open(reviews_file, "a") as file:
            json.dump({"review": review}, file)
            file.write("\n")

    # Перевіряємо, чи файл існує, перед відкриттям
    if os.path.exists(reviews_file):
        with open(reviews_file, "r") as file:
            all_reviews = [json.loads(line) for line in file if line.strip()]  # Ігноруємо порожні рядки
    else:
        all_reviews = []

    return render_template("reviews.html", reviews=all_reviews)


@app.route("/order", methods=["POST"])
def order():
    data = request.form  # Отримуємо дані з форми
    name = data.get("name")
    phone = data.get("phone")
    cart = session.get("cart", [])
    now = datetime.now()
    order_id = now.strftime("%m%d%H%M")  # Унікальний код за поточним часом
    session["order_id"] = order_id

    # Формуємо повідомлення для Telegram
    message = f"🛒 НОВЕ ЗАМОВЛЕННЯ! #{order_id}\n👤 Ім'я: {name}\n📞 Телефон: {phone}\n\nТовари:\n"
    for item in cart:
        message += f"🕯️ {item['name']} - {item['color_id']}–{item['color_name']}  (x{item['quantity']} шт.)\n"

    # Надсилаємо повідомлення в Telegram
    url = f"https://api.telegram.org/bot{MY_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": MY_CHAT_ID, "text": message}
    response = requests.post(url, json=payload)

    if response.status_code == 200:
        session.pop("cart", None)
        session.pop("order_id", None)
        session.modified = True
        session["last_order"] = {
            "order_id": order_id,
            "items": cart
        }

        return redirect(url_for("thank_you"))

    else:
        return jsonify(message="Помилка надсилання!"), 500

@app.route("/thank-you")
def thank_you():
    last_order = session.pop("last_order", None)
    return render_template("thank_you.html", last_order=last_order)

@app.route('/get-new-number/<int:product_id>/<int:color_id>')
def get_new_number(product_id, color_id):
    new_number = product_id + color_id  # Логіка зміни номера
    return jsonify({"new_number": new_number})


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)