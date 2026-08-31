import {
  ArrowRight,
  CalendarDays,
  Clock3,
  Dumbbell,
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
  type TrainingPlanStatus,
} from '../api/client';
import { Button, Card, Chip, PageHeader } from '../components/ui';
import {
  translateDayName,
  translateExerciseName,
  translatePlanText,
} from '../utils/plan-labels';

const USER_ID = 'demo-user';

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
    return `读取训练计划失败，FastAPI 返回 ${error.status}。`;
  }

  return '无法连接 FastAPI，请确认后端已在 127.0.0.1:8000 启动。';
}

export function PlansPage() {
  const navigate = useNavigate();
  const [plans, setPlans] = useState<TrainingPlanHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadPlans = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fitFlowApi.listTrainingPlans(USER_ID);
      setPlans(response.plans);
    } catch (requestError) {
      setError(describeError(requestError));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadPlans();
  }, []);

  const currentPlan =
    plans.find((plan) => plan.status === 'active') ??
    plans.find((plan) => plan.status === 'scheduled') ??
    plans[0];

  return (
    <div className="page">
      <PageHeader
        action={
          <Button
            icon={currentPlan ? RefreshCw : Plus}
            onClick={
              currentPlan
                ? () => void loadPlans()
                : () => navigate('/app/coach')
            }
            variant="secondary">
            {currentPlan ? '刷新计划' : '制定计划'}
          </Button>
        }
        eyebrow="PostgreSQL 正式计划"
        title="训练计划"
      />

      {loading ? (
        <Card className="plan-state-card">
          <RefreshCw className="plan-state-card__spinner" size={24} />
          <div>
            <h2>正在读取训练计划</h2>
            <p>从 FastAPI 加载用户 {USER_ID} 的正式计划。</p>
          </div>
        </Card>
      ) : null}

      {error ? (
        <Card className="plan-state-card plan-state-card--error">
          <div>
            <h2>训练计划暂时不可用</h2>
            <p>{error}</p>
          </div>
          <Button icon={RefreshCw} onClick={() => void loadPlans()}>
            重试
          </Button>
        </Card>
      ) : null}

      {!loading && !error && !currentPlan ? (
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

      {currentPlan ? (
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
    </div>
  );
}
