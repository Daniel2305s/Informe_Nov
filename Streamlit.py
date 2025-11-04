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
# 💳 ANÁLISIS ADDI / ADDI SHOP
# ==============================

# Ver columnas disponibles
st.write("🔍 **Columnas del DataFrame:**")
st.write(df.columns.tolist())

# Intentar encontrar la columna de tipo pago de múltiples formas
columna_tipo_pago = None

# Método 1: Buscar por nombre exacto (varias variaciones)
posibles_nombres = ['tipo pago', 'tipo_pago', 'tipopago', 'Tipo pago', 'Tipo Pago', 'TIPO PAGO']
for nombre in posibles_nombres:
    if nombre in df.columns:
        columna_tipo_pago = nombre
        st.success(f"✅ Columna encontrada: '{columna_tipo_pago}'")
        break

# Método 2: Buscar por contenido (contiene 'tipo' y 'pago')
if columna_tipo_pago is None:
    for col in df.columns:
        col_lower = col.lower().strip()
        if 'tipo' in col_lower and 'pago' in col_lower:
            columna_tipo_pago = col
            st.success(f"✅ Columna encontrada por búsqueda: '{columna_tipo_pago}'")
            break

# Método 3: Si tienes la columna al lado de 'pago', usar índice
if columna_tipo_pago is None:
    try:
        # Encontrar índice de 'pago'
        idx_pago = df.columns.tolist().index('pago')
        # La columna 'tipo pago' debería estar en el siguiente índice
        if idx_pago + 1 < len(df.columns):
            columna_tipo_pago = df.columns[idx_pago + 1]
            st.info(f"ℹ️ Usando columna siguiente a 'pago': '{columna_tipo_pago}'")
    except ValueError:
        pass

# Si aún no se encuentra, crear vacía
if columna_tipo_pago is None:
    df['tipo_pago'] = ''
    columna_tipo_pago = 'tipo_pago'
    st.warning("⚠️ No se encontró columna 'tipo pago'. Se creó vacía.")
else:
    # Mostrar valores únicos de la columna encontrada
    st.write(f"**Valores únicos en '{columna_tipo_pago}':**", df[columna_tipo_pago].unique().tolist())

# Normalizar datos de pago
df['pago_norm'] = df['pago'].astype(str).str.strip().str.lower()

# Normalizar datos de tipo pago
df['tipo_pago_norm'] = df[columna_tipo_pago].fillna('').astype(str).str.strip().str.lower()

# Filtrar solo ventas completadas
ventas_completadas_addi = df[df['Estado'].str.lower() == 'completed'].copy()

# ==============================
# 📊 CÁLCULOS ADDI
# ==============================

# 🔹 Total Addi (todas las ventas con pago = addi)
ventas_addi_total = ventas_completadas_addi[
    ventas_completadas_addi['pago_norm'] == 'addi'
]

# 🔹 Addi Shop (pago = addi y tipo pago = shop)
ventas_addi_shop = ventas_addi_total[
    ventas_addi_total['tipo_pago_norm'] == 'shop'
]

# 🔹 Addi Solo/Normal (pago = addi y tipo pago vacío)
ventas_addi_solo = ventas_addi_total[
    ventas_addi_total['tipo_pago_norm'] == ''
]

# ==============================
# 📈 MÉTRICAS
# ==============================

# Total Addi
total_addi_ventas = ventas_addi_total['Pedido #'].nunique()
total_addi_dinero = ventas_addi_total['Ventas netas (num)'].sum()

# Addi Shop
total_addi_shop_ventas = ventas_addi_shop['Pedido #'].nunique()
total_addi_shop_dinero = ventas_addi_shop['Ventas netas (num)'].sum()

# Addi Solo
total_addi_solo_ventas = ventas_addi_solo['Pedido #'].nunique()
total_addi_solo_dinero = ventas_addi_solo['Ventas netas (num)'].sum()

# Porcentaje de Addi Shop sobre Total Addi
porcentaje_shop_ventas = (total_addi_shop_ventas / total_addi_ventas * 100) if total_addi_ventas > 0 else 0
porcentaje_shop_dinero = (total_addi_shop_dinero / total_addi_dinero * 100) if total_addi_dinero > 0 else 0

# ==============================
# 🎨 MOSTRAR RESULTADOS
# ==============================
st.markdown("---")
st.markdown("### 💳 Análisis de ventas Addi")

# Primera fila: Total Addi
col1, col2 = st.columns(2)
col1.metric(
    "📊 Total Addi - Ventas",
    f"{total_addi_ventas} pedidos"
)
col2.metric(
    "💰 Total Addi - Valor",
    f"${total_addi_dinero:,.0f}"
)

st.markdown("---")

# Segunda fila: Desglose Addi Shop vs Addi Solo
col3, col4, col5, col6 = st.columns(4)

col3.metric(
    "🏪 Addi Shop - Ventas",
    f"{total_addi_shop_ventas}",
    f"{porcentaje_shop_ventas:.1f}% del total"
)

col4.metric(
    "💵 Addi Shop - Valor",
    f"${total_addi_shop_dinero:,.0f}",
    f"{porcentaje_shop_dinero:.1f}% del total"
)

col5.metric(
    "🔵 Addi Normal - Ventas",
    f"{total_addi_solo_ventas}"
)

col6.metric(
    "💵 Addi Normal - Valor",
    f"${total_addi_solo_dinero:,.0f}"
)

# ==============================
# 📋 RESUMEN DETALLADO
# ==============================
st.markdown("---")
st.markdown("#### 📋 Resumen Addi")

resumen_texto = f"""
**Total Addi:**
- 🛒 Ventas totales: **{total_addi_ventas}** pedidos
- 💰 Valor total: **${total_addi_dinero:,.0f}**

**Addi Shop:**
- 🛒 Ventas: **{total_addi_shop_ventas}** pedidos (**{porcentaje_shop_ventas:.1f}%** del total Addi)
- 💰 Valor: **${total_addi_shop_dinero:,.0f}** (**{porcentaje_shop_dinero:.1f}%** del total Addi)

**Addi Normal:**
- 🛒 Ventas: **{total_addi_solo_ventas}** pedidos
- 💰 Valor: **${total_addi_solo_dinero:,.0f}**
"""

st.markdown(resumen_texto)




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
