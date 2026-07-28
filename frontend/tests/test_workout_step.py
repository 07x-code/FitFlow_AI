from fitflow_ui.pages.workout_step import build_set_rows, normalize_set_rows


def plan_item() -> dict:
    return {
        "id": 12,
        "plan": {
            "days": [
                {
                    "name": "Day 1 - Full Body A",
                    "exercises": [
                        {
                            "exercise_id": "exercise-0001",
                            "exercise_name": "Goblet Squat",
                            "sets": 3,
                            "reps_min": 8,
                            "reps_max": 12,
                            "target_rpe": 7,
                        },
                        {
                            "exercise_name": "Chest Press",
                            "sets": 2,
                            "reps_min": 10,
                            "reps_max": 12,
                            "target_rpe": 6,
                        },
                    ],
                }
            ]
        },
    }


def test_build_set_rows_expands_plan_prescriptions_into_editable_sets():
    rows = build_set_rows(plan_item(), plan_day_index=1)

    assert len(rows) == 5
    assert rows[0] == {
        "exercise_id": "exercise-0001",
        "exercise_name": "Goblet Squat",
        "set_number": 1,
        "weight_kg": 0.0,
        "reps": 8,
        "rpe": 7.0,
    }
    assert rows[3]["exercise_name"] == "Chest Press"
    assert rows[3]["set_number"] == 1


def test_build_set_rows_returns_empty_list_for_unknown_day():
    assert build_set_rows(plan_item(), plan_day_index=2) == []


def test_normalize_set_rows_preserves_catalog_id_and_numeric_types():
    rows = [
        {
            "exercise_id": "exercise-0001",
            "exercise_name": "Goblet Squat",
            "set_number": 1.0,
            "weight_kg": 12,
            "reps": 10.0,
            "rpe": 7,
        }
    ]

    assert normalize_set_rows(rows) == [
        {
            "exercise_id": "exercise-0001",
            "exercise_name": "Goblet Squat",
            "set_number": 1,
            "weight_kg": 12.0,
            "reps": 10,
            "rpe": 7.0,
        }
    ]
