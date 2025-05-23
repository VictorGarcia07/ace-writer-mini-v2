
import streamlit as st
import pandas as pd
import docx
from io import BytesIO
import re

# --- FUNCIONES AUXILIARES ---
def contar_tokens(texto):
    palabras = texto.split()
    return int(len(palabras) * 1.33)

def contar_palabras(texto):
    return len(texto.split())

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

def exportar_a_word(texto, referencias, plantilla):
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
    return buffer

# --- INTERFAZ PRINCIPAL ---
st.title("ACE Writer Mini V38")

plantilla_word = st.file_uploader("Paso 1 – Cargar plantilla Word (.docx)", type="docx")

if plantilla_word:
    st.success("✅ Plantilla cargada correctamente.")

    archivo_csv = st.file_uploader("Paso 2 – Cargar referencias (.csv)", type="csv")
    if archivo_csv:
        df = pd.read_csv(archivo_csv)
        completas, incompletas = validar_citas(df)
        st.success(f"✅ {len(completas)} referencias completas cargadas")

        seleccionadas = []
        if not incompletas.empty:
            seleccionadas = st.multiselect("Selecciona manualmente las referencias incompletas:", list(incompletas['Autores']))
            if st.button("Seleccionar todas"):
                seleccionadas = list(incompletas['Autores'])

        referencias_validas = pd.concat([
            completas,
            incompletas[incompletas['Autores'].isin(seleccionadas)]
        ])

        subtitulo = st.text_input("Paso 3 – Ingresá el subtítulo del subtema")
        texto_generado = st.text_area("Paso 4 – Pegá aquí el texto generado por GPT", height=300)

        if st.button("Generar redacción") and texto_generado and subtitulo:
            palabras = contar_palabras(texto_generado)
            tokens = contar_tokens(texto_generado)
            st.write(f"📏 Palabras: {palabras} | Estimación de tokens: {tokens}")

            apellidos_en_texto = extraer_apellidos_citados(texto_generado)
            referencias_apa, usadas = construir_referencias_apa(apellidos_en_texto, referencias_validas)
            st.write(f"🔍 Citas usadas: {usadas} de {len(referencias_validas)} disponibles")

            buffer = exportar_a_word(texto_generado, referencias_apa, plantilla_word)
            st.download_button("📄 Descargar Word generado", data=buffer, file_name=f"{subtitulo}.docx")
else:
    st.info("Por favor, cargá primero la plantilla Word para comenzar.")
