# LangGraph Training Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a LangGraph workflow that orchestrates profile loading, risk assessment, plan generation, safety validation, and plan persistence.

**Architecture:** Keep existing domain rules unchanged. Add a workflow layer that composes repositories and domain functions, then make the FastAPI draft endpoint call the workflow instead of manually chaining each function.

**Tech Stack:** Python 3.11, FastAPI, Pydantic, SQLite repositories, LangGraph `StateGraph`, pytest.

---

### Task 1: Workflow Behavior Tests

**Files:**
- Create: `tests/test_training_plan_workflow.py`
- Create: `app/workflows/training_plan_workflow.py`
- Modify: `app/api/training_plans.py`

- [x] **Step 1: Write the failing test**

Add tests that expect `create_training_plan_workflow()` to generate and save a safe beginner plan, and to block a risky profile without saving history.

- [x] **Step 2: Run test to verify it fails**

Run: `F:\Anaconda\envs\fitflow\python.exe -m pytest tests\test_training_plan_workflow.py -v`

Expected: fails because `app.workflows.training_plan_workflow` does not exist yet.

- [x] **Step 3: Install LangGraph**

Run: `F:\Anaconda\envs\fitflow\python.exe -m pip install langgraph`

Expected: package installs into the `fitflow` conda environment.

- [x] **Step 4: Write minimal workflow implementation**

Create `TrainingPlanWorkflow` backed by `StateGraph`. It returns a result object with `status_code`, `response`, and `error_detail`.

- [x] **Step 5: Connect API endpoint**

Update `POST /api/training-plans/draft` to call `training_plan_workflow.run(user_id)` and map workflow errors to `HTTPException`.

- [x] **Step 6: Verify**

Run: `F:\Anaconda\envs\fitflow\python.exe -m pytest -v`

Expected: all tests pass.
