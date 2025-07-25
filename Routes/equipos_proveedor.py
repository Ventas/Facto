from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from Database import get_db
from fastapi.templating import Jinja2Templates
from modules import models 
from fastapi import HTTPException

templates = Jinja2Templates(directory="templates")

router = APIRouter()
 
@router.get("/equipos-proveedores", response_class=HTMLResponse)
def listar_equipos_proveedores(request: Request, db: Session = Depends(get_db)):
    equipos = db.query(models.EquipoProveedor).all()
    return templates.TemplateResponse("equipos_proveedores.html", {
        "request": request,
        "equipos": equipos
    })
# Ruta para crear nuevo equipo/proveedor
@router.post("/equipos-proveedores")
def crear_equipo_proveedor(
    nombre_empresa: str = Form(...),
    direccion: str = Form(""),
    telefono: str = Form(""),
    numero_contacto: str = Form(""),
    nombre_contacto: str = Form(""),
    equipos: str = Form(""),
    precios: str = Form(""),
    db: Session = Depends(get_db)
):
    nuevo_equipo = models.EquipoProveedor(
        nombre_empresa=nombre_empresa,
        direccion=direccion,
        telefono=telefono,
        numero_contacto=numero_contacto,
        nombre_contacto=nombre_contacto,
        equipos=equipos,
        precios=precios
    )
    db.add(nuevo_equipo)
    db.commit()
    return RedirectResponse(url="/equipos-proveedores", status_code=303)


@router.post("/equipos-proveedores/editar/{id}")
def editar_equipo(
    id: int,
    nombre_empresa: str = Form(...),
    direccion: str = Form(...),
    telefono: str = Form(...),
    numero_contacto: str = Form(...),
    nombre_contacto: str = Form(...),
    equipos: str = Form(...),
    precios: str = Form(...),
    db: Session = Depends(get_db)
):
    equipo = db.query(models.EquipoProveedor).filter(models.EquipoProveedor.id == id).first()

    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo/Proveedor no encontrado")

    equipo.nombre_empresa = nombre_empresa
    equipo.direccion = direccion
    equipo.telefono = telefono
    equipo.numero_contacto = numero_contacto
    equipo.nombre_contacto = nombre_contacto
    equipo.equipos = equipos
    equipo.precios = precios

    db.commit()
    return RedirectResponse(url="/equipos-proveedores", status_code=303)

# Ruta para eliminar equipo/proveedor
@router.post("/equipos-proveedores/eliminar/{id}")
def eliminar_equipo(id: int, db: Session = Depends(get_db)):
    equipo = db.query(models.EquipoProveedor).filter(models.EquipoProveedor.id == id).first()

    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo/Proveedor no encontrado")

    db.delete(equipo)
    db.commit()
    return RedirectResponse(url="/equipos-proveedores", status_code=303)
