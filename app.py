import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Carolina Data Challenge", layout="wide")
st.title("Carolina Data Challenge")


@st.cache_data
def load_data(file) -> pd.DataFrame:
    if file.name.endswith((".xlsx", ".xls")):
        return pd.read_excel(file)
    return pd.read_csv(file)


uploaded = st.sidebar.file_uploader("Upload a dataset", type=["csv", "xlsx", "xls"])

if uploaded is None:
    st.info("Upload a CSV or Excel file in the sidebar to get started.")
    st.stop()

df = load_data(uploaded)

st.subheader("Preview")
st.dataframe(df.head(100), use_container_width=True)

col1, col2 = st.columns(2)
col1.metric("Rows", f"{len(df):,}")
col2.metric("Columns", df.shape[1])

numeric_cols = df.select_dtypes("number").columns.tolist()
if numeric_cols:
    st.subheader("Explore")
    x = st.selectbox("X axis", df.columns)
    y = st.selectbox("Y axis", numeric_cols)
    st.plotly_chart(px.scatter(df, x=x, y=y), use_container_width=True)
