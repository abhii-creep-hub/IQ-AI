import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { HiOutlineCalendarDays, HiOutlineMagnifyingGlass } from 'react-icons/hi2'
import { useInterviews, useJobs } from '../hooks/useQueries'

const statuses = ['scheduled', 'rescheduled', 'completed', 'cancelled']
const types = ['technical', 'behavioral', 'hr', 'hiring_manager', 'phone_screen', 'other']

function dateLabel(interview) {
  const value = new Date(interview.scheduled_at)
  return Number.isNaN(value.getTime()) ? 'Time unavailable' : new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium', timeStyle: 'short', timeZone: interview.timezone || undefined,
  }).format(value)
}

export default function InterviewsPage() {
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [jobId, setJobId] = useState('')
  const [type, setType] = useState('')
  const [fromDate, setFromDate] = useState('')
  const [toDate, setToDate] = useState('')
  const jobsQuery = useJobs({ limit: 100 })
  const jobs = Array.isArray(jobsQuery.data) ? jobsQuery.data : (jobsQuery.data?.jobs || [])
  const params = useMemo(() => ({
    ...(search.trim() ? { search: search.trim() } : {}),
    ...(status ? { status } : {}), ...(jobId ? { job_id: jobId } : {}),
    ...(type ? { interview_type: type } : {}), ...(fromDate ? { from_date: fromDate } : {}),
    ...(toDate ? { to_date: toDate } : {}),
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
  }), [search, status, jobId, type, fromDate, toDate])
  const query = useInterviews(params)
  const clear = () => { setSearch(''); setStatus(''); setJobId(''); setType(''); setFromDate(''); setToDate('') }
  return (
    <div className="page-container">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-6">
        <div><p className="text-primary-400 text-sm font-medium">Recruitment operations</p><h1 className="text-2xl sm:text-3xl font-bold mt-1">Interviews</h1><p className="text-dark-400 mt-2">Review schedules, update interview details, and capture feedback.</p></div>
        <span className="rounded-xl border border-dark-700 bg-dark-900 px-3 py-2 text-sm text-dark-300"><HiOutlineCalendarDays className="inline w-4 h-4 mr-2 text-primary-400" />{query.data?.length || 0} interviews</span>
      </div>
      <section className="glass-card p-4 sm:p-5 mb-6">
        <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-3">
          <label className="text-xs text-dark-400">Search candidate or interviewer
            <span className="relative block mt-1.5"><HiOutlineMagnifyingGlass className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-500" /><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Name" className="glass-input pl-10" /></span>
          </label>
          <label className="text-xs text-dark-400">Status
            <select value={status} onChange={(e) => setStatus(e.target.value)} className="glass-input mt-1.5"><option value="">All statuses</option>{statuses.map((item) => <option key={item} value={item}>{item}</option>)}</select>
          </label>
          <label className="text-xs text-dark-400">Job
            <select value={jobId} onChange={(e) => setJobId(e.target.value)} className="glass-input mt-1.5"><option value="">All jobs</option>{jobs.map((job) => <option key={job.id} value={job.id}>{job.title}</option>)}</select>
          </label>
          <label className="text-xs text-dark-400">Interview type
            <select value={type} onChange={(e) => setType(e.target.value)} className="glass-input mt-1.5"><option value="">All types</option>{types.map((item) => <option key={item} value={item}>{item.replace('_', ' ')}</option>)}</select>
          </label>
          <label className="text-xs text-dark-400">From date<input type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)} className="glass-input mt-1.5" /></label>
          <label className="text-xs text-dark-400">To date<input type="date" value={toDate} onChange={(e) => setToDate(e.target.value)} className="glass-input mt-1.5" /></label>
          <div className="flex items-end"><button onClick={clear} className="glass-button-secondary w-full">Clear filters</button></div>
        </div>
        {jobsQuery.isError && <p className="text-amber-300 text-sm mt-3">Could not load job filters. Refresh to try again.</p>}
      </section>
      {query.isLoading ? <div className="glass-card p-8 text-center text-dark-400">Loading interviews…</div> : query.isError ? (
        <div className="glass-card p-8 text-center" role="alert"><p className="text-rose-300">Could not load interviews.</p><button className="glass-button mt-4" onClick={() => query.refetch()}>Try again</button></div>
      ) : query.data?.length ? (
        <div className="space-y-3">
          {query.data.map((interview) => <article key={interview.id} className="glass-card p-4 sm:p-5 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            <div className="min-w-0">
              <div className="flex flex-wrap gap-2 items-center"><Link to={`/dashboard/interviews/${interview.id}`} className="text-lg font-semibold hover:text-primary-300">{interview.candidate_name}</Link><span className={`text-xs px-2 py-1 rounded-full capitalize ${interview.status === 'completed' ? 'bg-emerald-500/10 text-emerald-300' : interview.status === 'cancelled' ? 'bg-rose-500/10 text-rose-300' : 'bg-primary-500/10 text-primary-300'}`}>{interview.status}</span></div>
              <p className="text-sm text-dark-400 mt-1">{dateLabel(interview)} · {interview.duration_minutes} min · {interview.interview_type.replace('_', ' ')}</p>
              <p className="text-xs text-dark-500 mt-1">{interview.job_title || 'General screening'} · Interviewer: {interview.interviewer_name}</p>
            </div>
            <div className="flex gap-3 items-center"><Link to={`/dashboard/candidates/${interview.candidate_id}`} className="text-sm text-dark-300 hover:text-white">Candidate</Link><Link to={`/dashboard/interviews/${interview.id}`} className="glass-button-secondary py-2 px-4 text-sm">Open interview</Link></div>
          </article>)}
        </div>
      ) : <div className="glass-card p-10 text-center"><HiOutlineCalendarDays className="w-10 h-10 text-dark-500 mx-auto" /><h2 className="font-semibold mt-3">No interviews found</h2><p className="text-sm text-dark-400 mt-1">Schedule an interview from a candidate profile or clear your filters.</p><button onClick={clear} className="glass-button-secondary mt-4">Clear filters</button></div>}
    </div>
  )
}
