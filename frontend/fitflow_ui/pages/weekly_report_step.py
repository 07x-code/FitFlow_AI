from typing import Any

import streamlit as st

from fitflow_ui.api_client import FitFlowApiClient, FitFlowApiError
from fitflow_ui.components import render_proposal, show_api_error
from fitflow_ui.demo_state import save_weekly_report


def render(client: FitFlowApiClient, state: Any) -> None:
    st.header("5. 周报与计划调整")
    st.caption("周报只生成调整 Proposal，不会直接替换正式计划。")

    if st.button("生成本周训练报告", type="primary"):
        try:
            report = client.create_weekly_report()
        except FitFlowApiError as error:
            show_api_error(error)
        else:
            save_weekly_report(state, report)

    report = state.get("weekly_report")
    if report is None:
        st.info("完成至少一次训练打卡后生成周报。")
        return

    metrics = report["metrics"]
    col1, col2, col3 = st.columns(3)
    col1.metric("训练次数", metrics["session_count"])
    col2.metric("完成次数", metrics["completed_sessions"])
    col3.metric("完成率", f"{metrics['completion_rate']:.0%}")
    col4, col5, col6 = st.columns(3)
    col4.metric("平均 RPE", _metric_value(metrics["average_rpe"]))
    col5.metric("平均疲劳", _metric_value(metrics["average_fatigue"]))
    col6.metric("最高疼痛", _metric_value(metrics["max_pain"], default=0))
    st.info(report["recommendation"])

    proposal = report.get("adjustment_proposal")
    if proposal is not None:
        st.warning("系统生成了调整 Proposal，批准前不会改变正式计划。")
        render_proposal(proposal)


def _metric_value(value: Any, *, default: Any = "-") -> Any:
    return default if value is None else value
