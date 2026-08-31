export type Exercise = {
  id: string;
  name: string;
  target: string;
  muscle: string;
  sets: number;
  reps: string;
  rpe: number;
  lastWeight: number;
};

export type WorkoutPlan = {
  id: string;
  name: string;
  focus: string;
  duration: number;
  calories: number;
  exercises: Exercise[];
};

export const weekDays = [
  { day: '一', date: 28, state: 'done' },
  { day: '二', date: 29, state: 'rest' },
  { day: '三', date: 30, state: 'today' },
  { day: '四', date: 31, state: 'upcoming' },
  { day: '五', date: 1, state: 'upcoming' },
] as const;

export const todayWorkout: WorkoutPlan = {
  id: 'full-body-a',
  name: '全身训练 A',
  focus: '胸 · 背 · 腿',
  duration: 58,
  calories: 360,
  exercises: [
    {
      id: 'goblet-squat',
      name: '高脚杯深蹲',
      target: '股四头肌',
      muscle: '腿部',
      sets: 3,
      reps: '8–12',
      rpe: 7,
      lastWeight: 20,
    },
    {
      id: 'chest-press',
      name: '器械推胸',
      target: '胸大肌',
      muscle: '胸部',
      sets: 3,
      reps: '8–12',
      rpe: 7,
      lastWeight: 35,
    },
    {
      id: 'lat-pulldown',
      name: '高位下拉',
      target: '背阔肌',
      muscle: '背部',
      sets: 3,
      reps: '10–12',
      rpe: 7,
      lastWeight: 40,
    },
    {
      id: 'romanian-deadlift',
      name: '哑铃罗马尼亚硬拉',
      target: '腘绳肌',
      muscle: '腿后侧',
      sets: 3,
      reps: '8–10',
      rpe: 7,
      lastWeight: 16,
    },
  ],
};

export const weeklyPlans: WorkoutPlan[] = [
  todayWorkout,
  {
    ...todayWorkout,
    id: 'full-body-b',
    name: '全身训练 B',
    focus: '肩 · 腿 · 核心',
    duration: 52,
    calories: 330,
  },
  {
    ...todayWorkout,
    id: 'full-body-c',
    name: '全身训练 C',
    focus: '背 · 臀 · 手臂',
    duration: 55,
    calories: 345,
  },
];

export const recentWorkouts = [
  {
    title: '全身训练 C',
    date: '7 月 28 日',
    duration: '54 分钟',
    volume: '3,860 kg',
  },
  {
    title: '全身训练 B',
    date: '7 月 25 日',
    duration: '49 分钟',
    volume: '3,420 kg',
  },
];

