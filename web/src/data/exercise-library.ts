export type LibraryExercise = {
  id: string;
  name: string;
  originalName: string;
  category: string;
  equipment: string;
  target: string;
  imageUrl: string;
  animationUrl: string;
  steps: string[];
};

export const exerciseCategories = [
  '胸',
  '上胸',
  '中下胸',
  '背',
  '腿',
  '肩',
  '前锯肌',
  '斜方肌',
  '二头',
  '三头',
  '小腿',
  '前臂',
  '颈部',
  '臀部',
  '功能性',
  '核心稳定',
  '腹部',
  '热身动作',
  '拉伸',
  '有氧',
] as const;

export const equipmentGroups = [
  '杠铃',
  '哑铃',
  '壶铃',
  '绳索',
  '史密斯',
  '器械',
  '自重',
  '弹力带',
  '辅助器械',
  '其他',
] as const;
