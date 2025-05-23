import streamlit as st
import pandas as pd
import docx
from docx.shared import Pt
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from io import BytesIO
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import streamlit.components.v1 as components

# --- FUNCIONES AUXILIARES ---
def contar_tokens(texto):
    palabras = texto.split()
    return int(len(palabras) * 1.33)  # Estimación aproximada de tokens

def contar_palabras(texto):
    return len(texto.split())

def detectar_redundancias(texto, umbral=0.85):
    oraciones = re.split(r'(?<=[.!?])\s+', texto)
    vectorizer = TfidfVectorizer().fit_transform(oraciones)
    sim_matrix = cosine_similarity(vectorizer)
    redundantes = set()
    for i in range(len(sim_matrix)):
        for j in range(i+1, len(sim_matrix)):
            if sim_matrix[i, j] > umbral:
                redundantes.add(oraciones[j])
    return list(redundantes)

def validar_citas(tabla):
    completas, incompletas = [], []
    for _, fila in tabla.iterrows():
        if pd.notnull(fila['DOI']) and pd.notnull(fila['Título del artículo']) and pd.notnull(fila['Journal']):
            completas.append(fila)
        else:
            incompletas.append(fila)
    return pd.DataFrame(completas), pd.DataFrame(incompletas)

def extraer_apellidos_citados(texto):
    return list(set(re.findall(r'\(([^\)]+), \d{4}\)', texto)))

def construir_referencias_apa(apellidos_usados, df_referencias):
    referencias_usadas = df_referencias[df_referencias['Autores'].isin(apellidos_usados)]
    referencias_apa = []
    for _, fila in referencias_usadas.iterrows():
        ref = f"{fila['Autores']} ({fila['Año']}). {fila['Título del artículo']}. {fila['Journal']}, {fila['Volumen']}, {fila['Páginas']}. {fila['DOI']}"
        referencias_apa.append(ref)
    return referencias_apa, len(referencias_apa)

def exportar_a_word(texto, referencias, plantilla, nombre_archivo):
    doc = docx.Document(plantilla)
    doc.add_paragraph(texto)
    doc.add_paragraph("\nAplicación práctica para el entrenador:")
    doc.add_paragraph("(Completar bloque de aplicación práctica aquí.)")
    doc.add_paragraph("\nReferencias:")
    for ref in referencias:
        doc.add_paragraph(ref, style='Normal')
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer, doc

def convertir_a_html(doc):
    html = ""
    for para in doc.paragraphs:
        html += f"<p>{para.text}</p>"
    return html

# --- INTERFAZ PRINCIPAL ---
st.title("AsyncWriter Mini V38")

subtitulo = st.text_input("Subtítulo del tema (usado como nombre del archivo Word)")
archivo_csv = st.file_uploader("Cargar archivo de referencias (.csv)", type="csv")
plantilla_word = st.file_uploader("Cargar plantilla Word (.dotx)", type="dotx")
texto_generado = st.text_area("Pega aquí el texto generado por GPT", height=300)

if archivo_csv and plantilla_word and subtitulo:
    df = pd.read_csv(archivo_csv)
    completas, incompletas = validar_citas(df)
    st.success(f"{len(completas)} referencias completas cargadas")

    seleccionadas = []
    if not incompletas.empty:
        st.write("### Referencias incompletas disponibles para selección manual")
        seleccionadas = st.multiselect("Selecciona referencias incompletas:", list(incompletas['Autores']), key="manual")
        if st.button("Seleccionar todas las incompletas"):
            seleccionadas = list(incompletas['Autores'])

    referencias_validas = pd.concat([
        completas,
        incompletas[incompletas['Autores'].isin(seleccionadas)]
    ])

    if texto_generado:
        token_count = contar_tokens(texto_generado)
        word_count = contar_palabras(texto_generado)
        st.write(f"Palabras totales del texto: {word_count}")

        if word_count < 1500:
            st.warning("El texto tiene menos de 1500 palabras. Asegúrate de que haya agotado las fuentes o justifica su brevedad.")

        if token_count > 4000:
            st.error("El texto excede los 4000 tokens. Por favor, divídelo en partes.")
        else:
            redundancias = detectar_redundancias(texto_generado)
            if redundancias:
                st.warning(f"Se detectaron {len(redundancias)} posibles frases redundantes en el texto.")
                with st.expander("Ver frases redundantes"):
                    for r in redundancias:
                        st.text(f"- {r}")

            apellidos_en_texto = extraer_apellidos_citados(texto_generado)
            referencias_apa, usadas = construir_referencias_apa(apellidos_en_texto, referencias_validas)

            st.write(f"Citas usadas: {usadas} de {len(referencias_validas)} disponibles")

            buffer_word, doc_preview = exportar_a_word(texto_generado, referencias_apa, plantilla_word, subtitulo)

            st.subheader("Vista previa del documento:")
            html_preview = convertir_a_html(doc_preview)
            components.html(html_preview, height=500, scrolling=True)

            st.download_button("Descargar Word generado", data=buffer_word, file_name=f"{subtitulo}.docx")
else:
    st.info("Por favor, carga todos los elementos requeridos.")
