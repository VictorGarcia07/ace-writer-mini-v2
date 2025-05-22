
import streamlit as st
import pandas as pd
import docx
import io

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
    st.sidebar.warning("Aún no se cargó ninguna tabla de referencias")

# ---------- SELECCIÓN DE SUBTEMA ----------
st.sidebar.header("🧩 Selección de subtema")
capitulo = st.sidebar.text_input("Capítulo")
subtema = st.sidebar.text_input("Subtema")

# ---------- REDACCIÓN DEL SUBTEMA ----------
st.header(f"Subtema: {subtema}")
texto = st.text_area("Redactá aquí el contenido del subtema (mínimo 1500 palabras)", height=600)

# ---------- CHECKLIST ----------
st.subheader("✅ Validación automática")

palabras = len(texto.split())
st.write(f"🔢 Palabras: {palabras} / 1500 mínimo")

if ref_file and texto:
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
if ref_file:
    st.subheader("📋 Referencias disponibles")
    st.dataframe(df_refs)
else:
    st.info("Subí una tabla .csv para ver las referencias")
