from typing import Any

import streamlit as st

from fitflow_ui.api_client import FitFlowApiClient, FitFlowApiError
from fitflow_ui.components import render_proposal, show_api_error
from fitflow_ui.demo_state import save_decision, save_proposal


def render(client: FitFlowApiClient, state: Any) -> None:
    st.header("3. 人工确认")
    st.caption("只有批准后的 Proposal 才会生成正式训练计划。")

    try:
        proposals = client.list_proposals()["proposals"]
    except FitFlowApiError as error:
        show_api_error(error)
        return

    if not proposals:
        st.info("当前用户还没有 Proposal，请先完成第 2 步。")
        return

    proposal_by_label = {
        f"#{item['id']} · {item['status']} · {item['created_at']}": item
        for item in proposals
    }
    selected_label = st.selectbox("选择 Proposal", list(proposal_by_label))
    proposal = proposal_by_label[selected_label]
    save_proposal(state, proposal)
    render_proposal(proposal)

    if proposal["status"] != "pending":
        if proposal.get("approved_plan_id") is not None:
            state["approved_plan_id"] = proposal["approved_plan_id"]
            st.success(f"正式训练计划 ID：{proposal['approved_plan_id']}")
        else:
            st.warning("该 Proposal 已被拒绝。")
        return

    note = st.text_area("决策备注（可选）", max_chars=500)
    approve_col, reject_col = st.columns(2)
    if approve_col.button("批准并生成正式计划", type="primary"):
        _decide(client, state, proposal["id"], "approve", note)
    if reject_col.button("拒绝 Proposal"):
        _decide(client, state, proposal["id"], "reject", note)


def _decide(
    client: FitFlowApiClient,
    state: Any,
    proposal_id: int,
    decision: str,
    note: str,
) -> None:
    try:
        result = client.decide_proposal(
            proposal_id=proposal_id,
            decision=decision,
            decision_note=note,
        )
    except FitFlowApiError as error:
        show_api_error(error)
        return

    save_decision(state, result)
    if result["status"] == "approved":
        st.success(
            f"已批准，正式训练计划 ID：{result['approved_plan_id']}"
        )
    else:
        st.warning("Proposal 已拒绝，正式计划没有发生变化。")
