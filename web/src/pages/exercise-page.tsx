import { ArrowLeft, Dumbbell, ShieldAlert, TrendingUp } from 'lucide-react';
import { useParams } from 'react-router';

import { Button, Card, Chip, PageHeader, SectionTitle } from '../components/ui';
import { todayWorkout } from '../data/mock-data';

const historyValues = [42, 54, 48, 66, 74, 83];

export function ExercisePage() {
  const { exerciseId } = useParams();
  const exercise =
    todayWorkout.exercises.find((item) => item.id === exerciseId) ??
    todayWorkout.exercises[0];

  return (
    <div className="page page--narrow">
      <PageHeader back eyebrow={exercise.target} title={exercise.name} />

      <div className="exercise-visual">
        <span>
          <Dumbbell size={48} strokeWidth={1.7} />
        </span>
        <div>
          <Chip tone="blue">{exercise.muscle}</Chip>
          <Chip>器械训练</Chip>
          <Chip tone="green">初学者友好</Chip>
        </div>
      </div>

      <div className="two-column-metrics">
        <Card>
          <span>个人最佳</span>
          <strong>{exercise.lastWeight + 5} kg</strong>
        </Card>
        <Card>
          <span>上次完成</span>
          <strong>{exercise.lastWeight} × 10</strong>
        </Card>
      </div>

      <SectionTitle>动作要点</SectionTitle>
      <Card className="steps-card">
        {[
          '调整起始位置，让关节处于自然稳定状态。',
          '控制离心阶段，保持核心收紧和均匀呼吸。',
          '动作幅度以稳定无痛为准，不用追求极限。',
        ].map((step, index) => (
          <div className="step-row" key={step}>
            <span>{index + 1}</span>
            <p>{step}</p>
          </div>
        ))}
      </Card>

      <SectionTitle>重量趋势</SectionTitle>
      <Card className="trend-card">
        <div>
          <span>
            <strong>+12.5%</strong>
            <small>最近 6 次训练</small>
          </span>
          <TrendingUp size={22} />
        </div>
        <div className="bar-chart">
          {historyValues.map((value, index) => (
            <span
              aria-label={`第${index + 1}次训练水平${value}%`}
              key={`${value}-${index}`}>
              <i style={{ height: `${value}%` }} />
            </span>
          ))}
        </div>
      </Card>

      <div className="safety-banner">
        <ShieldAlert size={20} />
        <span>如果动作过程中出现锐痛、关节疼痛或明显不适，请立即停止。</span>
      </div>

      <Button fullWidth icon={ArrowLeft} onClick={() => window.history.back()} variant="secondary">
        返回训练
      </Button>
    </div>
  );
}
