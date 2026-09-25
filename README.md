# Carolina Data Challenge

## Setup

```powershell
# Create the environment (skip if .venv already exists)
uv venv
uv pip install -r requirements.txt

# Or with plain pip
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run the Streamlit app

```powershell
.venv\Scripts\activate
streamlit run app.py
```

## Layout

- `app.py` — Streamlit dashboard
- `data/` — datasets
- `notebooks/` — exploratory Jupyter notebooks
