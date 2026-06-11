import io
import os
import sqlite3
import pandas as pd
from datetime import datetime
from fpdf import FPDF
from typing import List, Dict

import src.delivery.database as gold_db

# Gold DB Path for download
GOLD_DB_FILE = os.path.join("data", "3_gold_delivery.db")

def generate_excel_report(degree_type: str = "", academic_area: str = "", search_query: str = "") -> io.BytesIO:
    """
    Generates an Excel spreadsheet containing the filtered list of careers and returns it as a bytes buffer.
    """
    careers = gold_db.get_careers(degree_type, academic_area, search_query)
    
    # Create a DataFrame
    df = pd.DataFrame(careers)
    if df.empty:
        df = pd.DataFrame(columns=["id", "url", "title", "degree_type", "academic_area", "description", "extracted_at"])
    else:
        # Drop internal id, reorder columns for presentation
        df = df[["title", "degree_type", "academic_area", "url", "description", "extracted_at"]]
        df.columns = ["Carrera", "Tipo de Grado", "Área Académica", "Enlace URL", "Descripción", "Fecha de Extracción"]
        
    output = io.BytesIO()
    # Write to Excel using openpyxl engine
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Oferta Académica")
        
    output.seek(0)
    return output

class AcademicReportPDF(FPDF):
    def header(self):
        # Header banner
        self.set_fill_color(30, 41, 59) # Slate-800
        self.rect(0, 0, 210, 35, "F")
        
        self.set_text_color(255, 255, 255)
        self.set_font("helvetica", "B", 18)
        self.cell(0, 10, "REPORTE DE OFERTA ACADEMICA CRAWLER", ln=True, align="C")
        self.set_font("helvetica", "I", 10)
        self.cell(0, 5, f"Generado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="C")
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Pagina {self.page_no()}/{{nb}}", align="C")

def generate_pdf_report(degree_type: str = "", academic_area: str = "", search_query: str = "") -> bytes:
    """
    Generates a PDF summary report using fpdf2 and returns it as raw bytes.
    """
    careers = gold_db.get_careers(degree_type, academic_area, search_query)
    metrics = gold_db.get_metrics()
    
    pdf = AcademicReportPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Set spacing
    pdf.set_margins(15, 20, 15)
    pdf.ln(5)
    
    # 1. Summary Box
    pdf.set_fill_color(241, 245, 249) # Slate-100
    pdf.set_draw_color(203, 213, 225) # Slate-300
    pdf.rect(15, 45, 180, 25, "FD")
    
    pdf.set_xy(17, 47)
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(51, 65, 85) # Slate-700
    pdf.cell(0, 6, "Resumen General de Datos:", ln=True)
    
    pdf.set_xy(17, 54)
    pdf.set_font("helvetica", "", 10)
    pdf.cell(60, 6, f"Paginas Rastreadas: {metrics.get('total_pages_crawled', '0')}")
    pdf.cell(60, 6, f"Carreras Encontradas: {len(careers)}")
    pdf.cell(60, 6, f"Errores Registrados: {metrics.get('errors_intercepted', '0')}")
    
    pdf.ln(25)
    
    # 2. Section Title
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(15, 23, 42) # Slate-900
    pdf.cell(0, 8, "Listado de Programas Academicos Detectados", ln=True)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(5)
    
    # 3. Table/List of careers
    if not careers:
        pdf.set_font("helvetica", "I", 11)
        pdf.cell(0, 10, "No se encontraron programas academicos con los filtros seleccionados.", ln=True)
    else:
        for index, item in enumerate(careers, 1):
            # Page break check
            if pdf.get_y() > 240:
                pdf.add_page()
                pdf.ln(5)
                
            pdf.set_font("helvetica", "B", 11)
            pdf.set_text_color(30, 41, 59) # Slate-800
            
            # Safe Latin encoding for PDF core fonts
            title_text = f"{index}. {item['title']}"
            title_safe = title_text.encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(0, 6, title_safe, ln=True)
            
            # Meta line (Degree & Area)
            pdf.set_font("helvetica", "I", 9)
            pdf.set_text_color(100, 116, 139) # Slate-500
            meta_text = f"Grado: {item['degree_type']}  |  Area: {item['academic_area']}"
            meta_safe = meta_text.encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(0, 5, meta_safe, ln=True)
            
            # Description snippet
            pdf.set_font("helvetica", "", 9.5)
            pdf.set_text_color(71, 85, 105) # Slate-600
            desc = item['description']
            if len(desc) > 280:
                desc = desc[:280] + "..."
            desc_safe = desc.encode('latin-1', 'replace').decode('latin-1')
            
            # Use multi_cell for wrapping text
            pdf.multi_cell(0, 5, desc_safe)
            
            # URL
            pdf.set_font("helvetica", "U", 8.5)
            pdf.set_text_color(37, 99, 235) # Blue-600
            url_safe = item['url'].encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(0, 5, url_safe, ln=True, link=item['url'])
            
            pdf.ln(4)
            
            # Separator line
            pdf.set_draw_color(241, 245, 249)
            pdf.line(15, pdf.get_y(), 195, pdf.get_y())
            pdf.ln(3)

    return pdf.output()
