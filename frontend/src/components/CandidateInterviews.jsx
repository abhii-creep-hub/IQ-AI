import { useState } from 'react'
import { Link } from 'react-router-dom'
import { HiOutlineCalendarDays, HiOutlineXMark } from 'react-icons/hi2'
import { useCreateInterview, useInterviews } from '../hooks/useQueries'
import InterviewForm from './InterviewForm'

function formatInterviewDate(interview) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium', timeStyle: 'short', timeZone: interview.timezone || undefined,
  }).format(new Date(interview.scheduled_at))
}

export default function CandidateInterviews({ candidate }) {
  const [showForm, setShowForm] = useState(false)
  const query = useInterviews({ candidate_id: candidate.id })
  const create = useCreateInterview()
  const submit = (data) => create.mutate(data, { onSuccess: () => setShowForm(false) })
  return (
    <section className="glass-card p-6 mt-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div><h3 className="text-lg font-semibold">Interviews</h3><p className="text-sm text-dark-400 mt-1">Schedule and review this candidate’s interviews.</p></div>
        <button onClick={() => setShowForm((value) => !value)} className="glass-button py-2 px-4 inline-flex items-center gap-2"><HiOutlineCalendarDays className="w-4 h-4" /> Schedule interview</button>
      </div>
      {showForm && <div className="mt-5 rounded-xl bg-dark-900/70 border border-dark-700/60 p-4 sm:p-5"><div className="flex justify-between items-center mb-4"><h4 className="font-semibold">New interview</h4><button aria-label="Close interview form" onClick={() => setShowForm(false)}><HiOutlineXMark /></button></div><InterviewForm candidateId={candidate.id} candidateJobId={candidate.job_id} onSubmit={submit} onCancel={() => setShowForm(false)} saving={create.isPending} /></div>}
      {query.isLoading ? <p className="text-dark-400 mt-4">Loading interviews…</p> : query.isError ? <p role="alert" className="text-amber-300 mt-4">Could not load interviews. Refresh the page to try again.</p> : query.data?.length ? (
        <div className="mt-4 space-y-3">
          {query.data.map((interview) => <article key={interview.id} className="rounded-xl border border-dark-700/50 bg-dark-900/50 p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div><p className="font-medium capitalize">{interview.interview_type.replace('_', ' ')} · {formatInterviewDate(interview)}</p><p className="text-sm text-dark-400 mt-1">{interview.interviewer_name} · {interview.duration_minutes} min · <span className="capitalize">{interview.status}</span></p>{interview.feedback && <p className="text-xs text-emerald-300 mt-2">Feedback: {interview.feedback.recommendation.replace('_', ' ')} · {interview.feedback.overall_rating}/5</p>}</div>
            <Link to={`/dashboard/interviews/${interview.id}`} className="text-primary-300 hover:text-primary-200 text-sm font-medium">View details</Link>
          </article>)}
        </div>
      ) : !showForm ? <p className="text-sm text-dark-400 mt-4">No interviews scheduled for this candidate yet.</p> : null}
    </section>
  )
}
