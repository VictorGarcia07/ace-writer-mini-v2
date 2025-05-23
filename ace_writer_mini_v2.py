
import streamlit as st
import pandas as pd
from docx import Document

st.set_page_config(page_title="ACE Writer v2 – Redacción Validada", layout="wide")
st.title("✍️ ACE Writer v2 – Redacción Validada")

# ----------------------------
# Funciones de validación
# ----------------------------

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
    indices_incluir = []
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
            indices_incluir.append(i)

    return None, auto_incluidas, manuales

# ----------------------------
# Interfaz principal
# ----------------------------

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
                if refs_manual:
                    for i, row in refs_manual:
                        key = f"ref_manual_{i}"
                        incluir = st.checkbox(f"{i}. {row['Autores']} ({row['Año']}) - {row['Título del artículo']}", key=key)
                        if incluir:
                            refs_incluir.append((i, row))

                if st.button("📝 Redactar capítulo"):
                    total_refs = refs_auto + refs_incluir
                    st.success(f"Redacción habilitada con {len(total_refs)} referencias.")
