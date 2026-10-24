import { Sparkles } from 'lucide-react';
import { type FormEvent, useState } from 'react';

import { useLeaveDraft } from '@/api/ai';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/form';
import { useToast } from '@/components/ui/toast';
import type { LeaveDraft } from '@/types/api';

interface SmartLeaveInputProps {
  /** Called with the parsed draft, or ``null`` when the AI could not help (show the normal form). */
  onDraft: (draft: LeaveDraft | null) => void;
  disabled?: boolean;
}

/** "Need next Monday and Tuesday off for a wedding" → a pre-filled leave form. Nothing is saved here. */
export function SmartLeaveInput({ onDraft, disabled }: SmartLeaveInputProps) {
  const toast = useToast();
  const leaveDraft = useLeaveDraft();
  const [text, setText] = useState('');

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (text.trim().length < 3) return;
    leaveDraft.mutate(text.trim(), {
      onSuccess: ({ draft, message }) => {
        if (!draft && message) toast.error(message);
        onDraft(draft);
        if (draft) setText('');
      },
      onError: (error) => {
        toast.error(error);
        onDraft(null);
      },
    });
  };

  return (
    <form onSubmit={submit} className="flex flex-col gap-2 sm:flex-row">
      <div className="relative flex-1">
        <Sparkles className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-violet-500" />
        <Input
          value={text}
          onChange={(event) => setText(event.target.value)}
          placeholder="Describe your leave, e.g. “Need next Monday and Tuesday off for my sister's wedding”"
          maxLength={300}
          className="pl-9"
          disabled={disabled}
          aria-label="Describe your leave"
        />
      </div>
      <Button type="submit" variant="secondary" loading={leaveDraft.isPending} disabled={disabled || text.trim().length < 3}>
        Fill form
      </Button>
    </form>
  );
}
