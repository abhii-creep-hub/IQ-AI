import { Link, useSearchParams } from 'react-router-dom'
import { HiArrowLeft, HiScale } from 'react-icons/hi2'
import { useCandidateComparison } from '../hooks/useQueries'

function scoreText(value) {
  return value !== null && value !== undefined && value !== '' && Number.isFinite(Number(value))
    ? `${Number(value).toFixed(1)} / 100`
    : 'Not analyzed'
}

function skillName(value) {
  return typeof value === 'object' ? value?.skill || value?.name || '' : value
}

function SkillList({ items, emptyText, color = 'text-dark-300' }) {
  const values = (items || []).map(skillName).filter(Boolean)
  if (!values.length) return <span className="text-sm text-dark-500">{emptyText}</span>
  return (
    <div className="flex flex-wrap gap-2">
      {values.map((item, index) => (
        <span key={`${item}-${index}`} className={`px-2.5 py-1 rounded-lg text-xs bg-dark-800 border border-dark-700/60 ${color}`}>
          {item}
        </span>
      ))}
    </div>
  )
}

export default function CandidateComparisonPage() {
  const [searchParams] = useSearchParams()
  const ids = [...new Set((searchParams.get('ids') || '').split(',').filter(Boolean))]
  const { data, isLoading, isError, error } = useCandidateComparison(ids)

  if (ids.length < 2 || ids.length > 3) {
    return (
      <div className="page-container text-center py-20 glass-card">
        <p className="text-dark-300">Select 2 or 3 candidates from the same job to compare them.</p>
        <Link to="/dashboard/candidates" className="glass-button mt-4 text-sm inline-block">Back to Candidates</Link>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="page-container flex justify-center py-20">
        <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className="page-container text-center py-20 glass-card">
        <p className="text-dark-300">{error?.response?.data?.detail || 'Could not compare these candidates. Please try again.'}</p>
        <Link to="/dashboard/candidates" className="glass-button mt-4 text-sm inline-block">Back to Candidates</Link>
      </div>
    )
  }

  const rows = [
    { label: 'ATS score', render: (candidate) => <span className="font-semibold text-primary-300">{scoreText(candidate.ats_score)}</span> },
    { label: 'Job match score', render: (candidate) => <span className="font-semibold text-primary-300">{scoreText(candidate.job_match_score)}</span> },
    { label: 'Rank and status', render: (candidate) => <span className="capitalize">{candidate.rank} · {candidate.status}</span> },
    { label: 'Total experience', render: (candidate) => candidate.total_experience_years == null ? 'Not listed' : `${candidate.total_experience_years} years` },
    { label: 'Skills score', render: (candidate) => scoreText(candidate.score_breakdown?.skills) },
    { label: 'Experience score', render: (candidate) => scoreText(candidate.score_breakdown?.experience) },
    { label: 'Education score', render: (candidate) => scoreText(candidate.score_breakdown?.education) },
    { label: 'Project score', render: (candidate) => scoreText(candidate.score_breakdown?.projects) },
    { label: 'Skills', render: (candidate) => <SkillList items={candidate.skills} emptyText="No skills parsed" /> },
    { label: 'Matched job skills', render: (candidate) => <SkillList items={candidate.matched_skill_evidence} emptyText="No matches recorded" color="text-emerald-300" /> },
    { label: 'Missing job skills', render: (candidate) => <SkillList items={candidate.missing_skills} emptyText="No gaps recorded" color="text-rose-300" /> },
    {
      label: 'Recent experience',
      render: (candidate) => candidate.experience?.length ? (
        <ul className="space-y-2">
          {candidate.experience.slice(0, 3).map((item, index) => (
            <li key={`${item.title}-${index}`}>
              <span className="text-dark-200">{item.title || 'Role not listed'}</span>
              {item.company && <span className="block text-xs text-dark-500">{item.company}</span>}
              {(item.start_date || item.end_date) && <span className="block text-xs text-dark-500">{item.start_date || 'Start unknown'} - {item.is_current === 'true' ? 'Present' : item.end_date || 'End unknown'}</span>}
            </li>
          ))}
        </ul>
      ) : <span className="text-dark-500">No experience listed</span>,
    },
    {
      label: 'Education',
      render: (candidate) => candidate.education?.length ? (
        <ul className="space-y-2">
          {candidate.education.slice(0, 3).map((item, index) => (
            <li key={`${item.institution}-${index}`}>
              <span className="text-dark-200">{[item.degree, item.field_of_study].filter(Boolean).join(' - ') || 'Qualification not listed'}</span>
              {item.institution && <span className="block text-xs text-dark-500">{item.institution}</span>}
            </li>
          ))}
        </ul>
      ) : <span className="text-dark-500">No education listed</span>,
    },
  ]

  return (
    <div className="page-container">
      <Link to="/dashboard/candidates" className="inline-flex items-center gap-2 text-dark-400 hover:text-white mb-6 transition-colors">
        <HiArrowLeft className="w-4 h-4" /> Back to Candidates
      </Link>
      <div className="flex items-start gap-3 mb-6">
        <HiScale className="w-7 h-7 text-primary-400 mt-1" />
        <div>
          <h1 className="text-2xl font-bold">Candidate Comparison</h1>
          <p className="text-sm text-dark-400 mt-1">{data.job?.title || 'Unassigned candidates'}</p>
        </div>
      </div>
      {data.job && (data.job.requirements || data.job.description || data.job.required_skills?.length || data.job.preferred_skills?.length) && (
        <div className="glass-card p-5 mb-6">
          <h2 className="text-sm font-semibold text-dark-200 mb-2">Role criteria</h2>
          {(data.job.requirements || data.job.description) && (
            <p className="text-sm text-dark-400 whitespace-pre-line max-h-28 overflow-y-auto">
              {data.job.requirements || data.job.description}
            </p>
          )}
          {data.job.required_skills?.length > 0 && (
            <div className="mt-3">
              <p className="text-xs text-dark-500 mb-2">Required skills</p>
              <SkillList items={data.job.required_skills} emptyText="No required skills listed" color="text-primary-300" />
            </div>
          )}
          {data.job.preferred_skills?.length > 0 && (
            <div className="mt-3">
              <p className="text-xs text-dark-500 mb-2">Preferred skills</p>
              <SkillList items={data.job.preferred_skills} emptyText="No preferred skills listed" color="text-dark-300" />
            </div>
          )}
        </div>
      )}
      <div className="glass-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[760px]">
            <thead>
              <tr className="border-b border-dark-700/50">
                <th className="text-left text-xs font-semibold text-dark-400 uppercase tracking-wider p-4 sticky left-0 bg-dark-900">Details</th>
                {data.candidates.map((candidate) => (
                  <th key={candidate.id} className="text-left p-4 min-w-[230px] align-top">
                    <Link to={`/dashboard/candidates/${candidate.id}`} className="text-base font-semibold text-white hover:text-primary-300">
                      {candidate.name}
                    </Link>
                    <p className="text-xs text-dark-500 mt-1">Recruiter review recommended</p>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.label} className="border-b border-dark-700/30 align-top">
                  <th className="text-left text-sm font-medium text-dark-400 p-4 sticky left-0 bg-dark-900">{row.label}</th>
                  {data.candidates.map((candidate) => (
                    <td key={candidate.id} className="p-4 text-sm text-dark-300 min-w-[230px]">{row.render(candidate)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <p className="text-xs text-dark-500 mt-4">Scores are AI-generated decision support. Review the source resumes and make hiring decisions with human judgment.</p>
    </div>
  )
}
