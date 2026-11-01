import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { HiArrowLeft, HiOutlineArrowPath, HiOutlineCheckCircle, HiOutlinePause, HiOutlinePlay, HiOutlineSparkles } from 'react-icons/hi2'
import { useAIInterviewSession, useAIInterviewSessionAction, useAppendLiveAIInterviewFollowUp, useCompleteAIInterviewSession, useEvaluateAIInterviewAnswer, useGenerateAIInterviewFollowUp, useGenerateAIInterviewQuestions, useSaveAIInterviewAnswer, useTranscribeAIInterviewAnswer, useUpdateAIInterviewReview } from '../hooks/useQueries'

const MAX_AUDIO_BYTES = 10 * 1024 * 1024
const MAX_RECORDING_SECONDS = 120

function percent(value) {
  return value == null ? 'N/A' : `${Math.round(Number(value))}/100`
}

export default function AIInterviewSessionPage() {
  const { id } = useParams()
  const query = useAIInterviewSession(id)
  const generate = useGenerateAIInterviewQuestions()
  const start = useAIInterviewSessionAction('start', 'Interview started')
  const pause = useAIInterviewSessionAction('pause', 'Interview paused')
  const saveAnswer = useSaveAIInterviewAnswer()
  const evaluate = useEvaluateAIInterviewAnswer()
  const followUp = useGenerateAIInterviewFollowUp()
  const appendLiveFollowUp = useAppendLiveAIInterviewFollowUp()
  const transcribe = useTranscribeAIInterviewAnswer()
  const complete = useCompleteAIInterviewSession()
  const saveReview = useUpdateAIInterviewReview()
  const session = query.data
  const [activeIndex, setActiveIndex] = useState(0)
  const [draftAnswer, setDraftAnswer] = useState('')
  const [reviewNotes, setReviewNotes] = useState('')
  const [finalDecision, setFinalDecision] = useState('')
  const [audioConsent, setAudioConsent] = useState(false)
  const [recording, setRecording] = useState(false)
  const [recordingSeconds, setRecordingSeconds] = useState(0)
  const [audioBlob, setAudioBlob] = useState(null)
  const [audioUrl, setAudioUrl] = useState('')
  const [transcriptConfirmed, setTranscriptConfirmed] = useState(false)
  const [recordingError, setRecordingError] = useState('')
  const [speechNotice, setSpeechNotice] = useState('')
  const recorderRef = useRef(null)
  const streamRef = useRef(null)
  const chunksRef = useRef([])
  const timerRef = useRef(null)
  const recordStartRef = useRef(0)
  const questions = session?.questions || []
  const question = questions[activeIndex]
  const isDirty = Boolean(question) && draftAnswer !== (question.answer || '')
  const completedCount = useMemo(() => questions.filter((item) => ['answered', 'skipped', 'unevaluable'].includes(item.status)).length, [questions])
  const evaluatedCount = useMemo(() => questions.filter((item) => item.score != null).length, [questions])

  useEffect(() => {
    if (question) setDraftAnswer(question.answer || '')
    setAudioBlob(null)
    setTranscriptConfirmed(false)
    setRecordingError('')
    setRecordingSeconds(0)
    setAudioUrl((previous) => {
      if (previous) URL.revokeObjectURL(previous)
      return ''
    })
    setAudioConsent(false)
  }, [question?.id])

  useEffect(() => {
    if (!recording) return undefined
    const interval = window.setInterval(() => {
      setRecordingSeconds(Math.min(MAX_RECORDING_SECONDS, Math.floor((Date.now() - recordStartRef.current) / 1000)))
    }, 250)
    return () => window.clearInterval(interval)
  }, [recording])

  useEffect(() => () => {
    window.clearTimeout(timerRef.current)
    if (recorderRef.current?.state === 'recording') recorderRef.current.stop()
    streamRef.current?.getTracks().forEach((track) => track.stop())
    window.speechSynthesis?.cancel()
    if (audioUrl) URL.revokeObjectURL(audioUrl)
  }, [audioUrl])

  useEffect(() => {
    if (session) {
      setReviewNotes(session.recruiter_notes || '')
      setFinalDecision(session.final_decision || '')
    }
  }, [session?.id, session?.recruiter_notes, session?.final_decision])

  if (query.isLoading) return <div className="page-container text-center text-dark-400 py-20">Loading saved interview…</div>
  if (query.isError || !session) return <div className="page-container"><div className="glass-card p-8 text-center" role="alert"><p className="text-rose-300">Interview session could not be loaded.</p><Link to="/dashboard/ai-interview" className="glass-button-secondary inline-block mt-4">Back to AI Interview Assistant</Link></div></div>

  const questionPending = recording || generate.isPending || saveAnswer.isPending || evaluate.isPending || followUp.isPending || appendLiveFollowUp.isPending || transcribe.isPending || complete.isPending
  const stopRecording = () => {
    window.clearTimeout(timerRef.current)
    if (recorderRef.current?.state === 'recording') recorderRef.current.stop()
  }
  const startRecording = async () => {
    setRecordingError('')
    setSpeechNotice('')
    if (!audioConsent) {
      setRecordingError('Confirm the candidate has agreed to audio transcription before recording.')
      return
    }
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
      setRecordingError('This browser cannot record audio. Try a recent Chrome, Edge, Firefox, or Safari browser, or enter the answer manually.')
      return
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream
      const supportedType = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg;codecs=opus']
        .find((type) => MediaRecorder.isTypeSupported?.(type))
      const recorder = new MediaRecorder(stream, supportedType ? { mimeType: supportedType } : undefined)
      recorderRef.current = recorder
      chunksRef.current = []
      recordStartRef.current = Date.now()
      setRecordingSeconds(0)
      setAudioBlob(null)
      setTranscriptConfirmed(false)
      setAudioUrl((previous) => {
        if (previous) URL.revokeObjectURL(previous)
        return ''
      })
      recorder.ondataavailable = (event) => { if (event.data?.size) chunksRef.current.push(event.data) }
      recorder.onerror = () => setRecordingError('The browser could not record this answer. Retry or type it manually.')
      recorder.onstop = () => {
        const duration = Math.min(MAX_RECORDING_SECONDS, Math.max(1, Math.ceil((Date.now() - recordStartRef.current) / 1000)))
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || 'audio/webm' })
        stream.getTracks().forEach((track) => track.stop())
        streamRef.current = null
        setRecording(false)
        setRecordingSeconds(duration)
        if (!blob.size) {
          setRecordingError('No audio was captured. Check the microphone and try again.')
        } else if (blob.size > MAX_AUDIO_BYTES) {
          setRecordingError('This recording is over the 10 MB upload limit. Record a shorter answer.')
        } else {
          setAudioBlob(blob)
          setAudioUrl(URL.createObjectURL(blob))
        }
      }
      recorder.start(500)
      setRecording(true)
      timerRef.current = window.setTimeout(() => recorder.stop(), MAX_RECORDING_SECONDS * 1000)
    } catch (error) {
      const message = error?.name === 'NotAllowedError' || error?.name === 'PermissionDeniedError'
        ? 'Microphone access was denied. Allow microphone permission in the browser, or type the answer instead.'
        : error?.name === 'NotFoundError'
          ? 'No microphone was found. Connect a microphone or type the answer instead.'
          : 'The microphone could not be started. Check browser permissions and try again.'
      setRecordingError(message)
      streamRef.current?.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }
  }
  const transcribeRecording = async () => {
    if (!audioBlob || !question) return
    try {
      const result = await transcribe.mutateAsync({
        sessionId: session.id,
        questionId: question.id,
        audio: audioBlob,
        durationSeconds: recordingSeconds,
      })
      setDraftAnswer(result.transcript || '')
      setTranscriptConfirmed(false)
      setRecordingError('')
    } catch (error) {
      setRecordingError(error.response?.data?.detail || 'Transcription failed. Retry or enter the answer manually.')
    }
  }
  const speakQuestion = () => {
    if (!('speechSynthesis' in window) || typeof SpeechSynthesisUtterance === 'undefined') {
      setSpeechNotice('Text-to-speech is not available in this browser. Read the question displayed on screen.')
      return
    }
    window.speechSynthesis.cancel()
    const utterance = new SpeechSynthesisUtterance(question?.question || '')
    utterance.lang = 'en-US'
    utterance.onerror = () => setSpeechNotice('Speech playback failed. Use the question text on screen.')
    window.speechSynthesis.speak(utterance)
    setSpeechNotice('Reading the question aloud using your browser’s built-in speech voice.')
  }
  const saveAndEvaluateTranscript = async () => {
    if (!question || !draftAnswer.trim() || !transcriptConfirmed) return
    try {
      await saveAnswer.mutateAsync({ sessionId: session.id, questionId: question.id, data: { answer: draftAnswer, skip: false } })
      await evaluate.mutateAsync({ sessionId: session.id, questionId: question.id })
    } catch { /* mutations display actionable API errors */ }
  }
  const askLiveFollowUp = async () => {
    if (!question) return
    try {
      const updated = await appendLiveFollowUp.mutateAsync({ sessionId: session.id, questionId: question.id })
      const nextIndex = updated.questions.findIndex((item) => item.parent_question_id === question.id)
      if (nextIndex >= 0) setActiveIndex(nextIndex)
    } catch { /* mutation displays actionable API errors */ }
  }
  const updateAnswer = async (index = activeIndex) => {
    const selected = questions[index]
    if (!selected) return true
    const answer = index === activeIndex ? draftAnswer : (selected.answer || '')
    if (!answer.trim()) return false
    try {
      await saveAnswer.mutateAsync({ sessionId: session.id, questionId: selected.id, data: { answer, skip: false } })
      return true
    } catch {
      return false
    }
  }
  const goTo = async (index) => {
    if (index < 0 || index >= questions.length || index === activeIndex) return
    if (isDirty && !(await updateAnswer())) return
    setActiveIndex(index)
  }
  const skipQuestion = async () => {
    if (!question) return
    if (isDirty && draftAnswer.trim() && !window.confirm('Discard the unsaved answer and mark this question skipped?')) return
    try {
      await saveAnswer.mutateAsync({ sessionId: session.id, questionId: question.id, data: { answer: null, skip: true } })
      if (activeIndex < questions.length - 1) setActiveIndex(activeIndex + 1)
    } catch { /* mutation shows the API error */ }
  }
  const finish = () => {
    if (!window.confirm('Complete this interview and create the final report? You will no longer be able to edit its answers.')) return
    complete.mutate(session.id)
  }
  const updateRecruiterReview = (event) => {
    event.preventDefault()
    saveReview.mutate({
      sessionId: session.id,
      data: { recruiter_notes: reviewNotes, ...(finalDecision ? { final_decision: finalDecision } : {}) },
    })
  }
  const report = session.overall_report

  return (
    <div className="page-container space-y-6">
      <Link to="/dashboard/ai-interview" className="inline-flex items-center gap-2 text-dark-400 hover:text-white"><HiArrowLeft className="w-4 h-4" /> Back to Assistant</Link>
      <header className="glass-card p-5 sm:p-6 flex flex-col lg:flex-row lg:items-start lg:justify-between gap-5">
        <div><div className="flex flex-wrap items-center gap-3"><h1 className="text-2xl font-bold">{session.candidate_name}</h1><span className="rounded-full bg-primary-500/10 px-3 py-1 text-xs capitalize text-primary-300">{session.status.replace('_', ' ')}</span></div>
          <p className="text-dark-300 mt-2">{session.job_title || 'General screening'} · {session.interview_type.replace('_', ' ')} · {session.difficulty} · {session.question_count} questions · {session.mode === 'live_ai' ? 'Live AI' : session.mode === 'voice' ? 'Voice' : 'Written'} mode</p>
          <p className="text-sm text-dark-400 mt-1">{session.candidate_email || 'No email on file'}{session.candidate_experience_years != null ? ` · ${session.candidate_experience_years} years experience` : ''}{session.ats_score != null ? ` · ATS ${Number(session.ats_score).toFixed(0)}` : ''}</p>
          {session.candidate_summary && <p className="text-sm text-dark-300 mt-3 max-w-3xl">{session.candidate_summary}</p>}
          {session.candidate_skills?.length > 0 && <div className="flex flex-wrap gap-2 mt-3">{session.candidate_skills.slice(0, 12).map((skill) => <span key={skill} className="rounded-full bg-dark-700 px-2.5 py-1 text-xs text-dark-300">{skill}</span>)}</div>}
        </div>
        <div className="flex flex-wrap gap-2 shrink-0">
          {session.status === 'draft' && !questions.length && <button onClick={() => generate.mutate(session.id)} disabled={generate.isPending} className="glass-button inline-flex items-center gap-2"><HiOutlineSparkles className="w-5 h-5" />{generate.isPending ? 'Generating…' : 'Generate questions'}</button>}
          {session.status === 'draft' && questions.length > 0 && <button onClick={() => { if (session.mode === 'live_ai') speakQuestion(); start.mutate(session.id) }} disabled={start.isPending} className="glass-button inline-flex items-center gap-2"><HiOutlinePlay className="w-4 h-4" />Start interview</button>}
          {session.status === 'paused' && <button onClick={() => start.mutate(session.id)} disabled={start.isPending} className="glass-button inline-flex items-center gap-2"><HiOutlinePlay className="w-4 h-4" />Resume interview</button>}
          {session.status === 'in_progress' && <button onClick={() => pause.mutate(session.id)} disabled={pause.isPending || recording} className="glass-button-secondary inline-flex items-center gap-2"><HiOutlinePause className="w-4 h-4" />Pause</button>}
          {['in_progress', 'paused'].includes(session.status) && <button onClick={finish} disabled={complete.isPending || recording} className="glass-button-secondary inline-flex items-center gap-2"><HiOutlineCheckCircle className="w-4 h-4" />{complete.isPending ? 'Completing…' : 'Complete interview'}</button>}
          <button onClick={() => query.refetch()} className="glass-button-secondary p-3" aria-label="Refresh interview session"><HiOutlineArrowPath className="w-4 h-4" /></button>
        </div>
      </header>

      {session.status === 'draft' && questions.length === 0 && <section className="glass-card p-7 text-center"><HiOutlineSparkles className="w-9 h-9 text-primary-300 mx-auto" /><h2 className="font-semibold mt-3">Ready to build the question set</h2><p className="text-sm text-dark-400 mt-1">Questions will use the selected job and the candidate’s recorded skills and experience.</p>{generate.isError && <p role="alert" className="text-sm text-rose-300 mt-3">{generate.error?.response?.data?.detail || 'Question generation failed.'}</p>}</section>}

      {questions.length > 0 && <>
        <section className="glass-card p-4 sm:p-5">
          <div className="flex flex-wrap justify-between gap-2 text-sm"><span className="font-medium">Progress · {completedCount} of {questions.length} answered or skipped</span><span className="text-dark-400">{evaluatedCount} evaluated</span></div>
          <div className="h-2 rounded-full bg-dark-700 mt-3 overflow-hidden"><div className="h-full bg-gradient-to-r from-primary-600 to-cyan-400 transition-all" style={{ width: `${questions.length ? completedCount / questions.length * 100 : 0}%` }} /></div>
          <div className="flex gap-2 overflow-x-auto mt-4 pb-1">{questions.map((item, index) => <button key={item.id} onClick={() => goTo(index)} aria-label={`Question ${index + 1}, ${item.status}`} aria-current={index === activeIndex ? 'step' : undefined} className={`shrink-0 w-9 h-9 rounded-lg border text-xs ${index === activeIndex ? 'border-primary-400 bg-primary-500/20 text-white' : item.status === 'answered' ? 'border-emerald-500/40 text-emerald-300' : item.status === 'skipped' ? 'border-dark-600 text-dark-500' : item.status === 'unevaluable' ? 'border-amber-500/40 text-amber-300' : 'border-dark-700 text-dark-300'}`}>{index + 1}</button>)}</div>
        </section>

        {question && <div className="grid xl:grid-cols-[minmax(0,1fr)_minmax(300px,0.72fr)] gap-6 items-start">
          <section className="glass-card p-5 sm:p-7">
            <div className="flex flex-wrap items-center gap-2 text-xs mb-4"><span className="rounded-full bg-primary-500/10 text-primary-300 px-2.5 py-1">Question {activeIndex + 1} of {questions.length}</span><span className="rounded-full bg-dark-700 px-2.5 py-1 capitalize text-dark-300">{question.category.replaceAll('_', ' ')}</span><span className="rounded-full bg-dark-700 px-2.5 py-1 capitalize text-dark-300">{question.difficulty}</span><span className="text-dark-500">Evaluates: {question.competency}</span></div>
            <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3"><h2 className="text-xl font-semibold leading-relaxed">{question.question}</h2>{session.mode === 'live_ai' && <button onClick={speakQuestion} className="glass-button-secondary shrink-0">Read question aloud</button>}</div>
            {session.mode === 'live_ai' && <p className="text-xs text-dark-500 mt-2">Turn-based voice conversation: browser speech playback, then reviewed transcript and AI follow-up. This is not a low-latency streaming call.</p>}
            {speechNotice && <p role="status" className="text-xs text-cyan-300 mt-2">{speechNotice}</p>}
            <p className="text-sm text-dark-400 mt-3">Job relevance: {question.job_relevance}</p>
            <div className="rounded-xl bg-dark-900/70 border border-dark-700/50 p-4 mt-5"><p className="text-xs uppercase tracking-wide text-dark-500">Expected concepts</p><ul className="mt-2 space-y-1.5 text-sm text-dark-300 list-disc pl-5">{question.expected_concepts.map((concept) => <li key={concept}>{concept}</li>)}</ul></div>
            {session.mode !== 'written' && ['in_progress', 'paused'].includes(session.status) && <section className="rounded-xl border border-primary-500/20 bg-primary-500/5 p-4 mt-5 space-y-3">
              <h3 className="font-semibold">{session.mode === 'live_ai' ? 'Live spoken answer' : 'Voice answer'}</h3>
              <label className="flex items-start gap-2 text-xs text-dark-300"><input type="checkbox" checked={audioConsent} onChange={(event) => setAudioConsent(event.target.checked)} className="mt-0.5 accent-primary-500" /><span>The candidate agrees to record this answer and send it to the configured Gemini service for transcription. IQ-AI discards the uploaded audio after transcription; the confirmed transcript is saved with this interview.</span></label>
              <div className="flex flex-wrap items-center gap-2"><button type="button" onClick={recording ? stopRecording : startRecording} disabled={!audioConsent || transcribe.isPending} className={recording ? 'glass-button-secondary border-rose-500/40 text-rose-300' : 'glass-button'}>{recording ? `Stop recording (${recordingSeconds}s)` : 'Record answer'}</button>{recording && <span role="status" className="text-xs text-rose-300">Recording · {recordingSeconds}s / {MAX_RECORDING_SECONDS}s</span>}{audioBlob && <button type="button" onClick={transcribeRecording} disabled={transcribe.isPending} className="glass-button-secondary">{transcribe.isPending ? 'Transcribing…' : 'Transcribe recording'}</button>}</div>
              {audioUrl && <audio controls src={audioUrl} className="w-full" aria-label="Play back recorded answer" />}
              {recordingError && <p role="alert" className="text-sm text-rose-300">{recordingError}</p>}
              {transcribe.isError && !recordingError && <p role="alert" className="text-sm text-rose-300">{transcribe.error?.response?.data?.detail || 'Transcription failed. Retry or type the answer.'}</p>}
              <p className="text-xs text-dark-500">Maximum recording: 2 minutes and 10 MB. Microphone recording requires browser permission and a supported browser; transcript correction or typed answers remain available.</p>
            </section>}
            <label className="block mt-5 text-sm font-medium text-dark-300">{session.mode === 'written' ? 'Candidate answer' : 'Transcript / confirmed answer'}
              <textarea value={draftAnswer} onChange={(event) => { setDraftAnswer(event.target.value); if (session.mode !== 'written') setTranscriptConfirmed(false) }} maxLength={20000} rows={9} disabled={!['in_progress', 'paused'].includes(session.status)} placeholder={session.mode === 'written' ? "Capture the candidate's answer and relevant evidence…" : 'Review and correct the transcript here, or type the candidate’s answer…'} className="glass-input mt-2 resize-y" />
              <span className="text-xs text-dark-500 mt-1 block text-right">{draftAnswer.length.toLocaleString()} / 20,000</span>
            </label>
            {session.mode !== 'written' && ['in_progress', 'paused'].includes(session.status) && <label className="flex items-start gap-2 mt-3 text-sm text-dark-300"><input type="checkbox" checked={transcriptConfirmed} onChange={(event) => setTranscriptConfirmed(event.target.checked)} disabled={!draftAnswer.trim()} className="mt-1 accent-primary-500" /><span>I reviewed and confirmed this transcript. Only the transcript content will be evaluated; accent, pitch, and unrelated speech traits are not assessed.</span></label>}
            {session.status === 'in_progress' || session.status === 'paused' ? <div className="flex flex-wrap gap-2 mt-4">
              <button onClick={() => saveAnswer.mutate({ sessionId: session.id, questionId: question.id, data: { answer: draftAnswer, skip: false } })} disabled={!draftAnswer.trim() || questionPending || (session.mode !== 'written' && !transcriptConfirmed)} className="glass-button">{saveAnswer.isPending ? 'Saving…' : 'Save answer'}</button>
              {session.mode === 'written' ? <button onClick={() => evaluate.mutate({ sessionId: session.id, questionId: question.id })} disabled={question.status !== 'answered' || !question.answer || questionPending || Boolean(question.evaluation)} className="glass-button-secondary">{evaluate.isPending ? 'Evaluating…' : question.evaluation ? 'Evaluated' : 'Evaluate answer'}</button> : <button onClick={saveAndEvaluateTranscript} disabled={!draftAnswer.trim() || !transcriptConfirmed || questionPending || (Boolean(question.evaluation) && !isDirty)} className="glass-button-secondary">{saveAnswer.isPending || evaluate.isPending ? 'Saving and evaluating…' : question.evaluation && !isDirty ? 'Evaluated' : 'Save and evaluate confirmed transcript'}</button>}
              {session.mode === 'live_ai' && <button onClick={askLiveFollowUp} disabled={!question.answer || !question.evaluation || questionPending} className="glass-button-secondary">{appendLiveFollowUp.isPending ? 'Generating follow-up…' : 'Ask contextual follow-up'}</button>}
              <button onClick={skipQuestion} disabled={questionPending} className="glass-button-secondary">Skip question</button>
              {session.mode !== 'live_ai' && <button onClick={() => followUp.mutate({ sessionId: session.id, questionId: question.id })} disabled={!question.answer || questionPending} className="glass-button-secondary">Generate follow-up</button>}
            </div> : null}
            {(question.follow_up_question || question.evaluation?.suggested_follow_up) && <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/5 p-4 mt-4"><p className="text-xs uppercase tracking-wide text-cyan-300">Suggested follow-up</p><p className="text-sm text-dark-200 mt-1">{question.evaluation?.suggested_follow_up || question.follow_up_question}</p></div>}
            <div className="flex justify-between mt-6 pt-4 border-t border-dark-700/50"><button onClick={() => goTo(activeIndex - 1)} disabled={activeIndex === 0 || questionPending} className="glass-button-secondary">Previous</button><button onClick={() => goTo(activeIndex + 1)} disabled={activeIndex >= questions.length - 1 || questionPending} className="glass-button-secondary">Next</button></div>
          </section>

          <aside className="space-y-5">
            <section className="glass-card p-5"><h2 className="font-semibold">Evaluation rubric</h2><p className="text-xs text-dark-500 mt-1">Scores are assistive evidence, not a hiring decision.</p><div className="mt-4 space-y-3">{Object.entries(question.evaluation_rubric || {}).map(([key, value]) => <div key={key}><p className="text-xs text-primary-300 capitalize">{key.replaceAll('_', ' ')}</p><p className="text-sm text-dark-300 mt-1">{value}</p></div>)}</div></section>
            {question.evaluation && <section className="glass-card p-5">
              <div className="flex justify-between items-start gap-3"><div><h2 className="font-semibold">AI answer evaluation</h2><p className="text-xs text-dark-500 mt-1">Review the evidence before using it.</p></div><span className="text-xl font-bold text-primary-300">{percent(question.evaluation.score)}</span></div>
              {question.evaluation.uncertain ? <div className="rounded-lg bg-amber-500/10 border border-amber-500/20 p-3 mt-4"><p className="text-sm font-medium text-amber-300">Not enough evidence for a reliable score</p><p className="text-sm text-dark-300 mt-1">{question.evaluation.uncertainty_reason}</p></div> : <p className="text-sm text-dark-300 mt-3">Answer quality: <span className="capitalize text-white">{question.evaluation.answer_quality}</span> · Confidence: <span className="capitalize">{question.evaluation.confidence}</span></p>}
              <p className="text-sm text-dark-300 mt-3">{question.evaluation.explanation}</p>
              {!question.evaluation.uncertain && <div className="grid grid-cols-2 gap-2 mt-4">{[['Accuracy', question.evaluation.technical_accuracy], ['Relevance', question.evaluation.relevance], ['Depth', question.evaluation.depth_of_explanation], ['Practical use', question.evaluation.practical_application]].map(([label, value]) => <div key={label} className="rounded-lg bg-dark-900/70 p-3"><p className="text-xs text-dark-500">{label}</p><p className="font-semibold mt-1">{value}/100</p></div>)}</div>}
              {question.evaluation.strengths?.length > 0 && <div className="mt-4"><p className="text-xs text-emerald-300 uppercase">Strengths</p><ul className="list-disc pl-5 mt-2 text-sm text-dark-300 space-y-1">{question.evaluation.strengths.map((item) => <li key={item}>{item}</li>)}</ul></div>}
              {question.evaluation.missing_concepts?.length > 0 && <div className="mt-4"><p className="text-xs text-amber-300 uppercase">Missing concepts or gaps</p><ul className="list-disc pl-5 mt-2 text-sm text-dark-300 space-y-1">{question.evaluation.missing_concepts.map((item) => <li key={item}>{item}</li>)}</ul></div>}
              {question.evaluation.improvements?.length > 0 && <div className="mt-4"><p className="text-xs text-primary-300 uppercase">Suggestions</p><ul className="list-disc pl-5 mt-2 text-sm text-dark-300 space-y-1">{question.evaluation.improvements.map((item) => <li key={item}>{item}</li>)}</ul></div>}
            </section>}
          </aside>
        </div>}
      </>}

      {session.status === 'completed' && report && <section className="space-y-5">
        <div className="glass-card p-5 sm:p-7"><div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4"><div><p className="text-primary-300 text-sm font-medium">Final interview report</p><h2 className="text-2xl font-bold mt-1">{session.candidate_name} · {session.job_title || 'General screening'}</h2><p className="text-sm text-dark-400 mt-2">{new Date(report.interview_date).toLocaleString()} · {report.answered_questions} answered · {report.skipped_questions} skipped · {report.unevaluable_questions} unevaluable</p></div><div className="rounded-2xl bg-dark-900 border border-dark-700 p-4 min-w-44"><p className="text-xs text-dark-400">Overall score</p><p className="text-3xl font-bold mt-1">{report.overall_score == null ? 'N/A' : `${report.overall_score}/100`}</p><p className="text-xs text-dark-500 mt-1">Coverage {report.evaluation_coverage_percent}%</p></div></div><p className="text-sm text-dark-300 mt-5">{report.scoring_method}</p><div className="rounded-xl border border-primary-500/20 bg-primary-500/5 p-4 mt-4"><p className="text-sm font-semibold capitalize text-primary-200">{report.recruiter_recommendation.replaceAll('_', ' ')}</p><p className="text-sm text-dark-300 mt-1">{report.decision_notice}</p></div>
          <div className="grid md:grid-cols-2 xl:grid-cols-4 gap-3 mt-5">{Object.entries(report.category_performance || {}).map(([category, value]) => <div key={category} className="rounded-xl bg-dark-900/70 p-4"><p className="text-xs text-dark-400 capitalize">{category.replaceAll('_', ' ')}</p><p className="text-xl font-semibold mt-1">{value.score}/100</p><p className="text-xs text-dark-500">{value.evaluated_questions} evaluated</p></div>)}</div>
          <div className="grid md:grid-cols-2 gap-5 mt-6"><div><h3 className="font-semibold">Key strengths</h3>{report.key_strengths?.length ? <ul className="list-disc pl-5 mt-2 text-sm text-dark-300 space-y-1">{report.key_strengths.map((item) => <li key={item}>{item}</li>)}</ul> : <p className="text-sm text-dark-500 mt-2">No strengths were recorded in evaluated answers.</p>}</div><div><h3 className="font-semibold">Knowledge gaps</h3>{report.knowledge_gaps?.length ? <ul className="list-disc pl-5 mt-2 text-sm text-dark-300 space-y-1">{report.knowledge_gaps.map((item) => <li key={item}>{item}</li>)}</ul> : <p className="text-sm text-dark-500 mt-2">No gaps were recorded in evaluated answers.</p>}</div></div>
          {report.areas_requiring_verification?.length > 0 && <div className="mt-5"><h3 className="font-semibold">Areas requiring verification</h3><ul className="mt-2 space-y-2">{report.areas_requiring_verification.map((item, index) => <li key={`${item.question}-${index}`} className="rounded-lg bg-amber-500/5 border border-amber-500/15 p-3 text-sm text-dark-300"><span className="text-amber-300">{item.question}</span><br />{item.reason}</li>)}</ul></div>}
          {report.recommended_follow_up_questions?.length > 0 && <div className="mt-5"><h3 className="font-semibold">Recommended follow-up questions</h3><ul className="list-disc pl-5 mt-2 text-sm text-dark-300 space-y-1">{report.recommended_follow_up_questions.map((item) => <li key={item}>{item}</li>)}</ul></div>}
        </div>
        <form onSubmit={updateRecruiterReview} className="glass-card p-5 sm:p-6"><h2 className="text-lg font-semibold">Recruiter review</h2><p className="text-sm text-dark-400 mt-1">Your decision is stored separately from the AI recommendation.</p><label className="block text-sm text-dark-300 mt-4">Final recruiter decision<select value={finalDecision} onChange={(event) => setFinalDecision(event.target.value)} className="glass-input mt-1.5"><option value="">No decision recorded</option><option value="strong_evidence">Strong evidence of role readiness</option><option value="potential_fit">Potential fit; more assessment</option><option value="skill_gaps">Significant skill gaps to review</option><option value="insufficient_evidence">Insufficient evidence</option></select></label><label className="block text-sm text-dark-300 mt-4">Recruiter notes<textarea maxLength={10000} rows={4} value={reviewNotes} onChange={(event) => setReviewNotes(event.target.value)} className="glass-input mt-1.5 resize-y" placeholder="Your observations and next steps" /></label><button className="glass-button mt-4" disabled={saveReview.isPending}>{saveReview.isPending ? 'Saving…' : 'Save recruiter review'}</button></form>
      </section>}
      <p className="text-xs text-dark-500">AI-assisted assessment only. Numeric score is an unweighted mean of reliable question scores; skipped and unevaluable answers are excluded. Do not reject a candidate solely because of this score.</p>
    </div>
  )
}
