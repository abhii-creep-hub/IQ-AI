import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useCandidate, useFullReport } from '../hooks/useQueries'
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts'
import { HiArrowLeft, HiUser, HiAcademicCap, HiBriefcase, HiCodeBracket, HiDocumentCheck, HiChatBubbleLeftRight } from 'react-icons/hi2'
import { getScoreColor, getScoreLabel, formatDate, RANK_COLORS } from '../utils/helpers'

const TABS = ['Overview', 'Skills', 'Education', 'Experience', 'Questions']

export default function CandidateDetailPage() {
  const { id } = useParams()
  const { data: candidate, isLoading } = useCandidate(id)
  const { data: report } = useFullReport(id)

  if (isLoading) {
    return (
      <div className="page-container flex justify-center py-20">
        <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!candidate) {
    return (
      <div className="page-container text-center py-20">
        <p className="text-dark-400">Candidate not found</p>
        <Link to="/dashboard/candidates" className="glass-button mt-4 text-sm inline-block">Back to Candidates</Link>
      </div>
    )
  }

  const atsScore = report?.ats_result?.total_score || 0
  const matchScore = report?.ai_analysis?.match_score || 0
  const pieData = [
    { name: 'Score', value: atsScore },
    { name: 'Remaining', value: 100 - atsScore },
  ]

  return (
    <div className="page-container">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <Link to="/dashboard/candidates" className="inline-flex items-center gap-2 text-dark-400 hover:text-white mb-6 transition-colors">
          <HiArrowLeft className="w-4 h-4" /> Back to Candidates
        </Link>

        {/* Header */}
        <div className="glass-card p-6 mb-6">
          <div className="flex flex-col md:flex-row md:items-center gap-6">
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center text-2xl font-bold shadow-glow">
              {candidate.name?.[0] || '?'}
            </div>
            <div className="flex-1">
              <h1 className="text-2xl font-bold mb-1">{candidate.name}</h1>
              <div className="flex flex-wrap gap-3 text-sm text-dark-400">
                {candidate.email && <span>{candidate.email}</span>}
                {candidate.phone && <span>{candidate.phone}</span>}
                {candidate.location && <span>📍 {candidate.location}</span>}
                {candidate.total_experience_years > 0 && <span>📊 {candidate.total_experience_years} years exp</span>}
              </div>
            </div>
            <div className="flex flex-col items-center gap-2">
              <span className={`px-4 py-1.5 rounded-full text-sm font-semibold capitalize rank-${candidate.rank}`}>
                {candidate.rank}
              </span>
              {candidate.hiring_recommendation && (
                <span className="text-xs text-dark-400 capitalize">{candidate.hiring_recommendation.replace('_', ' ')}</span>
              )}
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Score Card */}
          <div className="glass-card p-6 flex flex-col items-center">
            <h3 className="text-sm font-semibold text-dark-300 mb-4">ATS Score</h3>
            <div className="relative w-40 h-40">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={70} startAngle={90} endAngle={-270} dataKey="value">
                    <Cell fill={getScoreColor(atsScore)} />
                    <Cell fill="#1e293b" />
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-3xl font-bold" style={{ color: getScoreColor(atsScore) }}>{atsScore.toFixed(1)}</span>
                <span className="text-xs text-dark-400">{getScoreLabel(atsScore)}</span>
              </div>
            </div>
            <div className="w-full mt-4 space-y-2">
              {report?.ats_result && [
                { label: 'Skills', value: report.ats_result.skills_score },
                { label: 'Experience', value: report.ats_result.experience_score },
                { label: 'Education', value: report.ats_result.education_score },
                { label: 'Projects', value: report.ats_result.projects_score },
                { label: 'Formatting', value: report.ats_result.formatting_score },
                { label: 'Certifications', value: report.ats_result.certifications_score },
              ].map((item) => (
                <div key={item.label} className="flex items-center gap-2">
                  <span className="text-xs text-dark-400 w-24">{item.label}</span>
                  <div className="flex-1 h-1.5 bg-dark-700 rounded-full overflow-hidden">
                    <div className="h-full rounded-full" style={{ width: `${item.value || 0}%`, backgroundColor: getScoreColor(item.value || 0) }} />
                  </div>
                  <span className="text-xs text-dark-500 w-8 text-right">{(item.value || 0).toFixed(0)}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Summary & Analysis */}
          <div className="lg:col-span-2 space-y-6">
            {/* AI Summary */}
            {candidate.ai_summary && (
              <div className="glass-card p-6">
                <h3 className="text-sm font-semibold text-dark-300 mb-3">AI Summary</h3>
                <p className="text-dark-400 leading-relaxed text-sm">{candidate.ai_summary}</p>
              </div>
            )}

            {/* Strengths & Weaknesses */}
            <div className="grid md:grid-cols-2 gap-4">
              <div className="glass-card p-6">
                <h3 className="text-sm font-semibold text-emerald-400 mb-3">Strengths</h3>
                <ul className="space-y-2">
                  {(candidate.ai_strengths || []).map((s, i) => (
                    <li key={i} className="text-sm text-dark-400 flex items-start gap-2">
                      <span className="text-emerald-400 mt-0.5">+</span> {s}
                    </li>
                  ))}
                  {(!candidate.ai_strengths || candidate.ai_strengths.length === 0) && (
                    <li className="text-sm text-dark-500">No data yet</li>
                  )}
                </ul>
              </div>
              <div className="glass-card p-6">
                <h3 className="text-sm font-semibold text-rose-400 mb-3">Weaknesses</h3>
                <ul className="space-y-2">
                  {(candidate.ai_weaknesses || []).map((w, i) => (
                    <li key={i} className="text-sm text-dark-400 flex items-start gap-2">
                      <span className="text-rose-400 mt-0.5">-</span> {w}
                    </li>
                  ))}
                  {(!candidate.ai_weaknesses || candidate.ai_weaknesses.length === 0) && (
                    <li className="text-sm text-dark-500">No data yet</li>
                  )}
                </ul>
              </div>
            </div>

            {/* Skills Gap */}
            {report?.ats_result?.matched_skills?.length > 0 && (
              <div className="glass-card p-6">
                <h3 className="text-sm font-semibold text-dark-300 mb-3">Skills Match</h3>
                <div className="flex flex-wrap gap-2 mb-4">
                  {report.ats_result.matched_skills.map((s, i) => (
                    <span key={i} className="px-3 py-1.5 text-xs rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      {typeof s === 'object' ? s.skill || JSON.stringify(s) : s}
                    </span>
                  ))}
                </div>
                {report.ats_result.missing_skills?.length > 0 && (
                  <>
                    <h4 className="text-xs font-semibold text-rose-400 mb-2">Missing Skills</h4>
                    <div className="flex flex-wrap gap-2">
                      {report.ats_result.missing_skills.map((s, i) => (
                        <span key={i} className="px-3 py-1.5 text-xs rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
                          {typeof s === 'object' ? s.skill || JSON.stringify(s) : s}
                        </span>
                      ))}
                    </div>
                  </>
                )}
                {report.ats_result.recommended_skills?.length > 0 && (
                  <>
                    <h4 className="text-xs font-semibold text-primary-400 mt-3 mb-2">Recommended</h4>
                    <div className="flex flex-wrap gap-2">
                      {report.ats_result.recommended_skills.map((s, i) => (
                        <span key={i} className="px-3 py-1.5 text-xs rounded-lg bg-primary-500/10 text-primary-400 border border-primary-500/20">
                          {typeof s === 'object' ? s.skill || JSON.stringify(s) : s}
                        </span>
                      ))}
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Interview Questions */}
        {report?.interview_questions?.length > 0 && (
          <div className="glass-card p-6 mt-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <HiChatBubbleLeftRight className="w-5 h-5 text-primary-400" />
              AI Interview Questions ({report.interview_questions.length})
            </h3>
            <div className="grid md:grid-cols-2 gap-4">
              {report.interview_questions.map((q, i) => (
                <div key={i} className="p-4 rounded-xl bg-dark-800/50 border border-dark-700/30">
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      q.category === 'technical' ? 'bg-blue-500/20 text-blue-400' :
                      q.category === 'hr' ? 'bg-purple-500/20 text-purple-400' :
                      q.category === 'behavioral' ? 'bg-emerald-500/20 text-emerald-400' :
                      q.category === 'coding' ? 'bg-amber-500/20 text-amber-400' :
                      'bg-cyan-500/20 text-cyan-400'
                    }`}>
                      {q.category}
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      q.difficulty === 'easy' ? 'bg-emerald-500/20 text-emerald-400' :
                      q.difficulty === 'hard' ? 'bg-rose-500/20 text-rose-400' :
                      'bg-yellow-500/20 text-yellow-400'
                    }`}>
                      {q.difficulty}
                    </span>
                  </div>
                  <p className="text-sm text-dark-200">{q.question}</p>
                  {q.expected_answer && (
                    <p className="text-xs text-dark-500 mt-2">Expected: {q.expected_answer}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Skills list */}
        {candidate.skills?.length > 0 && (
          <div className="glass-card p-6 mt-6">
            <h3 className="text-lg font-semibold mb-4">Skills</h3>
            <div className="flex flex-wrap gap-2">
              {candidate.skills.map((s, i) => (
                <span key={i} className="px-3 py-1.5 text-sm rounded-lg bg-dark-800 text-dark-300 border border-dark-700/50">
                  {s.name || s}
                </span>
              ))}
            </div>
          </div>
        )}
      </motion.div>
    </div>
  )
}
