import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import re

# ==============================
# 🌸 Apariencia personalizada
# ==============================
st.markdown("""
    <style>
        .reportview-container { font-family: 'Montserrat', sans-serif; }
        h1, h2 { color: #e72380; }
        body { background-color: #fff; }
        .sidebar .sidebar-content { background-color: #ed6da6; }
        .metric-text { font-size: 1.1rem; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Informe de Ventas (Octubre 2025)")

# ==============================
# 📥 Cargar datos desde Google Sheets
# ==============================
SHEET_ID = "16ngPt_QlQ353fVSBq1FoYfl-ytFk2n6BYlArnv8WddE"
csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

@st.cache_data
def cargar_datos(url):
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    return df

df = cargar_datos(csv_url)

# ==============================
# 🧮 Preprocesamiento
# ==============================
def extraer_cantidad(texto):
    match = re.match(r"(\d+)[×x]", str(texto).strip())
    if match:
        return int(match.group(1))
    return 1

df['Cantidad'] = df['Producto(s)'].apply(extraer_cantidad)

# Convertir Ventas netas a float (quitando símbolos $ y comas)
df['Ventas netas (num)'] = df['Ventas netas'].replace('[\$,]', '', regex=True).astype(float)

ventas_completadas = df[df['Estado'].str.lower() == 'completed']
ventas_devueltas = df[df['Estado'].str.lower() == 'refunded']

# ==============================
# 📌 Métricas principales
# ==============================
total_ventas_exitosas = ventas_completadas.shape[0]
total_ventas_devueltas = ventas_devueltas.shape[0]
total_productos_vendidos = ventas_completadas['Cantidad'].sum()
total_dinero = ventas_completadas['Ventas netas (num)'].sum()

# ==============================
# 🏆 Top Producto / Origen / Pago
# ==============================
# Producto top
producto_group = ventas_completadas.groupby('Producto(s)')['Cantidad'].sum().sort_values(ascending=False)
producto_top = producto_group.index[0]
producto_top_cant = producto_group.iloc[0]

# Origen top
origen_top = ventas_completadas.groupby('atribucion')['Cantidad'].sum().nlargest(1).index[0]

# Pago top
pago_group = ventas_completadas.groupby('pago')
pago_top_row = pago_group['Cantidad'].sum().sort_values(ascending=False).index[0]
pago_top_valor = pago_group['Ventas netas (num)'].sum().loc[pago_top_row]

# ✅ contar pedidos únicos correctamente
pago_top_ventas = ventas_completadas[ventas_completadas['pago'] == pago_top_row]['Pedido #'].nunique()


# ==============================
# 📊 Mostrar métricas
# ==============================
col1, col2, col3, col4 = st.columns(4)
col1.metric("Ventas exitosas", total_ventas_exitosas)
col2.metric("Ventas devueltas", total_ventas_devueltas)
col3.metric("Productos vendidos", int(total_productos_vendidos))

# 👇 Cambiamos col4.metric por markdown con estilo para evitar truncado
col4.markdown(
    f"""
    <div style="text-align: center;">
        <div style="font-size: 0.9rem; color: gray;">Total dinero</div>
        <div style="font-size: 1.4rem; font-weight: bold; white-space: nowrap;">
            ${total_dinero:,.0f}
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

#Producto Top
st.markdown(
    f"<p class='metric-text'>🏆 <b>Producto más vendido:</b> {producto_top} "
    f"(<b>{producto_top_cant}</b> unidades)</p>",
    unsafe_allow_html=True
)

# Origen top
st.markdown(
    f"<p class='metric-text'>📈 <b>Origen con más ventas:</b> {origen_top}</p>",
    unsafe_allow_html=True
)

# Método de pago top (con total + número de ventas)
st.markdown(
    f"<p class='metric-text'>💳 <b>Método de pago más usado:</b> {pago_top_row} "
    f"— Total: <b>${pago_top_valor:,.0f}</b> — Ventas: <b>{pago_top_ventas}</b></p>",
    unsafe_allow_html=True
)

# ==============================
# 🔸 Nueva función: Ventas devueltas
# ==============================
def mostrar_info_devoluciones(df_devueltas):
    if df_devueltas.empty:
        st.info("✅ No hay ventas devueltas en este periodo.")
        return

    # Calcular valor total devuelto
    total_valor_devueltas = df_devueltas['Ventas netas (num)'].sum()

    # Extraer números de pedido desde la columna correcta
    if 'Pedido #' in df_devueltas.columns:
        pedidos = df_devueltas['Pedido #'].astype(str).tolist()
        pedidos_texto = ", ".join(pedidos)
    else:
        pedidos_texto = "❌ No se encontró la columna 'Número de pedido' en los datos."

    # Mostrar en Streamlit
    st.markdown("### 💸 Ventas Devueltas")
    st.markdown(f"**Valor total devuelto:** ${total_valor_devueltas:,.0f}")
    st.markdown(f"**Números de pedido devueltos:** {pedidos_texto}")

mostrar_info_devoluciones(ventas_devueltas)

# ==============================
# 📈 Gráficos
# ==============================
fig, ax = plt.subplots(figsize=(10, 5))
ventas_completadas.groupby('Producto(s)')['Cantidad'].sum().sort_values(ascending=False).plot(
    kind='bar', color='#e72380', ax=ax
)
plt.title('Ventas por Producto')
plt.ylabel('Cantidad vendida')
plt.xticks(ha='right')
st.pyplot(fig)

fig2, ax2 = plt.subplots(figsize=(7, 5))
ventas_completadas.groupby('pago')['Cantidad'].sum().plot(
    kind='bar', color='#ed6da6', ax=ax2
)
plt.title('Ventas por Método de Pago')
plt.ylabel('Cantidad vendida')
st.pyplot(fig2)


# ==============================
# 🆕 Conteo y dinero por Addi / Addi Shop (CORREGIDO)
# ==============================

# Normalizamos el campo de pago para evitar errores por espacios o mayúsculas
ventas_completadas['pago_norm'] = ventas_completadas['pago'].astype(str).str.strip().str.lower()

# Filtrar exactamente Addi
ventas_addi = ventas_completadas[ventas_completadas['pago_norm'] == "addi"]

# Filtrar Addi Shop (usa contains para capturar variaciones como "addi shop orgánico")
ventas_addi_shop = ventas_completadas[ventas_completadas['pago_norm'].str.contains("addi shop", na=False)]

# Cantidades
cantidad_addi = ventas_addi.shape[0]
cantidad_addi_shop = ventas_addi_shop.shape[0]

# Totales de dinero
dinero_addi = ventas_addi['Ventas netas (num)'].sum()
dinero_addi_shop = ventas_addi_shop['Ventas netas (num)'].sum()

# Mostrar en streamlit
st.markdown("### 💳 Detalle pagos Addi / Addi Shop")

col_a, col_b = st.columns(2)

col_a.metric(
    "Addi",
    f"{cantidad_addi} ventas",
    f"${dinero_addi:,.0f}"
)

col_b.metric(
    "Addi Shop",
    f"{cantidad_addi_shop} ventas",
    f"${dinero_addi_shop:,.0f}"
)


st.markdown("### 🧾 Tabla Interactiva de Ventas")
st.dataframe(
    df[[
        'Pedido #',
        'Fecha',
        'Producto(s)',
        'Cantidad',
        'Ventas netas',
        'Estado',
        'pago',
        'atribucion'
    ]],
    use_container_width=True
)
