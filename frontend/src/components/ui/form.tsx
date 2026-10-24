import type { ComponentProps, ReactNode } from 'react';

import { cn } from '@/lib/cn';

const CONTROL =
  'block w-full rounded-lg border-0 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 ' +
  'placeholder:text-slate-400 focus:ring-2 focus:ring-inset focus:ring-brand-600 focus:outline-none ' +
  'disabled:bg-slate-50 disabled:text-slate-500 aria-invalid:ring-rose-400';

interface FieldProps {
  label: string;
  error?: string;
  hint?: string;
  className?: string;
  /** Render a <div> instead of a <label>; needed when the field contains buttons. */
  group?: boolean;
  children: ReactNode;
}

export function Field({ label, error, hint, className, group = false, children }: FieldProps) {
  const Wrapper = group ? 'div' : 'label';
  return (
    <Wrapper className={cn('block', className)}>
      <span className="mb-1.5 block text-sm font-medium text-slate-700">{label}</span>
      {children}
      {error ? (
        <span className="mt-1.5 block text-xs text-rose-600">{error}</span>
      ) : (
        hint && <span className="mt-1.5 block text-xs text-slate-500">{hint}</span>
      )}
    </Wrapper>
  );
}

export function Input({ className, ...props }: ComponentProps<'input'>) {
  return <input className={cn(CONTROL, 'h-10', className)} {...props} />;
}

export function Select({ className, ...props }: ComponentProps<'select'>) {
  return <select className={cn(CONTROL, 'h-10 pr-8', className)} {...props} />;
}

export function Textarea({ className, ...props }: ComponentProps<'textarea'>) {
  return <textarea className={cn(CONTROL, 'min-h-24 resize-y', className)} {...props} />;
}

export function Checkbox({ label, className, ...props }: ComponentProps<'input'> & { label: string }) {
  return (
    <label className={cn('inline-flex cursor-pointer items-center gap-2 text-sm text-slate-700', className)}>
      <input
        type="checkbox"
        className="size-4 rounded border-slate-300 text-brand-600 accent-brand-600 focus:ring-brand-600"
        {...props}
      />
      {label}
    </label>
  );
}

export function FormError({ message }: { message?: string | null }) {
  if (!message) return null;
  return <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700 ring-1 ring-rose-200">{message}</p>;
}
