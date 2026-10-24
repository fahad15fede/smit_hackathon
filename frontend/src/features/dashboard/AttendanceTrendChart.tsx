import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { formatShortDate } from '@/lib/format';
import type { TrendPoint } from '@/types/api';

const COLORS = { present: '#059669', late: '#f59e0b' };

export function AttendanceTrendChart({ data }: { data: TrendPoint[] }) {
  return (
    <div className="h-72">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }} barCategoryGap="28%">
          <CartesianGrid vertical={false} stroke="#e2e8f0" />
          <XAxis
            dataKey="day"
            tickFormatter={formatShortDate}
            tickLine={false}
            axisLine={false}
            tick={{ fontSize: 12, fill: '#64748b' }}
            interval="preserveStartEnd"
          />
          <YAxis allowDecimals={false} tickLine={false} axisLine={false} tick={{ fontSize: 12, fill: '#64748b' }} />
          <Tooltip
            cursor={{ fill: '#f1f5f9' }}
            labelFormatter={(label) => formatShortDate(String(label))}
            contentStyle={{ borderRadius: 10, border: '1px solid #e2e8f0', fontSize: 13 }}
          />
          <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 13, paddingTop: 8 }} />
          <Bar dataKey="present" name="On time" stackId="a" fill={COLORS.present} />
          <Bar dataKey="late" name="Late" stackId="a" fill={COLORS.late} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
