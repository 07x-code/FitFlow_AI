import { ArrowRight, Dumbbell, ShieldCheck } from 'lucide-react';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router';

import { FitFlowApiError, fitFlowApi } from '../api/client';
import { useAuth } from '../auth';
import { Button, Card, Chip, ProgressBar } from '../components/ui';

const goals = ['增肌', '减脂', '保持健康'];
const frequencies = ['每周 2 天', '每周 3 天', '每周 4 天'];
const goalValues = {
  增肌: 'muscle_gain',
  减脂: 'fat_loss',
  保持健康: 'general_fitness',
} as const;

export function ProfileSetupPage() {
  const [goal, setGoal] = useState('增肌');
  const [frequency, setFrequency] = useState('每周 3 天');
  const [sex, setSex] = useState<'male' | 'female'>('male');
  const [age, setAge] = useState('28');
  const [height, setHeight] = useState('175');
  const [weight, setWeight] = useState('70');
  const [minutes, setMinutes] = useState('60');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const { user } = useAuth();
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
        <Link className="text-link" to="/app">
          稍后设置
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
                <span>年龄</span>
                <span className="unit-field">
                  <input
                    max="80"
                    min="16"
                    inputMode="numeric"
                    onChange={(event) => setAge(event.target.value)}
                    onFocus={(event) => event.currentTarget.select()}
                    type="number"
                    value={age}
                  />
                  <em>岁</em>
                </span>
              </label>
              <label>
                <span>生理性别</span>
                <select
                  className="profile-select"
                  onChange={(event) => setSex(event.target.value as 'male' | 'female')}
                  value={sex}>
                  <option value="male">男</option>
                  <option value="female">女</option>
                </select>
              </label>
              <label>
                <span>身高</span>
                <span className="unit-field">
                  <input
                    max="230"
                    min="120"
                    inputMode="numeric"
                    onChange={(event) => setHeight(event.target.value)}
                    onFocus={(event) => event.currentTarget.select()}
                    type="number"
                    value={height}
                  />
                  <em>cm</em>
                </span>
              </label>
              <label>
                <span>体重</span>
                <span className="unit-field">
                  <input
                    max="250"
                    min="35"
                    inputMode="decimal"
                    onChange={(event) => setWeight(event.target.value)}
                    onFocus={(event) => event.currentTarget.select()}
                    step="0.1"
                    type="number"
                    value={weight}
                  />
                  <em>kg</em>
                </span>
              </label>
            </div>
          </div>

          <div className="form-section">
            <div><p className="eyebrow">04</p><h2>单次训练时长</h2></div>
            <label>
              <span className="unit-field">
                <input
                  max="120"
                  min="30"
                  inputMode="numeric"
                  onChange={(event) => setMinutes(event.target.value)}
                  onFocus={(event) => event.currentTarget.select()}
                  step="5"
                  type="number"
                  value={minutes}
                />
                <em>分钟</em>
              </span>
            </label>
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

          {error ? <p className="auth-form__error" role="alert">{error}</p> : null}
          <Button
            disabled={busy}
            fullWidth
            icon={ArrowRight}
            onClick={() => {
              setError('');
              if (!age || !height || !weight || !minutes) {
                setError('请完整填写年龄、身高、体重和单次训练时长。');
                return;
              }

              const ageValue = Number(age);
              const heightValue = Number(height);
              const weightValue = Number(weight);
              const minutesValue = Number(minutes);

              if (!Number.isInteger(ageValue) || ageValue < 16 || ageValue > 80) {
                setError('年龄应为 16 至 80 岁之间的整数。');
                return;
              }
              if (!Number.isInteger(heightValue) || heightValue < 120 || heightValue > 230) {
                setError('身高应为 120 至 230 厘米之间的整数。');
                return;
              }
              if (!Number.isFinite(weightValue) || weightValue < 35 || weightValue > 250) {
                setError('体重应在 35 至 250 千克之间。');
                return;
              }
              if (!Number.isInteger(minutesValue) || minutesValue < 30 || minutesValue > 120) {
                setError('单次训练时长应为 30 至 120 分钟之间的整数。');
                return;
              }

              setBusy(true);
              void fitFlowApi.createProfile({
                age: ageValue,
                sex,
                height_cm: heightValue,
                weight_kg: weightValue,
                goal: goalValues[goal as keyof typeof goalValues],
                sessions_per_week: Number(frequency.match(/\d/)?.[0] ?? 3),
                session_minutes: minutesValue,
                health_flags: [],
              })
                .then(() => navigate('/app/coach'))
                .catch((requestError: unknown) => {
                  setError(
                    requestError instanceof FitFlowApiError && typeof requestError.detail === 'string'
                      ? requestError.detail
                      : '画像保存失败，请检查输入后重试。',
                  );
                })
                .finally(() => setBusy(false));
            }}>
            {busy ? '正在保存…' : '保存并进入 AI 教练'}
          </Button>
          <p className="setup-account-note">当前账号：{user?.display_name}</p>
        </Card>
      </section>
    </main>
  );
}
