import { useMemo, useState } from 'react'
import { useJobs } from '../hooks/useQueries'
import { useAuth } from '../context/AuthContext'

function toLocalInput(value) {
  const date = value ? new Date(value) : new Date(Date.now() + 60 * 60 * 1000)
  if (Number.isNaN(date.getTime())) return ''
  const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60000)
  return localDate.toISOString().slice(0, 16)
}

export default function InterviewForm({ candidateId, candidateJobId, interview, onSubmit, onCancel, saving }) {
  const jobsQuery = useJobs({ limit: 100 })
  const { user } = useAuth()
  const jobs = Array.isArray(jobsQuery.data) ? jobsQuery.data : (jobsQuery.data?.jobs || [])
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC'
  const minDate = useMemo(() => toLocalInput(new Date()), [])
  const [form, setForm] = useState(() => ({
    job_id: interview?.job_id || candidateJobId || '',
    interviewer_name: interview?.interviewer_name || user?.full_name || user?.username || '',
    interview_type: interview?.interview_type || 'technical',
    scheduled_at: toLocalInput(interview?.scheduled_at),
    timezone: interview?.timezone || timezone,
    duration_minutes: interview?.duration_minutes || 60,
    location: interview?.location || '',
    meeting_link: interview?.meeting_link || '',
    notes: interview?.notes || '',
  }))
  const update = (event) => setForm((current) => ({ ...current, [event.target.name]: event.target.value }))
  const submit = (event) => {
    event.preventDefault()
    const data = {
      job_id: form.job_id || null,
      interviewer_name: form.interviewer_name.trim(),
      interview_type: form.interview_type,
      scheduled_at: new Date(form.scheduled_at).toISOString(),
      timezone: form.timezone.trim(),
      duration_minutes: Number(form.duration_minutes),
      location: form.location.trim() || null,
      meeting_link: form.meeting_link.trim() || null,
      notes: form.notes.trim() || null,
    }
    if (!interview) data.candidate_id = candidateId
    if (!interview && user?.id) data.interviewer_user_id = user.id
    onSubmit(data)
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="grid sm:grid-cols-2 gap-4">
        <label className="text-sm text-dark-300">Job posting
          <select name="job_id" value={form.job_id} onChange={update} className="glass-input mt-1.5">
            <option value="">No job linked</option>
            {jobs.map((job) => <option key={job.id} value={job.id}>{job.title}</option>)}
          </select>
        </label>
        <label className="text-sm text-dark-300">Interview type
          <select name="interview_type" value={form.interview_type} onChange={update} className="glass-input mt-1.5">
            <option value="technical">Technical</option><option value="behavioral">Behavioral</option>
            <option value="hr">HR</option><option value="hiring_manager">Hiring manager</option>
            <option value="phone_screen">Phone screen</option><option value="other">Other</option>
          </select>
        </label>
        <label className="text-sm text-dark-300">Interviewer name
          <input name="interviewer_name" required maxLength={255} value={form.interviewer_name} onChange={update} className="glass-input mt-1.5" placeholder="Interviewer" />
        </label>
        <label className="text-sm text-dark-300">Date and time
          <input name="scheduled_at" type="datetime-local" required min={minDate} value={form.scheduled_at} onChange={update} className="glass-input mt-1.5" />
        </label>
        <label className="text-sm text-dark-300">Timezone (IANA)
          <input name="timezone" required maxLength={100} value={form.timezone} onChange={update} className="glass-input mt-1.5" placeholder="Asia/Kolkata" />
        </label>
        <label className="text-sm text-dark-300">Duration
          <select name="duration_minutes" value={form.duration_minutes} onChange={update} className="glass-input mt-1.5">
            {[15, 30, 45, 60, 90, 120].map((duration) => <option key={duration} value={duration}>{duration} minutes</option>)}
          </select>
        </label>
        <label className="text-sm text-dark-300">Location
          <input name="location" maxLength={500} value={form.location} onChange={update} className="glass-input mt-1.5" placeholder="Office / phone" />
        </label>
        <label className="text-sm text-dark-300">Meeting link
          <input name="meeting_link" type="url" maxLength={1000} value={form.meeting_link} onChange={update} className="glass-input mt-1.5" placeholder="https://…" />
        </label>
      </div>
      <label className="block text-sm text-dark-300">Notes
        <textarea name="notes" maxLength={10000} rows={3} value={form.notes} onChange={update} className="glass-input mt-1.5 resize-y" placeholder="Topics or preparation notes" />
      </label>
      <div className="flex justify-end gap-3 pt-1">
        {onCancel && <button type="button" onClick={onCancel} className="glass-button-secondary">Cancel</button>}
        <button type="submit" disabled={saving} className="glass-button">{saving ? 'Saving…' : interview ? 'Save changes' : 'Schedule interview'}</button>
      </div>
    </form>
  )
}
