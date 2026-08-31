import { Check, CircleAlert, Info, TimerReset } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router';

import { Button, Card, Chip, PageHeader } from '../components/ui';
import { todayWorkout } from '../data/mock-data';

type SetRecord = {
  id: string;
  exerciseId: string;
  setNumber: number;
  weight: string;
  reps: string;
  rpe: string;
  completed: boolean;
};

const initialSets: SetRecord[] = todayWorkout.exercises.flatMap((exercise) =>
  Array.from({ length: exercise.sets }, (_, index) => ({
    id: `${exercise.id}-${index + 1}`,
    exerciseId: exercise.id,
    setNumber: index + 1,
    weight: String(exercise.lastWeight),
    reps: exercise.reps.split('–')[0],
    rpe: String(exercise.rpe),
    completed: false,
  })),
);

function formatTime(seconds: number) {
  const minutes = Math.floor(seconds / 60).toString().padStart(2, '0');
  const remaining = (seconds % 60).toString().padStart(2, '0');
  return `${minutes}:${remaining}`;
}

export function WorkoutPage() {
  const [elapsed, setElapsed] = useState(0);
  const [sets, setSets] = useState(initialSets);
  const navigate = useNavigate();

  useEffect(() => {
    const timer = window.setInterval(
      () => setElapsed((value) => value + 1),
      1000,
    );
    return () => window.clearInterval(timer);
  }, []);

  const completedCount = useMemo(
    () => sets.filter((item) => item.completed).length,
    [sets],
  );

  const updateSet = (
    id: string,
    patch: Partial<Pick<SetRecord, 'weight' | 'reps' | 'rpe' | 'completed'>>,
  ) => {
    setSets((current) =>
      current.map((item) => (item.id === id ? { ...item, ...patch } : item)),
    );
  };

  return (
    <div className="page page--workout">
      <PageHeader
        action={
          <Chip active>
            <TimerReset size={15} />
            {formatTime(elapsed)}
          </Chip>
        }
        back
        eyebrow="训练进行中"
        title={todayWorkout.name}
      />

      <Card className="workout-overview">
        <span>
          <strong>
            {completedCount} / {sets.length}
          </strong>
          <small>已完成组数</small>
        </span>
        <span>
          <strong>RPE 7</strong>
          <small>目标强度</small>
        </span>
        <span>
          <strong>90 秒</strong>
          <small>组间休息</small>
        </span>
      </Card>

      <div className="workout-exercises">
        {todayWorkout.exercises.map((exercise, exerciseIndex) => {
          const exerciseSets = sets.filter(
            (item) => item.exerciseId === exercise.id,
          );
          const allDone = exerciseSets.every((item) => item.completed);

          return (
            <Card
              className={`workout-exercise ${allDone ? 'is-completed' : ''}`}
              key={exercise.id}
              as="section">
              <div className="workout-exercise__head">
                <span className="exercise-order">
                  {allDone ? <Check size={17} /> : exerciseIndex + 1}
                </span>
                <div>
                  <h2>{exercise.name}</h2>
                  <p>
                    上次 {exercise.lastWeight} kg · {exercise.target}
                  </p>
                </div>
                <Link
                  aria-label={`查看${exercise.name}动作说明`}
                  className="icon-button"
                  to={`/app/exercises/${exercise.id}`}>
                  <Info size={19} />
                </Link>
              </div>

              <div className="set-table">
                <div className="set-row set-row--head">
                  <span>组</span>
                  <span>kg</span>
                  <span>次数</span>
                  <span>RPE</span>
                  <span>完成</span>
                </div>
                {exerciseSets.map((set) => (
                  <div
                    className={`set-row ${set.completed ? 'is-completed' : ''}`}
                    key={set.id}>
                    <strong>{set.setNumber}</strong>
                    {(['weight', 'reps', 'rpe'] as const).map((field) => (
                      <input
                        aria-label={`第${set.setNumber}组${field}`}
                        inputMode="decimal"
                        key={field}
                        onChange={(event) =>
                          updateSet(set.id, { [field]: event.target.value })
                        }
                        value={set[field]}
                      />
                    ))}
                    <button
                      aria-label={`${set.completed ? '取消' : '完成'}第${set.setNumber}组`}
                      className="set-check"
                      onClick={() =>
                        updateSet(set.id, { completed: !set.completed })
                      }
                      type="button">
                      <Check size={17} />
                    </button>
                  </div>
                ))}
              </div>
            </Card>
          );
        })}
      </div>

      <div className="feedback-banner">
        <CircleAlert size={20} />
        <span>
          <strong>训练反馈</strong>
          完成后记录疲劳与疼痛，系统会先执行安全规则。
        </span>
      </div>

      <Button
        disabled={completedCount === 0}
        fullWidth
        onClick={() => navigate('/app')}>
        完成训练 · {completedCount}/{sets.length} 组
      </Button>
    </div>
  );
}
