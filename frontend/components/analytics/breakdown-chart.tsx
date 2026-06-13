"use client"

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts"
import { formatCost } from "@/lib/format"

export function BreakdownChart({
  title,
  data,
  labelKey,
  valueKey,
  formatValue,
  color = "#5e6ad2",
}: {
  title: string
  data: object[]
  labelKey: string
  valueKey: string
  formatValue?: (v: number) => string
  color?: string
}) {
  const formatter = formatValue ?? ((v: number) => v.toLocaleString())

  return (
    <div className="panel-lift rounded-lg p-5 h-full">
      <h3 className="text-body font-medium text-ink mb-4">{title}</h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ left: 4, right: 16, top: 4, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#23252a" horizontal={false} />
            <XAxis type="number" tick={{ fill: "#8a8f98", fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis
              type="category"
              dataKey={labelKey}
              width={100}
              tick={{ fill: "#8a8f98", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                background: "#0f1011",
                border: "1px solid #23252a",
                borderRadius: "8px",
                fontSize: "12px",
              }}
              formatter={(v: number) => [formatter(v), ""]}
            />
            <Bar dataKey={valueKey} fill={color} radius={[0, 4, 4, 0]} maxBarSize={22} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

export function costFormatter(v: number) {
  return formatCost(v)
}
