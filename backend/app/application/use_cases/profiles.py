from dataclasses import dataclass

from app.application.errors import NotFoundError
from app.domain.models import FitnessProfileCreate, ProfileAssessmentResponse
from app.domain.nutrition_rules import calculate_nutrition_targets
from app.domain.risk_rules import assess_risk
from app.ports.repositories import ProfileRepositoryPort


@dataclass(frozen=True)
class ProfileUseCases:
    """用户健身画像应用用例。"""

    repository: ProfileRepositoryPort

    def create(
        self,
        user_id: str,
        profile: FitnessProfileCreate,
    ) -> ProfileAssessmentResponse:
        """
        保存用户画像并返回风险与营养评估。

        :param user_id: 用户标识。
        :param profile: 已校验的用户健身画像。
        :return: 用户画像评估结果。
        """
        self.repository.save(user_id, profile)
        return self._build_assessment(profile)

    def get(self, user_id: str) -> ProfileAssessmentResponse:
        """
        查询当前用户的画像评估。

        :param user_id: 用户标识。
        :return: 用户画像评估结果。
        """
        profile = self.repository.get(user_id)
        if profile is None:
            raise NotFoundError("Profile not found.")
        return self._build_assessment(profile)

    @staticmethod
    def _build_assessment(
        profile: FitnessProfileCreate,
    ) -> ProfileAssessmentResponse:
        return ProfileAssessmentResponse(
            profile=profile,
            risk=assess_risk(profile),
            nutrition=calculate_nutrition_targets(profile),
        )
