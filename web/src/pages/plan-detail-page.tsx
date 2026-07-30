import { ArrowRight, Dumbbell, Info, Play } from 'lucide-react';
import { Link, useParams } from 'react-router';

import { Card, Chip, PageHeader } from '../components/ui';
import { todayWorkout, weeklyPlans } from '../data/mock-data';

export function PlanDetailPage() {
  const { planId } = useParams();
  const plan = weeklyPlans.find((item) => item.id === planId) ?? todayWorkout;

  return (
    <div className="page page--narrow">
      <PageHeader
        action={<Chip tone="blue">目标 RPE 7</Chip>}
        back
        eyebrow="第 4 周 · 训练详情"
        title={plan.name}
      />

      <Card className="detail-summary">
        <span className="colored-icon">
          <Dumbbell size={23} />
        </span>
        <div>
          <h2>{plan.focus}</h2>
          <p>
            {plan.duration} 分钟 · 约 {plan.calories} kcal · {plan.exercises.length} 个动作
          </p>
        </div>
      </Card>

      <div className="info-banner">
        <Info size={19} />
        <span>先完成热身组。所有正式组保留约 3 次余力，不追求力竭。</span>
      </div>

      <div className="exercise-stack">
        {plan.exercises.map((exercise, index) => (
          <Link key={exercise.id} to={`/app/exercises/${exercise.id}`}>
            <Card className="exercise-row">
              <span className="exercise-order">{index + 1}</span>
              <span>
                <strong>{exercise.name}</strong>
                <small>
                  {exercise.sets} 组 × {exercise.reps} 次 · {exercise.target}
                </small>
              </span>
              <ArrowRight size={18} />
            </Card>
          </Link>
        ))}
      </div>

      <Link
        className="button button--primary button--full"
        to={`/app/workouts/${plan.id}`}>
        <Play aria-hidden="true" size={18} />
        <span>开始这次训练</span>
      </Link>
    </div>
  );
}
