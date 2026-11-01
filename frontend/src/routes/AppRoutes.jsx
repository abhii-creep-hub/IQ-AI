import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import DashboardLayout from '../layouts/DashboardLayout'
import LandingPage from '../pages/LandingPage'
import LoginPage from '../pages/LoginPage'
import RegisterPage from '../pages/RegisterPage'
import DashboardPage from '../pages/DashboardPage'
import UploadPage from '../pages/UploadPage'
import JobsPage from '../pages/JobsPage'
import JobDetailPage from '../pages/JobDetailPage'
import CandidatesPage from '../pages/CandidatesPage'
import CandidateDetailPage from '../pages/CandidateDetailPage'
import CandidateComparisonPage from '../pages/CandidateComparisonPage'
import ReportsPage from '../pages/ReportsPage'
import SettingsPage from '../pages/SettingsPage'
import ForgotPasswordPage from '../pages/ForgotPasswordPage'
import ResetPasswordPage from '../pages/ResetPasswordPage'
import PipelinePage from '../pages/PipelinePage'
import InterviewsPage from '../pages/InterviewsPage'
import InterviewDetailPage from '../pages/InterviewDetailPage'
import AIInterviewAssistantPage from '../pages/AIInterviewAssistantPage'
import AIInterviewSessionPage from '../pages/AIInterviewSessionPage'

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) {
    return (
      <div className="min-h-screen bg-dark-950 flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }
  if (!user) return <Navigate to="/login" replace />
  return children
}

function PublicRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return null
  if (user) return <Navigate to="/dashboard" replace />
  return children
}

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<PublicRoute><LandingPage /></PublicRoute>} />
      <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
      <Route path="/register" element={<PublicRoute><RegisterPage /></PublicRoute>} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
      <Route
        path="/dashboard"
        element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>}
      >
        <Route index element={<DashboardPage />} />
        <Route path="upload" element={<UploadPage />} />
        <Route path="jobs" element={<JobsPage />} />
        <Route path="jobs/:id" element={<JobDetailPage />} />
        <Route path="candidates" element={<CandidatesPage />} />
        <Route path="pipeline" element={<PipelinePage />} />
        <Route path="interviews" element={<InterviewsPage />} />
        <Route path="interviews/:id" element={<InterviewDetailPage />} />
        <Route path="ai-interview" element={<AIInterviewAssistantPage />} />
        <Route path="ai-interview/:id" element={<AIInterviewSessionPage />} />
        <Route path="candidates/compare" element={<CandidateComparisonPage />} />
        <Route path="candidates/:id" element={<CandidateDetailPage />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
