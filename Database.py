from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# with engine.connect() as conn:
#     conn.execute(text("DROP TABLE IF EXISTS sales"))
#     print("✅ Tabla 'sales' eliminada correctamente")

    
# with engine.connect() as conn:
#     conn.execute(text("DROP TABLE IF EXISTS products"))
#     print("✅ Tabla 'sales' eliminada correctamente")



# create_table_sql = """
#  CREATE TABLE IF NOT EXISTS proveedores  (
# #     id INT AUTO_INCREMENT PRIMARY KEY,
#     nombre VARCHAR(100) NOT NULL,
#     razon_social VARCHAR(100),
#     nit_ruc VARCHAR(50),
#     direccion VARCHAR(150),
#     telefono VARCHAR(20),
#     correo VARCHAR(100),
#     contacto VARCHAR(100),
#     metodo_pago VARCHAR(50),
#     creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
# # );
# # """   

# with engine.connect() as conn:
#     conn.execute(text(create_table_sql))
#     print("✅ Tabla 'proveedores' creada correctamente.")

# with engine.connect() as conn:
#     # Añadir columna iva a la tabla products
#     alter_table_sql = "ALTER TABLE products ADD COLUMN precio_proveedor FLOAT NOT NULL DEFAULT 0.0;"
#     conn.execute(text(alter_table_sql))
#     print("✅ Columna 'precio_proveedor' añadida a la tabla 'products' correctamente.")

# with engine.connect() as conn:
#     alter_table_sql = "ALTER TABLE sales ADD COLUMN subtotal FLOAT NOT NULL DEFAULT 0.0;"
#     conn.execute(text(alter_table_sql))
#     print("✅ Columna 'precio_proveedor' añadida a la tabla 'products' correctamente.")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

        