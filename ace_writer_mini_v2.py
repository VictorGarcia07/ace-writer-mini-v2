
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
st.text_area("Redactá aquí el contenido del subtema", height=600, value=st.session_state.final_text, key="final_text_display")

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
– NO incluyas la sección final de referencias, será añadida automáticamente

📚 Lista de referencias válidas:
{referencias}

Redactá el texto directamente a continuación, en tono técnico claro, orientado a entrenadores profesionales, con ejemplos prácticos y subtítulos."""

        with st.spinner("Generando contenido con GPT..."):
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
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
            st.session_state.final_text = texto
            st.success("✅ Subtema generado con éxito")

# 🔁 Botón para generar sección de referencias APA desde la tabla cargada
if st.button("🔁 Añadir sección de Referencias en APA 7"):
    if df_refs is not None and st.session_state.final_text:
        citas_en_texto = []
        for autor in df_refs['Referencia (APA 7)'].dropna().unique():
            apellido = autor.split(',')[0]
            if apellido in st.session_state.final_text:
                citas_en_texto.append(autor)
        if citas_en_texto:
            st.session_state.final_text += "\n\n**Referencias**\n" + "\n".join(sorted(citas_en_texto))
            st.success(f"Se añadieron {len(citas_en_texto)} referencias APA al final del texto.")
        else:
            st.warning("No se encontraron coincidencias de autores para generar las referencias.")

# Exportar a Word
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
