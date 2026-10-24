import { useMutation } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { useLocation, useNavigate } from 'react-router-dom';

import { authApi, type LoginInput, useSetupStatus } from '@/api/auth';
import { Button } from '@/components/ui/Button';
import { Field, FormError, Input } from '@/components/ui/form';
import { useAuth } from './auth-context';
import { AuthLayout } from './AuthLayout';

export function LoginPage() {
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { data: setup } = useSetupStatus();
  const { register, handleSubmit } = useForm<LoginInput>();

  const login = useMutation({
    mutationFn: authApi.login,
    onSuccess: (session) => {
      signIn(session);
      const from = (location.state as { from?: string } | null)?.from;
      navigate(from && from !== '/login' ? from : '/', { replace: true });
    },
  });

  return (
    <AuthLayout
      title="Welcome back"
      subtitle={setup?.company_name ? `Sign in to ${setup.company_name}.` : 'Sign in to your workspace.'}
    >
      <form onSubmit={handleSubmit((values) => login.mutate(values))} className="space-y-5">
        <FormError message={login.error?.message} />
        <Field label="Email">
          <Input type="email" autoComplete="email" autoFocus placeholder="you@company.com" {...register('email', { required: true })} />
        </Field>
        <Field label="Password">
          <Input type="password" autoComplete="current-password" {...register('password', { required: true })} />
        </Field>
        <Button type="submit" size="lg" className="w-full" loading={login.isPending}>
          Sign in
        </Button>
      </form>
      <p className="mt-8 text-center text-xs text-slate-500">
        Accounts are created by your HR team. Contact them if you cannot sign in.
      </p>
    </AuthLayout>
  );
}
