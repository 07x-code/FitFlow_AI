const exerciseNames: Record<string, string> = {
  'Goblet Squat': '高脚杯深蹲',
  'Chest Press': '器械推胸',
  'Seated Row': '坐姿划船',
  'Dumbbell Romanian Deadlift': '哑铃罗马尼亚硬拉',
  'Leg Press': '腿举',
  'Lat Pulldown': '高位下拉',
  'Dumbbell Shoulder Press': '哑铃肩推',
  'Glute Bridge': '臀桥',
  'Split Squat': '分腿蹲',
  'Incline Dumbbell Press': '上斜哑铃卧推',
  'Cable Row': '绳索划船',
  'Hamstring Curl': '腿弯举',
  'Step Up': '登台阶',
  'Assisted Pull Up': '辅助引体向上',
  'Push Up': '俯卧撑',
  'Cable Pallof Press': '绳索帕洛夫推举',
  'Flat Barbell Bench Press': '平板杠铃卧推',
  'Tricep Rope Pushdown': '绳索下压',
  Skullcrushers: '仰卧臂屈伸',
  'Seated Dumbbell Shoulder Press': '坐姿哑铃肩推',
  'Lateral Raise': '侧平举',
  'Barbell Bicep Curl': '杠铃弯举',
  'Hammer Curl': '锤式弯举',
  'Pull Up': '引体向上',
  'Seated Cable Row': '坐姿绳索划船',
  'Face Pulls': '面拉',
};

const dayNames: Record<string, string> = {
  'Day 1 - Full Body A': '第 1 天 · 全身训练（一）',
  'Day 2 - Full Body B': '第 2 天 · 全身训练（二）',
  'Day 3 - Full Body C': '第 3 天 · 全身训练（三）',
  'Day 4 - Full Body D': '第 4 天 · 全身训练（四）',
};

export function translateExerciseName(name: string) {
  if (exerciseNames[name]) {
    return exerciseNames[name];
  }

  return /[a-z]/i.test(name) ? '自定义训练动作' : name;
}

export function translateDayName(name: string) {
  if (dayNames[name]) {
    return dayNames[name];
  }

  const translated = name
    .replace(/Day\s*(\d+)/gi, '第 $1 天')
    .replace(/Full Body/gi, '全身训练');
  return /[a-z]/i.test(translated) ? translated.replace(/[a-z]+/gi, '').trim() : translated;
}

export function translatePlanText(text: string) {
  return text
    .replaceAll('muscle_gain', '增肌')
    .replaceAll('fat_loss', '减脂')
    .replaceAll('general_fitness', '提升综合体能');
}
