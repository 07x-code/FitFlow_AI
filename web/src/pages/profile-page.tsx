import {
  ArrowRight,
  Bell,
  Dumbbell,
  LogOut,
  Server,
  Settings,
  ShieldCheck,
  UserRound,
  Zap,
} from 'lucide-react';
import { Link, useNavigate } from 'react-router';

import { Card, Chip, PageHeader, ProgressBar } from '../components/ui';
import { useAuth } from '../auth';

const settings = [
  { icon: UserRound, label: '训练画像', value: '增肌', tone: 'green' },
  { icon: ShieldCheck, label: '健康与安全', value: '低风险', tone: 'blue' },
  { icon: Dumbbell, label: '器械偏好', value: '健身房', tone: 'orange' },
  { icon: Bell, label: '训练提醒', value: '已开启', tone: 'green' },
  { icon: Server, label: 'FastAPI 连接', value: '本地', tone: 'blue' },
] as const;

export function ProfilePage() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const avatarText = user?.display_name.trim().charAt(0).toUpperCase() || 'U';

  return (
    <div className="page page--profile">
      <PageHeader
        action={
          <button aria-label="设置" className="icon-button" type="button">
            <Settings size={20} />
          </button>
        }
        title="个人中心"
      />

      <div className="profile-grid">
        <section>
          <div className="profile-identity">
            <span className="profile-avatar">{avatarText}</span>
            <div>
              <span>
                <h2>{user?.display_name}</h2>
                <Chip tone="blue">第 4 周</Chip>
              </span>
              <p>{user?.email}</p>
            </div>
          </div>

          <Card className="level-card">
            <div>
              <span>
                <p className="eyebrow">FitFlow 等级</p>
                <h2>稳定训练者</h2>
              </span>
              <Chip tone="green">
                <Zap size={15} />
                Lv. 6
              </Chip>
            </div>
            <ProgressBar value={0.72} />
            <p>再完成 3 次训练升级</p>
          </Card>

          <div className="profile-stats">
            <span>
              <strong>28</strong>
              <small>总训练</small>
            </span>
            <span>
              <strong>4 周</strong>
              <small>连续达标</small>
            </span>
            <span>
              <strong>42.6t</strong>
              <small>累计训练量</small>
            </span>
          </div>
        </section>

        <Card className="settings-card">
          {settings.map(({ icon: Icon, label, value, tone }) => {
            const row = (
              <>
                <span className={`colored-icon colored-icon--${tone}`}>
                  <Icon size={19} />
                </span>
                <strong>{label}</strong>
                <small>{value}</small>
                <ArrowRight size={17} />
              </>
            );

            return label === '训练画像' ? (
              <Link className="setting-row" key={label} to="/profile-setup">
                {row}
              </Link>
            ) : (
              <button className="setting-row" key={label} type="button">
                {row}
              </button>
            );
          })}
        </Card>
      </div>

      <button
        className="logout-button"
        onClick={() => {
          void logout().then(() => navigate('/', { replace: true }));
        }}
        type="button">
        <LogOut size={18} />
        退出登录
      </button>
    </div>
  );
}
