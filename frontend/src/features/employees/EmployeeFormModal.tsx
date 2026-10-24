import { useEffect } from 'react';
import { useForm } from 'react-hook-form';

import { useCreateEmployee, useUpdateEmployee } from '@/api/employees';
import { useDepartments } from '@/api/organization';
import { Button } from '@/components/ui/Button';
import { Checkbox, Field, FormError, Input, Select } from '@/components/ui/form';
import { Modal } from '@/components/ui/Modal';
import { useToast } from '@/components/ui/toast';
import { useCurrentUser } from '@/features/auth/auth-context';
import { toIsoDate } from '@/lib/format';
import { ROLE_LABELS } from '@/lib/roles';
import type { Employee, Role } from '@/types/api';

interface EmployeeForm {
  full_name: string;
  email: string;
  designation: string;
  join_date: string;
  monthly_salary: string;
  department_id: string;
  phone: string;
  role: Role;
  password: string;
  is_active: boolean;
}

const emptyForm = (): EmployeeForm => ({
  full_name: '',
  email: '',
  designation: '',
  join_date: toIsoDate(new Date()),
  monthly_salary: '',
  department_id: '',
  phone: '',
  role: 'employee',
  password: '',
  is_active: true,
});

const toForm = (employee: Employee): EmployeeForm => ({
  ...emptyForm(),
  full_name: employee.full_name,
  email: employee.email,
  designation: employee.designation,
  join_date: employee.join_date,
  monthly_salary: String(employee.monthly_salary),
  department_id: employee.department ? String(employee.department.id) : '',
  phone: employee.phone ?? '',
  role: employee.role,
  is_active: employee.is_active,
});

interface EmployeeFormModalProps {
  open: boolean;
  onClose: () => void;
  /** When set, the modal edits this employee instead of creating a new one. */
  employee?: Employee | null;
}

export function EmployeeFormModal({ open, onClose, employee }: EmployeeFormModalProps) {
  const user = useCurrentUser();
  const toast = useToast();
  const departments = useDepartments();
  const createEmployee = useCreateEmployee();
  const updateEmployee = useUpdateEmployee();
  const mutation = employee ? updateEmployee : createEmployee;
  const { register, handleSubmit, reset, formState } = useForm<EmployeeForm>({ defaultValues: emptyForm() });
  const { errors } = formState;
  const isSelf = employee?.id === user.employee.id;

  useEffect(() => {
    if (open) reset(employee ? toForm(employee) : emptyForm());
  }, [open, employee, reset]);

  const close = () => {
    createEmployee.reset();
    updateEmployee.reset();
    onClose();
  };

  const onSubmit = handleSubmit((values) => {
    const shared = {
      full_name: values.full_name,
      designation: values.designation,
      monthly_salary: Number(values.monthly_salary),
      department_id: values.department_id ? Number(values.department_id) : null,
      phone: values.phone || null,
    };
    const onSuccess = () => {
      toast.success(employee ? 'Employee updated' : `${values.full_name} can now sign in with ${values.email}`);
      close();
    };
    if (employee) {
      updateEmployee.mutate({ id: employee.id, ...shared, is_active: values.is_active }, { onSuccess });
    } else {
      createEmployee.mutate(
        { ...shared, email: values.email, join_date: values.join_date, role: values.role, password: values.password },
        { onSuccess },
      );
    }
  });

  const roles: Role[] = user.role === 'admin' ? ['employee', 'hr', 'admin'] : ['employee'];

  return (
    <Modal
      open={open}
      onClose={close}
      size="lg"
      title={employee ? `Edit ${employee.full_name}` : 'Add employee'}
      description={employee ? undefined : 'This also creates their sign-in account.'}
      footer={
        <>
          <Button variant="secondary" onClick={close}>
            Cancel
          </Button>
          <Button type="submit" form="employee-form" loading={mutation.isPending}>
            {employee ? 'Save changes' : 'Create employee'}
          </Button>
        </>
      }
    >
      <form id="employee-form" onSubmit={onSubmit} className="grid gap-4 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <FormError message={mutation.error?.message} />
        </div>
        <Field label="Full name" error={errors.full_name && 'Required'}>
          <Input {...register('full_name', { required: true, minLength: 2 })} />
        </Field>
        <Field label="Email" hint={employee ? 'Email cannot be changed.' : undefined}>
          <Input type="email" disabled={!!employee} {...register('email', { required: !employee })} />
        </Field>
        <Field label="Designation" error={errors.designation && 'Required'}>
          <Input placeholder="Software Engineer" {...register('designation', { required: true, minLength: 2 })} />
        </Field>
        <Field label="Department">
          <Select {...register('department_id')}>
            <option value="">No department</option>
            {departments.data?.map((department) => (
              <option key={department.id} value={department.id}>
                {department.name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Monthly salary (PKR)" error={errors.monthly_salary && 'Enter a salary of 0 or more'}>
          <Input type="number" min={0} step="0.01" {...register('monthly_salary', { required: true, min: 0 })} />
        </Field>
        <Field label="Phone">
          <Input type="tel" {...register('phone')} />
        </Field>
        {employee ? (
          <div className="flex items-end pb-2 sm:col-span-2">
            <Checkbox
              label="Active (can sign in and is included in payroll)"
              disabled={isSelf}
              {...register('is_active')}
            />
          </div>
        ) : (
          <>
            <Field label="Join date">
              <Input type="date" {...register('join_date', { required: true })} />
            </Field>
            <Field label="Role">
              <Select {...register('role')} disabled={roles.length === 1}>
                {roles.map((role) => (
                  <option key={role} value={role}>
                    {ROLE_LABELS[role]}
                  </option>
                ))}
              </Select>
            </Field>
            <Field
              label="Temporary password"
              className="sm:col-span-2"
              error={errors.password?.message}
              hint="Share it securely. They can change it after signing in."
            >
              <Input
                type="text"
                autoComplete="off"
                {...register('password', { required: 'Required', minLength: { value: 8, message: 'At least 8 characters' } })}
              />
            </Field>
          </>
        )}
      </form>
    </Modal>
  );
}
