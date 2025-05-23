
import streamlit as st
import pandas as pd
from docx import Document
import openai
import io
import time
import re

st.set_page_config(page_title="ACE Writer Mini V2 Reparado", layout="wide")
st.title("🛠️ ACE Writer Mini – Versión Reparada con Verificación de Columnas")

# Estado
if "clave_ok" not in st.session_state:
    st.session_state["clave_ok"] = False
if "referencias_completas" not in st.session_state:
    st.session_state["referencias_completas"] = []
if "referencias_incompletas" not in st.session_state:
    st.session_state["referencias_incompletas"] = []
if "subtema" not in st.session_state:
    st.session_state["subtema"] = ""
if "redaccion" not in st.session_state:
    st.session_state["redaccion"] = ""
if "citadas" not in st.session_state:
    st.session_state["citadas"] = []

# Paso 0 – API Key
api_key = st.text_input("🔐 Clave OpenAI", type="password")
if api_key.startswith("sk-"):
    st.session_state["clave_ok"] = True
    st.success("✅ Clave válida")

# Paso 1 – Validar plantilla Word
st.subheader("Paso 1 – Validar plantilla Word")
plantilla = st.file_uploader("📂 Subí tu plantilla Word (.dotx)", type=["dotx"])
if plantilla:
    doc = Document(plantilla)
    requeridos = ['Heading 1', 'Heading 2', 'Normal', 'Reference']
    encontrados = [s.name for s in doc.styles]
    validacion = [{"Estilo": s, "Presente": "✅" if s in encontrados else "❌"} for s in requeridos]
    st.dataframe(pd.DataFrame(validacion))


# Paso 2 – Subir y seleccionar referencias
st.subheader("Paso 2 – Subir y seleccionar referencias")
archivo_csv = st.file_uploader("📄 Archivo .csv con referencias", type=["csv"])
refs_dict = {}

selected_refs = []
completas = []
incompletas = []

if archivo_csv:
    df = pd.read_csv(archivo_csv)
    required_cols = ["Autores", "Año", "Título del artículo", "Journal"]
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        st.error(f"❌ Faltan columnas obligatorias: {', '.join(missing_cols)}")
    else:
        for i, row in df.iterrows():
            try:
                ref_str = f"{row['Autores']} ({row['Año']}). {row['Título del artículo']}. {row['Journal']}."
                if "DOI" in df.columns and pd.notna(row["DOI"]):
                    ref_str += f" https://doi.org/{row['DOI']}"
                if all(pd.notna(row[c]) and str(row[c]).strip() != "" for c in required_cols):
                    completas.append((row['Autores'], ref_str))
                else:
                    incompletas.append((row['Autores'], ref_str))
            except Exception as e:
                incompletas.append((f"Error en fila {i}", str(e)))

        # Cargar todas las completas automáticamente
        for autor, ref in completas:
            selected_refs.append(ref)

        # Mostrar panel de selección para incompletas
        st.success(f"✅ {len(completas)} referencias completas encontradas")
        st.warning(f"⚠️ {len(incompletas)} referencias incompletas")

        if incompletas:
            st.markdown("### ✍️ Seleccioná manualmente si querés incluir alguna incompleta")
            seleccionar_todas_incompletas = st.checkbox("Seleccionar todas las incompletas")
            for i, (autor, ref) in enumerate(incompletas):
                key = f"incomp_{i}_{hash(ref)}"
                if seleccionar_todas_incompletas or st.checkbox(ref, key=key):
                    selected_refs.append(ref)


# Paso 3 – Escribí el subtítulo del subtema
st.subheader("Paso 3 – Escribí el subtítulo del subtema")
st.session_state["subtema"] = st.text_input("✏️ Subtítulo del capítulo:", value=st.session_state.get("subtema", ""))

# Paso 4 – Redacción
def redactar_con_ampliacion(subtema, referencias, api_key):
    client = openai.OpenAI(api_key=api_key)
    prompt = f"""Actuás como redactor científico del Proyecto eBooks ACE.
Tu tarea es redactar el subtema titulado "{subtema}" para un eBook de entrenamiento de fuerza y potencia.

📌 Condiciones:
– Mínimo 1500 palabras
– Cada 500 palabras: sugerí una imagen educativa
– Usá solo estas referencias:
{chr(10).join(referencias)}

Redactá en tono técnico claro, con subtítulos y ejemplos prácticos.
Cerrá con sección de referencias en formato APA 7, solo las citadas.
"""

    with st.spinner("✍️ Generando texto con GPT..."):
        import time
        time.sleep(1)
        r1 = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Sos redactor experto en ciencias del ejercicio."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.65,
            max_tokens=5000
        )
    texto = r1.choices[0].message.content
    if len(texto.split()) >= 1500:
        return texto
    prompt_ampliado = f"""El siguiente texto quedó incompleto ({len(texto.split())} palabras).
Extendelo hasta completar más de 1500 palabras, sin repetir lo anterior.

TEXTO ORIGINAL:
{texto}"""
    with st.spinner("🔁 Solicitando ampliación automática..."):
        r2 = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Sos redactor experto en ciencias del ejercicio."},
                {"role": "user", "content": prompt_ampliado}
            ],
            temperature=0.65,
            max_tokens=4000
        )
    return texto + "

" + r2.choices[0].message.content

# Paso 5 – Generar redacción
if st.button("🚀 Redactar capítulo completo"):
    if st.session_state["clave_ok"] and st.session_state["subtema"] and selected_refs:
        texto = redactar_con_ampliacion(st.session_state["subtema"], selected_refs, api_key)
        st.session_state["redaccion"] = texto
        st.success(f"✅ Redacción generada ({len(texto.split())} palabras)")

        # Contar referencias citadas
        citas = []
        for ref in selected_refs:
            apellido = ref.split(",")[0]
            if apellido in texto:
                citas.append(ref)
        st.session_state["citadas"] = citas

# Paso 6 – Mostrar resultados
if st.session_state.get("redaccion"):
    st.subheader("🧾 Redacción final")
    st.text_area("Texto generado", value=st.session_state["redaccion"], height=500)
    st.markdown(f"📊 Palabras totales: **{len(st.session_state['redaccion'].split())}**")
    st.markdown(f"📚 Referencias citadas: **{len(st.session_state['citadas'])}**")
    if st.session_state["citadas"]:
        st.markdown("### Referencias citadas en el texto:")
        for ref in st.session_state["citadas"]:
            st.markdown(f"- {ref}")

# Paso 7 – Exportar a Word
if st.session_state.get("redaccion"):
    if st.button("💾 Exportar a Word"):
        from docx import Document
        doc = Document(plantilla) if plantilla else Document()
        doc.add_heading(st.session_state["subtema"], level=1)
        doc.add_paragraph(st.session_state["redaccion"])
        doc.add_page_break()
        doc.add_heading("Referencias citadas", level=2)
        for ref in st.session_state["citadas"]:
            doc.add_paragraph(ref)
        ruta = "/mnt/data/acewriter_final_v28.docx"
        doc.save(ruta)
        with open(ruta, "rb") as f:
            st.download_button("📥 Descargar Word", data=f, file_name="ACEWriter_v28.docx")