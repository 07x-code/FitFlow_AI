import {
  ArrowRight,
  CalendarDays,
  Clock3,
  Dumbbell,
  FilePenLine,
  ListChecks,
  Plus,
  RefreshCw,
  ShieldCheck,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router';

import {
  FitFlowApiError,
  fitFlowApi,
  type TrainingPlanHistoryItem,
  type TrainingPlanProposalResponse,
  type TrainingPlanStatus,
  type WorkoutSessionResponse,
} from '../api/client';
import { TrainingCalendar } from '../components/training-calendar';
import { PlanEditor } from '../components/plan-editor';
import { Button, Card, Chip, PageHeader } from '../components/ui';
import {
  translateDayName,
  translateExerciseName,
  translatePlanText,
} from '../utils/plan-labels';

type EditingTarget = {
  planId: number;
  dayIndex?: number;
};

const statusLabels: Record<TrainingPlanStatus, string> = {
  scheduled: '待开始',
  active: '进行中',
  superseded: '已替换',
  completed: '已完成',
};

function formatDate(value: string) {
  return new Intl.DateTimeFormat('zh-CN', {
    month: 'long',
    day: 'numeric',
    weekday: 'short',
  }).format(new Date(`${value}T00:00:00`));
}

function describeError(error: unknown) {
  if (error instanceof FitFlowApiError) {
    return `读取训练数据失败，FastAPI 返回 ${error.status}。`;
  }

  return '无法连接 FastAPI，请确认后端已在 127.0.0.1:8000 启动。';
}

export function PlansPage() {
  const navigate = useNavigate();
  const [plans, setPlans] = useState<TrainingPlanHistoryItem[]>([]);
  const [proposals, setProposals] = useState<TrainingPlanProposalResponse[]>([]);
  const [sessions, setSessions] = useState<WorkoutSessionResponse[]>([]);
  const [editingTarget, setEditingTarget] = useState<EditingTarget | null>(null);
  const [activeView, setActiveView] = useState<'plan' | 'calendar'>('plan');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadTrainingData = async () => {
    setLoading(true);
    setError(null);

    try {
      const [planResponse, workoutResponse, proposalResponse] = await Promise.all([
        fitFlowApi.listTrainingPlans(),
        fitFlowApi.listWorkoutHistory(),
        fitFlowApi.listTrainingPlanProposals(),
      ]);
      setPlans(planResponse.plans);
      setSessions(workoutResponse.sessions);
      setProposals(proposalResponse.proposals);
    } catch (requestError) {
      setError(describeError(requestError));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadTrainingData();
  }, []);

  const currentPlan =
    plans.find((plan) => plan.status === 'active') ??
    plans.find((plan) => plan.status === 'scheduled') ??
    plans[0];
  const pendingReplacement = currentPlan
    ? proposals.find(
        (proposal) =>
          proposal.status === 'pending' &&
          proposal.operation === 'replace' &&
          proposal.base_plan_id === currentPlan.id,
      )
    : undefined;
  const editingPlan = editingTarget
    ? plans.find((plan) => plan.id === editingTarget.planId)
    : undefined;
  const editingProposal = editingPlan
    ? proposals.find(
        (proposal) =>
          proposal.status === 'pending' &&
          proposal.operation === 'replace' &&
          proposal.base_plan_id === editingPlan.id,
      )
    : undefined;

  return (
    <div className="page">
      <PageHeader
        action={
          <Button
            icon={activeView === 'calendar' || currentPlan ? RefreshCw : Plus}
            onClick={
              activeView === 'calendar' || currentPlan
                ? () => void loadTrainingData()
                : () => navigate('/app/coach')
            }
            variant="secondary">
            {activeView === 'calendar' || currentPlan
              ? '刷新数据'
              : '制定计划'}
          </Button>
        }
        eyebrow="计划与训练记录"
        title="训练"
      />

      <div aria-label="训练页面视图" className="training-view-tabs" role="tablist">
        <button
          aria-selected={activeView === 'plan'}
          className={activeView === 'plan' ? 'is-active' : ''}
          onClick={() => setActiveView('plan')}
          role="tab"
          type="button">
          <ListChecks size={17} />
          当前计划
        </button>
        <button
          aria-selected={activeView === 'calendar'}
          className={activeView === 'calendar' ? 'is-active' : ''}
          onClick={() => setActiveView('calendar')}
          role="tab"
          type="button">
          <CalendarDays size={17} />
          训练日历
        </button>
      </div>

      {loading ? (
        <Card className="plan-state-card">
          <RefreshCw className="plan-state-card__spinner" size={24} />
          <div>
            <h2>正在读取训练计划</h2>
            <p>正在从 FastAPI 加载当前账号的正式计划。</p>
          </div>
        </Card>
      ) : null}

      {error ? (
        <Card className="plan-state-card plan-state-card--error">
          <div>
            <h2>训练计划暂时不可用</h2>
            <p>{error}</p>
          </div>
          <Button icon={RefreshCw} onClick={() => void loadTrainingData()}>
            重试
          </Button>
        </Card>
      ) : null}

      {!loading && !error && activeView === 'plan' && !currentPlan ? (
        <Card className="plan-empty-card">
          <span className="colored-icon">
            <CalendarDays size={22} />
          </span>
          <h2>还没有正式训练计划</h2>
          <p>先让 AI 教练生成提案；只有你确认后，计划才会同步到这里。</p>
          <Button icon={Plus} onClick={() => navigate('/app/coach')}>
            前往 AI 教练
          </Button>
        </Card>
      ) : null}

      {activeView === 'plan' && currentPlan ? (
        <>
          <Card className="plan-overview">
            <div>
              <span className="colored-icon">
                <CalendarDays size={21} />
              </span>
              <div>
                <p className="eyebrow">
                  {currentPlan.plan.week_start} 至 {currentPlan.plan.week_end}
                </p>
                <h2>{translatePlanText(currentPlan.plan.goal_summary)}</h2>
                <p>
                  版本 {currentPlan.version} · 来源提案 #{currentPlan.source_proposal_id}
                </p>
              </div>
            </div>
            <div className="plan-overview__facts">
              <span>
                <strong>{currentPlan.plan.days.length}</strong>
                训练日
              </span>
              <Chip
                tone={currentPlan.status === 'completed' ? 'green' : 'blue'}>
                {statusLabels[currentPlan.status]}
              </Chip>
              {currentPlan.status === 'active' ||
              currentPlan.status === 'scheduled' ? (
                <Button
                  icon={pendingReplacement ? ShieldCheck : FilePenLine}
                  onClick={() =>
                    setEditingTarget({ planId: currentPlan.id })
                  }
                  variant={pendingReplacement ? 'primary' : 'secondary'}>
                  {pendingReplacement ? '确认修改' : '编辑计划'}
                </Button>
              ) : null}
            </div>
          </Card>

          <div className="plans-layout">
            <section className="plan-timeline">
              {currentPlan.plan.days.map((day, index) => (
                <article className="timeline-item" key={day.scheduled_date}>
                  <div className="timeline-marker">{index + 1}</div>
                  <Card className="plan-card">
                    <div className="plan-card__date">
                      <span>{formatDate(day.scheduled_date)}</span>
                      <small>{day.scheduled_date}</small>
                    </div>
                    <div className="plan-card__copy">
                      <div>
                        <h2>{translateDayName(day.name)}</h2>
                        <Chip>{day.focus}</Chip>
                      </div>
                      <p>
                        {day.exercises
                          .map((exercise) =>
                            translateExerciseName(exercise.exercise_name),
                          )
                          .join('、')}
                      </p>
                      <span>
                        <Clock3 size={16} />
                        {day.estimated_minutes} 分钟
                        <Dumbbell size={16} />
                        {day.exercises.length} 个动作
                      </span>
                    </div>
                  </Card>
                </article>
              ))}
            </section>

            <aside className="plan-sidebar">
              <Card className="plan-rule-card">
                <ShieldCheck size={20} />
                <p className="eyebrow">安全校验</p>
                <h3>
                  {currentPlan.safety_check.valid
                    ? '该计划已通过规则检查'
                    : '该计划包含安全提示'}
                </h3>
                <p>{translatePlanText(currentPlan.plan.goal_summary)}</p>
                <Link to="/app/coach">
                  让 AI 解释计划 <ArrowRight size={15} />
                </Link>
              </Card>

              {plans.length > 1 ? (
                <Card className="plan-history-card">
                  <p className="eyebrow">计划历史</p>
                  {plans.map((plan) => (
                    <div key={plan.id}>
                      <span>版本 {plan.version}</span>
                      <Chip>{statusLabels[plan.status]}</Chip>
                    </div>
                  ))}
                </Card>
              ) : null}
            </aside>
          </div>
        </>
      ) : null}

      {!loading && !error && activeView === 'calendar' ? (
        <TrainingCalendar
          onEditPlannedWorkout={(planId, dayIndex) =>
            setEditingTarget({ planId, dayIndex })
          }
          plans={plans}
          sessions={sessions}
        />
      ) : null}

      {editingTarget && editingPlan ? (
        <PlanEditor
          initialDayIndex={editingTarget.dayIndex}
          onChanged={() => void loadTrainingData()}
          onClose={() => setEditingTarget(null)}
          pendingProposal={editingProposal}
          plan={editingPlan}
        />
      ) : null}
    </div>
  );
}
