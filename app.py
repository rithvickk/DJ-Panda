import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Carolina Data Challenge", layout="wide")
st.title("Carolina Data Challenge")


DEFAULT_DATA = "data/mxmh_survey_results.csv"


@st.cache_data
def load_data(file) -> pd.DataFrame:
    name = file if isinstance(file, str) else file.name
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(file)
    return pd.read_csv(file)


uploaded = st.sidebar.file_uploader("Upload a different dataset", type=["csv", "xlsx", "xls"])
df = load_data(uploaded if uploaded is not None else DEFAULT_DATA)

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
