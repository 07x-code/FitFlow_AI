from typing import Any

import streamlit as st

from fitflow_ui.api_client import FitFlowApiClient, FitFlowApiError
from fitflow_ui.components import render_proposal, show_api_error
from fitflow_ui.demo_state import save_proposal


def render(client: FitFlowApiClient, state: Any) -> None:
    st.header("2. 生成训练计划草案")
    st.caption("建议先成为 Proposal，不会直接修改正式训练计划。")

    if state.get("risk_level") == "blocked":
        st.error("当前画像被安全规则阻断，不能生成训练计划 Proposal。")
        return

    if st.button("生成安全训练计划 Proposal", type="primary"):
        try:
            proposal = client.create_training_plan_proposal()
        except FitFlowApiError as error:
            show_api_error(error)
        else:
            save_proposal(state, proposal)

    proposal = state.get("proposal_result")
    if proposal is None:
        st.info("请先完成用户画像，然后生成训练计划草案。")
        return

    render_proposal(proposal)
