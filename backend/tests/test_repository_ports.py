from inspect import iscoroutinefunction, signature

from app.ports.repositories import (
    ProfileRepositoryPort,
    TrainingPlanRepositoryPort,
    UserRepositoryPort,
    UserMemoryRepositoryPort,
    TrainingPlanProposalRepositoryPort,
    WorkoutSessionRepositoryPort,
)


def test_user_repository_port_matches_async_contract() -> None:
    """
    验证用户账号仓储端口提供完整的异步接口。

    :return: 无返回值。
    """
    method_names = (
        "create",
        "get_by_id",
        "get_by_email",
        "get_authentication_by_email",
        "mark_login",
        "disable",
    )

    assert all(
        iscoroutinefunction(getattr(UserRepositoryPort, method_name))
        for method_name in method_names
    )


def test_training_plan_repository_port_matches_async_contract() -> None:
    """
    验证正式训练计划仓储端口使用异步方法和完整保存参数。

    :return: 无返回值。
    """
    assert iscoroutinefunction(TrainingPlanRepositoryPort.save)
    assert iscoroutinefunction(
        TrainingPlanRepositoryPort.list_by_user
    )
    assert iscoroutinefunction(
        TrainingPlanRepositoryPort.get_by_id_for_user
    )

    save_parameters = signature(
        TrainingPlanRepositoryPort.save
    ).parameters

    assert "source_proposal_id" in save_parameters
    assert "version" in save_parameters
    assert iscoroutinefunction(
    TrainingPlanRepositoryPort.mark_superseded
    )





def test_profile_repository_port_matches_async_contract() -> None:
    """
    验证用户画像仓储端口使用异步方法。

    :return: 无返回值。
    """
    assert iscoroutinefunction(ProfileRepositoryPort.save)
    assert iscoroutinefunction(ProfileRepositoryPort.get)


def test_user_memory_repository_port_matches_async_contract() -> None:
    """
    验证长期记忆仓储端口使用异步方法。

    :return: 无返回值。
    """
    assert iscoroutinefunction(UserMemoryRepositoryPort.create)
    assert iscoroutinefunction(
        UserMemoryRepositoryPort.list_by_user
    )
    assert iscoroutinefunction(
        UserMemoryRepositoryPort.delete_by_id_for_user
    )


def test_proposal_repository_port_matches_async_contract() -> None:
    """
    验证训练计划 Proposal 仓储端口使用完整的异步接口。

    :return: 无返回值。
    """
    method_names = (
        "create",
        "list_by_user",
        "get_by_id_for_user",
        "mark_approving",
        "approve",
        "reject",
        "create_revision",
        "create_replacement",
    )

    assert all(
        iscoroutinefunction(
            getattr(TrainingPlanProposalRepositoryPort, method_name)
        )
        for method_name in method_names
    )


def test_workout_repository_port_matches_async_contract() -> None:
    """
    验证训练记录仓储端口使用完整的异步接口。

    :return: 无返回值。
    """
    method_names = (
        "save",
        "list_by_user",
        "list_by_user_in_period",
    )

    assert all(
        iscoroutinefunction(
            getattr(WorkoutSessionRepositoryPort, method_name)
        )
        for method_name in method_names
    )
