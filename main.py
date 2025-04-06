from fastapi import FastAPI, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from modules.inventory import get_products, add_new_product

from modules.billing import get_sales, add_sale
from modules.reports import export_sales_excel, export_sales_pdf
from fastapi import Form


app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "products": get_products(),
        "page": "dashboard"
    })

@app.get("/sales", response_class=HTMLResponse)
def sales_page(request: Request):
    return templates.TemplateResponse("sales.html", {
        "request": request,
        "products": get_products(),
        "sales": get_sales(),
        "page": "sales"
    })

@app.post("/process-sale")
def process_sale(
    request: Request,
    product: str = Form(...),
    quantity: int = Form(...),
    payment_method: str = Form(...)
):
    result = add_sale(product, quantity, payment_method)
    return templates.TemplateResponse("sales.html", {
        "request": request,
        "products": get_products(),
        "sales": get_sales(),
        "result": result,
        "page": "sales"
    })

@app.get("/reports", response_class=HTMLResponse)
def reports_page(request: Request):
    return templates.TemplateResponse("reports.html", {"request": request, "page": "reports"})

@app.post("/add-product")
def add_product(request: Request, name: str = Form(...), price: float = Form(...), stock: int = Form(...)):
    add_new_product(name, price, stock)
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)



@app.get("/export-sales-excel")
def export_excel():
    return export_sales_excel()

@app.get("/export-sales-pdf")
def export_pdf():
    return export_sales_pdf()


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)