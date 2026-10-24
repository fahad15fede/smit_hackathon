import { Sparkles } from 'lucide-react';

import { useDashboardSummary } from '@/api/ai';
import { AiBadge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card, CardBody, CardHeader } from '@/components/ui/Card';

/** "Summarize": 3–5 AI insight bullets built only from the dashboard's own KPI numbers. */
export function DashboardSummaryCard() {
  const summary = useDashboardSummary();
  const result = summary.data;

  return (
    <Card>
      <CardHeader
        title="Insights"
        description="A short AI summary of today's numbers."
        action={
          <Button variant="secondary" size="sm" icon={Sparkles} loading={summary.isPending} onClick={() => summary.mutate()}>
            {result ? 'Refresh' : 'Summarize'}
          </Button>
        }
      />
      {(result || summary.error) && (
        <CardBody>
          {summary.error ? (
            <p className="text-sm text-rose-600">{summary.error.message}</p>
          ) : result && result.bullets.length > 0 ? (
            <>
              <ul className="list-disc space-y-1.5 pl-5 text-sm text-slate-700 marker:text-brand-500">
                {result.bullets.map((bullet) => (
                  <li key={bullet}>{bullet}</li>
                ))}
              </ul>
              {result.ai_generated && (
                <div className="mt-3">
                  <AiBadge />
                </div>
              )}
            </>
          ) : (
            <p className="text-sm text-slate-500">{result?.message}</p>
          )}
        </CardBody>
      )}
    </Card>
  );
}
