import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import AppLayout from './layouts/AppLayout'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Dashboard from './pages/Dashboard'
import Transactions from './pages/Transactions'
import Expenses from './pages/Expenses'
import Invoices from './pages/Invoices'
import Receivables from './pages/Receivables'
import Payables from './pages/Payables'
import Reconciliation from './pages/Reconciliation'
import Budgets from './pages/Budgets'
import Reports from './pages/Reports'
import Forecasting from './pages/Forecasting'
import Insights from './pages/Insights'
import AiAssistant from './pages/AiAssistant'
import Notifications from './pages/Notifications'
import AuditLogs from './pages/AuditLogs'
import Settings from './pages/Settings'

function RequireAuth({ children }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  return children
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route
        path="/"
        element={
          <RequireAuth>
            <AppLayout />
          </RequireAuth>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="transactions" element={<Transactions />} />
        <Route path="expenses" element={<Expenses />} />
        <Route path="invoices" element={<Invoices />} />
        <Route path="receivables" element={<Receivables />} />
        <Route path="payables" element={<Payables />} />
        <Route path="reconciliation" element={<Reconciliation />} />
        <Route path="budgets" element={<Budgets />} />
        <Route path="reports" element={<Reports />} />
        <Route path="forecasting" element={<Forecasting />} />
        <Route path="insights" element={<Insights />} />
        <Route path="assistant" element={<AiAssistant />} />
        <Route path="notifications" element={<Notifications />} />
        <Route path="audit-logs" element={<AuditLogs />} />
        <Route path="settings" element={<Settings />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
