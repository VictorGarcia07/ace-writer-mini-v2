
import streamlit as st
import pandas as pd
from docx import Document
import openai
import time

st.set_page_config(page_title="ACE Writer Mini v12", layout="wide")
st.title("ACE Writer – Redacción automática con validaciones completas")

# Estado de sesión
if "clave_confirmada" not in st.session_state:
    st.session_state["clave_confirmada"] = False
if "plantilla_valida" not in st.session_state:
    st.session_state["plantilla_valida"] = False
if "tabla_valida" not in st.session_state:
    st.session_state["tabla_valida"] = False
if "mostrar_redaccion" not in st.session_state:
    st.session_state["mostrar_redaccion"] = False
if "referencias_finales" not in st.session_state:
    st.session_state["referencias_finales"] = []
if "subtitulo" not in st.session_state:
    st.session_state["subtitulo"] = ""
if "contenido_redactado" not in st.session_state:
    st.session_state["contenido_redactado"] = ""
if "redaccion_iniciada" not in st.session_state:
    st.session_state["redaccion_iniciada"] = False

st.subheader("Paso 0 – Ingresá tu clave OpenAI")
api_key = st.text_input("API Key (formato sk-...)", type="password")
if api_key.startswith("sk-"):
    st.success("✅ Clave cargada correctamente.")
    st.session_state["clave_confirmada"] = True
else:
    st.info("Esperando una clave válida...")

def validar_plantilla_word(path):
    from docx import Document
    estilos = ['Heading 1', 'Heading 2', 'Heading 3', 'Normal', 'Quote', 'Reference', 'List Bullet', 'List Number']
    doc = Document(path)
    resultados = []
    for estilo in estilos:
        resultado = any(s.name == estilo for s in doc.styles)
        resultados.append({"Estilo requerido": estilo, "Presente": "✅" if resultado else "❌"})
    return pd.DataFrame(resultados)

def validar_tabla(df):
    completas, manuales = [], []
    for i, row in df.iterrows():
        criticos = [col for col in ["Autores", "Año", "Título del artículo", "Journal", "DOI/URL"]
                    if pd.isna(row[col]) or str(row[col]).strip() == ""]
        if not criticos:
            completas.append((i + 1, row))
        else:
            manuales.append((i + 1, row))
    return completas, manuales

def generar_redaccion(subtitulo, referencias, api_key):
    client = openai.OpenAI(api_key=api_key)
    ref_texto = "\n".join([
        f"{i+1}. {r['Autores']} ({r['Año']}). {r['Título del artículo']}. {r['Journal']}."
        for i, (_, r) in enumerate(referencias)
    ])
    prompt = f"""
Actuás como redactor científico del eBook ACE. Vas a redactar un subtema técnico en ciencias del ejercicio.

Subtema: {subtitulo}

Instrucciones:
- 1500 palabras mínimas
- Redactá en tono técnico-claro
- Cada 500 palabras sugerí una imagen educativa
- Citá con formato APA
- Referencias base:

{ref_texto}

Finalizá con sección de referencias en formato APA 7.
"""
    respuesta = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Sos redactor científico experto en ciencias del ejercicio."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=3000
    )
    return respuesta.choices[0].message.content

# Paso 1 – Plantilla
st.subheader("Paso 1 – Validar plantilla Word")
plantilla = st.file_uploader("Subí tu archivo .dotx", type=["dotx"])
if plantilla:
    df_estilos = validar_plantilla_word(plantilla)
    st.dataframe(df_estilos)
    if "❌" in df_estilos["Presente"].values:
        st.warning("Faltan estilos requeridos. Reemplazá la plantilla.")
        st.session_state["plantilla_valida"] = False
    else:
        st.success("✅ Plantilla válida.")
        st.session_state["plantilla_valida"] = True

# Paso 2 – Referencias
st.subheader("Paso 2 – Validar tabla de referencias")
archivo_csv = st.file_uploader("Subí tu archivo .csv", type=["csv"])
refs_completas, refs_incompletas = [], []
refs_seleccionadas = []

if archivo_csv:
    df = pd.read_csv(archivo_csv)
    refs_completas, refs_incompletas = validar_tabla(df)
    st.markdown("✅ Referencias validadas automáticamente:")
    st.dataframe(pd.DataFrame([{
        "N°": i, "Referencia": f"{r['Autores']} ({r['Año']}) - {r['Título del artículo']}"
    } for i, r in refs_completas]))

    st.markdown("🛠 Referencias con validación manual:")
    seleccionar_todas = st.checkbox("☑️ Seleccionar todas las incompletas")
    for i, r in refs_incompletas:
        key = f"checkbox_{i}"
        incluir = st.checkbox(f"{i}. {r['Autores']} ({r['Año']}) - {r['Título del artículo']}", key=key, value=seleccionar_todas)
        if incluir:
            refs_seleccionadas.append((i, r))

    if refs_completas or refs_seleccionadas:
        st.session_state["tabla_valida"] = True
        if st.button("Iniciar redacción automática con GPT") and api_key:
            st.session_state["mostrar_redaccion"] = True
            st.session_state["referencias_finales"] = refs_completas + refs_seleccionadas

# Paso 3 – Redacción
if st.session_state["mostrar_redaccion"]:
    st.subheader("Paso 3 – Redacción automática")
    st.session_state["subtitulo"] = st.text_input("Ingresá el subtítulo del capítulo:", value=st.session_state["subtitulo"])
    if st.button("Generar texto"):
        with st.spinner("Redactando con GPT..."):
            resultado = generar_redaccion(
                st.session_state["subtitulo"],
                st.session_state["referencias_finales"],
                api_key
            )
            st.session_state["contenido_redactado"] = resultado
            st.session_state["redaccion_iniciada"] = True

if st.session_state["redaccion_iniciada"]:
    st.text_area("Redacción generada", value=st.session_state["contenido_redactado"], height=500)
    if st.button("Exportar a Word"):
        doc = Document()
        doc.add_heading(st.session_state["subtitulo"], level=1)
        doc.add_paragraph(st.session_state["contenido_redactado"])
        file_path = "/mnt/data/redaccion_acewriter_v12.docx"
        doc.save(file_path)
        with open(file_path, "rb") as f:
            st.download_button("Descargar Word", data=f, file_name="Redaccion_ACEWriter_v12.docx")
