import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { HiArrowLeft, HiOutlineClipboardDocument, HiOutlineVideoCamera } from 'react-icons/hi2'
import toast from 'react-hot-toast'
import { useAuth } from '../context/AuthContext'
import { useInterview, useInterviewStatusAction, useSaveInterviewFeedback, useUpdateInterview } from '../hooks/useQueries'
import InterviewForm from '../components/InterviewForm'

function formatDate(interview) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'full', timeStyle: 'short', timeZone: interview.timezone || undefined,
  }).format(new Date(interview.scheduled_at))
}

function FeedbackForm({ interview, onSave, saving }) {
  const feedback = interview.feedback
  const [form, setForm] = useState({
    skills_rating: feedback?.skills_rating || 3,
    communication_rating: feedback?.communication_rating || 3,
    problem_solving_rating: feedback?.problem_solving_rating || 3,
    overall_rating: feedback?.overall_rating || 3,
    recommendation: feedback?.recommendation || 'maybe',
    notes: feedback?.notes || '',
  })
  const change = (event) => setForm((current) => ({ ...current, [event.target.name]: event.target.value }))
  return (
    <form onSubmit={(event) => { event.preventDefault(); onSave({ ...form, skills_rating: Number(form.skills_rating), communication_rating: Number(form.communication_rating), problem_solving_rating: Number(form.problem_solving_rating), overall_rating: Number(form.overall_rating) }) }} className="glass-card p-5 sm:p-6 mt-5">
      <h2 className="text-lg font-semibold">{feedback ? 'Update interview feedback' : 'Submit interview feedback'}</h2>
      <p className="text-sm text-dark-400 mt-1">Rate each area from 1 (low) to 5 (high), then add your recommendation.</p>
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-5">
        {[
          ['skills_rating', 'Relevant skills'], ['communication_rating', 'Communication'],
          ['problem_solving_rating', 'Problem solving'], ['overall_rating', 'Overall rating'],
        ].map(([key, label]) => <label key={key} className="text-sm text-dark-300">{label}
          <select name={key} value={form[key]} onChange={change} className="glass-input mt-1.5">{[1, 2, 3, 4, 5].map((value) => <option key={value} value={value}>{value} / 5</option>)}</select>
        </label>)}
        <label className="text-sm text-dark-300 sm:col-span-2">Recommendation
          <select name="recommendation" value={form.recommendation} onChange={change} className="glass-input mt-1.5"><option value="strong_yes">Strong Yes</option><option value="yes">Yes</option><option value="maybe">Maybe</option><option value="no">No</option></select>
        </label>
      </div>
      <label className="block text-sm text-dark-300 mt-4">Notes<textarea name="notes" maxLength={10000} rows={4} value={form.notes} onChange={change} className="glass-input mt-1.5 resize-y" placeholder="Evidence, strengths, concerns, and follow-up" /></label>
      <button disabled={saving} className="glass-button mt-4">{saving ? 'Saving…' : feedback ? 'Update feedback' : 'Save feedback'}</button>
    </form>
  )
}

export default function InterviewDetailPage() {
  const { id } = useParams()
  const { user } = useAuth()
  const query = useInterview(id)
  const update = useUpdateInterview()
  const complete = useInterviewStatusAction('complete')
  const cancel = useInterviewStatusAction('cancel')
  const saveFeedback = useSaveInterviewFeedback()
  const [editing, setEditing] = useState(false)
  const interview = query.data

  if (query.isLoading) return <div className="page-container text-center text-dark-400 py-20">Loading interview…</div>
  if (query.isError || !interview) return <div className="page-container"><div className="glass-card p-8 text-center" role="alert"><p className="text-rose-300">Interview could not be loaded.</p><Link to="/dashboard/interviews" className="glass-button-secondary inline-block mt-4">Back to Interviews</Link></div></div>

  const canManage = interview.created_by_id === user?.id
  const canGiveFeedback = interview.interviewer_user_id ? interview.interviewer_user_id === user?.id : canManage
  const active = ['scheduled', 'rescheduled'].includes(interview.status)
  const copyInvite = async () => {
    const invitation = [
      `Interview with ${interview.candidate_name}`,
      `Type: ${interview.interview_type.replace('_', ' ')}`,
      `When: ${formatDate(interview)} (${interview.timezone})`,
      `Duration: ${interview.duration_minutes} minutes`,
      interview.location && `Location: ${interview.location}`,
      interview.meeting_link && `Meeting link: ${interview.meeting_link}`,
      `Interviewer: ${interview.interviewer_name}`,
    ].filter(Boolean).join('\n')
    try { await navigator.clipboard.writeText(invitation); toast.success('Interview invitation copied') }
    catch { toast.error('Could not copy invitation') }
  }

  return (
    <div className="page-container">
      <Link to="/dashboard/interviews" className="inline-flex items-center gap-2 text-dark-400 hover:text-white mb-6"><HiArrowLeft className="w-4 h-4" /> Back to Interviews</Link>
      <div className="glass-card p-5 sm:p-7">
        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-5">
          <div><div className="flex flex-wrap items-center gap-3"><h1 className="text-2xl font-bold">{interview.candidate_name}</h1><span className="rounded-full bg-primary-500/10 px-3 py-1 text-xs capitalize text-primary-300">{interview.status}</span></div>
            <p className="text-dark-300 mt-3">{interview.interview_type.replace('_', ' ')} · {interview.duration_minutes} minutes</p>
            <p className="text-sm text-dark-400 mt-1">{formatDate(interview)} · {interview.timezone}</p>
            <p className="text-sm text-dark-400 mt-1">Job: {interview.job_title || 'General screening'} · Interviewer: {interview.interviewer_name}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link to={`/dashboard/candidates/${interview.candidate_id}`} className="glass-button-secondary py-2 px-4 text-sm">Candidate profile</Link>
            <button onClick={copyInvite} className="glass-button-secondary py-2 px-4 text-sm inline-flex items-center gap-2"><HiOutlineClipboardDocument className="w-4 h-4" /> Copy invitation</button>
            {active && canManage && <button onClick={() => setEditing((value) => !value)} className="glass-button-secondary py-2 px-4 text-sm">{editing ? 'Close editor' : 'Reschedule / Edit'}</button>}
            {active && canManage && <button onClick={() => { if (window.confirm('Cancel this interview?')) cancel.mutate(interview.id) }} className="rounded-xl border border-rose-500/30 px-4 py-2 text-sm text-rose-300 hover:bg-rose-500/10">Cancel interview</button>}
            {active && (canManage || interview.interviewer_user_id === user?.id) && <button onClick={() => { if (window.confirm('Mark this interview as completed?')) complete.mutate(interview.id) }} className="glass-button py-2 px-4 text-sm">Mark complete</button>}
          </div>
        </div>
        {(interview.location || interview.meeting_link) && <div className="mt-5 rounded-xl bg-dark-900/70 p-4 border border-dark-700/50 flex flex-wrap items-center gap-3">{interview.location && <span className="text-sm text-dark-300">Location: {interview.location}</span>}{interview.meeting_link && <a href={interview.meeting_link} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 text-primary-300 hover:text-primary-200"><HiOutlineVideoCamera className="w-4 h-4" /> Join meeting</a>}</div>}
        {interview.notes && <div className="mt-5"><h2 className="font-semibold">Interview notes</h2><p className="text-sm text-dark-300 whitespace-pre-wrap mt-2">{interview.notes}</p></div>}
      </div>

      {editing && <div className="glass-card p-5 sm:p-6 mt-5"><h2 className="font-semibold mb-4">Edit or reschedule</h2><InterviewForm interview={interview} candidateId={interview.candidate_id} candidateJobId={interview.job_id} onCancel={() => setEditing(false)} saving={update.isPending} onSubmit={(data) => update.mutate({ id: interview.id, data }, { onSuccess: () => setEditing(false) })} /></div>}

      {interview.status === 'completed' && canGiveFeedback && <FeedbackForm key={`${interview.id}-${interview.feedback?.updated_at || 'new'}`} interview={interview} saving={saveFeedback.isPending} onSave={(data) => saveFeedback.mutate({ id: interview.id, data })} />}
      {interview.feedback && <section className="glass-card p-5 sm:p-6 mt-5"><div className="flex flex-wrap items-start justify-between gap-3"><div><h2 className="text-lg font-semibold">Interview feedback</h2><p className="text-sm text-dark-400 mt-1">Submitted by {interview.feedback.submitted_by_name || 'Recruiter'}</p></div><span className="rounded-full bg-emerald-500/10 px-3 py-1.5 text-sm text-emerald-300">{interview.feedback.recommendation.replace('_', ' ').replace(/^./, (c) => c.toUpperCase())}</span></div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-5">{[['Relevant skills', 'skills_rating'], ['Communication', 'communication_rating'], ['Problem solving', 'problem_solving_rating'], ['Overall', 'overall_rating']].map(([label, key]) => <div key={key} className="rounded-xl bg-dark-900/70 border border-dark-700/50 p-3"><p className="text-xs text-dark-400">{label}</p><p className="text-xl font-semibold mt-1">{interview.feedback[key]}<span className="text-xs text-dark-500"> / 5</span></p></div>)}</div>
        {interview.feedback.notes && <p className="text-sm text-dark-300 whitespace-pre-wrap mt-4">{interview.feedback.notes}</p>}
      </section>}
      {interview.status === 'completed' && !canGiveFeedback && !interview.feedback && <p className="text-sm text-dark-400 mt-5">Feedback is available to the assigned interviewer.</p>}
    </div>
  )
}
