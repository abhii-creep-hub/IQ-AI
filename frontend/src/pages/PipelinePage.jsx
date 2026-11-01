import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { HiOutlineBriefcase, HiOutlineMagnifyingGlass, HiOutlineArrowPath, HiOutlineUserGroup } from 'react-icons/hi2'
import { useJobs, useMovePipelineCandidate, usePipeline } from '../hooks/useQueries'

const stages = [
  { id: 'applied', label: 'Applied', color: 'border-sky-400' },
  { id: 'screening', label: 'Screening', color: 'border-violet-400' },
  { id: 'shortlisted', label: 'Shortlisted', color: 'border-amber-400' },
  { id: 'interview', label: 'Interview', color: 'border-cyan-400' },
  { id: 'offer', label: 'Offer', color: 'border-emerald-400' },
  { id: 'hired', label: 'Hired', color: 'border-green-500' },
  { id: 'rejected', label: 'Rejected', color: 'border-rose-400' },
]

function dateLabel(value) {
  if (!value) return 'Date unavailable'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? 'Date unavailable' : date.toLocaleDateString()
}

export default function PipelinePage() {
  const [jobFilter, setJobFilter] = useState('all')
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [stageFilter, setStageFilter] = useState('all')
  const [draggingId, setDraggingId] = useState(null)
  const jobsQuery = useJobs({ limit: 100 })
  const jobs = Array.isArray(jobsQuery.data) ? jobsQuery.data : (jobsQuery.data?.jobs || [])
  const params = useMemo(() => ({
    ...(jobFilter !== 'all' && jobFilter !== 'unassigned' ? { job_id: jobFilter } : {}),
    ...(jobFilter === 'unassigned' ? { unassigned: true } : {}),
    ...(search.trim() ? { search: search.trim() } : {}),
    ...(stageFilter !== 'all' ? { stage: stageFilter } : {}),
  }), [jobFilter, search, stageFilter])
  const pipelineQuery = usePipeline(params)
  const moveCandidate = useMovePipelineCandidate()
  const candidates = pipelineQuery.data?.candidates || []
  const counts = pipelineQuery.data?.stage_counts || {}
  const filterCandidates = (stage) => candidates.filter((candidate) => candidate.recruitment_stage === stage)

  const move = (candidateId, stage) => {
    if (stage === 'rejected' && !window.confirm('Move this candidate to Rejected?')) return
    moveCandidate.mutate({ candidateId, stage })
  }
  const clearFilters = () => {
    setJobFilter('all')
    setSearchInput('')
    setSearch('')
    setStageFilter('all')
  }

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6">
      <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4">
        <div>
          <p className="text-primary-400 text-sm font-medium">Recruitment operations</p>
          <h1 className="text-2xl sm:text-3xl font-bold mt-1">Recruitment Pipeline</h1>
          <p className="text-dark-400 mt-2">Track candidates from application through hiring.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-sm text-dark-300">
          <span className="inline-flex items-center gap-2 rounded-xl border border-dark-700 bg-dark-900 px-3 py-2">
            <HiOutlineUserGroup className="w-4 h-4 text-primary-400" /> {candidates.length} shown
          </span>
          <button onClick={() => pipelineQuery.refetch()} className="inline-flex items-center gap-2 rounded-xl border border-dark-700 bg-dark-900 px-3 py-2 hover:bg-dark-800" aria-label="Refresh pipeline">
            <HiOutlineArrowPath className={`w-4 h-4 ${pipelineQuery.isFetching ? 'animate-spin' : ''}`} /> Refresh
          </button>
        </div>
      </div>

      <section className="glass-card p-4 sm:p-5">
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-[minmax(220px,1fr)_minmax(220px,1fr)_minmax(190px,0.8fr)_auto_auto] gap-3 items-end">
          <label className="block">
            <span className="text-xs font-medium text-dark-400 mb-2 block">Job role</span>
            <span className="relative block">
              <HiOutlineBriefcase className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-400 pointer-events-none" />
              <select value={jobFilter} onChange={(event) => setJobFilter(event.target.value)} className="glass-input pl-10 w-full" aria-label="Filter by job">
                <option value="all">All Jobs</option>
                {jobs.map((job) => <option key={job.id} value={job.id}>{job.title}</option>)}
                <option value="unassigned">Unassigned / General Screening</option>
              </select>
            </span>
          </label>
          <form onSubmit={(event) => { event.preventDefault(); setSearch(searchInput) }}>
            <label className="text-xs font-medium text-dark-400 mb-2 block" htmlFor="pipeline-search">Search candidates</label>
            <span className="relative block">
              <HiOutlineMagnifyingGlass className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-400" />
              <input id="pipeline-search" value={searchInput} onChange={(event) => setSearchInput(event.target.value)} placeholder="Name or email" className="glass-input pl-10 w-full" />
            </span>
          </form>
          <label className="block">
            <span className="text-xs font-medium text-dark-400 mb-2 block">Stage</span>
            <select value={stageFilter} onChange={(event) => setStageFilter(event.target.value)} className="glass-input w-full" aria-label="Filter by stage">
              <option value="all">All Stages</option>
              {stages.map((stage) => <option key={stage.id} value={stage.id}>{stage.label}</option>)}
            </select>
          </label>
          <button onClick={() => setSearch(searchInput)} className="glass-button h-[42px] py-2">Search</button>
          <button onClick={clearFilters} className="glass-button-secondary h-[42px] py-2">Clear filters</button>
        </div>
        {jobsQuery.isError && <p role="alert" className="text-amber-300 text-sm mt-3">Job list could not be loaded. You can still view all candidates and retry by refreshing.</p>}
      </section>

      {pipelineQuery.isLoading ? (
        <div className="flex gap-4 overflow-hidden" aria-label="Loading pipeline">
          {stages.slice(0, 4).map((stage) => <div key={stage.id} className="min-w-[260px] flex-1 h-80 rounded-2xl bg-dark-900 border border-dark-800 animate-pulse" />)}
        </div>
      ) : pipelineQuery.isError ? (
        <div className="glass-card p-8 text-center" role="alert">
          <p className="text-rose-300 font-medium">Could not load the recruitment pipeline.</p>
          <p className="text-dark-400 text-sm mt-2">Check that the backend is running, then try again.</p>
          <button onClick={() => pipelineQuery.refetch()} className="glass-button mt-4">Try again</button>
        </div>
      ) : candidates.length === 0 ? (
        <div className="glass-card p-10 text-center">
          <HiOutlineUserGroup className="w-10 h-10 text-dark-500 mx-auto" />
          <h2 className="font-semibold mt-3">No candidates match these filters</h2>
          <p className="text-sm text-dark-400 mt-1">Try another job or clear the filters. Candidates appear here when resumes are uploaded.</p>
          <button onClick={clearFilters} className="glass-button-secondary mt-4">Clear filters</button>
        </div>
      ) : (
        <div className="overflow-x-auto pb-3">
          <div className="flex items-start gap-4 min-w-max">
            {stages.map((stage) => {
              const stageCandidates = filterCandidates(stage.id)
              return (
                <section key={stage.id} className={`w-[280px] sm:w-[300px] rounded-2xl border border-dark-800 bg-dark-900/70 border-t-2 ${stage.color}`} onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); if (draggingId) move(draggingId, stage.id); setDraggingId(null) }} aria-label={`${stage.label} stage`}>
                  <header className="px-4 py-3 border-b border-dark-800 flex items-center justify-between">
                    <h2 className="font-semibold">{stage.label}</h2>
                    <span className="text-xs rounded-full bg-dark-800 px-2.5 py-1 text-dark-300">{counts[stage.id] ?? stageCandidates.length}</span>
                  </header>
                  <div className="p-3 space-y-3 min-h-32">
                    {stageCandidates.length === 0 ? <p className="text-sm text-dark-500 text-center py-6">No candidates in this stage</p> : stageCandidates.map((candidate) => (
                      <article key={candidate.id} draggable onDragStart={() => setDraggingId(candidate.id)} onDragEnd={() => setDraggingId(null)} className={`rounded-xl border border-dark-700/80 bg-dark-800/70 p-4 transition-opacity ${draggingId === candidate.id ? 'opacity-50' : ''}`}>
                        <div className="flex items-start justify-between gap-2">
                          <Link to={`/dashboard/candidates/${candidate.id}`} className="font-semibold hover:text-primary-300 focus-visible:outline focus-visible:outline-primary-400">{candidate.name || 'Unnamed candidate'}</Link>
                          {candidate.rank && candidate.rank !== 'pending' && <span className="text-[10px] uppercase tracking-wide text-primary-300 bg-primary-500/10 rounded-full px-2 py-1">{candidate.rank}</span>}
                        </div>
                        {candidate.email && <p className="text-xs text-dark-400 truncate mt-1">{candidate.email}</p>}
                        <div className="mt-3 space-y-1.5 text-xs text-dark-400">
                          <p className="truncate">{candidate.job_title || 'Unassigned / General Screening'}</p>
                          <p className="flex flex-wrap gap-x-3 gap-y-1">
                            {candidate.ats_score != null && <span>ATS {Number(candidate.ats_score).toFixed(0)}</span>}
                            {candidate.match_score != null && <span>Match {Number(candidate.match_score).toFixed(0)}%</span>}
                            {candidate.total_experience_years != null && <span>{candidate.total_experience_years} yrs exp.</span>}
                          </p>
                          <p>Added {dateLabel(candidate.created_at)}</p>
                        </div>
                        <label className="block mt-3">
                          <span className="sr-only">Move {candidate.name} to stage</span>
                          <select value={candidate.recruitment_stage} disabled={moveCandidate.isPending} onChange={(event) => move(candidate.id, event.target.value)} className="glass-input text-xs py-2 w-full" aria-label={`Move ${candidate.name} to stage`}>
                            {stages.map((option) => <option key={option.id} value={option.id}>{option.id === candidate.recruitment_stage ? `Current: ${option.label}` : `Move to ${option.label}`}</option>)}
                          </select>
                        </label>
                      </article>
                    ))}
                  </div>
                </section>
              )
            })}
          </div>
        </div>
      )}
      <p className="text-xs text-dark-500">Drag a card to another stage, or use its stage menu for keyboard and touch access. Moving a candidate to Rejected asks for confirmation.</p>
    </div>
  )
}
