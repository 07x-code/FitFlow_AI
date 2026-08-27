from app.domain.models.proposal import (
    ProposalStatus,
    can_transition_proposal_status,
)


def test_pending_proposal_allows_active_decisions() -> None:
    """
    验证待决定 Proposal 可以进入审批、拒绝或被修订替代状态。

    :return: 无返回值。
    """
    assert can_transition_proposal_status(
        ProposalStatus.PENDING,
        ProposalStatus.APPROVING,
    )
    assert can_transition_proposal_status(
        ProposalStatus.PENDING,
        ProposalStatus.REJECTED,
    )
    assert can_transition_proposal_status(
        ProposalStatus.PENDING,
        ProposalStatus.SUPERSEDED,
    )


def test_approving_proposal_only_allows_approval() -> None:
    """
    验证审批中的 Proposal 只能进入已批准状态。

    :return: 无返回值。
    """
    assert can_transition_proposal_status(
        ProposalStatus.APPROVING,
        ProposalStatus.APPROVED,
    )
    assert not can_transition_proposal_status(
        ProposalStatus.APPROVING,
        ProposalStatus.REJECTED,
    )


def test_terminal_proposal_statuses_reject_transitions() -> None:
    """
    验证终态 Proposal 不能继续发生状态转换。

    :return: 无返回值。
    """
    terminal_statuses = {
        ProposalStatus.APPROVED,
        ProposalStatus.REJECTED,
        ProposalStatus.SUPERSEDED,
    }

    for current in terminal_statuses:
        for target in ProposalStatus:
            assert not can_transition_proposal_status(current, target)


def test_pending_proposal_cannot_skip_approving_state() -> None:
    """
    验证待决定 Proposal 不能直接跳到已批准状态。

    :return: 无返回值。
    """
    assert not can_transition_proposal_status(
        ProposalStatus.PENDING,
        ProposalStatus.APPROVED,
    )