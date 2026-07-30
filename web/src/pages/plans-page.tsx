import { ArrowRight, CalendarDays, Check, Clock3, Dumbbell, Plus } from 'lucide-react';
import { Link } from 'react-router';

import { Button, Card, Chip, PageHeader, ProgressBar } from '../components/ui';
import { weeklyPlans } from '../data/mock-data';

export function PlansPage() {
  return (
    <div className="page">
      <PageHeader
        action={
          <Button icon={Plus} variant="secondary">
            新建计划
          </Button>
        }
        eyebrow="第 4 周"
        title="训练计划"
      />

      <Card className="plan-overview">
        <div>
          <span className="colored-icon">
            <CalendarDays size={21} />
          </span>
          <div>
            <p className="eyebrow">本周目标</p>
            <h2>3 次全身训练</h2>
            <p>侧重基础力量和动作稳定性</p>
          </div>
        </div>
        <div className="plan-overview__progress">
          <span>
            <strong>2 / 3</strong>
            已完成
          </span>
          <ProgressBar value={0.67} />
        </div>
      </Card>

      <div className="plans-layout">
        <section className="plan-timeline">
          {weeklyPlans.map((plan, index) => {
            const completed = index < 2;
            return (
              <article className={`timeline-item ${completed ? 'is-completed' : ''}`} key={plan.id}>
                <div className="timeline-marker">
                  {completed ? <Check size={17} /> : index + 1}
                </div>
                <Card className="plan-card">
                  <div className="plan-card__date">
                    <span>{index === 0 ? '周一' : index === 1 ? '周三' : '周五'}</span>
                    <small>{index === 0 ? '7 月 28 日' : index === 1 ? '今天' : '8 月 1 日'}</small>
                  </div>
                  <div className="plan-card__copy">
                    <div>
                      <h2>{plan.name}</h2>
                      <Chip tone={completed ? 'green' : 'default'}>
                        {completed ? '已完成' : '待训练'}
                      </Chip>
                    </div>
                    <p>{plan.focus}</p>
                    <span>
                      <Clock3 size={16} />
                      {plan.duration} 分钟
                      <Dumbbell size={16} />
                      {plan.exercises.length} 个动作
                    </span>
                  </div>
                  <Link aria-label={`查看${plan.name}`} className="round-link" to={`/app/plans/${plan.id}`}>
                    <ArrowRight size={19} />
                  </Link>
                </Card>
              </article>
            );
          })}
        </section>

        <aside>
          <Card className="plan-rule-card">
            <p className="eyebrow">计划逻辑</p>
            <h3>为什么这样安排？</h3>
            <p>
              结合每周 3 天训练频率和当前低风险画像，采用隔日全身训练，优先保证恢复与动作练习频率。
            </p>
            <Link to="/app/coach">
              让 AI 解释计划 <ArrowRight size={15} />
            </Link>
          </Card>
        </aside>
      </div>
    </div>
  );
}

