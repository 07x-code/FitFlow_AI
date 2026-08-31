import { Dumbbell, Play, Search, Target, X } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import { PageHeader } from '../components/ui';
import {
  equipmentGroups,
  exerciseCategories,
  type LibraryExercise,
} from '../data/exercise-library';

export function ExerciseLibraryPage() {
  const [exercises, setExercises] = useState<LibraryExercise[]>([]);
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState<string>('胸');
  const [selectedExercise, setSelectedExercise] =
    useState<LibraryExercise | null>(null);
  const [loadError, setLoadError] = useState('');

  useEffect(() => {
    const controller = new AbortController();

    fetch('/exercise-media/exercises.zh.json', {
      signal: controller.signal,
    })
      .then((response) => {
        if (!response.ok) throw new Error('动作数据加载失败');
        return response.json() as Promise<LibraryExercise[]>;
      })
      .then(setExercises)
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') return;
        setLoadError('动作数据暂时无法加载，请刷新页面重试。');
      });

    return () => controller.abort();
  }, []);

  const categoryCounts = useMemo(() => {
    const counts = new Map<string, number>();
    for (const exercise of exercises) {
      counts.set(exercise.category, (counts.get(exercise.category) ?? 0) + 1);
    }
    return counts;
  }, [exercises]);

  const visibleExercises = useMemo(() => {
    const keyword = query.trim().toLocaleLowerCase();

    if (!keyword) {
      return exercises.filter((exercise) => exercise.category === category);
    }

    return exercises.filter((exercise) =>
      `${exercise.name} ${exercise.originalName} ${exercise.target} ${exercise.equipment}`
        .toLocaleLowerCase()
        .includes(keyword),
    );
  }, [category, exercises, query]);

  const groupedExercises = useMemo(
    () =>
      equipmentGroups
        .map((equipment) => ({
          equipment,
          exercises: visibleExercises.filter(
            (exercise) => exercise.equipment === equipment,
          ),
        }))
        .filter((group) => group.exercises.length > 0),
    [visibleExercises],
  );

  const scrollToEquipment = (equipment?: string) => {
    const target = equipment
      ? document.getElementById(`exercise-equipment-${equipment}`)
      : document.querySelector('.exercise-library-content');
    target?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  return (
    <div className="page exercise-library-page">
      <PageHeader
        action={
          <span className="exercise-library-count">
            {exercises.length || '…'} 个动作
          </span>
        }
        eyebrow="动作讲解与动画"
        title="动作库"
      />

      <label className="exercise-search">
        <Search aria-hidden="true" size={20} />
        <input
          onChange={(event) => setQuery(event.target.value)}
          placeholder="输入动作名字搜索"
          type="search"
          value={query}
        />
        {query ? (
          <button
            aria-label="清空搜索"
            onClick={() => setQuery('')}
            type="button">
            <X aria-hidden="true" size={17} />
          </button>
        ) : null}
      </label>

      <div className="exercise-library-workspace">
        <aside aria-label="动作分类" className="exercise-category-rail">
          {exerciseCategories.map((option) => (
            <button
              className={!query && category === option ? 'is-active' : ''}
              key={option}
              onClick={() => {
                setCategory(option);
                setQuery('');
              }}
              type="button">
              <span>{option}</span>
              <small>{categoryCounts.get(option) ?? 0}</small>
            </button>
          ))}
        </aside>

        <section className="exercise-library-content">
          <nav aria-label="器械分组" className="exercise-equipment-nav">
            <button onClick={() => scrollToEquipment()} type="button">
              置顶
            </button>
            {groupedExercises.map((group) => (
              <button
                key={group.equipment}
                onClick={() => scrollToEquipment(group.equipment)}
                type="button">
                {group.equipment}
              </button>
            ))}
          </nav>

          <div className="exercise-library-summary">
            <span>
              <strong>{visibleExercises.length}</strong> 个动作
            </span>
            <span>{query ? `“${query}”的搜索结果` : category}</span>
          </div>

          {loadError ? (
            <div className="exercise-library-empty">
              <Search aria-hidden="true" size={28} />
              <strong>加载失败</strong>
              <span>{loadError}</span>
            </div>
          ) : null}

          {!loadError && exercises.length === 0 ? (
            <div className="exercise-library-loading">
              <span />
              正在加载动作库……
            </div>
          ) : null}

          {!loadError && exercises.length > 0 && groupedExercises.length === 0 ? (
            <div className="exercise-library-empty">
              <Search aria-hidden="true" size={28} />
              <strong>没有找到匹配动作</strong>
              <span>换一个动作名称试试。</span>
            </div>
          ) : null}

          {groupedExercises.map((group) => (
            <section
              className="exercise-equipment-section"
              id={`exercise-equipment-${group.equipment}`}
              key={group.equipment}>
              <header>
                <h2>{group.equipment}</h2>
                <span>{group.exercises.length} 个</span>
              </header>
              <div className="exercise-library-grid">
                {group.exercises.map((exercise) => (
                  <button
                    className="exercise-library-card"
                    key={exercise.id}
                    onClick={() => setSelectedExercise(exercise)}
                    type="button">
                    <span className="exercise-library-card__media">
                      <img
                        alt={`${exercise.name}动作示意图`}
                        height="180"
                        loading="lazy"
                        src={exercise.imageUrl}
                        width="180"
                      />
                      <span>
                        <Play aria-hidden="true" fill="currentColor" size={11} />
                        讲解
                      </span>
                    </span>
                    <span className="exercise-library-card__copy">
                      <strong>{exercise.name}</strong>
                      <small>{exercise.target}</small>
                    </span>
                  </button>
                ))}
              </div>
            </section>
          ))}
        </section>
      </div>

      {selectedExercise ? (
        <div
          className="exercise-detail-backdrop"
          onMouseDown={(event) => {
            if (event.currentTarget === event.target) setSelectedExercise(null);
          }}>
          <article
            aria-labelledby="exercise-detail-title"
            aria-modal="true"
            className="exercise-detail-dialog"
            role="dialog">
            <header>
              <span>
                <small>{selectedExercise.category}</small>
                <h2 id="exercise-detail-title">{selectedExercise.name}</h2>
              </span>
              <button
                aria-label="关闭动作讲解"
                className="icon-button"
                onClick={() => setSelectedExercise(null)}
                type="button">
                <X aria-hidden="true" size={20} />
              </button>
            </header>

            <div className="exercise-detail-animation">
              <img
                alt={`${selectedExercise.name}动作动画`}
                height="180"
                src={selectedExercise.animationUrl}
                width="180"
              />
              <a href="https://gymvisual.com/" rel="noreferrer" target="_blank">
                © Gym visual
              </a>
            </div>

            <div className="exercise-detail-facts">
              <span>
                <Target aria-hidden="true" size={18} />
                <small>目标肌群</small>
                <strong>{selectedExercise.target}</strong>
              </span>
              <span>
                <Dumbbell aria-hidden="true" size={18} />
                <small>所需器械</small>
                <strong>{selectedExercise.equipment}</strong>
              </span>
            </div>

            <section className="exercise-detail-steps">
              <h3>动作步骤</h3>
              {selectedExercise.steps.map((step, index) => (
                <div key={`${selectedExercise.id}-${index}`}>
                  <span>{index + 1}</span>
                  <p>{step}</p>
                </div>
              ))}
            </section>

            <p className="exercise-detail-safety">
              使用可稳定控制的重量；如出现锐痛、关节疼痛或明显不适，请立即停止训练。
            </p>
          </article>
        </div>
      ) : null}
    </div>
  );
}
