import { copyFile, mkdir, readFile, writeFile } from 'node:fs/promises';
import { basename, join, resolve } from 'node:path';

const sourceRoot = resolve(process.argv[2] ?? 'F:/python_project/exercises-dataset');
const targetRoot = resolve('public/exercise-media');
const sourceData = JSON.parse(
  await readFile(join(sourceRoot, 'data/exercises.json'), 'utf8'),
);

const targetLabels = {
  abs: '腹肌',
  pectorals: '胸大肌',
  biceps: '肱二头肌',
  glutes: '臀肌',
  delts: '三角肌',
  triceps: '肱三头肌',
  'upper back': '上背部',
  lats: '背阔肌',
  calves: '小腿肌群',
  quads: '股四头肌',
  forearms: '前臂肌群',
  'cardiovascular system': '心肺系统',
  hamstrings: '腘绳肌',
  spine: '脊柱稳定肌',
  traps: '斜方肌',
  adductors: '大腿内收肌',
  'serratus anterior': '前锯肌',
  abductors: '髋外展肌',
  'levator scapulae': '肩胛提肌',
};

const equipmentLabels = {
  barbell: '杠铃',
  'ez barbell': '杠铃',
  'olympic barbell': '杠铃',
  'trap bar': '杠铃',
  dumbbell: '哑铃',
  kettlebell: '壶铃',
  cable: '绳索',
  rope: '绳索',
  'smith machine': '史密斯',
  'leverage machine': '器械',
  'sled machine': '器械',
  'elliptical machine': '器械',
  'stationary bike': '器械',
  'stepmill machine': '器械',
  'upper body ergometer': '器械',
  'skierg machine': '器械',
  'body weight': '自重',
  band: '弹力带',
  'resistance band': '弹力带',
  weighted: '辅助器械',
  assisted: '辅助器械',
  'stability ball': '辅助器械',
  'medicine ball': '辅助器械',
  roller: '辅助器械',
  'bosu ball': '辅助器械',
  'wheel roller': '辅助器械',
};

const phraseLabels = [
  ['barbell bench press', '杠铃卧推'],
  ['dumbbell bench press', '哑铃卧推'],
  ['shoulder press', '肩上推举'],
  ['military press', '军式推举'],
  ['chest press', '胸部推举'],
  ['biceps curl', '二头弯举'],
  ['triceps pushdown', '三头下压'],
  ['romanian deadlift', '罗马尼亚硬拉'],
  ['stiff leg deadlift', '直腿硬拉'],
  ['lat pulldown', '高位下拉'],
  ['seated row', '坐姿划船'],
  ['upright row', '直立划船'],
  ['lateral raise', '侧平举'],
  ['front raise', '前平举'],
  ['rear delt', '三角肌后束'],
  ['calf raise', '提踵'],
  ['hip thrust', '臀推'],
  ['glute bridge', '臀桥'],
  ['leg press', '腿举'],
  ['leg extension', '腿屈伸'],
  ['leg curl', '腿弯举'],
  ['wrist curl', '腕弯举'],
  ['preacher curl', '牧师凳弯举'],
  ['concentration curl', '集中弯举'],
  ['hammer curl', '锤式弯举'],
  ['russian twist', '俄罗斯转体'],
  ['jump rope', '跳绳'],
  ['mountain climber', '登山跑'],
  ['good morning', '早安式'],
  ['pull-up', '引体向上'],
  ['push-up', '俯卧撑'],
  ['sit-up', '仰卧起坐'],
  ['step-up', '登台阶'],
];

const wordLabels = {
  dumbbell: '哑铃', barbell: '杠铃', cable: '绳索', band: '弹力带',
  kettlebell: '壶铃', smith: '史密斯', lever: '器械', machine: '器械',
  weighted: '负重', assisted: '辅助', bodyweight: '自重', body: '身体',
  bench: '卧推凳', ball: '球', stability: '稳定球', medicine: '药球',
  roller: '健腹轮', rope: '绳索', wheel: '轮式', bosu: '波速球',
  curl: '弯举', press: '推举', raise: '抬举', row: '划船', squat: '深蹲',
  deadlift: '硬拉', extension: '伸展', stretch: '拉伸', fly: '飞鸟',
  push: '推', pull: '拉', pulldown: '下拉', pullover: '上拉',
  lunge: '弓步', crunch: '卷腹', plank: '平板支撑', bridge: '桥式',
  dip: '臂屈伸', dips: '臂屈伸', shrug: '耸肩', kickback: '后踢',
  twist: '转体', rotation: '旋转', swing: '摆动', snatch: '抓举',
  clean: '翻举', jerk: '挺举', jump: '跳跃', run: '跑步', walk: '行走',
  walking: '行走', bend: '侧屈', hyperextension: '背伸', touch: '触碰',
  lift: '抬起', throw: '投掷', hang: '悬垂', hanging: '悬垂',
  seated: '坐姿', standing: '站姿', lying: '仰卧', prone: '俯卧',
  supine: '仰卧', kneeling: '跪姿', incline: '上斜', decline: '下斜',
  upright: '直立', bent: '俯身', overhead: '过顶', floor: '地面',
  wall: '靠墙', front: '前侧', rear: '后侧', side: '侧向', lateral: '侧向',
  reverse: '反向', alternate: '交替', alternating: '交替', single: '单侧',
  one: '单臂', two: '双侧', straight: '直臂', full: '全程',
  wide: '宽握', narrow: '窄握', close: '窄距', neutral: '对握',
  parallel: '平行握', grip: '握法', arm: '手臂', arms: '双臂',
  leg: '腿部', legs: '双腿', calf: '小腿', hip: '髋部', knee: '膝部',
  knees: '双膝', chest: '胸部', shoulder: '肩部', back: '背部',
  biceps: '肱二头肌', bicep: '肱二头肌', triceps: '肱三头肌',
  tricep: '肱三头肌', delt: '三角肌', glute: '臀肌', hamstring: '腘绳肌',
  wrist: '手腕', neck: '颈部', lat: '背阔肌', core: '核心',
  inner: '内侧', lower: '下部', high: '高位', low: '低位',
  forward: '向前', vertical: '垂直', cross: '交叉', split: '分腿',
  sumo: '相扑式', hack: '哈克', russian: '俄罗斯式', zottman: '佐特曼式',
  spider: '蜘蛛式', concentration: '集中式', preacher: '牧师凳',
  military: '军式', bicycle: '自行车式', air: '空中', burpee: '波比跳',
  bike: '自行车', heel: '脚跟', heels: '双脚跟', toucher: '触碰', touchers: '触碰',
  ankle: '脚踝', circle: '环绕', circles: '环绕', quadriceps: '股四头肌',
  chin: '反手引体', planche: '俄式挺身', inversion: '倒立', inverted: '倒置',
  flexion: '屈曲', abduction: '外展', adduction: '内收',
};

const ignoredWords = new Set([
  'a', 'and', 'at', 'behind', 'female', 'for', 'in', 'male', 'of', 'on', 'pov',
  'the', 'to', 'v', 'version', 'with', 'without',
]);

function classifyExercise(exercise) {
  const name = exercise.name.toLowerCase();

  if (exercise.target === 'levator scapulae' || exercise.body_part === 'neck') return '颈部';
  if (/warm.?up|ankle circles|wrist circles|high knee against wall/.test(name)) {
    return '热身动作';
  }
  if (/stretch|mobility|rollout massage/.test(name)) return '拉伸';
  if (/burpee|bear crawl|farmers? walk|mountain climber|tire|battle rope/.test(name)) {
    return '功能性';
  }
  if (exercise.target === 'serratus anterior') return '前锯肌';
  if (exercise.target === 'traps') return '斜方肌';
  if (exercise.target === 'biceps') return '二头';
  if (exercise.target === 'triceps') return '三头';
  if (exercise.target === 'calves') return '小腿';
  if (exercise.target === 'forearms') return '前臂';
  if (exercise.target === 'glutes') return '臀部';
  if (exercise.body_part === 'cardio') return '有氧';
  if (exercise.target === 'abs' || exercise.target === 'spine') {
    return /plank|dead bug|bird dog|pallof|hollow|rollout/.test(name)
      ? '核心稳定'
      : '腹部';
  }
  if (exercise.target === 'pectorals') {
    if (/incline|upward/.test(name)) return '上胸';
    if (/decline|lower/.test(name)) return '中下胸';
    return '胸';
  }
  if (exercise.target === 'delts') return '肩';
  if (exercise.target === 'upper back' || exercise.target === 'lats') return '背';
  return '腿';
}

function translateName(exercise) {
  let value = exercise.name.toLowerCase().replaceAll('°', '度');

  for (const [source, translated] of phraseLabels) {
    value = value.replaceAll(source, ` ${translated} `);
  }

  const parts = value.match(/[\u3400-\u9fff]+|[a-z]+|\d+/g) ?? [];
  const translated = parts
    .map((part) => {
      if (/^[\u3400-\u9fff]+$/.test(part)) return part;
      if (/^\d+$/.test(part)) return part;
      if (ignoredWords.has(part)) return '';
      return wordLabels[part] ?? '';
    })
    .filter(Boolean)
    .join('')
    .replace(/(杠铃|哑铃|绳索|器械|弹力带)\1/g, '$1');

  if (translated.length >= 2) return translated;

  const equipment = equipmentLabels[exercise.equipment] ?? '辅助器械';
  const target = targetLabels[exercise.target] ?? '全身';
  return `${equipment}${target}训练`;
}

const exercises = sourceData.map((exercise) => ({
  id: exercise.id,
  name: translateName(exercise),
  originalName: exercise.name,
  category: classifyExercise(exercise),
  equipment: equipmentLabels[exercise.equipment] ?? '其他',
  target: targetLabels[exercise.target] ?? '全身',
  imageUrl: `/exercise-media/${exercise.image}`,
  animationUrl: `/exercise-media/${exercise.gif_url}`,
  steps: exercise.instruction_steps.zh,
}));

const usedNames = new Map();
for (const exercise of exercises) {
  const count = (usedNames.get(exercise.name) ?? 0) + 1;
  usedNames.set(exercise.name, count);
  if (count > 1) exercise.name = `${exercise.name} · ${count}`;
}

await mkdir(join(targetRoot, 'images'), { recursive: true });
await mkdir(join(targetRoot, 'videos'), { recursive: true });

for (const exercise of sourceData) {
  await copyFile(
    join(sourceRoot, exercise.image),
    join(targetRoot, 'images', basename(exercise.image)),
  );
  await copyFile(
    join(sourceRoot, exercise.gif_url),
    join(targetRoot, 'videos', basename(exercise.gif_url)),
  );
}

await copyFile(join(sourceRoot, 'NOTICE.md'), join(targetRoot, 'NOTICE.md'));
await copyFile(join(sourceRoot, 'LICENSE'), join(targetRoot, 'DATA-LICENSE.txt'));
await writeFile(
  join(targetRoot, 'exercises.zh.json'),
  JSON.stringify(exercises),
  'utf8',
);

console.log(`已导入 ${exercises.length} 个动作。`);
