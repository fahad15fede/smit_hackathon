import { AlertTriangle, Loader2, type LucideIcon, RotateCw } from 'lucide-react';
import type { ReactNode } from 'react';

import { cn } from '@/lib/cn';
import { Button } from './Button';

export function Spinner({ className }: { className?: string }) {
  return <Loader2 className={cn('size-5 animate-spin text-brand-600', className)} aria-label="Loading" />;
}

export function PageLoader() {
  return (
    <div className="grid min-h-[50vh] place-items-center">
      <Spinner className="size-7" />
    </div>
  );
}

export function SectionLoader() {
  return (
    <div className="grid h-40 place-items-center">
      <Spinner />
    </div>
  );
}

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({ icon: Icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div className={cn('flex flex-col items-center px-6 py-12 text-center', className)}>
      <div className="grid size-12 place-items-center rounded-full bg-slate-100">
        <Icon className="size-6 text-slate-400" />
      </div>
      <h3 className="mt-4 text-sm font-semibold text-slate-900">{title}</h3>
      {description && <p className="mt-1 max-w-sm text-sm text-slate-500">{description}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

interface ErrorStateProps {
  error: Error;
  onRetry?: () => void;
  fullScreen?: boolean;
}

export function ErrorState({ error, onRetry, fullScreen }: ErrorStateProps) {
  return (
    <div className={cn('grid place-items-center', fullScreen ? 'min-h-screen' : 'py-12')}>
      <EmptyState
        icon={AlertTriangle}
        title="Something went wrong"
        description={error.message}
        action={
          onRetry && (
            <Button variant="secondary" icon={RotateCw} onClick={onRetry}>
              Try again
            </Button>
          )
        }
      />
    </div>
  );
}
