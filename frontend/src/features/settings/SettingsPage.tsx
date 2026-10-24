import { Building2, CalendarDays, Plus, Tags, Trash2 } from 'lucide-react';
import { type ReactNode, useEffect, useMemo } from 'react';
import { useForm } from 'react-hook-form';

import {
  useAddDepartment,
  useAddHoliday,
  useAddLeaveType,
  useCompany,
  useDeleteHoliday,
  useDepartments,
  useHolidays,
  useLeaveTypes,
  useUpdateCompany,
} from '@/api/organization';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card, CardBody, CardHeader } from '@/components/ui/Card';
import { PageHeader } from '@/components/ui/display';
import { EmptyState, SectionLoader } from '@/components/ui/feedback';
import { Checkbox, Field, FormError, Input, Select } from '@/components/ui/form';
import { useToast } from '@/components/ui/toast';
import { formatDate, titleCase } from '@/lib/format';
import type { Weekday } from '@/types/api';

const WEEKDAYS: Weekday[] = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];

interface PolicyForm {
  name: string;
  timezone: string;
  office_start: string;
  grace_minutes: number;
  weekend_days: Weekday[];
}

function CompanyPolicyCard() {
  const toast = useToast();
  const company = useCompany();
  const update = useUpdateCompany();
  const { register, handleSubmit, reset, formState } = useForm<PolicyForm>();
  const timezones = useMemo(() => Intl.supportedValuesOf('timeZone'), []);

  useEffect(() => {
    if (company.data) reset({ ...company.data, office_start: company.data.office_start.slice(0, 5) });
  }, [company.data, reset]);

  const onSubmit = handleSubmit((values) =>
    update.mutate(
      { ...values, grace_minutes: Number(values.grace_minutes), weekend_days: values.weekend_days || [] },
      { onSuccess: () => toast.success('Company settings saved') },
    ),
  );

  return (
    <Card>
      <CardHeader title="Company & working hours" description="Used for late marking, leave day counts and payroll." />
      {company.isPending ? (
        <SectionLoader />
      ) : (
        <form onSubmit={onSubmit}>
          <CardBody className="grid gap-5 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <FormError message={update.error?.message} />
            </div>
            <Field label="Company name">
              <Input {...register('name', { required: true, minLength: 2 })} />
            </Field>
            <Field label="Timezone">
              <Select {...register('timezone')}>
                {timezones.map((zone) => (
                  <option key={zone} value={zone}>
                    {zone.replaceAll('_', ' ')}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Office start time">
              <Input type="time" {...register('office_start', { required: true })} />
            </Field>
            <Field label="Grace period (minutes)" hint="Check-ins after start time + grace are marked late.">
              <Input type="number" min={0} max={240} {...register('grace_minutes', { required: true, min: 0, max: 240 })} />
            </Field>
            <fieldset className="sm:col-span-2">
              <legend className="mb-2 text-sm font-medium text-slate-700">Weekend days</legend>
              <div className="flex flex-wrap gap-x-5 gap-y-2">
                {WEEKDAYS.map((day) => (
                  <Checkbox key={day} label={titleCase(day)} value={day} {...register('weekend_days')} />
                ))}
              </div>
            </fieldset>
          </CardBody>
          <div className="flex justify-end border-t border-slate-100 px-5 py-4">
            <Button type="submit" loading={update.isPending} disabled={!formState.isDirty}>
              Save changes
            </Button>
          </div>
        </form>
      )}
    </Card>
  );
}

/** A compact card with an inline "add" form above a list of items. */
function ListCard({ title, description, form, children }: { title: string; description: string; form: ReactNode; children: ReactNode }) {
  return (
    <Card className="flex flex-col">
      <CardHeader title={title} description={description} />
      <div className="border-b border-slate-100 bg-slate-50/60 px-5 py-4">{form}</div>
      <div className="flex-1">{children}</div>
    </Card>
  );
}

function DepartmentsCard() {
  const toast = useToast();
  const departments = useDepartments();
  const add = useAddDepartment();
  const { register, handleSubmit, reset } = useForm<{ name: string }>();

  return (
    <ListCard
      title="Departments"
      description="Group employees by team."
      form={
        <form
          className="space-y-2"
          onSubmit={handleSubmit((values) =>
            add.mutate(values, {
              onSuccess: () => {
                toast.success('Department added');
                reset();
              },
            }),
          )}
        >
          <div className="flex gap-2">
            <Input placeholder="e.g. Engineering" {...register('name', { required: true, minLength: 2 })} />
            <Button type="submit" icon={Plus} loading={add.isPending}>
              Add
            </Button>
          </div>
          <FormError message={add.error?.message} />
        </form>
      }
    >
      {departments.data?.length ? (
        <ul className="divide-y divide-slate-100">
          {departments.data.map((department) => (
            <li key={department.id} className="px-5 py-3 text-sm text-slate-700">
              {department.name}
            </li>
          ))}
        </ul>
      ) : (
        <EmptyState icon={Building2} title="No departments" className="py-8" />
      )}
    </ListCard>
  );
}

interface LeaveTypeForm {
  name: string;
  annual_quota: number;
  is_paid: boolean;
}

function LeaveTypesCard() {
  const toast = useToast();
  const leaveTypes = useLeaveTypes();
  const add = useAddLeaveType();
  const { register, handleSubmit, reset } = useForm<LeaveTypeForm>({ defaultValues: { is_paid: true } });

  return (
    <ListCard
      title="Leave types"
      description="Annual allowance per employee."
      form={
        <form
          className="space-y-3"
          onSubmit={handleSubmit((values) =>
            add.mutate(
              { ...values, annual_quota: Number(values.annual_quota) },
              {
                onSuccess: () => {
                  toast.success('Leave type added');
                  reset();
                },
              },
            ),
          )}
        >
          <div className="flex gap-2">
            <Input placeholder="e.g. Annual leave" {...register('name', { required: true, minLength: 2 })} />
            <Input
              type="number"
              min={0}
              max={365}
              placeholder="Days"
              className="w-24"
              {...register('annual_quota', { required: true, min: 0, max: 365 })}
            />
          </div>
          <div className="flex items-center justify-between gap-2">
            <Checkbox label="Paid leave" {...register('is_paid')} />
            <Button type="submit" icon={Plus} loading={add.isPending}>
              Add
            </Button>
          </div>
          <FormError message={add.error?.message} />
        </form>
      }
    >
      {leaveTypes.data?.length ? (
        <ul className="divide-y divide-slate-100">
          {leaveTypes.data.map((type) => (
            <li key={type.id} className="flex items-center justify-between gap-2 px-5 py-3 text-sm">
              <span className="text-slate-700">{type.name}</span>
              <span className="flex items-center gap-2">
                {!type.is_paid && <Badge>Unpaid</Badge>}
                <span className="text-slate-500 tabular-nums">{type.annual_quota} days</span>
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <EmptyState icon={Tags} title="No leave types" description="Employees cannot request leave until you add one." className="py-8" />
      )}
    </ListCard>
  );
}

function HolidaysCard() {
  const toast = useToast();
  const holidays = useHolidays();
  const add = useAddHoliday();
  const remove = useDeleteHoliday();
  const { register, handleSubmit, reset } = useForm<{ name: string; day: string }>();

  return (
    <ListCard
      title="Public holidays"
      description="Excluded from leave and payroll day counts."
      form={
        <form
          className="space-y-2"
          onSubmit={handleSubmit((values) =>
            add.mutate(values, {
              onSuccess: () => {
                toast.success('Holiday added');
                reset();
              },
            }),
          )}
        >
          <Input placeholder="e.g. Independence Day" {...register('name', { required: true, minLength: 2 })} />
          <div className="flex gap-2">
            <Input type="date" {...register('day', { required: true })} />
            <Button type="submit" icon={Plus} loading={add.isPending}>
              Add
            </Button>
          </div>
          <FormError message={add.error?.message} />
        </form>
      }
    >
      {holidays.data?.length ? (
        <ul className="divide-y divide-slate-100">
          {holidays.data.map((holiday) => (
            <li key={holiday.id} className="flex items-center justify-between gap-2 px-5 py-2.5 text-sm">
              <div>
                <p className="text-slate-700">{holiday.name}</p>
                <p className="text-xs text-slate-500">{formatDate(holiday.day)}</p>
              </div>
              <Button
                size="icon"
                variant="danger-ghost"
                icon={Trash2}
                aria-label={`Delete ${holiday.name}`}
                onClick={() => remove.mutate(holiday.id, { onError: toast.error })}
              />
            </li>
          ))}
        </ul>
      ) : (
        <EmptyState icon={CalendarDays} title="No holidays" className="py-8" />
      )}
    </ListCard>
  );
}

export function SettingsPage() {
  return (
    <>
      <PageHeader title="Settings" description="Configure your company policies and reference data." />
      <div className="space-y-6">
        <CompanyPolicyCard />
        <div className="grid gap-6 lg:grid-cols-3">
          <DepartmentsCard />
          <LeaveTypesCard />
          <HolidaysCard />
        </div>
      </div>
    </>
  );
}
