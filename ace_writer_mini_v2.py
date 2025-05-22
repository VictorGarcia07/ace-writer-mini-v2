
import streamlit as st
import pandas as pd
import docx
import io
import openai
import os

# ---------- CONFIG ----------
st.set_page_config(page_title="ACE Writer Mini V2", layout="wide")
st.title("✍️ ACE Writer Mini V2")

# ---------- CARGA DE REFERENCIAS ----------
st.sidebar.header("📚 Cargar referencias validadas")
ref_file = st.sidebar.file_uploader("Subí la tabla de referencias (.csv)", type="csv")
if ref_file:
    df_refs = pd.read_csv(ref_file)
    st.sidebar.success("Referencias cargadas correctamente")
else:
    df_refs = None
    st.sidebar.warning("Aún no se cargó ninguna tabla de referencias")

# ---------- SELECCIÓN DE SUBTEMA ----------
st.sidebar.header("🧩 Selección de subtema")
capitulo = st.sidebar.text_input("Capítulo", value="Entrenar con datos: apps, sensores, encoders y sentido común")
subtema = st.sidebar.text_input("Subtema", value="Confusión entre precisión y exactitud")

# ---------- REDACCIÓN AUTOMÁTICA ----------
st.header(f"Subtema: {subtema}")
texto = st.text_area("Redactá aquí el contenido del subtema (mínimo 1500 palabras)", height=600)

# ---------- BOTÓN DE GENERACIÓN ----------
if df_refs is not None and capitulo and subtema:
    if st.button("✍️ Generar redacción del subtema"):
        referencias = "\n".join([
            f"{row['Referencia (APA 7)']}" for _, row in df_refs.iterrows() if 'Referencia (APA 7)' in row
        ])
        prompt = f"""Actuás como redactor científico del Proyecto eBooks ACE.
Tu tarea es redactar el subtema titulado **{subtema}**, que forma parte del capítulo **{capitulo}** del eBook ACE.

📌 Condiciones obligatorias:
– El texto debe tener mínimo **1500 palabras reales**
– Incluir al menos **1 recurso visual sugerido cada 500 palabras** (imagen de paper, prompt Napkin o prompt DALL·E)
– Utilizar **solo** las referencias incluidas a continuación
– Cerrar con una sección de referencias en formato **APA 7**, solo con las fuentes citadas realmente en el cuerpo

📚 Lista de referencias válidas:
{referencias}

Redactá el texto directamente a continuación, en tono técnico claro, orientado a entrenadores profesionales, con ejemplos prácticos y subtítulos."""
        with st.spinner("Generando contenido con GPT..."):
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Sos un redactor técnico de contenidos científicos sobre entrenamiento."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            texto = response.choices[0].message.content
            st.success("✅ Subtema generado con éxito")
            st.text_area("Redactá aquí el contenido del subtema (mínimo 1500 palabras)", value=texto, height=600, key="final_text")

# ---------- CHECKLIST ----------
st.subheader("✅ Validación automática")
palabras = len(texto.split())
st.write(f"🔢 Palabras: {palabras} / 1500 mínimo")

if df_refs is not None and texto:
    citas_encontradas = []
    for autor in df_refs['Autor'].dropna().unique():
        if autor in texto:
            citas_encontradas.append(autor)
    st.write(f"📎 Citas usadas: {len(citas_encontradas)}")
    st.write("Autores citados:", citas_encontradas)
else:
    st.info("Esperando texto y tabla para verificar citas...")

# ---------- EXPORTACIÓN ----------
st.subheader("📤 Exportar texto")
col1, col2 = st.columns(2)
with col1:
    if st.button("⬇️ Exportar como Word"):
        doc = docx.Document()
        doc.add_heading(f"{capitulo} – {subtema}", level=1)
        for linea in texto.split('\n'):
            doc.add_paragraph(linea)
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        st.download_button("Descargar .docx", buffer, file_name=f"{subtema}_ACE.docx")

with col2:
    if st.button("⬇️ Exportar como Markdown"):
        st.download_button("Descargar .md", texto, file_name=f"{subtema}_ACE.md")

# ---------- MOSTRAR REFERENCIAS ----------
if df_refs is not None:
    st.subheader("📋 Referencias disponibles")
    st.dataframe(df_refs)
