import { useEffect } from 'react';
import { useForm } from 'react-hook-form';

import { useRequestLeave } from '@/api/leaves';
import { AiBadge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Field, FormError, Input, Select, Textarea } from '@/components/ui/form';
import { Modal } from '@/components/ui/Modal';
import { useToast } from '@/components/ui/toast';
import { toIsoDate } from '@/lib/format';
import type { LeaveBalance, LeaveDraft } from '@/types/api';

interface LeaveForm {
  leave_type_id: string;
  start_date: string;
  end_date: string;
  reason: string;
}

interface RequestLeaveModalProps {
  open: boolean;
  onClose: () => void;
  balances: LeaveBalance[];
  /** An AI-parsed draft to pre-fill. The user still reviews and submits it themselves. */
  draft?: LeaveDraft | null;
}

const emptyForm = (): LeaveForm => ({
  leave_type_id: '',
  start_date: toIsoDate(new Date()),
  end_date: toIsoDate(new Date()),
  reason: '',
});

export function RequestLeaveModal({ open, onClose, balances, draft }: RequestLeaveModalProps) {
  const toast = useToast();
  const requestLeave = useRequestLeave();
  const { register, handleSubmit, reset, watch, formState } = useForm<LeaveForm>({ defaultValues: emptyForm() });
  const startDate = watch('start_date');

  useEffect(() => {
    if (!open) return;
    reset(
      draft
        ? { leave_type_id: String(draft.leave_type_id), start_date: draft.start_date, end_date: draft.end_date, reason: draft.reason }
        : emptyForm(),
    );
  }, [open, draft, reset]);

  const close = () => {
    reset();
    requestLeave.reset();
    onClose();
  };

  const onSubmit = handleSubmit((values) =>
    requestLeave.mutate(
      { ...values, leave_type_id: Number(values.leave_type_id) },
      {
        onSuccess: (leave) => {
          toast.success(`Leave requested for ${leave.working_days} working day(s)`);
          close();
        },
      },
    ),
  );

  return (
    <Modal
      open={open}
      onClose={close}
      title="Request leave"
      description="Weekends and company holidays are not counted."
      footer={
        <>
          <Button variant="secondary" onClick={close}>
            Cancel
          </Button>
          <Button type="submit" form="leave-form" loading={requestLeave.isPending}>
            Submit request
          </Button>
        </>
      }
    >
      <form id="leave-form" onSubmit={onSubmit} className="space-y-4">
        {draft && (
          <div className="flex items-center justify-between gap-3 rounded-lg bg-violet-50/60 px-3 py-2 text-sm text-violet-900 ring-1 ring-violet-200">
            Pre-filled from your description. Check it before submitting.
            <AiBadge />
          </div>
        )}
        <FormError message={requestLeave.error?.message} />
        <Field label="Leave type" error={formState.errors.leave_type_id && 'Choose a leave type'}>
          <Select {...register('leave_type_id', { required: true })}>
            <option value="" disabled>
              Choose a leave type
            </option>
            {balances.map(({ leave_type, remaining }) => (
              <option key={leave_type.id} value={leave_type.id} disabled={remaining <= 0}>
                {leave_type.name} ({remaining} day{remaining === 1 ? '' : 's'} left)
              </option>
            ))}
          </Select>
        </Field>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="From">
            <Input type="date" {...register('start_date', { required: true })} />
          </Field>
          <Field label="To" error={formState.errors.end_date?.message}>
            <Input
              type="date"
              min={startDate}
              {...register('end_date', {
                required: true,
                validate: (value, values) => value >= values.start_date || 'Must be on or after the start date',
              })}
            />
          </Field>
        </div>
        <Field label="Reason" error={formState.errors.reason && 'Please add a short reason (3+ characters)'}>
          <Textarea placeholder="Family event, medical appointment…" {...register('reason', { required: true, minLength: 3 })} />
        </Field>
      </form>
    </Modal>
  );
}
