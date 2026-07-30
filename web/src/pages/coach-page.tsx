import { ArrowUp, Bot, Layers3, ShieldCheck, Sparkles } from 'lucide-react';
import { useState } from 'react';
import type { FormEvent } from 'react';

import { Card, Chip, PageHeader } from '../components/ui';

type Message = {
  id: number;
  role: 'assistant' | 'user';
  content: string;
};

const initialMessages: Message[] = [
  {
    id: 1,
    role: 'assistant',
    content:
      '晚上好，Alex。今天安排的是全身训练 A，准备度 86。你可以问我动作、重量或恢复方面的问题。',
  },
  {
    id: 2,
    role: 'user',
    content: '今天高脚杯深蹲应该用多重？',
  },
  {
    id: 3,
    role: 'assistant',
    content:
      '上次你用 20 kg 完成 3×10，平均 RPE 7。今天先保持 20 kg；如果前两组动作稳定且 RPE 不超过 7，最后一组可以尝试 22 kg。',
  },
];

const suggestions = [
  '今天应该加重量吗？',
  '训练前怎么热身？',
  '解释这周的计划',
];

export function CoachPage() {
  const [messages, setMessages] = useState(initialMessages);
  const [draft, setDraft] = useState('');

  const send = (message: string) => {
    const content = message.trim();
    if (!content) {
      return;
    }

    const nextId = Date.now();
    setMessages((current) => [
      ...current,
      { id: nextId, role: 'user', content },
      {
        id: nextId + 1,
        role: 'assistant',
        content:
          '我会结合你的画像、当前计划和训练记录回答。当前是 UI 演示；接入 FastAPI 后，这里会展示真实模型回复与知识来源。',
      },
    ]);
    setDraft('');
  };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    send(draft);
  };

  return (
    <div className="page page--coach">
      <PageHeader
        action={
          <span className="online-pill">
            <i />
            在线
          </span>
        }
        eyebrow="安全规则已启用"
        title="AI Coach"
      />

      <div className="coach-layout">
        <section className="chat-panel">
          <div className="context-banner">
            <Layers3 size={19} />
            <span>
              <strong>已加载训练上下文</strong>
              用户画像 · 第 4 周计划 · 2 条长期记忆
            </span>
          </div>

          <div aria-live="polite" className="message-list">
            {messages.map((message) => (
              <div className={`message message--${message.role}`} key={message.id}>
                {message.role === 'assistant' ? (
                  <span className="message__avatar">
                    <Sparkles size={16} />
                  </span>
                ) : null}
                <p>{message.content}</p>
              </div>
            ))}
          </div>

          <div className="suggestion-row">
            {suggestions.map((suggestion) => (
              <Chip key={suggestion} onClick={() => send(suggestion)}>
                {suggestion}
              </Chip>
            ))}
          </div>

          <form className="chat-composer" onSubmit={submit}>
            <textarea
              aria-label="向 AI Coach 提问"
              onChange={(event) => setDraft(event.target.value)}
              placeholder="询问训练、动作或恢复……"
              rows={1}
              value={draft}
            />
            <button aria-label="发送消息" type="submit">
              <ArrowUp size={20} />
            </button>
          </form>
        </section>

        <aside className="coach-context">
          <Card>
            <span className="colored-icon">
              <Bot size={20} />
            </span>
            <p className="eyebrow">回答依据</p>
            <h3>当前上下文</h3>
            <ul>
              <li>目标：增肌与基础力量</li>
              <li>频率：每周训练 3 天</li>
              <li>风险等级：低</li>
              <li>最近训练 RPE：7.1</li>
            </ul>
          </Card>
          <Card className="safety-card">
            <span className="colored-icon colored-icon--orange">
              <ShieldCheck size={20} />
            </span>
            <div>
              <strong>安全边界</strong>
              <p>不诊断疾病，不提供康复处方，疼痛问题优先停止训练。</p>
            </div>
          </Card>
        </aside>
      </div>
    </div>
  );
}

