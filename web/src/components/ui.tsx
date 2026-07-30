import type {
  ButtonHTMLAttributes,
  HTMLAttributes,
  PropsWithChildren,
  ReactNode,
} from 'react';
import { ArrowLeft, type LucideIcon } from 'lucide-react';
import { useNavigate } from 'react-router';

type CardProps = PropsWithChildren<HTMLAttributes<HTMLElement>> & {
  as?: 'article' | 'section' | 'div';
};

export function Card({
  as: Element = 'div',
  className = '',
  children,
  ...props
}: CardProps) {
  return (
    <Element className={`card ${className}`.trim()} {...props}>
      {children}
    </Element>
  );
}

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  icon?: LucideIcon;
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  fullWidth?: boolean;
};

export function Button({
  icon: Icon,
  variant = 'primary',
  fullWidth = false,
  className = '',
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={`button button--${variant} ${fullWidth ? 'button--full' : ''} ${className}`.trim()}
      type="button"
      {...props}>
      {Icon ? <Icon aria-hidden="true" size={18} strokeWidth={2.2} /> : null}
      <span>{children}</span>
    </button>
  );
}

type ChipProps = PropsWithChildren<{
  active?: boolean;
  tone?: 'default' | 'blue' | 'orange' | 'green';
  onClick?: () => void;
}>;

export function Chip({
  active = false,
  tone = 'default',
  onClick,
  children,
}: ChipProps) {
  const className = `chip chip--${tone} ${active ? 'is-active' : ''}`.trim();

  if (onClick) {
    return (
      <button className={className} onClick={onClick} type="button">
        {children}
      </button>
    );
  }

  return <span className={className}>{children}</span>;
}

export function ProgressBar({
  value,
  color = 'var(--primary)',
}: {
  value: number;
  color?: string;
}) {
  const safeValue = Math.max(0, Math.min(1, value));

  return (
    <div
      aria-label={`完成 ${Math.round(safeValue * 100)}%`}
      aria-valuemax={100}
      aria-valuemin={0}
      aria-valuenow={Math.round(safeValue * 100)}
      className="progress"
      role="progressbar">
      <span style={{ background: color, width: `${safeValue * 100}%` }} />
    </div>
  );
}

export function SectionTitle({
  children,
  action,
}: {
  children: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="section-title">
      <h2>{children}</h2>
      {action}
    </div>
  );
}

export function PageHeader({
  title,
  eyebrow,
  back = false,
  action,
}: {
  title: string;
  eyebrow?: string;
  back?: boolean;
  action?: ReactNode;
}) {
  const navigate = useNavigate();

  return (
    <header className="page-header">
      <div className="page-header__copy">
        {back ? (
          <button
            aria-label="返回"
            className="icon-button"
            onClick={() => navigate(-1)}
            type="button">
            <ArrowLeft aria-hidden="true" size={20} />
          </button>
        ) : null}
        <div>
          {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
          <h1>{title}</h1>
        </div>
      </div>
      {action}
    </header>
  );
}

