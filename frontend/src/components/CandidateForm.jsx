import { useState } from 'react'
import { useCreateCandidate, useJobs } from '../hooks/useQueries'

export default function CandidateForm({ onClose }) {
  const [form, setForm] = useState({ name: '', email: '', phone: '', location: '', total_experience_years: '', job_id: '' })
  const { data: jobs = [], isLoading: jobsLoading } = useJobs({ limit: 100 })
  const createCandidate = useCreateCandidate()

  const update = (event) => setForm((current) => ({ ...current, [event.target.name]: event.target.value }))

  const submit = async (event) => {
    event.preventDefault()
    const payload = {
      ...form,
      total_experience_years: form.total_experience_years === '' ? null : Number(form.total_experience_years),
      job_id: form.job_id || null,
    }
    delete payload.job_id
    if (form.job_id) payload.job_id = form.job_id
    try {
      await createCandidate.mutateAsync(payload)
      onClose()
    } catch {
      // The shared mutation displays the API error.
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section role="dialog" aria-modal="true" aria-labelledby="candidate-form-title" className="glass-card w-full max-w-lg p-6">
        <div className="mb-5 flex items-center justify-between">
          <h2 id="candidate-form-title" className="text-xl font-semibold">Add candidate</h2>
          <button type="button" onClick={onClose} className="text-dark-300 hover:text-white" aria-label="Close">✕</button>
        </div>
        <form onSubmit={submit} className="space-y-4">
          <label className="block text-sm text-dark-200">Full name<input required name="name" value={form.name} onChange={update} className="glass-input mt-1" /></label>
          <label className="block text-sm text-dark-200">Email<input type="email" name="email" value={form.email} onChange={update} className="glass-input mt-1" /></label>
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block text-sm text-dark-200">Phone<input name="phone" value={form.phone} onChange={update} className="glass-input mt-1" /></label>
            <label className="block text-sm text-dark-200">Location<input name="location" value={form.location} onChange={update} className="glass-input mt-1" /></label>
          </div>
          <label className="block text-sm text-dark-200">Experience (years)<input type="number" min="0" step="0.1" name="total_experience_years" value={form.total_experience_years} onChange={update} className="glass-input mt-1" /></label>
          <label className="block text-sm text-dark-200">Job posting<select name="job_id" value={form.job_id} onChange={update} disabled={jobsLoading} className="glass-input mt-1"><option value="">Unassigned / General Screening</option>{jobs.map((job) => <option key={job.id} value={job.id}>{job.title}</option>)}</select></label>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="glass-button" disabled={createCandidate.isPending}>Cancel</button>
            <button type="submit" className="primary-button" disabled={createCandidate.isPending}>{createCandidate.isPending ? 'Saving…' : 'Add candidate'}</button>
          </div>
        </form>
      </section>
    </div>
  )
}
