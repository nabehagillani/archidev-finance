import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer, Legend } from 'recharts'
import { api } from '../services/api'
import PageHeader from '../components/PageHeader'

const METRICS = [
  { key: 'revenue', label: 'Revenue' },
  { key: 'expense', label: 'Expenses' },
  { key: 'profit', label: 'Profit' },
]

export default function Forecasting() {
  const [metric, setMetric] = useState('revenue')
  const [data, setData] = useState(null)

  useEffect(() => {
    api.get(`/forecasting/${metric}`, { months_forward: 3 }).then(setData)
  }, [metric])

  const chartData = data ? [...data.history, ...data.forecast] : []

  return (
    <div>
      <PageHeader title="Forecasting" subtitle="Linear-trend estimates from historical data. Always labeled as estimates, never presented as actuals." />
      <div className="p-8">
        <div className="flex gap-2 mb-6">
          {METRICS.map((m) => (
            <button
              key={m.key} onClick={() => setMetric(m.key)}
              className={`text-sm px-4 py-1.5 border ${metric === m.key ? 'bg-ink-950 text-white border-ink-950' : 'border-ink-950/15 text-ink-700'}`}
            >
              {m.label}
            </button>
          ))}
        </div>
        {data && (
          <div className="border border-ink-950/10 bg-white p-5">
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={chartData}>
                <CartesianGrid stroke="#0B122010" />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v, name, props) => [`$${Number(v).toLocaleString()}`, props.payload.actual ? 'Actual' : 'Forecast (estimate)']} />
                <Line type="monotone" dataKey="value" stroke="#186142" strokeWidth={2} dot={(props) => (
                  <circle key={props.payload.month} cx={props.cx} cy={props.cy} r={3.5} fill={props.payload.actual ? '#186142' : '#B8862E'} />
                )} />
              </LineChart>
            </ResponsiveContainer>
            <div className="text-[11px] text-ink-600 mt-3">
              Amber points are forecast (estimate); green points are actuals. Method: {data.method.replace('_', ' ')}.
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
