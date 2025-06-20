from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from Database import get_db
from modules import models
from fastapi.responses import RedirectResponse
from datetime import date
from sqlalchemy import func
from typing import List
import os
from openpyxl import Workbook
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime
from fastapi.responses import HTMLResponse
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import tempfile

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

    # Devuelve solo los datos iniciales sin result (que es para POST)
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

    # Inicializa total_general al principio
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
        total_general += total  # Ahora total_general está definida
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

    # Obtener el ID de la última venta
    last_sale_id = sales_to_save[-1].id if sales_to_save else None

    # Actualizar resumen después de commit
    ventas_hoy = db.query(models.Sale).filter(func.date(models.Sale.timestamp) == hoy).all()
    resumen = {
        "total_vendido": sum(v.total for v in ventas_hoy),
        "productos_vendidos": sum(v.quantity for v in ventas_hoy),
        "numero_ventas": len(ventas_hoy)
    }

    return templates.TemplateResponse("sales.html", {
        "request": request,
        "result": {
            "status": "ok", 
            "total": total_general,  # Usando total_general que ahora está definida
            "change": change,
            "sale_id": last_sale_id  # Asegurando que sale_id está incluido
        },
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

@router.post("/get-product-by-barcode")
def get_product_by_barcode(barcode: str = Form(...), db: Session = Depends(get_db)):
    producto = db.query(models.Product).filter(models.Product.codigo_barras == barcode).first()
    
    if producto:
        return {
            "status": "ok",
            "product": {
                "nombre": producto.nombre,
                "precio": producto.precio,
                "stock": producto.stock
            }
        }
    return {"status": "error", "message": "Producto no encontrado"}

@router.get("/export-sales-excel")
def export_sales_excel(db: Session = Depends(get_db)):
    hoy = date.today()
    ventas = db.query(models.Sale).filter(func.date(models.Sale.timestamp) == hoy).all()

    total_vendido = sum(v.total for v in ventas)
    productos_vendidos = sum(v.quantity for v in ventas)
    numero_ventas = len(ventas)

    file_path = "ventas_dia.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "Ventas del Día"

    # Cabeceras
    ws.append(["ID", "Producto", "Cantidad", "Total", "Método de Pago", "Fecha"])

    for venta in ventas:
        producto = db.query(models.Product).filter(models.Product.id == venta.product_id).first()
        ws.append([
            venta.id,
            producto.nombre if producto else "Desconocido",
            venta.quantity,
            venta.total,
            venta.payment_method,
            venta.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        ])

    # Espacio + resumen al final
    ws.append([])
    ws.append(["Resumen del Día"])
    ws.append(["Total Vendido", total_vendido])
    ws.append(["Productos Vendidos", productos_vendidos])
    ws.append(["Número de Ventas", numero_ventas])

    wb.save(file_path)

    return FileResponse(path=file_path, filename="ventas_dia.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@router.get("/export-sales-by-date")
async def export_sales_by_date(selected_date: str, db: Session = Depends(get_db)):
    date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
    filepath = generar_excel_para_fecha(date_obj, db)
    return FileResponse(
        path=filepath,
        filename=f"ventas_{selected_date}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
@router.get("/export-sales-by-date")
async def export_sales_by_date(selected_date: str):
    # Convertir la fecha
    date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()

    # Aquí deberías generar el archivo (Excel o PDF) según la fecha
    filepath = generar_excel_para_fecha(date_obj)  # <-- tu función personalizada

    return FileResponse(path=filepath, filename=f"ventas_{selected_date}.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

def generar_excel_para_fecha(fecha: date, db: Session) -> str:
    ventas = db.query(models.Sale).filter(func.date(models.Sale.timestamp) == fecha).all()

    total_vendido = sum(v.total for v in ventas)
    productos_vendidos = sum(v.quantity for v in ventas)
    numero_ventas = len(ventas)

    wb = Workbook()
    ws = wb.active
    ws.title = f"Ventas {fecha}"

    # Cabeceras
    ws.append(["ID", "Producto", "Cantidad", "Total", "Método de Pago", "Fecha"])

    for venta in ventas:
        producto = db.query(models.Product).filter(models.Product.id == venta.product_id).first()
        ws.append([
            venta.id,
            producto.nombre if producto else "Desconocido",
            venta.quantity,
            venta.total,
            venta.payment_method,
            venta.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        ])

    # Espacio + resumen
    ws.append([])
    ws.append(["Resumen del Día"])
    ws.append(["Total Vendido", total_vendido])
    ws.append(["Productos Vendidos", productos_vendidos])
    ws.append(["Número de Ventas", numero_ventas])

    filename = f"ventas_{fecha}.xlsx"
    filepath = os.path.join(".", filename)
    wb.save(filepath)

    return filepath
@router.get("/ticket/{sale_id}")
async def generate_ticket(sale_id: int, db: Session = Depends(get_db)):
    # Obtener los datos de la venta
    venta = db.query(models.Sale).filter(models.Sale.id == sale_id).first()
    if not venta:
        return {"error": "Venta no encontrada"}
    
    producto = db.query(models.Product).filter(models.Product.id == venta.product_id).first()
    
    # Crear un PDF temporal
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    doc = SimpleDocTemplate(temp_pdf.name, pagesize=(2.8*inch, 100*inch), 
                          rightMargin=10, leftMargin=10, topMargin=10, bottomMargin=10)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Center", alignment=1))
    styles.add(ParagraphStyle(name="Small", fontSize=8, leading=10))
    
    elements = []
    
    # Encabezado del ticket
    elements.append(Paragraph("MI TIENDA", styles["Center"]))
    elements.append(Paragraph("Dirección: Calle Principal 123", styles["Small"]))
    elements.append(Paragraph("Tel: 555-1234", styles["Small"]))
    elements.append(Paragraph("RFC: XXXX000000XX", styles["Small"]))
    elements.append(Spacer(1, 10))
    
    # Detalles de la venta
    elements.append(Paragraph(f"Fecha: {venta.timestamp.strftime('%d/%m/%Y %H:%M')}", styles["Small"]))
    elements.append(Paragraph(f"Ticket: {venta.id}", styles["Small"]))
    elements.append(Spacer(1, 10))
    
    # Tabla de productos
    data = [
        ["Producto", "Cant", "Precio", "Total"],
        [producto.nombre, venta.quantity, f"${producto.precio:.2f}", f"${venta.total:.2f}"]
    ]
    
    t = Table(data, colWidths=[1.5*inch, 0.5*inch, 0.5*inch, 0.5*inch])
    t.setStyle(TableStyle([
        ('FONT', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
        ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
        ('BOX', (0,0), (-1,-1), 0.25, colors.black),
    ]))
    
    elements.append(t)
    elements.append(Spacer(1, 10))
    
    # Totales
    elements.append(Paragraph(f"Subtotal: ${venta.total:.2f}", styles["Small"]))
    elements.append(Paragraph(f"Total: ${venta.total:.2f}", styles["Small"]))
    elements.append(Spacer(1, 10))
    
    # Método de pago
    elements.append(Paragraph(f"Pago: {venta.payment_method.upper()}", styles["Small"]))
    elements.append(Spacer(1, 20))
    
    # Pie de página
    elements.append(Paragraph("¡Gracias por su compra!", styles["Center"]))
    elements.append(Paragraph("Sistema de Ventas Wellmade v1.0", styles["Small"]))
    
    doc.build(elements)
    temp_pdf.close()
    
    return FileResponse(temp_pdf.name, filename=f"ticket_{sale_id}.pdf")

@router.get("/thermal-ticket/{sale_id}", response_class=HTMLResponse)
async def thermal_ticket(sale_id: int, db: Session = Depends(get_db)):
    # Obtener los datos de la venta
    venta = db.query(models.Sale).filter(models.Sale.id == sale_id).first()
    if not venta:
        return "<h1>Venta no encontrada</h1>"
    
    producto = db.query(models.Product).filter(models.Product.id == venta.product_id).first()
    
    # Generar HTML simple para impresión térmica
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ticket de Venta</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                font-size: 12px;
                width: 80mm;
                margin: 0;
                padding: 5px;
            }}
            .header {{
                text-align: center;
                font-weight: bold;
                margin-bottom: 10px;
            }}
            .info {{
                margin-bottom: 5px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 10px 0;
            }}
            th {{
                text-align: left;
                border-bottom: 1px dashed #000;
                padding: 2px 0;
            }}
            td {{
                padding: 2px 0;
            }}
            .right {{
                text-align: right;
            }}
            .total {{
                font-weight: bold;
                margin-top: 10px;
            }}
            .footer {{
                text-align: center;
                margin-top: 20px;
                font-size: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="header">MI TIENDA</div>
        <div class="info">Dirección: Calle Principal 123</div>
        <div class="info">Tel: 555-1234 | RFC: XXXX000000XX</div>
        <div class="info">Fecha: {venta.timestamp.strftime('%d/%m/%Y %H:%M')}</div>
        <div class="info">Ticket: {venta.id}</div>
        
        <table>
            <thead>
                <tr>
                    <th>Producto</th>
                    <th class="right">Cant</th>
                    <th class="right">Precio</th>
                    <th class="right">Total</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>{producto.nombre}</td>
                    <td class="right">{venta.quantity}</td>
                    <td class="right">${producto.precio:.2f}</td>
                    <td class="right">${venta.total:.2f}</td>
                </tr>
            </tbody>
        </table>
        
        <div class="total">Total: ${venta.total:.2f}</div>
        <div class="info">Método de pago: {venta.payment_method.upper()}</div>
        
        <div class="footer">
            ¡Gracias por su compra!<br>
            Sistema de Ventas Wellmade 
        </div>
        
        <script>
            // Imprimir automáticamente al cargar
            window.onload = function() {{
                setTimeout(function() {{
                    window.print();
                    setTimeout(function() {{
                        window.close();
                    }}, 100);
                }}, 100);
            }};
        </script>
    </body>
    </html>
    """
    
    return html_content
