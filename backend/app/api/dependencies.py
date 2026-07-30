from app.application.use_cases import (
    CoachUseCases,
    MemoryUseCases,
    ProfileUseCases,
    ProposalUseCases,
    ReportUseCases,
    TrainingPlanUseCases,
    WorkoutUseCases,
)
from app.bootstrap.container import get_container


def get_profile_use_cases() -> ProfileUseCases:
    """
    获取用户画像应用用例。

    :return: 用户画像应用用例。
    """
    return get_container().profiles


def get_training_plan_use_cases() -> TrainingPlanUseCases:
    """
    获取训练计划应用用例。

    :return: 训练计划应用用例。
    """
    return get_container().training_plans


def get_memory_use_cases() -> MemoryUseCases:
    """
    获取用户记忆应用用例。

    :return: 用户记忆应用用例。
    """
    return get_container().memories


def get_coach_use_cases() -> CoachUseCases:
    """
    获取 AI 教练应用用例。

    :return: AI 教练应用用例。
    """
    return get_container().coach


def get_proposal_use_cases() -> ProposalUseCases:
    """
    获取训练计划提案应用用例。

    :return: 训练计划提案应用用例。
    """
    return get_container().proposals


def get_workout_use_cases() -> WorkoutUseCases:
    """
    获取训练记录应用用例。

    :return: 训练记录应用用例。
    """
    return get_container().workouts


def get_report_use_cases() -> ReportUseCases:
    """
    获取训练周报应用用例。

    :return: 训练周报应用用例。
    """
    return get_container().reports
