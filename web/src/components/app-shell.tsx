import {
  Activity,
  Bot,
  Dumbbell,
  Home,
  LogOut,
  Menu,
  UserRound,
  X,
} from 'lucide-react';
import { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router';

import { PwaPrompt } from './pwa-prompt';
import { useAuth } from '../auth';

const navigation = [
  { to: '/app', label: '首页', icon: Home, end: true },
  { to: '/app/plans', label: '训练', icon: Dumbbell, end: false },
  { to: '/app/coach', label: 'AI 教练', icon: Bot, end: false },
  { to: '/app/exercises', label: '动作', icon: Activity, end: false },
  { to: '/app/profile', label: '我的', icon: UserRound, end: false },
] as const;

export function AppShell() {
  const [menuOpen, setMenuOpen] = useState(false);
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const avatarText = user?.display_name.trim().charAt(0).toUpperCase() || 'U';

  return (
    <div className="app-shell">
      <aside className={`sidebar ${menuOpen ? 'is-open' : ''}`}>
        <div className="sidebar__head">
          <NavLink aria-label="FitFlow AI 首页" className="brand" to="/app">
            <span className="brand__mark">
              <Dumbbell aria-hidden="true" size={20} />
            </span>
            <span>
              <strong>FitFlow</strong>
              <small>智能教练</small>
            </span>
          </NavLink>
          <button
            aria-label="关闭菜单"
            className="icon-button sidebar__close"
            onClick={() => setMenuOpen(false)}
            type="button">
            <X aria-hidden="true" size={20} />
          </button>
        </div>

        <nav aria-label="主导航" className="sidebar__nav">
          {navigation.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              className={({ isActive }) =>
                `nav-item ${isActive ? 'is-active' : ''}`
              }
              end={end}
              key={to}
              onClick={() => setMenuOpen(false)}
              to={to}>
              <Icon aria-hidden="true" size={20} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar__profile">
          <span className="avatar">{avatarText}</span>
          <span>
            <strong>{user?.display_name}</strong>
            <small>{user?.email}</small>
          </span>
          <button
            aria-label="退出登录"
            className="icon-button"
            onClick={() => {
              void logout().then(() => navigate('/', { replace: true }));
            }}
            type="button">
            <LogOut aria-hidden="true" size={18} />
          </button>
        </div>
      </aside>

      {menuOpen ? (
        <button
          aria-label="关闭导航遮罩"
          className="sidebar-backdrop"
          onClick={() => setMenuOpen(false)}
          type="button"
        />
      ) : null}

      <div className="app-shell__content">
        <div className="mobile-topbar">
          <button
            aria-label="打开菜单"
            className="icon-button"
            onClick={() => setMenuOpen(true)}
            type="button">
            <Menu aria-hidden="true" size={21} />
          </button>
          <span className="mobile-topbar__title">FitFlow AI</span>
          <span className="avatar avatar--small">{avatarText}</span>
        </div>
        <main className="app-main">
          <Outlet />
        </main>
      </div>

      <nav aria-label="移动端主导航" className="bottom-nav">
        {navigation.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            className={({ isActive }) =>
              `bottom-nav__item ${isActive ? 'is-active' : ''}`
            }
            end={end}
            key={to}
            to={to}>
            <Icon aria-hidden="true" size={20} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      <PwaPrompt />
    </div>
  );
}
