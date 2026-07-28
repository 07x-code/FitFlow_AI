from pathlib import Path

from streamlit.testing.v1 import AppTest

from fitflow_ui.demo_state import STEPS


APP_PATH = Path(__file__).resolve().parents[1] / "streamlit_app.py"


def load_app() -> AppTest:
    app = AppTest.from_file(APP_PATH, default_timeout=10)
    app.session_state["api_base_url"] = "http://127.0.0.1:1"
    return app.run()


def test_streamlit_app_loads_without_backend():
    app = load_app()

    assert not app.exception
    assert app.title[0].value == "FitFlow AI"
    assert any("FastAPI" in item.value for item in app.warning)


def test_streamlit_app_has_six_step_navigation():
    app = load_app()

    step_radio = app.sidebar.radio(key="current_step")

    assert step_radio.options == list(STEPS)


def test_each_demo_step_renders_without_uncaught_exception():
    app = load_app()

    for step in STEPS:
        app.sidebar.radio(key="current_step").set_value(step)
        app.run()
        assert not app.exception
