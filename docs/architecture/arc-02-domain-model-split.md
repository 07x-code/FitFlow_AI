# ARC-02：领域模型拆分

状态：已完成  
完成日期：2026-07-30

## 目标

将原来的 `backend/app/domain/models.py` 拆成按业务职责组织的模型模块，避免所有领域对象集中在一个文件中。

## 当前结构

```text
backend/app/domain/models/
├── __init__.py    # 兼容导出入口
├── profile.py     # 用户画像、风险、营养目标
├── plan.py        # 动作处方、训练日、训练计划、安全检查
├── proposal.py    # 提案类型、状态、决策和响应
├── workout.py     # 训练组、训练记录和安全提醒
├── memory.py      # 长期记忆类型、输入和响应
├── report.py      # 周报指标和周报响应
└── coach.py       # AI 教练对话和知识来源
```

## 模型归属

| 模块 | 主要模型 |
|---|---|
| `profile.py` | `FitnessProfileCreate`、`RiskAssessment`、`NutritionTargets` |
| `plan.py` | `TrainingPlanDraft`、`SafetyCheckResult`、`TrainingPlanHistoryItem` |
| `proposal.py` | `ProposalDecisionRequest`、`TrainingPlanProposalResponse` |
| `workout.py` | `WorkoutSessionCreate`、`WorkoutSessionResponse` |
| `memory.py` | `UserMemoryCreate`、`UserMemoryResponse` |
| `report.py` | `WeeklyReportMetrics`、`WeeklyReportResponse` |
| `coach.py` | `CoachChatRequest`、`CoachChatResponse`、`FitnessKnowledgeItem` |

## 依赖规则

- `profile.py`、`plan.py`、`workout.py`、`memory.py`、`coach.py` 是叶子模型模块，不依赖其他模型组。
- `proposal.py` 可以依赖 `plan.py`，因为提案携带训练计划和安全检查结果。
- `report.py` 可以依赖 `proposal.py`，因为周报可能返回调整提案。
- 业务代码新增加的导入优先指向具体模块。
- `models/__init__.py` 只用于兼容旧的 `from app.domain.models import ...` 导入。

## 兼容策略

本次拆分没有修改模型名称、字段、校验范围和序列化结构。旧导入路径继续可用：

```python
from app.domain.models import FitnessProfileCreate
```

新代码推荐使用：

```python
from app.domain.models.profile import FitnessProfileCreate
```

## 验收

- 原 `domain/models.py` 已删除。
- 七个领域模型模块独立存在。
- 兼容导出与具体模块中的类对象一致。
- 叶子模型模块依赖方向测试通过。
- 前后端完整回归测试通过。
