import {
  ArrowRight,
  Dumbbell,
  LockKeyhole,
  Mail,
  UserRound,
} from 'lucide-react';
import { useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router';

import { FitFlowApiError } from '../api/client';
import { useAuth } from '../auth';
import { Button } from '../components/ui';

export function RegisterPage() {
  const { user, loading, register } = useAuth();
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  if (!loading && user !== null) {
    return <Navigate replace to="/profile-setup" />;
  }

  return (
    <main className="auth-page auth-page--register">
      <section className="auth-visual">
        <Link className="brand brand--large" to="/">
          <span className="brand__mark"><Dumbbell size={22} /></span>
          <span><strong>FitFlow</strong><small>智能教练</small></span>
        </Link>
        <div className="auth-visual__copy">
          <p className="eyebrow">创建专属训练空间</p>
          <h1>每位用户，<br />都有独立的计划与记忆。</h1>
          <p>账号数据、长期记忆、训练计划和反馈按用户严格隔离。</p>
        </div>
      </section>

      <section className="auth-panel">
        <div className="auth-panel__inner">
          <div className="auth-panel__heading">
            <span className="auth-panel__icon"><UserRound size={21} /></span>
            <div><p className="eyebrow">新用户注册</p><h2>创建 FitFlow 账号</h2></div>
          </div>
          <form
            className="auth-form"
            onSubmit={(event) => {
              event.preventDefault();
              const data = new FormData(event.currentTarget);
              const password = String(data.get('password') ?? '');
              const confirmation = String(data.get('confirmation') ?? '');
              if (password !== confirmation) {
                setError('两次输入的密码不一致。');
                return;
              }
              setBusy(true);
              setError('');
              void register(
                String(data.get('email') ?? ''),
                password,
                String(data.get('displayName') ?? ''),
              )
                .then(() => navigate('/profile-setup'))
                .catch((requestError: unknown) => {
                  setError(describeAuthError(requestError));
                })
                .finally(() => setBusy(false));
            }}>
            <label><span>显示名称</span><span className="field">
              <UserRound size={18} /><input autoComplete="name" maxLength={100} name="displayName" required />
            </span></label>
            <label><span>邮箱</span><span className="field">
              <Mail size={18} /><input autoComplete="email" inputMode="email" maxLength={320} name="email" required type="email" />
            </span></label>
            <label><span>密码（至少 8 位）</span><span className="field">
              <LockKeyhole size={18} /><input autoComplete="new-password" maxLength={128} minLength={8} name="password" required type="password" />
            </span></label>
            <label><span>确认密码</span><span className="field">
              <LockKeyhole size={18} /><input autoComplete="new-password" maxLength={128} minLength={8} name="confirmation" required type="password" />
            </span></label>
            {error ? <p className="auth-form__error" role="alert">{error}</p> : null}
            <Button disabled={busy} fullWidth icon={ArrowRight} type="submit">
              {busy ? '正在创建…' : '创建账号'}
            </Button>
          </form>
          <p className="auth-signup">已有账号？<Link to="/">返回登录</Link></p>
        </div>
      </section>
    </main>
  );
}

function describeAuthError(error: unknown) {
  if (error instanceof FitFlowApiError && typeof error.detail === 'string') {
    return error.detail;
  }
  return '注册暂时不可用，请稍后重试。';
}
