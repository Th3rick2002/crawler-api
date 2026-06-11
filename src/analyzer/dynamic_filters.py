import re
from typing import Tuple

def infer_degree_type(title: str, text: str) -> str:
    """
    Infers the degree type based on keywords present in the title (higher priority) or body text.
    """
    combined = (title + " | " + text).lower()
    
    # We define patterns for classification
    if re.search(r"\b(doctorado|doctor|phd)\b", combined):
        return "Doctorado"
    if re.search(r"\b(maestría|maestria|master|máster|magister|magíster)\b", combined):
        return "Maestría"
    if re.search(r"\b(especialidad|especialización|especializacion|postítulo|postitulo)\b", combined):
        return "Especialidad"
    if re.search(r"\b(ingeniería|ingenieria|ingeniero|ingeniera)\b", combined):
        return "Ingeniería"
    if re.search(r"\b(licenciatura|licenciado|licenciada)\b", combined):
        return "Licenciatura"
    if re.search(r"\b(técnico|tecnico|tecnólogo|tecnologo|tecnología|tecnologia en)\b", combined):
        return "Técnico"
        
    # Extra check specifically for title
    title_lower = title.lower()
    if "ing." in title_lower or "ingeniería" in title_lower:
        return "Ingeniería"
    if "lic." in title_lower or "licenciatura" in title_lower:
        return "Licenciatura"
    if "tec." in title_lower or "técnico" in title_lower or "tecnico" in title_lower:
        return "Técnico"
        
    return "Otros / No especificado"

def infer_academic_area(title: str, text: str) -> str:
    """
    Infers the academic area/field of study based on keywords in the title and description.
    """
    combined = (title + " | " + text).lower()
    
    # Technology & Informatics
    if re.search(r"\b(computación|computacion|sistemas|software|informática|informatica|programación|programacion|redes|ciberseguridad|datos|desarrollo web|tecnología|tecnologia)\b", combined):
        return "Tecnología e Informática"
        
    # Health & Medicine
    if re.search(r"\b(medicina|salud|enfermería|enfermeria|odontología|odontologia|clínica|clinica|nutrición|nutricion|farmacia|psicología|psicologia|kinesiología|kinesiologia|veterinaria|médico|medico)\b", combined):
        return "Salud y Medicina"
        
    # Business, Administration & Economics
    if re.search(r"\b(administración|administracion|negocios|finanzas|economía|economia|contabilidad|marketing|comercio|contable|empresariales|empresas|logística|logistica)\b", combined):
        return "Negocios y Administración"
        
    # Law & Criminology
    if re.search(r"\b(derecho|leyes|jurídico|juridico|abogacía|abogado|criminología|criminologia|legal)\b", combined):
        return "Derecho y Leyes"
        
    # Education
    if re.search(r"\b(educación|educacion|pedagogía|pedagogia|docencia|profesorado|enseñanza|didáctica)\b", combined):
        return "Educación"
        
    # Art, Design & Architecture
    if re.search(r"\b(diseño|diseñador|diseñadora|arte|arquitectura|música|musica|teatro|cine|gráfico|grafico|artístico|artistico|moda|artes)\b", combined):
        return "Arte y Diseño"
        
    # Social Sciences & Humanities
    if re.search(r"\b(sociales|social|humanidades|filosofía|filosofia|historia|letras|literatura|sociología|sociologia|periodismo|comunicación|comunicacion|antropología|antropologia|arqueología|arqueologia)\b", combined):
        return "Ciencias Sociales y Humanidades"
        
    # Exact and Natural Sciences
    if re.search(r"\b(química|quimica|física|fisica|biología|biologia|matemáticas|matematicas|ciencia|geología|geologia|astronomía|astronomia|cálculo|calculo|biotecnología|biotecnologia)\b", combined):
        return "Ciencias Exactas y Naturales"
        
    # Engineering, Industrial & Construction (general non-software engineering)
    if re.search(r"\b(industrial|civil|construcción|construccion|eléctrica|electrica|mecánica|mecanica|electrónica|electronica|minas|metalurgia|química industrial)\b", combined):
        return "Ingeniería e Industria"
        
    # Agronomy, Agriculture & Environment
    if re.search(r"\b(agronomía|agronomia|agrícola|agricola|agropecuario|veterinaria|zootecnia|forestal|ambiental|ambiente)\b", combined):
        return "Agronomía y Veterinaria"
        
    return "Otras Ciencias / General"

def infer_categories(title: str, text: str) -> Tuple[str, str]:
    """Runs both inference methods and returns a tuple (degree_type, academic_area)"""
    return infer_degree_type(title, text), infer_academic_area(title, text)
