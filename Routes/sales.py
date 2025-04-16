from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from Database import get_db
from modules import models
from fastapi.responses import RedirectResponse
from datetime import date
from sqlalchemy import func
from typing import List

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/sales")
def sales_page(request: Request, db: Session = Depends(get_db)):
    productos = db.query(models.Product).all()
    ventas = db.query(models.Sale).all()

    hoy = date.today()
    ventas_hoy = db.query(models.Sale).filter(func.date(models.Sale.timestamp) == hoy).all()

    resumen = {
        "total_vendido": sum(v.total for v in ventas_hoy),
        "productos_vendidos": sum(v.quantity for v in ventas_hoy),
        "numero_ventas": len(ventas_hoy)
    }

    return templates.TemplateResponse("sales.html", {
        "request": request,
        "productos": productos,
        "ventas": ventas,
        "resumen": resumen
    })


@router.post("/process-sale")
def process_sale(
    request: Request,
    product: List[str] = Form(...),
    quantity: List[int] = Form(...),
    payment_method: str = Form(...),
    money_received: float = Form(...),
    db: Session = Depends(get_db)
):
    hoy = date.today()
    ventas = db.query(models.Sale).all()
    ventas_hoy = db.query(models.Sale).filter(func.date(models.Sale.timestamp) == hoy).all()

    resumen = {
        "total_vendido": sum(v.total for v in ventas_hoy),
        "productos_vendidos": sum(v.quantity for v in ventas_hoy),
        "numero_ventas": len(ventas_hoy)
    }

    total_general = 0
    sales_to_save = []

    for p, q in zip(product, quantity):
        selected_product = db.query(models.Product).filter(models.Product.nombre == p).first()

        if not selected_product or selected_product.stock < q:
            return templates.TemplateResponse("sales.html", {
                "request": request,
                "result": {"status": "error", "message": f"Producto '{p}' no disponible o sin stock suficiente"},
                "productos": db.query(models.Product).all(),
                "ventas": ventas,
                "resumen": resumen
            })

        total = selected_product.precio * q
        total_general += total
        selected_product.stock -= q

        sales_to_save.append(models.Sale(
            product_id=selected_product.id,
            quantity=q,
            total=total,
            payment_method=payment_method
        ))

    change = money_received - total_general

    if change < 0:
        return templates.TemplateResponse("sales.html", {
            "request": request,
            "result": {"status": "error", "message": "El dinero recibido no es suficiente"},
            "productos": db.query(models.Product).all(),
            "ventas": ventas,
            "resumen": resumen
        })

    for s in sales_to_save:
        db.add(s)

    db.commit()

    ventas = db.query(models.Sale).all()
    ventas_hoy = db.query(models.Sale).filter(func.date(models.Sale.timestamp) == hoy).all()
    resumen = {
        "total_vendido": sum(v.total for v in ventas_hoy),
        "productos_vendidos": sum(v.quantity for v in ventas_hoy),
        "numero_ventas": len(ventas_hoy)
    }

    return templates.TemplateResponse("sales.html", {
        "request": request,
        "result": {"status": "ok", "total": total_general, "change": change},
        "productos": db.query(models.Product).all(),
        "ventas": ventas,
        "resumen": resumen
    })

@router.post("/delete-sale")
def delete_sale(sale_id: int = Form(...), db: Session = Depends(get_db)):
    venta = db.query(models.Sale).filter(models.Sale.id == sale_id).first()

    if not venta:
        return {"error": "Venta no encontrada"}

    producto = db.query(models.Product).filter(models.Product.id == venta.product_id).first()
    if producto:
        producto.stock += venta.quantity
        db.commit()

    db.delete(venta)
    db.commit()

    return RedirectResponse(url="/sales", status_code=303)