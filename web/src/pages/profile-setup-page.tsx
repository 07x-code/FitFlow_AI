import { ArrowRight, Dumbbell, ShieldCheck } from 'lucide-react';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router';

import { Button, Card, Chip, ProgressBar } from '../components/ui';

const goals = ['增肌', '减脂', '保持健康'];
const frequencies = ['每周 2 天', '每周 3 天', '每周 4 天'];

export function ProfileSetupPage() {
  const [goal, setGoal] = useState('增肌');
  const [frequency, setFrequency] = useState('每周 3 天');
  const navigate = useNavigate();

  return (
    <main className="setup-page">
      <header className="setup-topbar">
        <Link className="brand" to="/">
          <span className="brand__mark">
            <Dumbbell size={20} />
          </span>
          <span>
            <strong>FitFlow</strong>
            <small>智能教练</small>
          </span>
        </Link>
        <Link className="text-link" to="/">
          返回登录
        </Link>
      </header>

      <section className="setup-layout">
        <div className="setup-intro">
          <p className="eyebrow">训练画像 · 1 / 2</p>
          <h1>先了解你的目标</h1>
          <p>这些信息用于安全规则校验、训练计划生成和后续反馈调整。</p>
          <div className="setup-progress">
            <span>基础信息</span>
            <ProgressBar value={0.5} />
          </div>
          <ul className="setup-points">
            <li>
              <ShieldCheck size={19} />
              健康风险由后端规则优先判断
            </li>
            <li>
              <ArrowRight size={19} />
              画像会参与训练计划和 AI 教练上下文
            </li>
          </ul>
        </div>

        <Card className="setup-form" as="section">
          <div className="form-section">
            <div>
              <p className="eyebrow">01</p>
              <h2>主要目标</h2>
            </div>
            <div className="chip-group">
              {goals.map((item) => (
                <Chip
                  active={goal === item}
                  key={item}
                  onClick={() => setGoal(item)}>
                  {item}
                </Chip>
              ))}
            </div>
          </div>

          <div className="form-section">
            <div>
              <p className="eyebrow">02</p>
              <h2>身体数据</h2>
            </div>
            <div className="form-grid">
              <label>
                <span>身高</span>
                <span className="unit-field">
                  <input defaultValue="175" inputMode="numeric" />
                  <em>cm</em>
                </span>
              </label>
              <label>
                <span>体重</span>
                <span className="unit-field">
                  <input defaultValue="70" inputMode="numeric" />
                  <em>kg</em>
                </span>
              </label>
            </div>
          </div>

          <div className="form-section">
            <div>
              <p className="eyebrow">03</p>
              <h2>训练频率</h2>
            </div>
            <div className="chip-group">
              {frequencies.map((item) => (
                <Chip
                  active={frequency === item}
                  key={item}
                  onClick={() => setFrequency(item)}>
                  {item}
                </Chip>
              ))}
            </div>
          </div>

          <button className="health-field" type="button">
            <span className="health-field__icon">
              <ShieldCheck size={21} />
            </span>
            <span>
              <strong>健康与伤病情况</strong>
              <small>当前未选择风险项</small>
            </span>
            <ArrowRight size={19} />
          </button>

          <Button
            fullWidth
            icon={ArrowRight}
            onClick={() => navigate('/app')}>
            保存并生成计划
          </Button>
        </Card>
      </section>
    </main>
  );
}
