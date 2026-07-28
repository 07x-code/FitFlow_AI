import streamlit as st


THEME_CSS = """
<style>
:root {
  --fitflow-primary: #087f73;
  --fitflow-dark: #123d3a;
  --fitflow-soft: #edf8f5;
  --fitflow-border: #dce9e6;
}
.stApp {
  background: #f4f8f7;
}
[data-testid="stSidebar"] {
  background: #123d3a;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label {
  color: #f7fffd;
}
.fitflow-hero {
  padding: 1.25rem 1.5rem;
  border-radius: 1rem;
  color: white;
  background: linear-gradient(135deg, #123d3a, #087f73);
  margin-bottom: 1rem;
}
.fitflow-card {
  padding: 1rem;
  border: 1px solid #dce9e6;
  border-radius: .9rem;
  background: white;
  margin-bottom: .75rem;
}
.fitflow-source {
  padding: .8rem;
  border-left: 4px solid #087f73;
  background: #edf8f5;
  border-radius: .5rem;
  margin-bottom: .5rem;
}
div.stButton > button[kind="primary"] {
  background: #087f73;
  border-color: #087f73;
}
</style>
"""


def apply_theme() -> None:
    st.markdown(THEME_CSS, unsafe_allow_html=True)
