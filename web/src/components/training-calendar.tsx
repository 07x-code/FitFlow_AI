import {
  CalendarDays,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  CircleAlert,
  Clock3,
  Dumbbell,
  PencilLine,
} from 'lucide-react';
import { useMemo, useState } from 'react';

import type {
  TrainingPlanHistoryItem,
  WorkoutDayDraft,
  WorkoutSessionResponse,
} from '../api/client';
import {
  translateDayName,
  translateExerciseName,
} from '../utils/plan-labels';
import { Card, Chip } from './ui';

type TrainingCalendarProps = {
  plans: TrainingPlanHistoryItem[];
  sessions: WorkoutSessionResponse[];
  onEditPlannedWorkout: (planId: number, dayIndex: number) => void;
};

type PlannedWorkout = {
  planId: number;
  planDayIndex: number;
  editable: boolean;
  day: WorkoutDayDraft;
};

const weekDays = ['一', '二', '三', '四', '五', '六', '日'];

function toDateKey(date: Date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function parseDateKey(value: string) {
  const [year, month, day] = value.split('-').map(Number);
  return new Date(year, month - 1, day, 12);
}

function formatSelectedDate(value: string) {
  return new Intl.DateTimeFormat('zh-CN', {
    month: 'long',
    day: 'numeric',
    weekday: 'long',
  }).format(parseDateKey(value));
}

function formatSessionTime(value: string) {
  return new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value));
}

function buildCalendarDays(month: Date) {
  const first = new Date(month.getFullYear(), month.getMonth(), 1, 12);
  const mondayOffset = (first.getDay() + 6) % 7;
  const start = new Date(first);
  start.setDate(first.getDate() - mondayOffset);

  return Array.from({ length: 42 }, (_, index) => {
    const date = new Date(start);
    date.setDate(start.getDate() + index);
    return date;
  });
}

function uniqueExerciseNames(session: WorkoutSessionResponse) {
  return Array.from(
    new Set(
      session.sets.map((set) =>
        translateExerciseName(set.exercise_name),
      ),
    ),
  );
}

export function TrainingCalendar({
  plans,
  sessions,
  onEditPlannedWorkout,
}: TrainingCalendarProps) {
  const today = useMemo(() => new Date(), []);
  const todayKey = toDateKey(today);
  const [visibleMonth, setVisibleMonth] = useState(
    () => new Date(today.getFullYear(), today.getMonth(), 1, 12),
  );
  const [selectedDate, setSelectedDate] = useState(todayKey);

  const plannedWorkouts = useMemo(
    () =>
      plans
        .filter((plan) => plan.status !== 'superseded')
        .flatMap((plan) =>
          plan.plan.days.map((day, index) => ({
            planId: plan.id,
            planDayIndex: index + 1,
            editable: plan.status === 'active' || plan.status === 'scheduled',
            day,
          })),
        ),
    [plans],
  );
  const plannedByDate = useMemo(() => {
    const result = new Map<string, PlannedWorkout[]>();
    for (const workout of plannedWorkouts) {
      const current = result.get(workout.day.scheduled_date) ?? [];
      current.push(workout);
      result.set(workout.day.scheduled_date, current);
    }
    return result;
  }, [plannedWorkouts]);
  const sessionsByDate = useMemo(() => {
    const result = new Map<string, WorkoutSessionResponse[]>();
    for (const session of sessions) {
      const key = toDateKey(new Date(session.created_at));
      const current = result.get(key) ?? [];
      current.push(session);
      result.set(key, current);
    }
    return result;
  }, [sessions]);
  const completedPlanDays = useMemo(
    () =>
      new Set(
        sessions.map(
          (session) => `${session.plan_id}:${session.plan_day_index}`,
        ),
      ),
    [sessions],
  );

  const calendarDays = useMemo(
    () => buildCalendarDays(visibleMonth),
    [visibleMonth],
  );
  const monthPrefix = `${visibleMonth.getFullYear()}-${String(
    visibleMonth.getMonth() + 1,
  ).padStart(2, '0')}`;
  const visiblePlannedCount = plannedWorkouts.filter((workout) =>
    workout.day.scheduled_date.startsWith(monthPrefix),
  ).length;
  const visibleSessions = sessions.filter((session) =>
    toDateKey(new Date(session.created_at)).startsWith(monthPrefix),
  );
  const selectedPlans = plannedByDate.get(selectedDate) ?? [];
  const selectedSessions = sessionsByDate.get(selectedDate) ?? [];

  const changeMonth = (offset: number) => {
    const next = new Date(
      visibleMonth.getFullYear(),
      visibleMonth.getMonth() + offset,
      1,
      12,
    );
    setVisibleMonth(next);
    setSelectedDate(toDateKey(next));
  };

  return (
    <div className="training-calendar">
      <section className="calendar-summary" aria-label="本月训练概况">
        <span>
          <strong>{visiblePlannedCount}</strong>
          <small>计划训练</small>
        </span>
        <span>
          <strong>{visibleSessions.length}</strong>
          <small>实际记录</small>
        </span>
        <span>
          <strong>
            {visibleSessions.reduce(
              (total, session) => total + session.sets.length,
              0,
            )}
          </strong>
          <small>完成组数</small>
        </span>
      </section>

      <Card className="calendar-card">
        <header className="calendar-card__header">
          <button
            aria-label="查看上个月"
            className="icon-button"
            onClick={() => changeMonth(-1)}
            type="button">
            <ChevronLeft size={19} />
          </button>
          <div>
            <small>{visibleMonth.getFullYear()}</small>
            <h2>{visibleMonth.getMonth() + 1} 月</h2>
          </div>
          <button
            aria-label="查看下个月"
            className="icon-button"
            onClick={() => changeMonth(1)}
            type="button">
            <ChevronRight size={19} />
          </button>
        </header>

        <div className="calendar-legend" aria-label="日历状态说明">
          <span><i className="is-planned" />有计划</span>
          <span><i className="is-completed" />已训练</span>
          <span><i className="is-warning" />需注意</span>
        </div>

        <div className="calendar-weekdays" aria-hidden="true">
          {weekDays.map((day) => <span key={day}>{day}</span>)}
        </div>

        <div className="calendar-grid">
          {calendarDays.map((date) => {
            const key = toDateKey(date);
            const dayPlans = plannedByDate.get(key) ?? [];
            const daySessions = sessionsByDate.get(key) ?? [];
            const hasCompletedPlan = dayPlans.some((workout) =>
              completedPlanDays.has(
                `${workout.planId}:${workout.planDayIndex}`,
              ),
            );
            const hasWarning = daySessions.some(
              (session) => session.safety_alert !== null,
            );
            const className = [
              'calendar-day',
              date.getMonth() === visibleMonth.getMonth()
                ? ''
                : 'is-outside',
              key === todayKey ? 'is-today' : '',
              key === selectedDate ? 'is-selected' : '',
            ].filter(Boolean).join(' ');

            return (
              <button
                aria-label={`${formatSelectedDate(key)}${
                  dayPlans.length ? `，${dayPlans.length}项训练计划` : ''
                }${daySessions.length ? `，${daySessions.length}条训练记录` : ''}`}
                className={className}
                key={key}
                onClick={() => setSelectedDate(key)}
                type="button">
                <time dateTime={key}>{date.getDate()}</time>
                <span className="calendar-day__markers">
                  {dayPlans.length ? <i className="is-planned" /> : null}
                  {daySessions.length || hasCompletedPlan ? (
                    <i className="is-completed" />
                  ) : null}
                  {hasWarning ? <i className="is-warning" /> : null}
                </span>
              </button>
            );
          })}
        </div>
      </Card>

      <section className="calendar-detail" aria-live="polite">
        <header>
          <div>
            <p className="eyebrow">每日训练内容</p>
            <h2>{formatSelectedDate(selectedDate)}</h2>
          </div>
          <Chip tone={selectedSessions.length ? 'green' : 'blue'}>
            {selectedSessions.length
              ? `${selectedSessions.length} 条记录`
              : selectedPlans.length
                ? '等待训练'
                : '休息日'}
          </Chip>
        </header>

        {!selectedPlans.length && !selectedSessions.length ? (
          <Card className="calendar-empty-day">
            <CalendarDays size={22} />
            <strong>这一天没有训练安排</strong>
            <span>计划中的训练和实际训练记录都会显示在这里。</span>
          </Card>
        ) : null}

        {selectedPlans.map((workout) => {
          const completed = completedPlanDays.has(
            `${workout.planId}:${workout.planDayIndex}`,
          );
          return (
            <button
              aria-label={`编辑${translateDayName(workout.day.name)}`}
              className="card calendar-entry calendar-entry--planned calendar-entry--editable"
              disabled={!workout.editable}
              key={`${workout.planId}:${workout.planDayIndex}`}
              onClick={() =>
                onEditPlannedWorkout(
                  workout.planId,
                  workout.planDayIndex - 1,
                )
              }
              type="button">
              <span className="colored-icon colored-icon--blue">
                <Dumbbell size={20} />
              </span>
              <div>
                <small>计划训练</small>
                <h3>{translateDayName(workout.day.name)}</h3>
                <p>{workout.day.exercises
                  .map((exercise) =>
                    translateExerciseName(exercise.exercise_name),
                  )
                  .join('、')}</p>
                <span>
                  <Clock3 size={14} />
                  {workout.day.estimated_minutes} 分钟 · {workout.day.exercises.length} 个动作
                </span>
              </div>
              <span className="calendar-entry__controls">
                <Chip tone={completed ? 'green' : 'blue'}>
                  {completed ? '已完成' : '待训练'}
                </Chip>
                {workout.editable ? (
                  <small><PencilLine size={13} />点击编辑</small>
                ) : null}
              </span>
            </button>
          );
        })}

        {selectedSessions.map((session) => (
          <Card
            className="calendar-entry calendar-entry--completed"
            key={session.id}>
            <span className="colored-icon colored-icon--green">
              {session.safety_alert ? (
                <CircleAlert size={20} />
              ) : (
                <CheckCircle2 size={20} />
              )}
            </span>
            <div>
              <small>实际训练 · {formatSessionTime(session.created_at)}</small>
              <h3>{translateDayName(session.plan_day_name)}</h3>
              <p>{uniqueExerciseNames(session).join('、')}</p>
              <span>
                {session.sets.length} 组 · 疲劳 {session.fatigue_level}/10 · 疼痛 {session.pain_level}/10
              </span>
              {session.notes ? <em>{session.notes}</em> : null}
              {session.safety_alert ? (
                <em className="calendar-entry__warning">
                  {session.safety_alert.message}
                </em>
              ) : null}
            </div>
            <Chip tone={session.safety_alert ? 'orange' : 'green'}>
              {session.completed ? '已完成' : '未完成'}
            </Chip>
          </Card>
        ))}
      </section>
    </div>
  );
}
