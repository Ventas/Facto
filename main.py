from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from Routes import auth, inventario,sales, Proveedor
from modules import models
from Database import engine
from fastapi.responses import HTMLResponse , RedirectResponse
from sqlalchemy import text
from starlette.status import HTTP_302_FOUND
import hashlib

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Inventario & Facturación")

app.include_router(auth.router)
app.include_router(inventario.router)
app.include_router(sales.router)
templates = Jinja2Templates(directory="templates")
app.include_router(Proveedor.router)


# ✅ Función para cifrar contraseñas con SHA-256
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

# Ruta principal con menú
@app.get("/menu", response_class=HTMLResponse)
async def menu_principal(request: Request):
    return templates.TemplateResponse("menu.html", {"request": request})

# Mostrar el formulario de login
@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    with engine.connect() as conn:
        # Ejecutar la consulta para obtener al usuario
        result = conn.execute(
            text("SELECT * FROM StoreUser WHERE username = :username"),
            {"username": username}
        ).fetchone()

        # Agregar print para depurar
        print("Resultado de la consulta:", result)

        if result:
            print(f"Contraseña almacenada: {result[3]}")  # Muestra la contraseña almacenada
            if password == result[3]:  # Comparación directa sin cifrado
                # Login exitoso
                print("Login exitoso")
                return RedirectResponse(url="/menu", status_code=HTTP_302_FOUND)
            else:
                print("Contraseña incorrecta")
        else:
            print("Usuario no encontrado")

    # Si no hay coincidencia
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": "Usuario o contraseña incorrectos"
    })

@app.get("/crear-usuario", response_class=HTMLResponse)
async def crear_usuario_form(request: Request):
    return templates.TemplateResponse("crear_usuario.html", {"request": request})

@app.get("/usuarios", response_class=HTMLResponse)
async def mostrar_usuarios(request: Request):
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM StoreUser"))
        usuarios = [dict(row) for row in result]
    return templates.TemplateResponse("usuarios.html", {"request": request, "usuarios": usuarios, "usuario": None})

@app.post("/usuarios/guardar")
async def guardar_usuario(
    request: Request,
    id: str = Form(None),
    nombre: str = Form(...),
    username: str = Form(...),
    password: str = Form(None),
    rol: str = Form(...)
):
    try:
        with engine.connect() as conn:
            if id:  # Actualizar
                if password:
                    conn.execute(
                        text("""
                            UPDATE StoreUser
                            SET nombre=:nombre, username=:username, password=:password, rol=:rol
                            WHERE id=:id
                        """),
                        {"id": id, "nombre": nombre, "username": username, "password": password, "rol": rol}
                    )
                else:
                    conn.execute(
                        text("""
                            UPDATE StoreUser
                            SET nombre=:nombre, username=:username, rol=:rol
                            WHERE id=:id
                        """),
                        {"id": id, "nombre": nombre, "username": username, "rol": rol}
                    )
            else:  # Crear nuevo
                conn.execute(
                    text("""
                        INSERT INTO StoreUser (nombre, username, password, rol)
                        VALUES (:nombre, :username, :password, :rol)
                    """),
                    {"nombre": nombre, "username": username, "password": password, "rol": rol}
                )
            conn.commit()
        return RedirectResponse(url="/usuarios", status_code=HTTP_302_FOUND)
    except Exception as e:
        return templates.TemplateResponse("usuarios.html", {
            "request": request,
            "error": "Error al guardar usuario: " + str(e),
            "usuarios": [],
            "usuario": None
        })
    
    
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)