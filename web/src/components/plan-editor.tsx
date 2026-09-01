import {
  Check,
  ChevronLeft,
  Dumbbell,
  Plus,
  Search,
  ShieldCheck,
  Trash2,
  X,
} from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import {
  FitFlowApiError,
  fitFlowApi,
  type ExercisePrescription,
  type TrainingPlanDraft,
  type TrainingPlanHistoryItem,
  type TrainingPlanProposalResponse,
} from '../api/client';
import {
  equipmentGroups,
  exerciseCategories,
  type LibraryExercise,
} from '../data/exercise-library';
import { translateDayName, translateExerciseName } from '../utils/plan-labels';
import { Button, Chip } from './ui';

type PlanEditorProps = {
  plan: TrainingPlanHistoryItem;
  userId: string;
  initialDayIndex?: number;
  pendingProposal?: TrainingPlanProposalResponse;
  onClose: () => void;
  onChanged: () => void;
};

type ExerciseNumberField = 'sets' | 'reps_min' | 'reps_max' | 'target_rpe';

function describeError(error: unknown) {
  if (!(error instanceof FitFlowApiError)) {
    return '操作未完成，请检查网络后重试。';
  }
  if (
    error.detail &&
    typeof error.detail === 'object' &&
    'message' in error.detail &&
    typeof error.detail.message === 'string'
  ) {
    return error.detail.message;
  }
  if (typeof error.detail === 'string') return error.detail;
  return `操作未完成，FastAPI 返回 ${error.status}。`;
}

function clonePlan(plan: TrainingPlanDraft): TrainingPlanDraft {
  return structuredClone(plan);
}

export function PlanEditor({
  plan,
  userId,
  initialDayIndex,
  pendingProposal,
  onClose,
  onChanged,
}: PlanEditorProps) {
  const [draft, setDraft] = useState(() => clonePlan(plan.plan));
  const [proposal, setProposal] = useState(pendingProposal);
  const [pickerDayIndex, setPickerDayIndex] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const visibleDays = initialDayIndex === undefined
    ? draft.days.map((day, dayIndex) => ({ day, dayIndex }))
    : [{ day: draft.days[initialDayIndex], dayIndex: initialDayIndex }];
  const editorTitle = initialDayIndex === undefined
    ? '编辑训练计划'
    : `编辑 ${new Intl.DateTimeFormat('zh-CN', {
        month: 'long',
        day: 'numeric',
      }).format(new Date(`${draft.days[initialDayIndex].scheduled_date}T00:00:00`))}训练`;

  const updateExercise = (
    dayIndex: number,
    exerciseIndex: number,
    field: ExerciseNumberField,
    value: number,
  ) => {
    setDraft((current) => {
      const next = clonePlan(current);
      next.days[dayIndex].exercises[exerciseIndex][field] = value;
      return next;
    });
  };

  const removeExercise = (dayIndex: number, exerciseIndex: number) => {
    setDraft((current) => {
      const next = clonePlan(current);
      next.days[dayIndex].exercises.splice(exerciseIndex, 1);
      return next;
    });
  };

  const addExercises = (dayIndex: number, exercises: LibraryExercise[]) => {
    setDraft((current) => {
      const next = clonePlan(current);
      const day = next.days[dayIndex];
      const existingNames = new Set(
        day.exercises.map((exercise) => exercise.exercise_name),
      );
      const prescriptions = exercises
        .filter((exercise) => !existingNames.has(exercise.name))
        .slice(0, Math.max(0, 7 - day.exercises.length))
        .map<ExercisePrescription>((exercise) => ({
          exercise_name: exercise.name,
          sets: 3,
          reps_min: 8,
          reps_max: 12,
          target_rpe: 7,
        }));
      day.exercises.push(...prescriptions);
      return next;
    });
    setPickerDayIndex(null);
  };

  const createProposal = async () => {
    setBusy(true);
    setError('');
    try {
      const created = await fitFlowApi.createManualTrainingPlanProposal(
        userId,
        plan.id,
        draft,
      );
      setProposal(created);
    } catch (requestError) {
      setError(describeError(requestError));
    } finally {
      setBusy(false);
    }
  };

  const decide = async (decision: 'approve' | 'reject') => {
    if (!proposal) return;
    setBusy(true);
    setError('');
    try {
      await fitFlowApi.decideTrainingPlanProposal(
        userId,
        proposal.id,
        decision,
      );
      onChanged();
      onClose();
    } catch (requestError) {
      setError(describeError(requestError));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="plan-editor-backdrop">
      <section
        aria-labelledby="plan-editor-title"
        aria-modal="true"
        className="plan-editor"
        role="dialog">
        <header className="plan-editor__header">
          <button
            aria-label="关闭计划编辑"
            className="icon-button"
            disabled={busy}
            onClick={onClose}
            type="button">
            {proposal ? <X size={22} /> : <ChevronLeft size={22} />}
          </button>
          <div>
            <p className="eyebrow">版本 {plan.version} · 力量训练</p>
            <h2 id="plan-editor-title">
              {proposal ? '确认计划修改' : editorTitle}
            </h2>
          </div>
          <Chip tone={proposal ? 'orange' : 'green'}>
            {proposal ? '待确认' : '人工编辑'}
          </Chip>
        </header>

        {proposal ? (
          <ProposalConfirmation proposal={proposal} />
        ) : (
          <div className="plan-editor__content">
            <div className="plan-editor__notice">
              <ShieldCheck size={19} />
              <p>
                每个训练日保留 4–7 个动作。保存后先生成修改提案，确认同步才会替换当前计划。
              </p>
            </div>

            {visibleDays.map(({ day, dayIndex }) => (
              <article className="plan-edit-day" key={day.scheduled_date}>
                <header>
                  <div>
                    <small>{day.scheduled_date}</small>
                    <h3>{translateDayName(day.name)}</h3>
                    <p>{day.focus}</p>
                  </div>
                  <Chip tone="blue">{day.exercises.length} / 7 个动作</Chip>
                </header>

                <div className="plan-edit-exercises">
                  {day.exercises.map((exercise, exerciseIndex) => (
                    <div
                      className="plan-edit-exercise"
                      key={`${day.scheduled_date}-${exercise.exercise_name}-${exerciseIndex}`}>
                      <span className="plan-edit-exercise__index">
                        {exerciseIndex + 1}
                      </span>
                      <div className="plan-edit-exercise__main">
                        <strong>
                          {translateExerciseName(exercise.exercise_name)}
                        </strong>
                        <div className="plan-edit-fields">
                          <NumberInput
                            label="组"
                            max={5}
                            min={1}
                            onChange={(value) =>
                              updateExercise(
                                dayIndex,
                                exerciseIndex,
                                'sets',
                                value,
                              )
                            }
                            value={exercise.sets}
                          />
                          <NumberInput
                            label="最低次数"
                            max={30}
                            min={1}
                            onChange={(value) =>
                              updateExercise(
                                dayIndex,
                                exerciseIndex,
                                'reps_min',
                                value,
                              )
                            }
                            value={exercise.reps_min}
                          />
                          <NumberInput
                            label="最高次数"
                            max={30}
                            min={1}
                            onChange={(value) =>
                              updateExercise(
                                dayIndex,
                                exerciseIndex,
                                'reps_max',
                                value,
                              )
                            }
                            value={exercise.reps_max}
                          />
                          <NumberInput
                            label="RPE"
                            max={8}
                            min={1}
                            onChange={(value) =>
                              updateExercise(
                                dayIndex,
                                exerciseIndex,
                                'target_rpe',
                                value,
                              )
                            }
                            value={exercise.target_rpe}
                          />
                        </div>
                      </div>
                      <button
                        aria-label={`删除${translateExerciseName(exercise.exercise_name)}`}
                        className="plan-edit-exercise__remove"
                        disabled={day.exercises.length <= 4}
                        onClick={() => removeExercise(dayIndex, exerciseIndex)}
                        title={
                          day.exercises.length <= 4
                            ? '每个训练日至少保留 4 个动作'
                            : '删除动作'
                        }
                        type="button">
                        <Trash2 size={17} />
                      </button>
                    </div>
                  ))}
                </div>

                <Button
                  disabled={day.exercises.length >= 7}
                  icon={Plus}
                  onClick={() => setPickerDayIndex(dayIndex)}
                  variant="secondary">
                  {day.exercises.length >= 7
                    ? '已达到 7 个动作'
                    : '从动作库添加'}
                </Button>
              </article>
            ))}
          </div>
        )}

        {error ? <p className="plan-editor__error">{error}</p> : null}

        <footer className="plan-editor__footer">
          {proposal ? (
            <>
              <Button
                disabled={busy}
                onClick={() => void decide('reject')}
                variant="secondary">
                放弃修改
              </Button>
              <Button
                disabled={busy}
                icon={Check}
                onClick={() => void decide('approve')}>
                {busy ? '正在同步…' : '确认并同步'}
              </Button>
            </>
          ) : (
            <>
              <Button disabled={busy} onClick={onClose} variant="secondary">
                取消
              </Button>
              <Button
                disabled={busy}
                icon={ShieldCheck}
                onClick={() => void createProposal()}>
                {busy ? '正在检查…' : '保存修改'}
              </Button>
            </>
          )}
        </footer>
      </section>

      {pickerDayIndex !== null ? (
        <ExercisePicker
          existingNames={new Set(
            draft.days[pickerDayIndex].exercises.map(
              (exercise) => exercise.exercise_name,
            ),
          )}
          limit={7 - draft.days[pickerDayIndex].exercises.length}
          onCancel={() => setPickerDayIndex(null)}
          onConfirm={(exercises) => addExercises(pickerDayIndex, exercises)}
        />
      ) : null}
    </div>
  );
}

function NumberInput({
  label,
  value,
  min,
  max,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  onChange: (value: number) => void;
}) {
  return (
    <label>
      <span>{label}</span>
      <input
        inputMode="numeric"
        max={max}
        min={min}
        onChange={(event) => {
          const next = Number(event.target.value);
          if (Number.isFinite(next)) onChange(next);
        }}
        type="number"
        value={value}
      />
    </label>
  );
}

function ProposalConfirmation({
  proposal,
}: {
  proposal: TrainingPlanProposalResponse;
}) {
  return (
    <div className="plan-confirmation">
      <span className="plan-confirmation__icon">
        <ShieldCheck size={28} />
      </span>
      <div>
        <p className="eyebrow">替换提案 #{proposal.id}</p>
        <h3>修改已通过安全检查</h3>
        <p>
          确认后将生成新的正式计划版本，当前版本会保留在计划历史中。
        </p>
      </div>
      <div className="plan-confirmation__days">
        {proposal.plan.days.map((day) => (
          <article key={day.scheduled_date}>
            <span>{day.scheduled_date}</span>
            <strong>{translateDayName(day.name)}</strong>
            <small>{day.exercises.length} 个动作</small>
          </article>
        ))}
      </div>
    </div>
  );
}

function ExercisePicker({
  existingNames,
  limit,
  onCancel,
  onConfirm,
}: {
  existingNames: Set<string>;
  limit: number;
  onCancel: () => void;
  onConfirm: (exercises: LibraryExercise[]) => void;
}) {
  const [exercises, setExercises] = useState<LibraryExercise[]>([]);
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState<string>('胸');
  const [equipment, setEquipment] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [loadError, setLoadError] = useState('');

  useEffect(() => {
    const controller = new AbortController();
    fetch('/exercise-media/exercises.zh.json', { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error('动作数据加载失败');
        return response.json() as Promise<LibraryExercise[]>;
      })
      .then(setExercises)
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') return;
        setLoadError('动作库暂时无法加载，请刷新后重试。');
      });
    return () => controller.abort();
  }, []);

  const visibleExercises = useMemo(() => {
    const keyword = query.trim().toLocaleLowerCase();
    return exercises
      .filter((exercise) => {
        if (!keyword && exercise.category !== category) return false;
        if (equipment && exercise.equipment !== equipment) return false;
        if (!keyword) return true;
        return `${exercise.name} ${exercise.originalName} ${exercise.target} ${exercise.equipment}`
          .toLocaleLowerCase()
          .includes(keyword);
      })
      .slice(0, 80);
  }, [category, equipment, exercises, query]);

  const availableEquipment = useMemo(
    () =>
      equipmentGroups.filter((group) =>
        exercises.some(
          (exercise) =>
            exercise.category === category && exercise.equipment === group,
        ),
      ),
    [category, exercises],
  );

  const selectedExercises = exercises.filter((exercise) =>
    selectedIds.has(exercise.id),
  );

  const toggleSelection = (exercise: LibraryExercise) => {
    if (existingNames.has(exercise.name)) return;
    setSelectedIds((current) => {
      const next = new Set(current);
      if (next.has(exercise.id)) {
        next.delete(exercise.id);
      } else if (next.size < limit) {
        next.add(exercise.id);
      }
      return next;
    });
  };

  return (
    <section
      aria-labelledby="exercise-picker-title"
      aria-modal="true"
      className="exercise-picker"
      role="dialog">
      <header className="exercise-picker__header">
        <button aria-label="关闭动作选择" className="icon-button" onClick={onCancel} type="button">
          <X size={22} />
        </button>
        <label>
          <Search size={18} />
          <input
            autoFocus
            onChange={(event) => setQuery(event.target.value)}
            placeholder="输入动作名称搜索"
            type="search"
            value={query}
          />
        </label>
        <div>
          <small>还可添加</small>
          <strong>{limit - selectedIds.size}</strong>
        </div>
      </header>

      <div className="exercise-picker__body">
        <aside aria-label="动作分类" className="exercise-picker__categories">
          {exerciseCategories.map((option) => (
            <button
              className={!query && option === category ? 'is-active' : ''}
              key={option}
              onClick={() => {
                setCategory(option);
                setEquipment(null);
                setQuery('');
              }}
              type="button">
              {option}
            </button>
          ))}
        </aside>

        <main>
          <h2 id="exercise-picker-title">{query ? '搜索结果' : category}</h2>
          {!query ? (
            <nav aria-label="器械筛选" className="exercise-picker__equipment">
              {availableEquipment.map((option) => (
                <button
                  className={equipment === option ? 'is-active' : ''}
                  key={option}
                  onClick={() =>
                    setEquipment((current) =>
                      current === option ? null : option,
                    )
                  }
                  type="button">
                  {option}
                </button>
              ))}
            </nav>
          ) : null}

          {loadError ? <p className="exercise-picker__state">{loadError}</p> : null}
          {!loadError && exercises.length === 0 ? (
            <p className="exercise-picker__state">正在加载动作库……</p>
          ) : null}
          {!loadError && exercises.length > 0 && visibleExercises.length === 0 ? (
            <p className="exercise-picker__state">没有找到匹配动作。</p>
          ) : null}

          <div className="exercise-picker__grid">
            {visibleExercises.map((exercise) => {
              const selected = selectedIds.has(exercise.id);
              const exists = existingNames.has(exercise.name);
              return (
                <button
                  className={selected ? 'is-selected' : ''}
                  disabled={exists || (!selected && selectedIds.size >= limit)}
                  key={exercise.id}
                  onClick={() => toggleSelection(exercise)}
                  type="button">
                  <span>
                    <img
                      alt={`${exercise.name}动作示意图`}
                      height="140"
                      loading="lazy"
                      src={exercise.imageUrl}
                      width="140"
                    />
                    {selected ? <Check size={18} /> : <Dumbbell size={15} />}
                  </span>
                  <strong>{exercise.name}</strong>
                  <small>{exists ? '计划中已有' : exercise.equipment}</small>
                </button>
              );
            })}
          </div>
        </main>
      </div>

      <footer className="exercise-picker__footer">
        <span>已选 {selectedIds.size} 个动作</span>
        <Button
          disabled={selectedIds.size === 0}
          onClick={() => onConfirm(selectedExercises)}>
          完成添加
        </Button>
      </footer>
    </section>
  );
}
