from typing import Any

import streamlit as st

from fitflow_ui.api_client import FitFlowApiClient, FitFlowApiError
from fitflow_ui.components import show_api_error
from fitflow_ui.demo_state import save_workout_result


def build_set_rows(
    plan_item: dict[str, Any],
    plan_day_index: int,
) -> list[dict[str, Any]]:
    days = plan_item.get("plan", {}).get("days", [])
    if plan_day_index < 1 or plan_day_index > len(days):
        return []

    rows = []
    for exercise in days[plan_day_index - 1]["exercises"]:
        for set_number in range(1, int(exercise["sets"]) + 1):
            row = {
                "exercise_name": exercise["exercise_name"],
                "set_number": set_number,
                "weight_kg": 0.0,
                "reps": int(exercise["reps_min"]),
                "rpe": float(exercise["target_rpe"]),
            }
            if exercise.get("exercise_id"):
                row["exercise_id"] = exercise["exercise_id"]
            rows.append(row)

    return rows


def normalize_set_rows(rows: Any) -> list[dict[str, Any]]:
    if hasattr(rows, "to_dict"):
        rows = rows.to_dict(orient="records")

    normalized = []
    for row in rows:
        exercise_name = str(row.get("exercise_name", "")).strip()
        if not exercise_name:
            continue

        workout_set = {
            "exercise_name": exercise_name,
            "set_number": int(row["set_number"]),
            "weight_kg": float(row["weight_kg"]),
            "reps": int(row["reps"]),
            "rpe": float(row["rpe"]),
        }
        exercise_id = row.get("exercise_id")
        if exercise_id:
            workout_set["exercise_id"] = str(exercise_id)
        normalized.append(workout_set)

    return normalized


def render(client: FitFlowApiClient, state: Any) -> None:
    st.header("4. 训练打卡")
    st.caption("选择正式计划中的训练日，记录每一组的重量、次数和 RPE。")

    try:
        plans = client.list_training_plans()["plans"]
    except FitFlowApiError as error:
        show_api_error(error)
        return

    if not plans:
        st.info("还没有正式计划，请先批准一个 Proposal。")
        return

    plan_labels = {
        f"计划 #{plan['id']} · {plan['created_at']}": plan
        for plan in plans
    }
    selected_plan_label = st.selectbox("正式训练计划", list(plan_labels))
    selected_plan = plan_labels[selected_plan_label]
    selected_plan_id = selected_plan["id"]
    state["approved_plan_id"] = selected_plan_id

    days = selected_plan["plan"]["days"]
    plan_day_index = st.selectbox(
        "本次训练日",
        options=list(range(1, len(days) + 1)),
        format_func=lambda index: f"第 {index} 天 · {days[index - 1]['name']}",
    )
    selected_day = days[plan_day_index - 1]
    st.caption(_build_day_summary(selected_day))

    completed = st.checkbox("本次训练已完成", value=True)
    fatigue = st.slider("疲劳程度", 1, 10, 6)
    pain = st.slider("疼痛程度", 0, 10, 0)
    notes = st.text_area("训练备注", max_chars=1000)
    default_rows = build_set_rows(selected_plan, plan_day_index)
    edited_rows = st.data_editor(
        default_rows,
        num_rows="fixed",
        disabled=["exercise_id", "exercise_name", "set_number"],
        use_container_width=True,
        key=f"workout-sets-editor-{selected_plan_id}-{plan_day_index}",
    )

    if st.button("提交训练记录", type="primary"):
        payload = {
            "plan_day_index": plan_day_index,
            "completed": completed,
            "fatigue_level": fatigue,
            "pain_level": pain,
            "notes": notes or None,
            "sets": normalize_set_rows(edited_rows),
        }

        try:
            result = client.create_workout_session(
                plan_id=selected_plan_id,
                payload=payload,
            )
        except FitFlowApiError as error:
            show_api_error(error)
        else:
            save_workout_result(state, result)
            st.success(
                f"训练记录 #{result['id']} 已保存：{result['plan_day_name']}。"
            )
            if result.get("safety_alert"):
                st.error(result["safety_alert"]["message"])

    _render_history(client, selected_plan_id)


def _build_day_summary(day: dict[str, Any]) -> str:
    prescriptions = [
        (
            f"{exercise['exercise_name']} "
            f"{exercise['sets']} 组 × {exercise['reps_min']}-{exercise['reps_max']} 次 "
            f"(RPE {exercise['target_rpe']})"
        )
        for exercise in day["exercises"]
    ]
    return "计划内容：" + "；".join(prescriptions)


def _render_history(client: FitFlowApiClient, plan_id: int) -> None:
    st.subheader("训练历史")
    try:
        sessions = client.list_workout_history(plan_id=plan_id)["sessions"]
    except FitFlowApiError as error:
        show_api_error(error)
        return

    if not sessions:
        st.info("这份计划还没有训练记录。")
        return

    for session in sessions[:10]:
        status = "已完成" if session["completed"] else "未完成"
        with st.expander(
            f"#{session['id']} · {session['plan_day_name']} · {status} · {session['created_at']}"
        ):
            st.write(
                f"疲劳 {session['fatigue_level']}/10，疼痛 {session['pain_level']}/10"
            )
            if session.get("notes"):
                st.write(session["notes"])
            st.dataframe(session["sets"], use_container_width=True)
