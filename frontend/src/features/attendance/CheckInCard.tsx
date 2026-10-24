import { Clock, LogIn, LogOut } from 'lucide-react';

import { useCheckIn, useCheckOut } from '@/api/attendance';
import { StatusBadge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { useToast } from '@/components/ui/toast';
import { formatDate, formatTime } from '@/lib/format';
import type { AttendanceRecord } from '@/types/api';

interface CheckInCardProps {
  today: string;
  isWorkingDay: boolean;
  record: AttendanceRecord | null;
}

export function CheckInCard({ today, isWorkingDay, record }: CheckInCardProps) {
  const toast = useToast();
  const checkIn = useCheckIn();
  const checkOut = useCheckOut();

  const handleCheckIn = () =>
    checkIn.mutate(undefined, {
      onSuccess: (result) =>
        toast.success(result.status === 'late' ? 'Checked in (marked late)' : 'Checked in. Have a great day!'),
      onError: toast.error,
    });

  const handleCheckOut = () =>
    checkOut.mutate(undefined, { onSuccess: () => toast.success('Checked out. See you tomorrow!'), onError: toast.error });

  let message = 'You have not checked in yet today.';
  if (!isWorkingDay) message = 'Today is a non-working day. Enjoy your time off.';
  else if (record?.check_out) message = `Day complete: ${formatTime(record.check_in)} to ${formatTime(record.check_out)}.`;
  else if (record) message = `Checked in at ${formatTime(record.check_in)}. Remember to check out.`;

  return (
    <Card className="overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-5 bg-gradient-to-r from-brand-600 to-brand-500 px-6 py-6 text-white">
        <div className="flex items-center gap-4">
          <span className="grid size-12 place-items-center rounded-xl bg-white/15 ring-1 ring-white/25">
            <Clock className="size-6" />
          </span>
          <div>
            <p className="text-sm text-brand-50/90">{formatDate(today)}</p>
            <p className="mt-0.5 text-lg font-semibold">{message}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {record && (
            <span className="rounded-md bg-white px-0.5 py-0.5">
              <StatusBadge status={record.status} />
            </span>
          )}
          {isWorkingDay && !record && (
            <Button variant="secondary" size="lg" icon={LogIn} loading={checkIn.isPending} onClick={handleCheckIn}>
              Check in
            </Button>
          )}
          {record && !record.check_out && (
            <Button variant="secondary" size="lg" icon={LogOut} loading={checkOut.isPending} onClick={handleCheckOut}>
              Check out
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
}
