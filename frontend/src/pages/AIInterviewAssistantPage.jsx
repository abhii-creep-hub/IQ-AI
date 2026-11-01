import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { HiOutlineChatBubbleLeftRight, HiOutlineClipboardDocumentCheck, HiOutlineSparkles } from 'react-icons/hi2'
import { useAIInterviewCandidates, useAIInterviewJobs, useAIInterviewSessions, useCreateAIInterviewSession } from '../hooks/useQueries'

const interviewTypes = [
  ['technical', 'Technical'], ['behavioral', 'Behavioral'], ['hr', 'HR'],
  ['situational', 'Situational'], ['project_based', 'Project-based'], ['mixed', 'Mixed interview'],
]
const interviewModes = [
  ['written', 'Written Interview', 'Type answers and review evidence-based feedback.'],
  ['voice', 'Voice Interview', 'Record a short answer, review the transcript, then evaluate it.'],
  ['live_ai', 'Live AI Interview', 'Hear questions, answer by voice, and continue with contextual spoken follow-ups.'],
]

function formatDate(value) {
  if (!value) return 'Date unavailable'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? 'Date unavailable' : date.toLocaleString()
}

export default function AIInterviewAssistantPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [candidateId, setCandidateId] = useState(searchParams.get('candidate') || '')
  const [jobId, setJobId] = useState('')
  const [interviewType, setInterviewType] = useState('mixed')
  const [mode, setMode] = useState('written')
  const [difficulty, setDifficulty] = useState('intermediate')
  const [countChoice, setCountChoice] = useState('5')
  const [customCount, setCustomCount] = useState(8)
  const [duration, setDuration] = useState('')
  const candidatesQuery = useAIInterviewCandidates()
  const jobsQuery = useAIInterviewJobs()
  const candidateOptions = candidatesQuery.data || []
  const candidate = candidateOptions.find((item) => item.id === candidateId)
  const selectedJobId = jobId || candidate?.job_id || ''
  const job = jobsQuery.data?.find((item) => item.id === selectedJobId)
  const historyParams = useMemo(() => candidateId ? { candidate_id: candidateId } : {}, [candidateId])
  const historyQuery = useAIInterviewSessions(historyParams)
  const createSession = useCreateAIInterviewSession()
  const jobOptions = jobsQuery.data || []

  useEffect(() => {
    if (candidate?.id === candidateId) setJobId(candidate.job_id || '')
  }, [candidate?.id, candidate?.job_id, candidateId])

  const questionCount = countChoice === 'custom' ? Number(customCount) : Number(countChoice)
  const create = (event) => {
    event.preventDefault()
    createSession.mutate({
      candidate_id: candidateId,
      job_id: selectedJobId || null,
      interview_type: interviewType,
      mode,
      difficulty,
      question_count: questionCount,
      duration_minutes: duration ? Number(duration) : null,
    }, { onSuccess: (session) => navigate(`/dashboard/ai-interview/${session.id}`) })
  }

  const skills = candidate?.skills || []
  const atsScore = candidate?.ats_score

  return (
    <div className="page-container space-y-6">
      <header>
        <p className="text-primary-400 text-sm font-medium">Structured candidate assessment</p>
        <h1 className="text-2xl sm:text-3xl font-bold mt-1">AI Interview Assistant</h1>
        <p className="text-dark-400 mt-2 max-w-3xl">Create a job-specific question set, record answers as you interview, and review evidence-based AI feedback. Recruiters make the final decision.</p>
      </header>

      <div className="grid xl:grid-cols-[minmax(0,1.2fr)_minmax(300px,0.8fr)] gap-6 items-start">
        <section className="glass-card p-5 sm:p-6">
          <div className="flex items-center gap-3 mb-5"><span className="rounded-xl bg-primary-500/15 p-2.5 text-primary-300"><HiOutlineSparkles className="w-5 h-5" /></span><div><h2 className="text-lg font-semibold">Configure interview</h2><p className="text-sm text-dark-400">Candidate and job data load from your account.</p></div></div>
          {candidatesQuery.isLoading || jobsQuery.isLoading ? <p className="text-dark-400 py-6">Loading candidates and jobs…</p> : candidatesQuery.isError ? <div role="alert" className="text-rose-300">Could not load candidates. <button className="underline" onClick={() => candidatesQuery.refetch()}>Try again</button></div> : candidateOptions.length === 0 ? <div className="rounded-xl bg-dark-900 p-5 text-center"><p className="text-dark-300">Upload or add a candidate before starting an AI interview.</p><Link to="/dashboard/upload" className="glass-button inline-block mt-4">Upload resume</Link></div> : (
            <form onSubmit={create} className="space-y-4">
              <label className="block text-sm text-dark-300">Candidate
                <select required value={candidateId} onChange={(event) => { setCandidateId(event.target.value); setJobId('') }} className="glass-input mt-1.5">
                  <option value="">Select a candidate</option>
                  {candidateOptions.map((item) => <option key={item.id} value={item.id}>{item.name}{item.email ? ` — ${item.email}` : ''}</option>)}
                </select>
              </label>
              <label className="block text-sm text-dark-300">Job position
                <select value={selectedJobId} onChange={(event) => setJobId(event.target.value)} className="glass-input mt-1.5" disabled={!candidateId || Boolean(candidate?.job_id)}>
                  <option value="">General / no job selected</option>
                  {jobOptions.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}
                </select>
                {candidate?.job_id && <span className="text-xs text-dark-500 mt-1 block">This candidate is already associated with a job, so the interview uses that posting.</span>}
              </label>
              <fieldset className="space-y-2">
                <legend className="text-sm text-dark-300 mb-2">Interview mode</legend>
                <div className="grid md:grid-cols-3 gap-3">
                  {interviewModes.map(([value, label, description]) => <label key={value} className={`cursor-pointer rounded-xl border p-3 transition-colors ${mode === value ? 'border-primary-400 bg-primary-500/10' : 'border-dark-700 bg-dark-900/50 hover:border-dark-500'}`}>
                    <span className="flex items-center gap-2 font-medium text-dark-100"><input type="radio" name="interview-mode" value={value} checked={mode === value} onChange={() => setMode(value)} className="accent-primary-500" />{label}</span>
                    <span className="block text-xs text-dark-400 mt-2">{description}</span>
                  </label>)}
                </div>
                {mode !== 'written' && <p className="text-xs text-amber-300">Voice modes need a microphone, browser speech playback, and the configured Gemini API key for transcription. Audio is sent to Gemini for transcription and is not saved by IQ-AI; only the reviewed transcript is saved.</p>}
              </fieldset>
              <div className="grid sm:grid-cols-2 gap-4">
                <label className="text-sm text-dark-300">Interview type
                  <select value={interviewType} onChange={(event) => setInterviewType(event.target.value)} className="glass-input mt-1.5">{interviewTypes.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select>
                </label>
                <label className="text-sm text-dark-300">Difficulty
                  <select value={difficulty} onChange={(event) => setDifficulty(event.target.value)} className="glass-input mt-1.5"><option value="easy">Easy</option><option value="intermediate">Intermediate</option><option value="advanced">Advanced</option></select>
                </label>
                <label className="text-sm text-dark-300">Number of questions
                  <select value={countChoice} onChange={(event) => setCountChoice(event.target.value)} className="glass-input mt-1.5"><option value="5">5 questions</option><option value="10">10 questions</option><option value="15">15 questions</option><option value="custom">Custom (5–20)</option></select>
                </label>
                {countChoice === 'custom' && <label className="text-sm text-dark-300">Custom count<input type="number" min="5" max="20" required value={customCount} onChange={(event) => setCustomCount(event.target.value)} className="glass-input mt-1.5" /></label>}
                <label className="text-sm text-dark-300">Target duration <span className="text-dark-500">(optional)</span>
                  <select value={duration} onChange={(event) => setDuration(event.target.value)} className="glass-input mt-1.5"><option value="">No target</option><option value="30">30 minutes</option><option value="45">45 minutes</option><option value="60">60 minutes</option><option value="90">90 minutes</option><option value="120">120 minutes</option></select>
                </label>
              </div>
              <button type="submit" disabled={!candidateId || !candidate || createSession.isPending || (countChoice === 'custom' && (questionCount < 5 || questionCount > 20))} className="glass-button w-full sm:w-auto inline-flex items-center justify-center gap-2"><HiOutlineChatBubbleLeftRight className="w-5 h-5" />{createSession.isPending ? 'Creating session…' : 'Create interview session'}</button>
              {createSession.isError && <p role="alert" className="text-sm text-rose-300">{createSession.error?.response?.data?.detail || 'Could not create interview session.'}</p>}
            </form>
          )}
        </section>

        <aside className="space-y-6">
          {candidate && <section className="glass-card p-5">
            <div className="flex items-start justify-between gap-3"><div><p className="text-xs uppercase tracking-wide text-dark-500">Selected candidate</p><h2 className="font-semibold text-lg mt-1">{candidate.name}</h2>{candidate.email && <p className="text-xs text-dark-400 mt-1">{candidate.email}</p>}</div>{atsScore != null && <span className="rounded-xl bg-primary-500/10 px-3 py-2 text-sm text-primary-300">ATS {Number(atsScore).toFixed(0)}</span>}</div>
            {candidate.summary && <p className="text-sm text-dark-300 mt-4">{candidate.summary}</p>}
            <div className="flex flex-wrap gap-2 mt-4">{skills.slice(0, 12).map((skill) => <span key={skill} className="rounded-full bg-dark-700/80 px-2.5 py-1 text-xs text-dark-300">{skill}</span>)}</div>
            {candidate.experience_years != null && <p className="text-sm text-dark-400 mt-3">Experience: {candidate.experience_years} years</p>}
          </section>}
          {selectedJobId && <section className="glass-card p-5"><p className="text-xs uppercase tracking-wide text-dark-500">Selected job requirements</p>{jobsQuery.isLoading ? <p className="text-sm text-dark-400 mt-3">Loading job details…</p> : jobsQuery.isError ? <p role="alert" className="text-sm text-amber-300 mt-3">Job details could not be loaded.</p> : job ? <><h2 className="font-semibold mt-1">{job.title}</h2><p className="text-sm text-dark-300 mt-3 line-clamp-5">{job.description}</p>{job.requirements && <p className="text-xs text-dark-400 mt-3">Requirements: {job.requirements}</p>}{job.responsibilities && <p className="text-xs text-dark-400 mt-2">Responsibilities: {job.responsibilities}</p>}<div className="flex flex-wrap gap-2 mt-3">{[...(job.required_skills || []), ...(job.preferred_skills || [])].slice(0, 12).map((skill) => <span key={skill} className="rounded-full bg-primary-500/10 px-2.5 py-1 text-xs text-primary-300">{skill}</span>)}</div>{job.experience_min != null && <p className="text-xs text-dark-400 mt-3">Experience: {job.experience_min}–{job.experience_max ?? '…'} years</p>}</> : <p className="text-sm text-dark-400 mt-2">General screening; questions will use candidate evidence only.</p>}</section>}
        </aside>
      </div>

      <section className="glass-card p-5 sm:p-6">
        <div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-lg font-semibold">Interview history</h2><p className="text-sm text-dark-400 mt-1">Saved sessions can be resumed after leaving this page.</p></div><HiOutlineClipboardDocumentCheck className="w-6 h-6 text-primary-300" /></div>
        {historyQuery.isLoading ? <p className="text-sm text-dark-400 mt-4">Loading saved sessions…</p> : historyQuery.isError ? <p role="alert" className="text-sm text-amber-300 mt-4">Could not load interview history. <button onClick={() => historyQuery.refetch()} className="underline">Retry</button></p> : historyQuery.data?.length ? <div className="mt-4 divide-y divide-dark-700/50">{historyQuery.data.map((session) => <div key={session.id} className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2"><div><p className="font-medium">{session.candidate_name} <span className="text-dark-500 font-normal">· {session.job_title || 'General screening'}</span></p><p className="text-xs text-dark-400 mt-1 capitalize">{session.interview_type.replace('_', ' ')} · {session.difficulty} · {session.question_count} questions · {session.status} · {formatDate(session.created_at)}</p></div><Link to={`/dashboard/ai-interview/${session.id}`} className="text-sm text-primary-300 hover:text-primary-200">{session.status === 'completed' ? 'Open report' : 'Resume session'}</Link></div>)}</div> : <p className="text-sm text-dark-400 mt-4">No AI interview sessions yet.</p>}
      </section>
      <p className="text-xs text-dark-500">AI-generated questions and evaluations are job-related assistance. Review the answers and evidence yourself; the assistant does not make hiring decisions.</p>
    </div>
  )
}
