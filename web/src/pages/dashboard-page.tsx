import {
  ArrowRight,
  Bell,
  CalendarDays,
  Check,
  Clock3,
  Dumbbell,
  Flame,
  Play,
  ShieldCheck,
  Sparkles,
  TrendingUp,
} from 'lucide-react';
import { Link } from 'react-router';

import { Card, Chip, PageHeader, ProgressBar, SectionTitle } from '../components/ui';
import { recentWorkouts, todayWorkout, weekDays } from '../data/mock-data';

export function DashboardPage() {
  return (
    <div className="page page--dashboard">
      <PageHeader
        action={
          <button aria-label="通知" className="icon-button notification-button" type="button">
            <Bell size={20} />
            <span />
          </button>
        }
        eyebrow="7 月 30 日 · 星期三"
        title="晚上好，Alex"
      />

      <div className="dashboard-grid">
        <section className="dashboard-main">
          <div className="week-strip">
            {weekDays.map((item) => (
              <div className="week-day" key={`${item.day}-${item.date}`}>
                <span>{item.day}</span>
                <b className={`week-day__date is-${item.state}`}>
                  {item.state === 'done' ? <Check size={17} /> : item.date}
                </b>
              </div>
            ))}
          </div>

          <Card className="workout-hero" as="article">
            <div className="workout-hero__glow" />
            <div className="workout-hero__top">
              <div>
                <p className="eyebrow">今日训练</p>
                <h2>{todayWorkout.name}</h2>
                <p>{todayWorkout.focus}</p>
              </div>
              <div className="readiness-gauge">
                <strong>86</strong>
                <span>准备度</span>
              </div>
            </div>
            <div className="inline-stats">
              <span>
                <Clock3 size={17} />
                {todayWorkout.duration} 分钟
              </span>
              <span>
                <Dumbbell size={17} />
                {todayWorkout.exercises.length} 个动作
              </span>
              <span>
                <Flame size={17} />
                {todayWorkout.calories} kcal
              </span>
            </div>
            <Link
              className="button button--primary button--full"
              to={`/app/workouts/${todayWorkout.id}`}>
              <Play aria-hidden="true" size={18} />
              <span>开始训练</span>
            </Link>
          </Card>

          <SectionTitle
            action={
              <Link className="section-link" to="/app/progress">
                查看报告 <ArrowRight size={15} />
              </Link>
            }>
            本周节奏
          </SectionTitle>
          <Card className="weekly-card">
            <div className="weekly-card__head">
              <div>
                <strong>2 / 3 次</strong>
                <p>再完成一次，达成本周目标</p>
              </div>
              <Chip tone="blue">连续 4 周</Chip>
            </div>
            <ProgressBar value={0.67} />
            <div className="metric-row">
              <span>
                <strong>103</strong>
                <small>训练分钟</small>
              </span>
              <span>
                <strong>7,280 kg</strong>
                <small>总训练量</small>
              </span>
              <span>
                <strong>RPE 7.1</strong>
                <small>平均强度</small>
              </span>
            </div>
          </Card>

          <SectionTitle
            action={
              <Link className="section-link" to="/app/progress">
                全部记录 <ArrowRight size={15} />
              </Link>
            }>
            最近训练
          </SectionTitle>
          <div className="recent-list">
            {recentWorkouts.map((workout) => (
              <Card className="recent-row" key={workout.title}>
                <span className="colored-icon colored-icon--blue">
                  <Dumbbell size={19} />
                </span>
                <span className="recent-row__copy">
                  <strong>{workout.title}</strong>
                  <small>
                    {workout.date} · {workout.duration}
                  </small>
                </span>
                <span className="recent-row__volume">{workout.volume}</span>
              </Card>
            ))}
          </div>
        </section>

        <aside className="dashboard-aside">
          <Card className="coach-card">
            <div className="coach-card__icon">
              <Sparkles size={22} />
            </div>
            <p className="eyebrow">AI COACH 提示</p>
            <h3>今天状态不错</h3>
            <p>
              保持计划重量。如果前两组 RPE 低于 7，最后一组可以增加 2.5 kg。
            </p>
            <Link to="/app/coach">
              问问 AI Coach <ArrowRight size={15} />
            </Link>
          </Card>

          <Card className="safety-card">
            <span className="colored-icon colored-icon--orange">
              <ShieldCheck size={20} />
            </span>
            <div>
              <strong>安全规则已启用</strong>
              <p>低风险 · 训练计划校验通过</p>
            </div>
          </Card>

          <Card className="next-card">
            <div className="next-card__head">
              <CalendarDays size={20} />
              <span>下次训练</span>
            </div>
            <strong>全身训练 B</strong>
            <p>周五 · 肩、腿与核心</p>
            <span>
              <TrendingUp size={16} />
              预计 52 分钟
            </span>
          </Card>
        </aside>
      </div>
    </div>
  );
}

