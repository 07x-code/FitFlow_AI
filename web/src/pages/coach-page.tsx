import {
  AlertCircle,
  ArrowUp,
  BookOpen,
  Bot,
  Layers3,
  RefreshCw,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import type { FormEvent, KeyboardEvent } from 'react';

import {
  FitFlowApiError,
  fitFlowApi,
  type CoachChatResponse,
} from '../api/client';
import { Card, Chip, PageHeader } from '../components/ui';
import './coach-api.css';

type Message = {
  id: number;
  role: 'assistant' | 'user';
  content: string;
  response?: CoachChatResponse;
};

type ConnectionStatus = 'checking' | 'online' | 'offline';

type RequestFailure = {
  question: string;
  message: string;
};

const USER_ID = 'demo-user';

const initialMessages: Message[] = [
  {
    id: 1,
    role: 'assistant',
    content:
      '你好，我是 FitFlow AI Coach。发送问题后，我会通过 FastAPI 读取你的画像、最新计划、长期记忆和本地健身知识，再返回真实回答。',
  },
];

const suggestions = [
  '今天应该加重量吗？',
  'RPE 是什么？',
  '解释这周的计划',
];

function describeError(error: unknown) {
  if (error instanceof FitFlowApiError) {
    if (error.status === 404) {
      return `后端未找到 ${USER_ID} 的用户画像。请先用现有 Streamlit 流程保存该用户画像。`;
    }

    if (error.status === 422) {
      return '问题格式未通过后端校验，请输入 1 到 1000 个字符。';
    }

    if (typeof error.detail === 'string' && error.detail.trim()) {
      return error.detail;
    }

    return `FastAPI 返回 ${error.status}，请查看后端终端日志。`;
  }

  if (error instanceof TypeError) {
    return '无法连接 FastAPI。请确认后端已在 127.0.0.1:8000 启动。';
  }

  return '请求失败，请查看浏览器控制台和 FastAPI 终端日志。';
}

export function CoachPage() {
  const [messages, setMessages] = useState(initialMessages);
  const [draft, setDraft] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [failure, setFailure] = useState<RequestFailure | null>(null);
  const [connection, setConnection] =
    useState<ConnectionStatus>('checking');
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let active = true;

    void fitFlowApi
      .health()
      .then(() => {
        if (active) {
          setConnection('online');
        }
      })
      .catch(() => {
        if (active) {
          setConnection('offline');
        }
      });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({
      behavior: 'smooth',
      block: 'nearest',
    });
  }, [failure, isSending, messages]);

  const send = async (message: string, appendUser = true) => {
    const content = message.trim();
    if (!content || isSending) {
      return;
    }

    const nextId = Date.now();
    if (appendUser) {
      setMessages((current) => [
        ...current,
        { id: nextId, role: 'user', content },
      ]);
    }

    setDraft('');
    setFailure(null);
    setIsSending(true);

    try {
      const response = await fitFlowApi.chatWithCoach(USER_ID, content);
      setMessages((current) => [
        ...current,
        {
          id: nextId + 1,
          role: 'assistant',
          content: response.answer,
          response,
        },
      ]);
      setConnection('online');
    } catch (error) {
      setFailure({
        question: content,
        message: describeError(error),
      });
      setConnection(error instanceof FitFlowApiError ? 'online' : 'offline');
    } finally {
      setIsSending(false);
    }
  };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    void send(draft);
  };

  const submitOnEnter = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      void send(draft);
    }
  };

  const connectionText = {
    checking: '检查连接',
    online: '后端在线',
    offline: '后端离线',
  }[connection];

  return (
    <div className="page page--coach">
      <PageHeader
        action={
          <span className={`online-pill is-${connection}`}>
            <i />
            {connectionText}
          </span>
        }
        eyebrow="真实 FastAPI 对话"
        title="AI Coach"
      />

      <div className="coach-layout">
        <section className="chat-panel">
          <div className="context-banner">
            <Layers3 size={19} />
            <span>
              <strong>后端动态加载训练上下文</strong>
              用户 {USER_ID} · 画像 · 最新计划 · 长期记忆 · 本地知识库
            </span>
          </div>

          <div aria-live="polite" aria-busy={isSending} className="message-list">
            {messages.map((message) => (
              <div className={`message message--${message.role}`} key={message.id}>
                {message.role === 'assistant' ? (
                  <span className="message__avatar">
                    <Sparkles size={16} />
                  </span>
                ) : null}
                <div className="message__body">
                  <p>{message.content}</p>
                  {message.response ? (
                    <ResponseEvidence response={message.response} />
                  ) : null}
                </div>
              </div>
            ))}

            {isSending ? (
              <div className="message message--assistant message--loading">
                <span className="message__avatar">
                  <Sparkles size={16} />
                </span>
                <div className="message__body">
                  <span className="typing-dots" aria-label="AI Coach 正在回答">
                    <i />
                    <i />
                    <i />
                  </span>
                  <small>正在查询画像、计划和知识库……</small>
                </div>
              </div>
            ) : null}

            {failure ? (
              <div className="coach-error" role="alert">
                <AlertCircle size={19} />
                <span>
                  <strong>本次请求失败</strong>
                  <small>{failure.message}</small>
                </span>
                <button
                  disabled={isSending}
                  onClick={() => void send(failure.question, false)}
                  type="button">
                  <RefreshCw size={15} />
                  重试
                </button>
              </div>
            ) : null}
            <div ref={endRef} />
          </div>

          <div className="suggestion-row">
            {suggestions.map((suggestion) => (
              <Chip
                key={suggestion}
                onClick={() => void send(suggestion)}>
                {suggestion}
              </Chip>
            ))}
          </div>

          <form className="chat-composer" onSubmit={submit}>
            <textarea
              aria-label="向 AI Coach 提问"
              disabled={isSending}
              maxLength={1000}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={submitOnEnter}
              placeholder="询问训练、动作或恢复……"
              rows={1}
              value={draft}
            />
            <button
              aria-label="发送消息"
              disabled={isSending || !draft.trim()}
              type="submit">
              <ArrowUp size={20} />
            </button>
          </form>
          <p className="composer-help">
            Enter 发送，Shift + Enter 换行 · 当前用户：{USER_ID}
          </p>
        </section>

        <aside className="coach-context">
          <Card>
            <span className="colored-icon">
              <Bot size={20} />
            </span>
            <p className="eyebrow">真实请求链路</p>
            <h3>回答由后端生成</h3>
            <ul>
              <li>POST /api/coach/chat</li>
              <li>X-User-ID: {USER_ID}</li>
              <li>模型与 Key 使用后端配置</li>
              <li>前端不保存千问 Key</li>
            </ul>
          </Card>
          <Card className="safety-card">
            <span className="colored-icon colored-icon--orange">
              <ShieldCheck size={20} />
            </span>
            <div>
              <strong>安全边界</strong>
              <p>后端规则优先执行；高风险情况不会调用大模型生成训练建议。</p>
            </div>
          </Card>
        </aside>
      </div>
    </div>
  );
}

function ResponseEvidence({ response }: { response: CoachChatResponse }) {
  return (
    <div className="response-evidence">
      <div className="response-meta">
        <span className={`safety-level is-${response.safety_level}`}>
          安全等级：{response.safety_level}
        </span>
        {response.referenced_plan_id ? (
          <span>引用计划 #{response.referenced_plan_id}</span>
        ) : null}
      </div>

      {response.knowledge_sources.length > 0 ? (
        <div className="knowledge-sources">
          <div className="knowledge-sources__title">
            <BookOpen size={15} />
            本地知识依据
          </div>
          {response.knowledge_sources.map((source) => (
            <article key={`${source.category}-${source.title}`}>
              <span>{source.category}</span>
              <strong>{source.title}</strong>
              <p>{source.summary}</p>
            </article>
          ))}
        </div>
      ) : null}
    </div>
  );
}

