import { useForm } from 'react-hook-form';

import { useRequestLeave } from '@/api/leaves';
import { Button } from '@/components/ui/Button';
import { Field, FormError, Input, Select, Textarea } from '@/components/ui/form';
import { Modal } from '@/components/ui/Modal';
import { useToast } from '@/components/ui/toast';
import { toIsoDate } from '@/lib/format';
import type { LeaveBalance } from '@/types/api';

interface LeaveForm {
  leave_type_id: string;
  start_date: string;
  end_date: string;
  reason: string;
}

export function RequestLeaveModal({ open, onClose, balances }: { open: boolean; onClose: () => void; balances: LeaveBalance[] }) {
  const toast = useToast();
  const requestLeave = useRequestLeave();
  const { register, handleSubmit, reset, watch, formState } = useForm<LeaveForm>({
    defaultValues: { start_date: toIsoDate(new Date()), end_date: toIsoDate(new Date()) },
  });
  const startDate = watch('start_date');

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
        <FormError message={requestLeave.error?.message} />
        <Field label="Leave type" error={formState.errors.leave_type_id && 'Choose a leave type'}>
          <Select {...register('leave_type_id', { required: true })} defaultValue="">
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
