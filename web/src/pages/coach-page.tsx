import {
  AlertCircle,
  ArrowUp,
  BookOpen,
  Bot,
  CalendarDays,
  CheckCircle2,
  Layers3,
  PencilLine,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  XCircle,
} from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import type { FormEvent, KeyboardEvent } from 'react';
import { Link } from 'react-router';

import {
  FitFlowApiError,
  fitFlowApi,
  type CoachChatResponse,
  type ProposalDecision,
  type TrainingPlanProposalResponse,
} from '../api/client';
import { useAuth } from '../auth';
import { Button, Card, Chip, PageHeader } from '../components/ui';
import {
  translateDayName,
  translateExerciseName,
  translatePlanText,
} from '../utils/plan-labels';
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

const initialMessages: Message[] = [
  {
    id: 1,
    role: 'assistant',
    content:
      '你好，我是 FitFlow AI 教练。发送问题后，我会读取你的画像、最新计划、长期记忆和健身知识，再给出针对性的回答。',
  },
];

const suggestions = [
  '今天应该加重量吗？',
  'RPE 是什么？',
  '解释这周的计划',
];

const planningVerbs = ['制定', '指定', '安排', '生成', '设计', '做一份'];
const revisionWords = ['修改', '调整', '改成', '换成', '不要', '增加', '减少', '没时间'];
const approvalPhrases = ['同意', '采用', '确认', '就按这版', '这版可以'];

function isPlanningRequest(message: string) {
  return (
    message.includes('计划') &&
    planningVerbs.some((verb) => message.includes(verb))
  );
}

function isRevisionRequest(message: string) {
  return revisionWords.some((word) => message.includes(word));
}

function isApprovalRequest(message: string) {
  const normalized = message.replace(/[，。！？!\s]/g, '');
  return approvalPhrases.some((phrase) => normalized === phrase);
}

function describeError(error: unknown) {
  if (error instanceof FitFlowApiError) {
    if (error.status === 404) {
      return '当前账号还没有训练画像，请先在个人中心完成画像设置。';
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
  const { user } = useAuth();
  const [messages, setMessages] = useState(initialMessages);
  const [draft, setDraft] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [isPlanning, setIsPlanning] = useState(false);
  const [isRevising, setIsRevising] = useState(false);
  const [isDeciding, setIsDeciding] = useState(false);
  const [proposal, setProposal] =
    useState<TrainingPlanProposalResponse | null>(null);
  const [proposalError, setProposalError] = useState<string | null>(null);
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

        return fitFlowApi.listTrainingPlanProposals();
      })
      .then((response) => {
        if (active) {
          setProposal(response.proposals[0] ?? null);
        }
      })
      .catch((error) => {
        if (active) {
          if (error instanceof FitFlowApiError) {
            setConnection('online');
            setProposalError(describeError(error));
          } else {
            setConnection('offline');
          }
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
  }, [failure, isDeciding, isPlanning, isRevising, isSending, messages, proposal]);

  const send = async (message: string, appendUser = true) => {
    const content = message.trim();
    if (!content || isSending || isPlanning || isRevising || isDeciding) {
      return;
    }

    if (proposal?.status === 'pending' && isApprovalRequest(content)) {
      setMessages((current) => [
        ...current,
        { id: Date.now(), role: 'user', content },
      ]);
      setDraft('');
      await decideProposal('approve');
      return;
    }

    if (
      proposal &&
      ['pending', 'approved'].includes(proposal.status) &&
      isRevisionRequest(content)
    ) {
      setMessages((current) => [
        ...current,
        { id: Date.now(), role: 'user', content },
      ]);
      setDraft('');
      await reviseProposal(content);
      return;
    }

    if (isPlanningRequest(content)) {
      await createProposal(content);
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
      const response = await fitFlowApi.chatWithCoach(content);
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

  const createProposal = async (requestText = '帮我制定下周的训练计划') => {
    const canCreate =
      proposal === null ||
      proposal.status === 'rejected' ||
      proposal.status === 'superseded';
    if (isPlanning || isRevising || isDeciding) {
      return;
    }

    const nextId = Date.now();
    setMessages((current) => [
      ...current,
      {
        id: nextId,
        role: 'user',
        content: requestText,
      },
    ]);
    setDraft('');

    if (!canCreate) {
      setMessages((current) => [
        ...current,
        {
          id: nextId + 1,
          role: 'assistant',
          content:
            proposal?.status === 'approved'
              ? '下周计划已经同步。如需变化，请在计划卡片中选择“调整这份计划”。'
              : '下周计划正在等待你确认，请在计划卡片中选择采用、修改或暂不采用。',
        },
      ]);
      return;
    }
    setProposalError(null);
    setIsPlanning(true);

    try {
      const created = await fitFlowApi.createTrainingPlanProposal(
        requestText,
      );
      setProposal(created);
      setMessages((current) => [
        ...current,
        {
          id: nextId + 1,
          role: 'assistant',
          content: '下周计划已经生成。请检查训练日和动作，确认后再同步为正式计划。',
        },
      ]);
      setConnection('online');
    } catch (error) {
      setProposalError(describeError(error));
      setConnection(error instanceof FitFlowApiError ? 'online' : 'offline');
    } finally {
      setIsPlanning(false);
    }
  };

  const reviseProposal = async (feedback: string) => {
    if (
      !proposal ||
      !['pending', 'approved'].includes(proposal.status) ||
      isPlanning ||
      isRevising ||
      isDeciding
    ) {
      return;
    }

    setProposalError(null);
    setIsRevising(true);

    try {
      const revised = await fitFlowApi.reviseTrainingPlanProposal(
        proposal.id,
        feedback,
      );
      setProposal(revised);
      setMessages((current) => [
        ...current,
        {
          id: Date.now(),
          role: 'assistant',
          content: `已按你的意见生成第 ${revised.revision} 版计划，请再次确认。`,
        },
      ]);
      setConnection('online');
    } catch (error) {
      setProposalError(describeError(error));
      setConnection(error instanceof FitFlowApiError ? 'online' : 'offline');
    } finally {
      setIsRevising(false);
    }
  };

  const decideProposal = async (decision: ProposalDecision) => {
    if (!proposal || proposal.status !== 'pending' || isDeciding) {
      return;
    }

    setProposalError(null);
    setIsDeciding(true);

    try {
      const decided = await fitFlowApi.decideTrainingPlanProposal(
        proposal.id,
        decision,
      );
      setProposal(decided);
      setMessages((current) => [
        ...current,
        {
          id: Date.now(),
          role: 'assistant',
          content:
            decision === 'approve'
              ? '计划已确认，并已同步到训练计划。'
              : '这份计划已停止采用，你可以重新制定一份。',
        },
      ]);
      setConnection('online');
    } catch (error) {
      setProposalError(describeError(error));
      setConnection(error instanceof FitFlowApiError ? 'online' : 'offline');
    } finally {
      setIsDeciding(false);
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
        eyebrow="智能训练助手"
        title="AI 教练"
      />

      <div className="coach-layout">
        <section className="chat-panel">
          <div className="context-banner">
            <Layers3 size={19} />
            <span>
              <strong>后端动态加载训练上下文</strong>
              {user?.display_name} · 画像 · 最新计划 · 长期记忆 · 本地知识库
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
                  <span className="typing-dots" aria-label="AI 教练正在回答">
                    <i />
                    <i />
                    <i />
                  </span>
                  <small>正在查询画像、计划和知识库……</small>
                </div>
              </div>
            ) : null}

            {isPlanning ? (
              <div className="message message--assistant message--loading">
                <span className="message__avatar">
                  <Sparkles size={16} />
                </span>
                <div className="message__body">
                  <span className="typing-dots" aria-label="正在制定训练计划">
                    <i />
                    <i />
                    <i />
                  </span>
                  <small>正在读取用户画像并执行安全检查……</small>
                </div>
              </div>
            ) : null}

            {isRevising ? (
              <div className="message message--assistant message--loading">
                <span className="message__avatar">
                  <Sparkles size={16} />
                </span>
                <div className="message__body">
                  <span className="typing-dots" aria-label="正在修改训练计划">
                    <i />
                    <i />
                    <i />
                  </span>
                  <small>正在根据你的意见生成新版本并重新检查安全性……</small>
                </div>
              </div>
            ) : null}

            {proposal ? (
              <ProposalCard
                busy={isDeciding}
                onCreate={() => void createProposal()}
                onDecision={(decision) => void decideProposal(decision)}
                onRevision={(feedback) => void reviseProposal(feedback)}
                proposal={proposal}
                revising={isRevising}
              />
            ) : null}

            {proposalError ? (
              <div className="coach-error" role="alert">
                <AlertCircle size={19} />
                <span>
                  <strong>训练计划请求失败</strong>
                  <small>{proposalError}</small>
                </span>
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
                  disabled={isSending || isPlanning || isRevising || isDeciding}
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
            {proposal?.status === 'approved' ? (
              <Chip tone="green">
                <CheckCircle2 size={15} />
                下周计划已同步
              </Chip>
            ) : proposal?.status === 'pending' ||
              proposal?.status === 'approving' ? (
              <Chip tone="blue">
                <CalendarDays size={15} />
                下周计划待确认
              </Chip>
            ) : (
              <Chip onClick={() => void createProposal()} tone="green">
                <CalendarDays size={15} />
                制定下周计划
              </Chip>
            )}
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
              aria-label="向 AI 教练提问"
              disabled={isSending || isPlanning || isRevising || isDeciding}
              maxLength={1000}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={submitOnEnter}
              placeholder="询问训练、动作或恢复……"
              rows={1}
              value={draft}
            />
            <button
              aria-label="发送消息"
              disabled={isSending || isPlanning || isRevising || isDeciding || !draft.trim()}
              type="submit">
              <ArrowUp size={20} />
            </button>
          </form>
          <p className="composer-help">
            Enter 发送，Shift + Enter 换行 · 当前账号：{user?.display_name}
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
              <li>HttpOnly Cookie 登录会话</li>
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

function ProposalCard({
  proposal,
  busy,
  onDecision,
  onCreate,
  onRevision,
  revising,
}: {
  proposal: TrainingPlanProposalResponse;
  busy: boolean;
  onDecision: (decision: ProposalDecision) => void;
  onCreate: () => void;
  onRevision: (feedback: string) => void;
  revising: boolean;
}) {
  const [editing, setEditing] = useState(false);
  const [feedback, setFeedback] = useState('');
  const pending = proposal.status === 'pending';
  const approved = proposal.status === 'approved';
  const rejected = proposal.status === 'rejected';

  return (
    <Card as="article" className="proposal-card">
      <div className="proposal-card__header">
        <span className="colored-icon">
          <CalendarDays size={20} />
        </span>
        <div>
          <p className="eyebrow">下周训练提案 · 修订 {proposal.revision}</p>
          <h2>{translatePlanText(proposal.plan.goal_summary)}</h2>
          <small>
            {proposal.plan.week_start} 至 {proposal.plan.week_end}
          </small>
        </div>
        <Chip tone={approved ? 'green' : rejected ? 'orange' : 'blue'}>
          {approved ? '已同步' : rejected ? '未采用' : '待确认'}
        </Chip>
      </div>

      <div className="proposal-days">
        {proposal.plan.days.map((day) => (
          <article key={day.scheduled_date}>
            <span>{day.scheduled_date}</span>
            <strong>{translateDayName(day.name)}</strong>
            <p>{day.focus}</p>
            <small>
              {day.estimated_minutes} 分钟 · {day.exercises.length} 个动作
            </small>
            <ul>
              {day.exercises.map((exercise) => (
                <li key={exercise.exercise_name}>
                  <span>{translateExerciseName(exercise.exercise_name)}</span>
                  <small>
                    {exercise.sets} 组 × {exercise.reps_min}–{exercise.reps_max} 次 · RPE {exercise.target_rpe}
                  </small>
                </li>
              ))}
            </ul>
          </article>
        ))}
      </div>

      <div className="proposal-safety">
        <ShieldCheck size={17} />
        {proposal.safety_check.valid
          ? '确定性安全检查已通过'
          : `发现 ${proposal.safety_check.violations.length} 项安全问题`}
      </div>

      {pending ? (
        <div className="proposal-actions">
          <Button
            disabled={busy}
            icon={CheckCircle2}
            onClick={() => onDecision('approve')}>
            {busy ? '正在同步…' : '同意并同步'}
          </Button>
          <Button
            disabled={busy || revising}
            icon={PencilLine}
            onClick={() => setEditing(true)}
            variant="secondary">
            提出修改
          </Button>
          <Button
            disabled={busy}
            icon={XCircle}
            onClick={() => onDecision('reject')}
            variant="danger">
            不采用
          </Button>
        </div>
      ) : null}

      {approved ? (
        <Button
          disabled={revising}
          icon={PencilLine}
          onClick={() => setEditing(true)}
          variant="secondary">
          调整这份计划
        </Button>
      ) : null}

      {editing ? (
        <form
          className="proposal-revision"
          onSubmit={(event) => {
            event.preventDefault();
            if (!feedback.trim()) {
              return;
            }
            onRevision(feedback.trim());
            setEditing(false);
            setFeedback('');
          }}>
          <label htmlFor={`proposal-feedback-${proposal.id}`}>告诉 AI 需要怎么修改</label>
          <textarea
            disabled={revising}
            id={`proposal-feedback-${proposal.id}`}
            maxLength={500}
            onChange={(event) => setFeedback(event.target.value)}
            placeholder="例如：周三没时间，改到周四；动作尽量使用哑铃。"
            rows={3}
            value={feedback}
          />
          <div>
            <Button disabled={revising || !feedback.trim()} type="submit">
              {revising ? '正在生成…' : '生成修改版'}
            </Button>
            <Button onClick={() => setEditing(false)} type="button" variant="secondary">
              取消
            </Button>
          </div>
        </form>
      ) : null}

      {approved ? (
        <Link className="proposal-link" to="/app/plans">
          查看已同步的训练计划
        </Link>
      ) : null}

      {rejected ? (
        <Button icon={RefreshCw} onClick={onCreate} variant="secondary">
          重新制定
        </Button>
      ) : null}
    </Card>
  );
}

function ResponseEvidence({ response }: { response: CoachChatResponse }) {
  const [deletedMemoryIds, setDeletedMemoryIds] = useState<number[]>([]);

  const deleteMemory = async (memoryId: number) => {
    await fitFlowApi.deleteMemory(memoryId);
    setDeletedMemoryIds((current) => [...current, memoryId]);
  };

  return (
    <div className="response-evidence">
      <div className="response-meta">
        <span className={`safety-level is-${response.safety_level}`}>
          安全等级：{response.safety_level === 'low' ? '低' : response.safety_level}
        </span>
        {response.referenced_plan_id ? (
          <span>引用计划 #{response.referenced_plan_id}</span>
        ) : null}
      </div>

      {response.memory_events.length > 0 ? (
        <div className="memory-events">
          {response.memory_events.map((event) => {
            const deleted = deletedMemoryIds.includes(event.memory_id);
            return (
              <div key={`${event.action}-${event.memory_id}`}>
                <CheckCircle2 size={15} />
                <span>
                  {deleted
                    ? '这条长期记忆已删除'
                    : event.action === 'remembered'
                      ? `已记住：${event.content}`
                      : event.content}
                </span>
                {event.action === 'remembered' && !deleted ? (
                  <button
                    onClick={() => void deleteMemory(event.memory_id)}
                    type="button">
                    删除
                  </button>
                ) : null}
              </div>
            );
          })}
        </div>
      ) : null}

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

