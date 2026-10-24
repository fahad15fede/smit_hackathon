import { useForm } from 'react-hook-form';

import { useChangePassword } from '@/api/auth';
import { Button } from '@/components/ui/Button';
import { Field, FormError, Input } from '@/components/ui/form';
import { Modal } from '@/components/ui/Modal';
import { useToast } from '@/components/ui/toast';

interface PasswordForm {
  current_password: string;
  new_password: string;
  confirm: string;
}

export function ChangePasswordModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const toast = useToast();
  const changePassword = useChangePassword();
  const { register, handleSubmit, reset, formState } = useForm<PasswordForm>();

  const close = () => {
    reset();
    changePassword.reset();
    onClose();
  };

  const onSubmit = handleSubmit(({ current_password, new_password }) =>
    changePassword.mutate(
      { current_password, new_password },
      {
        onSuccess: () => {
          toast.success('Password updated');
          close();
        },
      },
    ),
  );

  return (
    <Modal
      open={open}
      onClose={close}
      title="Change password"
      description="Use at least 8 characters."
      footer={
        <>
          <Button variant="secondary" onClick={close}>
            Cancel
          </Button>
          <Button type="submit" form="password-form" loading={changePassword.isPending}>
            Update password
          </Button>
        </>
      }
    >
      <form id="password-form" onSubmit={onSubmit} className="space-y-4">
        <FormError message={changePassword.error?.message} />
        <Field label="Current password">
          <Input type="password" autoComplete="current-password" {...register('current_password', { required: true })} />
        </Field>
        <Field label="New password" error={formState.errors.new_password?.message}>
          <Input
            type="password"
            autoComplete="new-password"
            {...register('new_password', { required: true, minLength: { value: 8, message: 'At least 8 characters' } })}
          />
        </Field>
        <Field label="Confirm new password" error={formState.errors.confirm?.message}>
          <Input
            type="password"
            autoComplete="new-password"
            {...register('confirm', {
              validate: (value, values) => value === values.new_password || 'Passwords do not match',
            })}
          />
        </Field>
      </form>
    </Modal>
  );
}
