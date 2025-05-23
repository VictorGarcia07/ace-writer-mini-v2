
import streamlit as st
import pandas as pd
from docx import Document
import time

st.set_page_config(page_title="ACE Writer v2 – Redacción Validada", layout="wide")
st.title("✍️ ACE Writer v2 – Redacción Validada")

if "mostrar_redaccion" not in st.session_state:
    st.session_state["mostrar_redaccion"] = False

if "referencias_finales" not in st.session_state:
    st.session_state["referencias_finales"] = []

if "subtitulo" not in st.session_state:
    st.session_state["subtitulo"] = ""

if "contenido_redactado" not in st.session_state:
    st.session_state["contenido_redactado"] = ""

def validar_plantilla_word(path_plantilla):
    required_styles = [
        'Heading 1', 'Heading 2', 'Heading 3', 'Normal',
        'Quote', 'Reference', 'List Bullet', 'List Number'
    ]
    doc = Document(path_plantilla)
    styles = doc.styles
    results = []
    for style in required_styles:
        results.append({
            'Estilo': style,
            '¿Presente?': '✅ Sí' if style in styles else '❌ No'
        })
    return pd.DataFrame(results)

def validar_tabla_referencias_con_checkboxes(df):
    required_columns = [
        "Autores", "Año", "Título del artículo", "Journal",
        "Volumen", "Número", "Páginas", "DOI/URL",
        "Nivel de evidencia", "Cuartil", "Subtema asignado", "¿Incluir?", "Justificación"
    ]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return pd.DataFrame([{"Error": f"Faltan columnas: {', '.join(missing_columns)}"}]), [], []

    auto_incluidas, manuales = [], []
    for i, row in df.iterrows():
        criticos = [col for col in ["Autores", "Año", "Título del artículo", "Journal", "DOI/URL"]
                    if pd.isna(row[col]) or str(row[col]).strip() == ""]
        secundarios = [col for col in required_columns if col not in criticos and 
                       (pd.isna(row[col]) or str(row[col]).strip() == "")]
        if not criticos and not secundarios:
            auto_incluidas.append((i + 1, row))
        elif not criticos:
            auto_incluidas.append((i + 1, row))
        else:
            manuales.append((i + 1, row))

    return None, auto_incluidas, manuales

st.subheader("Paso 1️⃣ – Cargar Plantilla Word (.dotx)")
plantilla_file = st.file_uploader("Subí tu plantilla Word con estilos predefinidos", type=["dotx"])

if plantilla_file:
    plantilla_result = validar_plantilla_word(plantilla_file)
    st.write("✅ Resultado de validación de estilos:")
    st.dataframe(plantilla_result)

    if "❌ No" in plantilla_result["¿Presente?"].values:
        st.warning("La plantilla tiene errores. Subí una nueva antes de continuar.")
    else:
        st.success("Plantilla válida. Podés continuar al paso 2.")
        st.subheader("Paso 2️⃣ – Cargar tabla de referencias (.csv)")
        referencias_file = st.file_uploader("Subí la tabla con referencias científicas", type=["csv"])

        if referencias_file:
            df_refs = pd.read_csv(referencias_file)
            error_df, refs_auto, refs_manual = validar_tabla_referencias_con_checkboxes(df_refs)

            if error_df is not None:
                st.error("⚠ Error en la tabla de referencias:")
                st.dataframe(error_df)
            else:
                st.success("✅ Validación automática completada")
                st.write("📚 Referencias válidas automáticamente:")
                if refs_auto:
                    df_auto = pd.DataFrame([{
                        "N°": i,
                        "Referencia": f"{row['Autores']} ({row['Año']}) - {row['Título del artículo']}"
                    } for i, row in refs_auto])
                    st.dataframe(df_auto)

                st.write("🛠 Referencias con validación manual:")
                refs_incluir = []
                select_all = st.checkbox("☑️ Seleccionar todas las referencias manuales")
                if refs_manual:
                    for i, row in refs_manual:
                        key = f"ref_manual_{i}"
                        incluir = st.checkbox(
                            f"{i}. {row['Autores']} ({row['Año']}) - {row['Título del artículo']}",
                            key=key,
                            value=select_all
                        )
                        if incluir:
                            refs_incluir.append((i, row))

                if st.button("📝 Redactar capítulo"):
                    with st.spinner("🛠 Preparando entorno de redacción..."):
                        time.sleep(1)
                        st.session_state["mostrar_redaccion"] = True
                        st.session_state["referencias_finales"] = refs_auto + refs_incluir

# Paso 3 – Redacción
if st.session_state["mostrar_redaccion"]:
    st.subheader("Paso 3️⃣ – Redacción del subtema")
    st.session_state["subtitulo"] = st.text_input("✏️ Ingresá aquí el subtítulo del capítulo:", value=st.session_state["subtitulo"])
    st.session_state["contenido_redactado"] = st.text_area("🧾 Redactá el contenido del subtema (mínimo 1500 palabras):", height=300)

    palabras = len(st.session_state["contenido_redactado"].split())
    st.markdown(f"📊 **Palabras escritas:** {palabras} / 1500 mínimo")

    if palabras < 1500:
        st.warning("⚠ Aún no alcanzaste el mínimo de palabras.")
    else:
        st.success("✅ Mínimo de palabras alcanzado. Podés exportar.")

    if st.session_state["contenido_redactado"]:
        if st.button("📤 Exportar redacción"):
            doc = Document()
            doc.add_heading(st.session_state["subtitulo"], level=1)
            doc.add_paragraph(st.session_state["contenido_redactado"])
            file_path = "/mnt/data/redaccion_exportada.docx"
            doc.save(file_path)
            st.success("✅ Exportación completada.")
            with open(file_path, "rb") as f:
                st.download_button("📥 Descargar documento Word", data=f, file_name="Redaccion_ACEWriter.docx")
