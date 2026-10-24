import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { Navigate, useNavigate } from 'react-router-dom';

import { authApi, type SetupInput, useSetupStatus } from '@/api/auth';
import { queryKeys } from '@/api/keys';
import { Button } from '@/components/ui/Button';
import { PageLoader } from '@/components/ui/feedback';
import { Field, FormError, Input } from '@/components/ui/form';
import { useAuth } from './auth-context';
import { AuthLayout } from './AuthLayout';

export function SetupPage() {
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const status = useSetupStatus();
  const { register, handleSubmit, formState } = useForm<SetupInput>();

  const setup = useMutation({
    mutationFn: authApi.setup,
    onSuccess: async (session) => {
      signIn(session);
      await queryClient.invalidateQueries({ queryKey: queryKeys.setup });
      navigate('/settings', { replace: true });
    },
  });

  if (status.isPending) return <PageLoader />;
  if (status.data?.ready) return <Navigate to="/login" replace />;

  return (
    <AuthLayout title="Set up your company" subtitle="Create your company workspace and the first Admin account.">
      <form onSubmit={handleSubmit((values) => setup.mutate(values))} className="space-y-5">
        <FormError message={setup.error?.message} />
        <Field label="Company name">
          <Input autoFocus placeholder="Acme Pvt Ltd" {...register('company_name', { required: true, minLength: 2 })} />
        </Field>
        <Field label="Your full name">
          <Input autoComplete="name" {...register('admin_name', { required: true, minLength: 2 })} />
        </Field>
        <Field label="Work email">
          <Input type="email" autoComplete="email" {...register('email', { required: true })} />
        </Field>
        <Field label="Password" error={formState.errors.password?.message} hint="At least 8 characters.">
          <Input
            type="password"
            autoComplete="new-password"
            {...register('password', { required: true, minLength: { value: 8, message: 'At least 8 characters' } })}
          />
        </Field>
        <Button type="submit" size="lg" className="w-full" loading={setup.isPending}>
          Create workspace
        </Button>
      </form>
    </AuthLayout>
  );
}
