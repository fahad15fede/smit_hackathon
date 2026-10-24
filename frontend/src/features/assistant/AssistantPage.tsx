import { SendHorizontal, Sparkles } from 'lucide-react';
import { type FormEvent, useEffect, useRef, useState } from 'react';

import { useAiChat } from '@/api/ai';
import { AiBadge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { FormattedText } from '@/components/ui/FormattedText';
import { Avatar, PageHeader } from '@/components/ui/display';
import { Input } from '@/components/ui/form';
import { useCurrentUser } from '@/features/auth/auth-context';
import { cn } from '@/lib/cn';
import { isManager } from '@/lib/roles';
import type { ChatTurn } from '@/types/api';

interface Message {
  id: number;
  from: 'user' | 'assistant';
  text: string;
  aiGenerated?: boolean;
}

/** How many previous messages are sent as context with each question. */
const HISTORY_LIMIT = 10;

const MANAGER_PROMPTS = [
  'How many active employees are in each department?',
  'Who came late most often this month?',
  "What is this month's attendance rate?",
  'Who is on leave today?',
];
const EMPLOYEE_PROMPTS = [
  'How many sick leaves do I have left this year?',
  'What is my attendance this month?',
  'What happens if I check in after office start?',
];

function AssistantAvatar() {
  return (
    <span className="grid size-8 shrink-0 place-items-center rounded-full bg-brand-600 text-white">
      <Sparkles className="size-4" />
    </span>
  );
}

export function AssistantPage() {
  const user = useCurrentUser();
  const chat = useAiChat();
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const endRef = useRef<HTMLDivElement>(null);
  const prompts = isManager(user.role) ? MANAGER_PROMPTS : EMPLOYEE_PROMPTS;

  // Block body on purpose: scrollIntoView can return a Promise, and an effect must return nothing or a cleanup function.
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, chat.isPending]);

  const reply = (text: string, aiGenerated: boolean) =>
    setMessages((current) => [...current, { id: Date.now(), from: 'assistant', text, aiGenerated }]);

  const send = (text: string) => {
    const trimmed = text.trim();
    if (trimmed.length < 2 || chat.isPending) return;
    const history: ChatTurn[] = messages
      .slice(-HISTORY_LIMIT)
      .map((message) => ({ role: message.from, text: message.text.slice(0, 2000) }));
    setMessages((current) => [...current, { id: Date.now(), from: 'user', text: trimmed }]);
    setQuestion('');
    chat.mutate(
      { message: trimmed, history },
      {
        onSuccess: ({ answer, ai_generated }) => reply(answer, ai_generated),
        onError: (error) => reply(error.message, false),
      },
    );
  };

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    send(question);
  };

  return (
    <>
      <PageHeader
        title="Assistant"
        description="Ask about people, attendance, leave, payroll and company policy. Answers use only data your role can see."
      />
      <Card className="flex h-[calc(100vh-14rem)] min-h-[420px] flex-col">
        <div className="flex-1 space-y-5 overflow-y-auto p-5">
          {messages.length === 0 && (
            <div className="flex h-full flex-col items-center justify-center text-center">
              <span className="grid size-14 place-items-center rounded-2xl bg-brand-50 text-brand-600">
                <Sparkles className="size-7" />
              </span>
              <h2 className="mt-4 text-lg font-semibold text-slate-900">How can I help?</h2>
              <p className="mt-1 text-sm text-slate-500">Try one of these questions:</p>
              <div className="mt-5 flex max-w-2xl flex-wrap justify-center gap-2">
                {prompts.map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    onClick={() => send(prompt)}
                    className="rounded-full bg-white px-4 py-2 text-sm text-slate-700 shadow-sm ring-1 ring-slate-200 hover:bg-slate-50"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message) => (
            <div key={message.id} className={cn('flex gap-3', message.from === 'user' && 'flex-row-reverse')}>
              {message.from === 'user' ? <Avatar name={user.employee.full_name} size="sm" /> : <AssistantAvatar />}
              <div
                className={cn(
                  'max-w-[75%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed',
                  message.from === 'user' ? 'rounded-tr-sm bg-brand-600 text-white' : 'rounded-tl-sm bg-slate-100 text-slate-800',
                )}
              >
                {message.from === 'assistant' ? <FormattedText text={message.text} /> : message.text}
                {message.aiGenerated && (
                  <div className="mt-2">
                    <AiBadge />
                  </div>
                )}
              </div>
            </div>
          ))}

          {chat.isPending && (
            <div className="flex gap-3">
              <AssistantAvatar />
              <div className="flex items-center gap-1 rounded-2xl rounded-tl-sm bg-slate-100 px-4 py-3">
                {[0, 150, 300].map((delay) => (
                  <span key={delay} className="size-1.5 animate-bounce rounded-full bg-slate-400" style={{ animationDelay: `${delay}ms` }} />
                ))}
              </div>
            </div>
          )}
          <div ref={endRef} />
        </div>

        <form onSubmit={onSubmit} className="flex gap-2 border-t border-slate-100 p-4">
          <Input
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Ask a question…"
            maxLength={500}
            aria-label="Question"
          />
          <Button type="submit" icon={SendHorizontal} disabled={question.trim().length < 2} loading={chat.isPending}>
            Send
          </Button>
        </form>
      </Card>
    </>
  );
}
