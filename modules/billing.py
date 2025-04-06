from modules.inventory import get_products

# Lista de ventas simuladas (almacenamiento en memoria)
sales = []

# Simulación de inventario (puedes mover esto a inventory.py si ya lo tienes allá)
inventory = [
    {"name": "Empanada de carne", "price": 3000, "stock": 100},
    {"name": "Gaseosa", "price": 2000, "stock": 50},
]

def get_sales():
    return sales

def add_sale(product_name: str, quantity: int, payment_method: str):
    product = next((p for p in inventory if p["name"] == product_name), None)
    if not product:
        return {"status": "error", "message": "Producto no encontrado"}

    if product["stock"] < quantity:
        return {"status": "error", "message": "Stock insuficiente"}

    total = round(product["price"] * quantity, 2)
    product["stock"] -= quantity

    sales.append({
        "product": product_name,
        "quantity": quantity,
        "total": total,
        "payment_method": payment_method
    })

    return {"status": "ok", "total": total}
