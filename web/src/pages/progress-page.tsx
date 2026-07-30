import { ArrowUpRight, Dumbbell, Flame, Gauge, TrendingUp } from 'lucide-react';
import { useState } from 'react';

import { Card, Chip, PageHeader, SectionTitle } from '../components/ui';
import { progressPoints, recentWorkouts } from '../data/mock-data';

const labels = ['一', '二', '三', '四', '五', '六', '日'];
const qualityItems = [
  { label: '计划完成率', value: '86%', width: '86%', color: 'var(--primary)' },
  { label: '平均 RPE', value: '7.1', width: '71%', color: 'var(--blue)' },
  { label: '恢复状态', value: '良好', width: '82%', color: 'var(--orange)' },
] as const;

export function ProgressPage() {
  const [range, setRange] = useState('4 周');

  return (
    <div className="page">
      <PageHeader eyebrow="训练数据" title="进度报告" />

      <div className="range-tabs">
        {['本周', '4 周', '12 周'].map((item) => (
          <Chip active={range === item} key={item} onClick={() => setRange(item)}>
            {item}
          </Chip>
        ))}
      </div>

      <div className="report-metrics">
        <Card>
          <span className="colored-icon colored-icon--blue">
            <Dumbbell size={20} />
          </span>
          <strong>12</strong>
          <small>完成训练</small>
          <em>
            <ArrowUpRight size={14} /> 20%
          </em>
        </Card>
        <Card>
          <span className="colored-icon colored-icon--orange">
            <Flame size={20} />
          </span>
          <strong>18.6t</strong>
          <small>总训练量</small>
          <em>
            <ArrowUpRight size={14} /> 8.4%
          </em>
        </Card>
        <Card>
          <span className="colored-icon">
            <Gauge size={20} />
          </span>
          <strong>7.1</strong>
          <small>平均 RPE</small>
          <em>稳定区间</em>
        </Card>
      </div>

      <div className="report-layout">
        <section>
          <SectionTitle>训练量趋势</SectionTitle>
          <Card className="report-chart">
            <div className="report-chart__head">
              <span>
                <small>本周总训练量</small>
                <strong>7,280 kg</strong>
              </span>
              <Chip tone="blue">
                <TrendingUp size={14} /> 稳定增长
              </Chip>
            </div>
            <div className="chart-bars">
              {progressPoints.map((point, index) => (
                <span key={labels[index]}>
                  <i style={{ height: `${point}%` }} />
                  <small>{labels[index]}</small>
                </span>
              ))}
            </div>
          </Card>
        </section>

        <section>
          <SectionTitle>训练质量</SectionTitle>
          <Card className="quality-card">
            {qualityItems.map((item) => (
              <div className="quality-item" key={item.label}>
                <span>
                  <strong>{item.label}</strong>
                  <small>{item.value}</small>
                </span>
                <div>
                  <i style={{ background: item.color, width: item.width }} />
                </div>
              </div>
            ))}
          </Card>
        </section>
      </div>

      <SectionTitle>最近记录</SectionTitle>
      <Card className="history-list">
        {recentWorkouts.map((workout) => (
          <div className="history-row" key={workout.title}>
            <i />
            <span>
              <strong>{workout.title}</strong>
              <small>
                {workout.date} · {workout.duration}
              </small>
            </span>
            <b>{workout.volume}</b>
          </div>
        ))}
      </Card>
    </div>
  );
}

