
import streamlit as st
import pandas as pd
import docx
import io
import openai
import os

st.set_page_config(page_title="ACE Writer Mini V2", layout="wide")
st.title("✍️ ACE Writer Mini V2")

ref_file = st.sidebar.file_uploader("📚 Subí la tabla de referencias (.csv)", type="csv")
if ref_file:
    df_refs = pd.read_csv(ref_file)
    st.sidebar.success("Referencias cargadas correctamente")
else:
    df_refs = None
    st.sidebar.warning("Aún no se cargó ninguna tabla de referencias")

capitulo = st.sidebar.text_input("Capítulo", value="Entrenar con datos: apps, sensores, encoders y sentido común")
subtema = st.sidebar.text_input("Subtema", value="Confusión entre precisión y exactitud")

if "final_text" not in st.session_state:
    st.session_state.final_text = ""

st.header(f"Subtema: {subtema}")
st.text_area("Redactá aquí el contenido del subtema (mínimo 1500 palabras)", height=600, value=st.session_state.final_text, key="final_text_display")

if df_refs is not None and capitulo and subtema:
    if st.button("✍️ Generar redacción del subtema"):
        referencias = "\n".join([
            f"{row['Referencia (APA 7)']}" for _, row in df_refs.iterrows() if 'Referencia (APA 7)' in row
        ])
        prompt = f"""Actuás como redactor científico del Proyecto eBooks ACE.
Tu tarea es redactar el subtema titulado **{subtema}**, que forma parte del capítulo **{capitulo}** del eBook ACE.

📌 Condiciones obligatorias:
– El texto debe tener mínimo **1500 palabras reales**
– Incluir al menos **1 recurso visual sugerido cada 500 palabras**
– Utilizar **solo** las referencias incluidas a continuación
– Cerrar con una sección de referencias en formato **APA 7**, solo con las fuentes citadas realmente en el cuerpo

📚 Lista de referencias válidas:
{referencias}

Redactá el texto directamente a continuación, en tono técnico claro, orientado a entrenadores profesionales, con ejemplos prácticos y subtítulos."""

        with st.spinner("Generando contenido con GPT..."):
            api_key = st.sidebar.text_input("🔐 Ingresá tu OpenAI API Key", type="password")
client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Sos un redactor técnico de contenidos científicos sobre entrenamiento."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=3200
            )
            texto = response.choices[0].message.content

            if len(texto.split()) < 1500:
                extend_prompt = f"""El siguiente texto está incompleto o es demasiado corto ({len(texto.split())} palabras).
Extendelo hasta alcanzar al menos 1500 palabras, sin repetir ideas, profundizando contenido y ampliando ejemplos.

TEXTO ORIGINAL:
{texto}"""
                st.warning("Solicitando ampliación...")
                extension = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "Sos un redactor técnico de contenidos científicos sobre entrenamiento."},
                        {"role": "user", "content": extend_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )
                texto = extension.choices[0].message.content

            st.session_state.final_text = texto
            st.success("✅ Subtema generado y almacenado con éxito")

# ---------- Validación ----------
st.subheader("✅ Validación automática")
palabras = len(st.session_state.final_text.split())
st.write(f"🔢 Palabras: {palabras} / 1500 mínimo")

if df_refs is not None and st.session_state.final_text:
    citas_encontradas = []
    for autor in df_refs['Referencia (APA 7)'].dropna().unique():
        if autor in st.session_state.final_text:
            citas_encontradas.append(autor)
    st.write(f"📎 Citas usadas: {len(citas_encontradas)}")
    st.write("Autores citados:", citas_encontradas)

# ---------- Exportar texto ----------
st.subheader("📤 Exportar texto")
col1, col2 = st.columns(2)
with col1:
    if st.button("⬇️ Exportar como Word"):
        doc = docx.Document()
        doc.add_heading(f"{capitulo} – {subtema}", level=1)
        for linea in st.session_state.final_text.split('\n'):
            doc.add_paragraph(linea)
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        st.download_button("Descargar .docx", buffer, file_name=f"{subtema}_ACE.docx")

with col2:
    if st.button("⬇️ Exportar como Markdown"):
        st.download_button("Descargar .md", st.session_state.final_text, file_name=f"{subtema}_ACE.md")

if df_refs is not None:
    st.subheader("📋 Referencias disponibles")
    st.dataframe(df_refs)
