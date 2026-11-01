import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useCandidates, useDeleteCandidate, useJobs } from '../hooks/useQueries'
import { HiUsers, HiMagnifyingGlass, HiTrash, HiEye, HiFunnel } from 'react-icons/hi2'
import { formatDate } from '../utils/helpers'
import CandidateForm from '../components/CandidateForm'

export default function CandidatesPage() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [rankFilter, setRankFilter] = useState('')
  const [jobFilter, setJobFilter] = useState('all')
  const [selectedForCompare, setSelectedForCompare] = useState([])
  const [compareMessage, setCompareMessage] = useState('')
  const [showCandidateForm, setShowCandidateForm] = useState(false)
  const {
    data: jobs,
    isLoading: isJobsLoading,
    isError: isJobsError,
  } = useJobs({ limit: 100 })
  const candidateParams = {
    skip: 0,
    limit: 100,
    search: search.trim() || undefined,
    rank: rankFilter || undefined,
    job_id: jobFilter !== 'all' && jobFilter !== 'unassigned' ? jobFilter : undefined,
    unassigned: jobFilter === 'unassigned' ? true : undefined,
  }
  const {
    data: candidates,
    isLoading,
    isError: isCandidatesError,
    error: candidatesError,
    refetch: refetchCandidates,
  } = useCandidates(candidateParams)
  const deleteMutation = useDeleteCandidate()

  const filteredCandidates = candidates || []
  const jobOptions = jobs || []

  const clearComparisonSelection = () => {
    setSelectedForCompare([])
    setCompareMessage('')
  }

  useEffect(() => {
    if (
      jobFilter !== 'all' &&
      jobFilter !== 'unassigned' &&
      !isJobsLoading &&
      Array.isArray(jobs) &&
      !jobs.some((job) => job.id === jobFilter)
    ) {
      setJobFilter('all')
      setSelectedForCompare([])
      setCompareMessage('The selected job is no longer available. Showing all jobs.')
    }
  }, [jobFilter, isJobsLoading, jobs])

  useEffect(() => {
    if (!isLoading && !isCandidatesError && Array.isArray(candidates)) {
      const visibleIds = new Set(candidates.map((candidate) => candidate.id))
      setSelectedForCompare((current) => current.filter((candidate) => visibleIds.has(candidate.id)))
    }
  }, [candidates, isCandidatesError, isLoading])

  const toggleCompareCandidate = (candidate) => {
    setCompareMessage('')
    const alreadySelected = selectedForCompare.some((item) => item.id === candidate.id)
    if (alreadySelected) {
      setSelectedForCompare((current) => current.filter((item) => item.id !== candidate.id))
      return
    }
    if (selectedForCompare.length >= 3) {
      setCompareMessage('You can compare up to 3 candidates at a time.')
      return
    }
    const selectedJobId = selectedForCompare[0]?.job_id || null
    const candidateJobId = candidate.job_id || null
    if (selectedForCompare.length && selectedJobId !== candidateJobId) {
      setCompareMessage('Choose candidates assigned to the same job to compare them.')
      return
    }
    setSelectedForCompare((current) => [...current, candidate])
  }

  const startComparison = () => {
    if (selectedForCompare.length < 2) return
    const ids = selectedForCompare.map((candidate) => candidate.id).join(',')
    navigate(`/dashboard/candidates/compare?ids=${encodeURIComponent(ids)}`)
  }

  return (
    <div className="page-container">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center justify-between gap-3 mb-8">
          <div className="flex items-center gap-3">
            <HiUsers className="w-7 h-7 text-primary-400" />
            <h1 className="text-2xl font-bold">Candidates</h1>
          </div>
          <button type="button" onClick={() => setShowCandidateForm(true)} className="glass-button text-sm">+ Add candidate</button>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-3 mb-6">
          <div className="relative flex-1">
            <HiMagnifyingGlass className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-400" />
            <input
              value={search}
              onChange={(e) => { setSearch(e.target.value); clearComparisonSelection() }}
              className="glass-input pl-10"
              placeholder="Search candidates..."
            />
          </div>
          <div className="relative">
            <HiFunnel className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-400" />
            <select
              value={rankFilter}
              onChange={(e) => { setRankFilter(e.target.value); clearComparisonSelection() }}
              className="glass-input pl-9 pr-4 w-44"
            >
              <option value="">All Ranks</option>
              <option value="gold">Gold</option>
              <option value="silver">Silver</option>
              <option value="bronze">Bronze</option>
              <option value="shortlisted">Shortlisted</option>
              <option value="pending">Pending</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>
          <select
            value={jobFilter}
            onChange={(e) => { setJobFilter(e.target.value); clearComparisonSelection() }}
            className="glass-input w-full sm:w-56"
            aria-label="Filter candidates by job role"
            disabled={isJobsLoading || isJobsError}
          >
            <option value="all">All Jobs</option>
            {jobOptions.map((job) => (
              <option key={job.id} value={job.id}>{job.title}</option>
            ))}
            <option value="unassigned">Unassigned / General Screening</option>
          </select>
        </div>

        {isJobsError && (
          <p role="alert" className="text-sm text-amber-300 mb-4">
            Job postings could not be loaded. Candidate search and rank filters are still available.
          </p>
        )}

        <p className="text-xs text-dark-400 mb-4" aria-live="polite">
          Showing {filteredCandidates.length} candidate{filteredCandidates.length === 1 ? '' : 's'} · {selectedForCompare.length} selected for comparison
        </p>

        {(selectedForCompare.length > 0 || compareMessage) && (
          <div className="glass-card p-4 mb-6 flex flex-col sm:flex-row sm:items-center gap-3 sm:justify-between">
            <div>
              <p className="text-sm font-medium text-dark-200">
                {selectedForCompare.length}/3 candidates selected for comparison
              </p>
              {selectedForCompare.length > 0 && (
                <p className="text-xs text-dark-400 mt-1">
                  {selectedForCompare.map((candidate) => candidate.name).join(' · ')} · Same job only
                </p>
              )}
              {selectedForCompare.length === 0 && <p className="text-xs text-dark-500 mt-1">Select 2-3 candidates assigned to the same job.</p>}
              {compareMessage && <p role="alert" className="text-xs text-amber-300 mt-1">{compareMessage}</p>}
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={clearComparisonSelection}
                className="glass-button text-sm"
              >
                Clear
              </button>
              <button
                type="button"
                disabled={selectedForCompare.length < 2}
                onClick={startComparison}
                className="glass-button text-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Compare candidates
              </button>
            </div>
          </div>
        )}

        {/* Table */}
        {isLoading ? (
          <div className="flex justify-center py-20">
            <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : isCandidatesError ? (
          <div className="text-center py-16 glass-card">
            <p role="alert" className="text-rose-300">{candidatesError?.response?.data?.detail || 'Candidates could not be loaded.'}</p>
            <button type="button" onClick={() => refetchCandidates()} className="glass-button mt-4 text-sm">Retry</button>
          </div>
        ) : filteredCandidates.length > 0 ? (
          <div className="glass-card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-dark-700/50">
                    <th className="text-left text-xs font-semibold text-dark-400 uppercase tracking-wider p-4">Compare</th>
                    <th className="text-left text-xs font-semibold text-dark-400 uppercase tracking-wider p-4">Candidate</th>
                    <th className="text-left text-xs font-semibold text-dark-400 uppercase tracking-wider p-4">Rank</th>
                    <th className="text-left text-xs font-semibold text-dark-400 uppercase tracking-wider p-4">Status</th>
                    <th className="text-left text-xs font-semibold text-dark-400 uppercase tracking-wider p-4">Recommendation</th>
                    <th className="text-left text-xs font-semibold text-dark-400 uppercase tracking-wider p-4">Experience</th>
                    <th className="text-left text-xs font-semibold text-dark-400 uppercase tracking-wider p-4">Uploaded</th>
                    <th className="text-right text-xs font-semibold text-dark-400 uppercase tracking-wider p-4">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredCandidates.map((c) => (
                    <tr key={c.id} className="border-b border-dark-700/30 hover:bg-dark-800/50 transition-colors">
                      <td className="p-4">
                        <input
                          type="checkbox"
                          checked={selectedForCompare.some((item) => item.id === c.id)}
                          onChange={() => toggleCompareCandidate(c)}
                          disabled={
                            !selectedForCompare.some((item) => item.id === c.id) &&
                            (selectedForCompare.length >= 3 ||
                              (selectedForCompare.length > 0 &&
                                (selectedForCompare[0].job_id || null) !== (c.job_id || null)))
                          }
                          aria-label={`Select ${c.name} for comparison`}
                          title={
                            selectedForCompare.length >= 3 && !selectedForCompare.some((item) => item.id === c.id)
                              ? 'You can compare up to 3 candidates'
                              : selectedForCompare.length > 0 &&
                                  (selectedForCompare[0].job_id || null) !== (c.job_id || null)
                                ? 'Candidates must be assigned to the same job'
                                : `Select ${c.name} for comparison`
                          }
                          className="w-4 h-4 accent-blue-500 disabled:opacity-40"
                        />
                      </td>
                      <td className="p-4">
                        <Link
                          to={`/dashboard/candidates/${c.id}`}
                          className="flex items-center gap-3 group"
                        >
                          <div className="w-9 h-9 rounded-full bg-primary-500/20 flex items-center justify-center text-sm font-semibold text-primary-400">
                            {c.name?.[0] || '?'}
                          </div>
                          <div>
                            <p className="font-medium text-sm group-hover:text-primary-400 transition-colors">{c.name}</p>
                            <p className="text-xs text-dark-400">{c.email || 'No email'}</p>
                          </div>
                        </Link>
                      </td>
                      <td className="p-4">
                        <span className={`px-3 py-1 rounded-full text-xs font-medium capitalize rank-${c.rank}`}>
                          {c.rank}
                        </span>
                      </td>
                      <td className="p-4">
                        <span className={`text-xs px-2 py-1 rounded-full ${c.status === 'analyzed' ? 'bg-emerald-500/20 text-emerald-400' : c.status === 'error' ? 'bg-rose-500/20 text-rose-400' : 'bg-dark-600 text-dark-400'}`}>
                          {c.status}
                        </span>
                      </td>
                      <td className="p-4 text-sm text-dark-400 capitalize">{c.hiring_recommendation || '-'}</td>
                      <td className="p-4 text-sm text-dark-400">{c.total_experience_years || 0}y</td>
                      <td className="p-4 text-xs text-dark-500">{formatDate(c.created_at)}</td>
                      <td className="p-4">
                        <div className="flex items-center justify-end gap-2">
                          <Link
                            to={`/dashboard/candidates/${c.id}`}
                            className="p-2 rounded-lg hover:bg-dark-700/50 text-dark-400 hover:text-primary-400 transition-colors"
                            aria-label={`View ${c.name} analytics`}
                            title="View candidate analytics"
                          >
                            <HiEye className="w-4 h-4" />
                          </Link>
                          <button
                            onClick={() => {
                              if (confirm('Delete this candidate?')) deleteMutation.mutate(c.id)
                            }}
                            className="p-2 rounded-lg hover:bg-dark-700/50 text-dark-400 hover:text-rose-400 transition-colors"
                          >
                            <HiTrash className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="text-center py-20 glass-card">
            <HiUsers className="w-12 h-12 text-dark-500 mx-auto mb-3" />
            <p className="text-dark-400">
              {jobFilter === 'unassigned'
                ? 'No unassigned candidates found.'
                : jobFilter !== 'all'
                  ? `No candidates are linked to ${jobOptions.find((job) => job.id === jobFilter)?.title || 'this job'} yet.`
                  : 'No candidates found for these filters.'}
            </p>
            <Link to="/dashboard/upload" className="glass-button mt-4 text-sm inline-block">Upload resumes</Link>
          </div>
        )}
      </motion.div>
      {showCandidateForm && <CandidateForm onClose={() => setShowCandidateForm(false)} />}
    </div>
  )
}
