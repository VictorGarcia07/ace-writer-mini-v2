import streamlit as st
import pandas as pd
import docx
import re
from io import BytesIO
import openai

# ---------------- FUNCIONES ---------------- #

def contar_tokens(texto):
    return int(len(texto.split()) * 1.33)

def contar_palabras(texto):
    return len(texto.split())

def validar_citas(df):
    completas = df[df[['DOI', 'Título del artículo', 'Journal']].notnull().all(axis=1)]
    incompletas = df[~df.index.isin(completas.index)]
    return completas, incompletas

def construir_referencias_apa(texto, df_referencias):
    citas = []
    for _, fila in df_referencias.iterrows():
        apellido = fila['Autores'].split(',')[0].strip()
        if re.search(rf'\({apellido}, \d{{4}}\)', texto):
            citas.append(fila)
    referencias = []
    for _, fila in pd.DataFrame(citas).drop_duplicates().iterrows():
        ref = f"{fila['Autores']} ({fila['Año']}). {fila['Título del artículo']}. {fila['Journal']}, {fila['Volumen']}, {fila['Páginas']}. {fila['DOI']}"
        referencias.append(ref)
    return referencias

def exportar_word(texto, referencias, plantilla):
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

def generar_texto(subtema, referencias, api_key):
    lista = [f"{a}, {b}" for a, b in zip(referencias['Autores'], referencias['Año'])]
    prompt = f"""Actuás como redactor técnico de eBooks en ciencias del ejercicio.

Tu tarea es desarrollar el subtema: "{subtema}" con un tono técnico-claro, voz cercana, ejemplos aplicados y subtítulos útiles.

Citas solo permitidas (APA): 
{chr(10).join(lista)}

Texto completo (≥1500 palabras si el tema lo permite):"""

    try:
        cliente = openai.OpenAI(api_key=api_key)
        r = cliente.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=4096
        )
        return r.choices[0].message.content
    except Exception as e:
        st.error(f"Error: {e}")
        return ""

# ---------------- INTERFAZ ---------------- #

st.set_page_config(page_title="ACE Writer Mini – Versión Final", layout="wide")
st.title("ACE Writer Mini – Generador de capítulos científicos")

api_key = st.text_input("🔐 Clave OpenAI", type="password")
plantilla = st.file_uploader("📂 Paso 1 – Subí tu plantilla Word (.dotx)", type="dotx")
csv = st.file_uploader("📂 Paso 2 – Subí tu archivo .csv con referencias", type="csv")

if api_key and plantilla and csv:
    df = pd.read_csv(csv)
    completas, incompletas = validar_citas(df)
    st.success(f"✅ {len(completas)} referencias completas encontradas")
    seleccionadas = []

    if not incompletas.empty:
        seleccionadas = st.multiselect("⚠️ Referencias incompletas. Seleccioná manualmente si querés usarlas:", list(incompletas['Autores']))
        if st.button("📎 Seleccionar todas las incompletas"):
            seleccionadas = list(incompletas['Autores'])

    referencias = pd.concat([completas, incompletas[incompletas['Autores'].isin(seleccionadas)]])

    subtema = st.text_input("📝 Paso 3 – Ingresá el subtítulo del subtema")
    if st.button("🧾 Generar redacción"):
        texto = generar_texto(subtema, referencias, api_key)
        st.session_state["texto"] = texto
        st.session_state["subtema"] = subtema
        st.session_state["referencias"] = referencias

if "texto" in st.session_state:
    texto = st.session_state["texto"]
    st.subheader("🧠 Texto generado")
    st.markdown(texto)

    st.write(f"📊 Palabras: {contar_palabras(texto)} | Tokens estimados: {contar_tokens(texto)}")

    if st.button("🤔 ¿Por qué se truncó?"):
        if contar_palabras(texto) < 1500:
            st.info("El modelo consideró que el tema se agotó antes de llegar a 1500 palabras.")
        else:
            st.success("El texto fue generado completamente.")

    if st.button("📤 Descargar Word"):
        referencias_apa = construir_referencias_apa(texto, st.session_state["referencias"])
        buffer = exportar_word(texto, referencias_apa, plantilla)
        st.download_button("⬇️ Descargar .docx", buffer, file_name=f"{st.session_state['subtema']}.docx")

    if st.button("🔄 Nuevo subtema"):
        for key in ["texto", "subtema", "referencias"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()