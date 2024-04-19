from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet

import pymongo
from bson import ObjectId

app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todas las solicitudes
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Conexión a la base de datos MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")  # Cambia la URL según tu configuración
db = client["pdf-prueba"]
collection = db["reportes"]

class IncidentReport(BaseModel):
    title: str
    description: str
    date: str
    time: str
    name: str
    checador: str  # Agregado campo para el checador

@app.post("/crear_pdf/")
async def crear_pdf(incident_report: IncidentReport):
    try:
        # Crear el PDF
        buffer = BytesIO()

        # Personalizar el diseño del PDF
        pdf = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        title_style = styles["Title"]
        normal_style = styles["Normal"]

        # Contenido del PDF
        content = []
        
        # Agregar imagen al encabezado
        img_path = "./statics/image.jpg"  # Reemplaza con la ruta de tu imagen
        image = Image(img_path, width=200, height=100)  # Modifica el ancho y alto según tus necesidades
        content.append(image)
        content.append(Spacer(1, 20))

        content.append(Paragraph("Reporte de Incidente", title_style))
        content.append(Spacer(1, 20))
        content.append(Paragraph(f"Nombre del conductor: {incident_report.name}", normal_style))
        content.append(Paragraph(f"Número de la unidad: {incident_report.title}", normal_style))
        content.append(Paragraph(f"Fecha del incidente: {incident_report.date}", normal_style))
        content.append(Paragraph(f"Hora del incidente: {incident_report.time}", normal_style))
        content.append(Paragraph(f"Descripción del incidente: {incident_report.description}", normal_style))

        pdf.build(content)

        # Obtener los datos del PDF
        pdf_data = buffer.getvalue()

        # Guardar el PDF en la base de datos
        pdf_id = str(collection.insert_one({"pdf_data": pdf_data, "checador": incident_report.checador}).inserted_id)
        
        # Devolver el ID del PDF generado
        return {"pdf_id": pdf_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear el PDF: {str(e)}")

@app.get("/mostrar_pdf/{pdf_id}")
async def mostrar_pdf(pdf_id: str):
    try:
        # Obtener el PDF de la base de datos
        pdf_data = collection.find_one({"_id": ObjectId(pdf_id)})["pdf_data"]
        
        # Devolver el PDF como respuesta
        return Response(content=pdf_data, media_type="application/pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al mostrar el PDF: {str(e)}")
