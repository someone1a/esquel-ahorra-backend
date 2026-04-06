import os
import sys
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal, engine
from app.models import User, Store, Product, Price
from app.models.price import PriceConfirmation
from app.models.shopping_list import ShoppingList, ShoppingListItem
from app.services.auth_service import hash_password

STORES = [
    {"name": "Carrefour", "branch": "Palermo", "address": "Av. Córdoba 3247, Buenos Aires", "lat": -34.5897, "lng": -58.4165, "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5b/Carrefour_logo.svg/240px-Carrefour_logo.svg.png"},
    {"name": "Carrefour", "branch": "Caballito", "address": "Av. Rivadavia 5200, Buenos Aires", "lat": -34.6185, "lng": -58.4434, "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5b/Carrefour_logo.svg/240px-Carrefour_logo.svg.png"},
    {"name": "Día", "branch": "Villa Crespo", "address": "Thames 1540, Buenos Aires", "lat": -34.5990, "lng": -58.4422, "logo_url": None},
    {"name": "Coto", "branch": "Belgrano", "address": "Av. Cabildo 2500, Buenos Aires", "lat": -34.5621, "lng": -58.4547, "logo_url": None},
    {"name": "Walmart", "branch": "Liniers", "address": "Av. Rivadavia 11500, Buenos Aires", "lat": -34.6388, "lng": -58.5247, "logo_url": None},
    {"name": "La Anónima", "branch": "San Telmo", "address": "Av. San Juan 450, Buenos Aires", "lat": -34.6199, "lng": -58.3718, "logo_url": None},
    {"name": "Jumbo", "branch": "Unicenter", "address": "Paraná 3745, Martínez", "lat": -34.4957, "lng": -58.5133, "logo_url": None},
    {"name": "Disco", "branch": "Recoleta", "address": "Av. Santa Fe 3253, Buenos Aires", "lat": -34.5888, "lng": -58.3986, "logo_url": None},
    {"name": "Vea", "branch": "Flores", "address": "Av. Directorio 2800, Buenos Aires", "lat": -34.6319, "lng": -58.4633, "logo_url": None},
    {"name": "Changomas", "branch": "Haedo", "address": "Gaona 3500, Haedo", "lat": -34.6470, "lng": -58.5991, "logo_url": None},
]

PRODUCTS = [
    {"name": "Leche entera", "brand": "La Serenísima", "presentation": "1L", "category": "Lácteos", "barcode": "7790070010012"},
    {"name": "Leche descremada", "brand": "Sancor", "presentation": "1L", "category": "Lácteos", "barcode": "7790070010029"},
    {"name": "Yogur natural", "brand": "Ser", "presentation": "200g", "category": "Lácteos", "barcode": "7790070010036"},
    {"name": "Aceite de girasol", "brand": "Cocinero", "presentation": "900ml", "category": "Aceites y aderezos", "barcode": "7790070020011"},
    {"name": "Aceite de oliva extra virgen", "brand": "Nucete", "presentation": "500ml", "category": "Aceites y aderezos", "barcode": "7790070020028"},
    {"name": "Arroz largo fino", "brand": "Gallo", "presentation": "1kg", "category": "Secos y legumbres", "barcode": "7790070030014"},
    {"name": "Fideos spaghetti", "brand": "Knorr", "presentation": "500g", "category": "Pastas", "barcode": "7790070040011"},
    {"name": "Harina 000", "brand": "Cañuelas", "presentation": "1kg", "category": "Harinas", "barcode": "7790070050018"},
    {"name": "Azúcar común", "brand": "Ledesma", "presentation": "1kg", "category": "Azúcares", "barcode": "7790070060015"},
    {"name": "Sal fina", "brand": "Celusal", "presentation": "500g", "category": "Condimentos", "barcode": "7790070070012"},
    {"name": "Pan de molde blanco", "brand": "Bimbo", "presentation": "500g", "category": "Panadería", "barcode": "7790070080019"},
    {"name": "Manteca", "brand": "La Paulina", "presentation": "200g", "category": "Lácteos", "barcode": "7790070090016"},
    {"name": "Queso cremoso", "brand": "Molfino", "presentation": "300g", "category": "Lácteos", "barcode": "7790070100018"},
    {"name": "Tomate triturado", "brand": "Arcor", "presentation": "390g", "category": "Conservas", "barcode": "7790070110015"},
    {"name": "Atún en aceite", "brand": "La Campagnola", "presentation": "170g", "category": "Conservas", "barcode": "7790070120012"},
    {"name": "Jabón líquido", "brand": "Skip", "presentation": "1L", "category": "Limpieza", "barcode": "7790070130019"},
    {"name": "Detergente", "brand": "Magistral", "presentation": "750ml", "category": "Limpieza", "barcode": "7790070140016"},
    {"name": "Papel higiénico", "brand": "Elite", "presentation": "4 rollos", "category": "Higiene", "barcode": "7790070150013"},
    {"name": "Shampoo", "brand": "Dove", "presentation": "400ml", "category": "Higiene personal", "barcode": "7790070160010"},
    {"name": "Gaseosa cola", "brand": "Coca-Cola", "presentation": "1.5L", "category": "Bebidas", "barcode": "7790070170017"},
]


def seed():
    db = SessionLocal()
    try:
        if db.query(Store).count() > 0:
            print("Database already seeded. Skipping.")
            return

        print("Seeding stores...")
        stores = []
        for s in STORES:
            store = Store(**s)
            db.add(store)
            stores.append(store)
        db.flush()

        print("Seeding products...")
        products = []
        for p in PRODUCTS:
            product = Product(**p)
            db.add(product)
            products.append(product)
        db.flush()

        print("Creating demo users...")
        demo_user = User(
            email="demo@preciojusto.ar",
            password_hash=hash_password("demo1234"),
            role="collaborator",
            points=150,
            prices_loaded=10,
            confirmations=5,
        )
        db.add(demo_user)
        db.flush()

        print("Seeding sample prices...")
        import random

        base_prices = {
            "Leche entera": 950.0,
            "Leche descremada": 1050.0,
            "Yogur natural": 650.0,
            "Aceite de girasol": 2100.0,
            "Aceite de oliva extra virgen": 4500.0,
            "Arroz largo fino": 800.0,
            "Fideos spaghetti": 700.0,
            "Harina 000": 600.0,
            "Azúcar común": 850.0,
            "Sal fina": 400.0,
            "Pan de molde blanco": 1200.0,
            "Manteca": 1600.0,
            "Queso cremoso": 2400.0,
            "Tomate triturado": 750.0,
            "Atún en aceite": 1100.0,
            "Jabón líquido": 1800.0,
            "Detergente": 950.0,
            "Papel higiénico": 1400.0,
            "Shampoo": 2200.0,
            "Gaseosa cola": 1350.0,
        }

        for product in products:
            selected_stores = random.sample(stores, k=random.randint(3, 6))
            for store in selected_stores:
                base = base_prices.get(product.name, 1000.0)
                variance = random.uniform(-0.15, 0.20)
                final_price = round(base * (1 + variance), 2)
                price = Price(
                    product_id=product.id,
                    store_id=store.id,
                    price=final_price,
                    reported_by=demo_user.id,
                    status="confirmed",
                )
                db.add(price)

        db.commit()
        print("Seed completed successfully!")
        print(f"  - {len(stores)} stores")
        print(f"  - {len(products)} products")
        print(f"  - 1 demo user (demo@preciojusto.ar / demo1234)")
        print(f"  - Sample prices for all products across multiple stores")

    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
