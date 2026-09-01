import {
  ArrowRight,
  CheckCircle2,
  Dumbbell,
  LockKeyhole,
  Mail,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';
import { useState } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router';

import { FitFlowApiError } from '../api/client';
import { useAuth } from '../auth';
import { Button } from '../components/ui';

export function LoginPage() {
  const { user, loading, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  if (!loading && user !== null) {
    return <Navigate replace to="/app" />;
  }

  return (
    <main className="auth-page">
      <section className="auth-visual">
        <Link className="brand brand--large" to="/">
          <span className="brand__mark">
            <Dumbbell aria-hidden="true" size={22} />
          </span>
          <span>
            <strong>FitFlow</strong>
            <small>智能教练</small>
          </span>
        </Link>

        <div className="auth-visual__copy">
          <span className="status-pill">
            <ShieldCheck aria-hidden="true" size={16} />
            安全优先的 AI 健身教练
          </span>
          <h1>
            训练有计划，
            <br />
            进步看得见。
          </h1>
          <p>
            结合用户画像、训练反馈和长期记忆，持续调整属于你的训练节奏。
          </p>
        </div>

        <div className="auth-preview">
          <div className="auth-preview__head">
            <span>今日训练</span>
            <span className="readiness">准备度 86</span>
          </div>
          <h2>全身训练 A</h2>
          <p>胸 · 背 · 腿</p>
          <div className="auth-preview__stats">
            <span>
              <strong>58</strong> 分钟
            </span>
            <span>
              <strong>4</strong> 个动作
            </span>
            <span>
              <strong>RPE 7</strong> 强度
            </span>
          </div>
        </div>
      </section>

      <section className="auth-panel">
        <div className="auth-panel__inner">
          <div className="auth-panel__heading">
            <span className="auth-panel__icon">
              <Sparkles aria-hidden="true" size={21} />
            </span>
            <div>
              <p className="eyebrow">欢迎回来</p>
              <h2>继续今天的训练</h2>
            </div>
          </div>

          <form
            className="auth-form"
            onSubmit={(event) => {
              event.preventDefault();
              const data = new FormData(event.currentTarget);
              setBusy(true);
              setError('');
              void login(
                String(data.get('email') ?? ''),
                String(data.get('password') ?? ''),
              )
                .then(() => {
                  const destination =
                    typeof location.state?.from === 'string'
                      ? location.state.from
                      : '/app';
                  navigate(destination, { replace: true });
                })
                .catch((requestError: unknown) => {
                  setError(describeLoginError(requestError));
                })
                .finally(() => setBusy(false));
            }}>
            <label>
              <span>邮箱</span>
              <span className="field">
                <Mail aria-hidden="true" size={18} />
                <input
                  autoComplete="email"
                  inputMode="email"
                  maxLength={320}
                  name="email"
                  required
                  type="email"
                />
              </span>
            </label>
            <label>
              <span>密码</span>
              <span className="field">
                <LockKeyhole aria-hidden="true" size={18} />
                <input
                  autoComplete="current-password"
                  name="password"
                  maxLength={128}
                  required
                  type="password"
                />
              </span>
            </label>
            {error ? <p className="auth-form__error" role="alert">{error}</p> : null}
            <Button disabled={busy} fullWidth icon={ArrowRight} type="submit">
              {busy ? '正在登录…' : '进入 FitFlow'}
            </Button>
          </form>

          <div className="auth-benefits">
            <span>
              <CheckCircle2 size={16} />
              规则先于模型
            </span>
            <span>
              <CheckCircle2 size={16} />
              训练全程可追踪
            </span>
          </div>

          <p className="auth-signup">
            第一次使用？
            <Link to="/register">创建账号</Link>
          </p>
          <p className="safety-note">
            FitFlow 不替代医疗诊断。出现疼痛或明显不适时，请停止训练并咨询专业人士。
          </p>
        </div>
      </section>
    </main>
  );
}

function describeLoginError(error: unknown) {
  if (error instanceof FitFlowApiError && typeof error.detail === 'string') {
    return error.detail;
  }
  return '登录暂时不可用，请稍后重试。';
}
