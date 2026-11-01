import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { dashboardAPI, candidatesAPI, jobsAPI, reportsAPI, pipelineAPI, interviewsAPI, aiInterviewsAPI } from '../services/api'
import toast from 'react-hot-toast'

export function useDashboardStats() {
  return useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const response = await dashboardAPI.getStats()
      return response.data
    },
  })
}

export function useSkillAnalytics() {
  return useQuery({
    queryKey: ['skill-analytics'],
    queryFn: async () => {
      const response = await dashboardAPI.getSkillAnalytics()
      return response.data
    },
  })
}

export function useCandidates(params) {
  return useQuery({
    queryKey: ['candidates', params],
    queryFn: async () => {
      const response = await candidatesAPI.list(params)
      return response.data
    },
  })
}

export function useCandidate(id) {
  return useQuery({
    queryKey: ['candidate', id],
    queryFn: async () => {
      const response = await candidatesAPI.get(id)
      return response.data
    },
    enabled: !!id,
  })
}

export function useCreateCandidate() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data) => {
      const response = await candidatesAPI.create(data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidates'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] })
      toast.success('Candidate added successfully')
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to add candidate')
    },
  })
}

export function useJobs(params) {
  return useQuery({
    queryKey: ['jobs', params],
    queryFn: async () => {
      const response = await jobsAPI.list(params)
      return response.data
    },
  })
}

export function useJob(id) {
  return useQuery({
    queryKey: ['job', id],
    queryFn: async () => {
      const response = await jobsAPI.get(id)
      return response.data
    },
    enabled: !!id,
  })
}

export function useUploadResume() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (formData) => {
      const response = await candidatesAPI.upload(formData)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidates'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] })
      toast.success('Resume uploaded successfully')
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Upload failed')
    },
  })
}

export function useUploadMultipleResumes() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (formData) => {
      const response = await candidatesAPI.uploadMultiple(formData)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidates'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] })
      toast.success('Resumes uploaded successfully')
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Upload failed')
    },
  })
}

export function useParseResume() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (candidateId) => {
      const response = await candidatesAPI.parse(candidateId)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidates'] })
      toast.success('Resume parsed successfully')
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Parsing failed')
    },
  })
}

export function useAnalyzeCandidate() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ candidateId, jobId }) => {
      const response = await candidatesAPI.analyze(candidateId, jobId)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidates'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] })
      toast.success('Analysis completed')
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Analysis failed')
    },
  })
}

export function useParseAndAnalyze() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ candidateId, jobId }) => {
      const response = await candidatesAPI.parseAndAnalyze(candidateId, jobId)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidates'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] })
      toast.success('Resume processed and analyzed')
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Processing failed')
    },
  })
}

export function useCreateJob() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data) => {
      const response = await jobsAPI.create(data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] })
      toast.success('Job created successfully')
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to create job')
    },
  })
}

export function useDeleteJob() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id) => {
      await jobsAPI.delete(id)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
      toast.success('Job deleted')
    },
  })
}

export function useDeleteCandidate() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id) => {
      await candidatesAPI.delete(id)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidates'] })
      toast.success('Candidate deleted')
    },
  })
}

export function useFullReport(candidateId) {
  return useQuery({
    queryKey: ['full-report', candidateId],
    queryFn: async () => {
      const response = await reportsAPI.getFullReport(candidateId)
      return response.data
    },
    enabled: !!candidateId,
  })
}

export function useRankingReport(jobId) {
  return useQuery({
    queryKey: ['ranking-report', jobId],
    queryFn: async () => {
      const response = await reportsAPI.getRanking(jobId)
      return response.data
    },
  })
}

export function useCandidateComparison(candidateIds) {
  const sortedIds = [...candidateIds].sort()
  return useQuery({
    queryKey: ['candidate-comparison', sortedIds],
    queryFn: async () => {
      const response = await reportsAPI.compareCandidates(sortedIds)
      return response.data
    },
    enabled: sortedIds.length >= 2 && sortedIds.length <= 3,
  })
}

export function usePipeline(params) {
  return useQuery({
    queryKey: ['pipeline', params],
    queryFn: async () => (await pipelineAPI.list(params)).data,
  })
}

export function useMovePipelineCandidate() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ candidateId, stage }) => (await pipelineAPI.updateStage(candidateId, stage)).data,
    onMutate: async ({ candidateId, stage }) => {
      await queryClient.cancelQueries({ queryKey: ['pipeline'] })
      const snapshots = queryClient.getQueriesData({ queryKey: ['pipeline'] })
      snapshots.forEach(([key, value]) => {
        if (!value?.candidates) return
        const candidate = value.candidates.find((item) => item.id === candidateId)
        if (!candidate) return
        const oldStage = candidate.recruitment_stage
        const params = key[1] || {}
        const moved = { ...candidate, recruitment_stage: stage }
        const filteredOut = (params.stage && params.stage !== stage)
          || (params.job_id && params.job_id !== candidate.job_id)
          || (params.unassigned && candidate.job_id)
        const candidates = filteredOut
          ? value.candidates.filter((item) => item.id !== candidateId)
          : value.candidates.map((item) => item.id === candidateId ? moved : item)
        const stage_counts = { ...value.stage_counts }
        if (oldStage !== stage) {
          stage_counts[oldStage] = Math.max(0, (stage_counts[oldStage] || 0) - 1)
          if (!filteredOut) stage_counts[stage] = (stage_counts[stage] || 0) + 1
        }
        queryClient.setQueryData(key, { ...value, candidates, stage_counts })
      })
      return { snapshots }
    },
    onError: (error, _variables, context) => {
      context?.snapshots?.forEach(([key, value]) => queryClient.setQueryData(key, value))
      toast.error(error.response?.data?.detail || 'Could not update candidate stage')
    },
    onSuccess: () => toast.success('Candidate moved to the new stage'),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['pipeline'] })
      queryClient.invalidateQueries({ queryKey: ['candidate'] })
    },
  })
}

export function useCandidateStageHistory(id) {
  return useQuery({
    queryKey: ['candidate-stage-history', id],
    queryFn: async () => (await pipelineAPI.history(id)).data,
    enabled: !!id,
  })
}

export function useInterviews(params) {
  return useQuery({
    queryKey: ['interviews', params],
    queryFn: async () => (await interviewsAPI.list(params)).data,
  })
}

export function useInterview(id) {
  return useQuery({
    queryKey: ['interview', id],
    queryFn: async () => (await interviewsAPI.get(id)).data,
    enabled: !!id,
  })
}

export function useCreateInterview() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data) => (await interviewsAPI.create(data)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interviews'] })
      toast.success('Interview scheduled')
    },
    onError: (error) => toast.error(error.response?.data?.detail || 'Could not schedule interview'),
  })
}

export function useUpdateInterview() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, data }) => (await interviewsAPI.update(id, data)).data,
    onSuccess: (data) => {
      queryClient.setQueryData(['interview', data.id], data)
      queryClient.invalidateQueries({ queryKey: ['interviews'] })
      toast.success('Interview updated')
    },
    onError: (error) => toast.error(error.response?.data?.detail || 'Could not update interview'),
  })
}

export function useInterviewStatusAction(action) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id) => (await interviewsAPI[action](id)).data,
    onSuccess: (data) => {
      queryClient.setQueryData(['interview', data.id], data)
      queryClient.invalidateQueries({ queryKey: ['interviews'] })
      toast.success(action === 'complete' ? 'Interview marked complete' : 'Interview cancelled')
    },
    onError: (error) => toast.error(error.response?.data?.detail || 'Could not update interview status'),
  })
}

export function useSaveInterviewFeedback() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, data }) => (await interviewsAPI.saveFeedback(id, data)).data,
    onSuccess: (data) => {
      queryClient.setQueryData(['interview', data.id], data)
      queryClient.invalidateQueries({ queryKey: ['interviews'] })
      toast.success('Interview feedback saved')
    },
    onError: (error) => toast.error(error.response?.data?.detail || 'Could not save interview feedback'),
  })
}

function useAssistantMutation(mutationFn, successText) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn,
    onSuccess: (data) => {
      if (data?.id && data?.questions) queryClient.setQueryData(['ai-interview-session', data.id], data)
      queryClient.invalidateQueries({ queryKey: ['ai-interview-sessions'] })
      if (data?.id) queryClient.invalidateQueries({ queryKey: ['ai-interview-session', data.id] })
      if (successText) toast.success(successText)
    },
    onError: (error) => toast.error(error.response?.data?.detail || 'AI Interview Assistant request failed'),
  })
}

export function useAIInterviewSessions(params) {
  return useQuery({
    queryKey: ['ai-interview-sessions', params],
    queryFn: async () => (await aiInterviewsAPI.list(params)).data,
  })
}

export function useAIInterviewCandidates(params = { skip: 0, limit: 100 }) {
  return useQuery({
    queryKey: ['ai-interview-candidates', params],
    queryFn: async () => (await aiInterviewsAPI.candidates(params)).data,
  })
}

export function useAIInterviewJobs(params = { skip: 0, limit: 100 }) {
  return useQuery({
    queryKey: ['ai-interview-jobs', params],
    queryFn: async () => (await aiInterviewsAPI.jobs(params)).data,
  })
}

export function useAIInterviewSession(id) {
  return useQuery({
    queryKey: ['ai-interview-session', id],
    queryFn: async () => (await aiInterviewsAPI.get(id)).data,
    enabled: !!id,
  })
}

export function useCreateAIInterviewSession() {
  return useAssistantMutation(async (data) => (await aiInterviewsAPI.create(data)).data, 'Interview session created')
}

export function useGenerateAIInterviewQuestions() {
  return useAssistantMutation(async (id) => (await aiInterviewsAPI.generate(id)).data, 'Job-specific questions generated')
}

export function useAIInterviewSessionAction(action, successText) {
  return useAssistantMutation(async (id) => (await aiInterviewsAPI[action](id)).data, successText)
}

export function useCompleteAIInterviewSession() {
  return useAIInterviewSessionAction('complete', 'Interview completed; report ready')
}

export function useSaveAIInterviewAnswer() {
  return useAssistantMutation(async ({ sessionId, questionId, data }) => (await aiInterviewsAPI.saveAnswer(sessionId, questionId, data)).data, 'Answer saved')
}

export function useTranscribeAIInterviewAnswer() {
  return useMutation({
    mutationFn: async ({ sessionId, questionId, audio, durationSeconds }) =>
      (await aiInterviewsAPI.transcribeAnswer(sessionId, questionId, audio, durationSeconds)).data,
    onError: (error) => toast.error(error.response?.data?.detail || 'Could not transcribe the recording. Retry or enter the answer manually.'),
  })
}

export function useEvaluateAIInterviewAnswer() {
  return useAssistantMutation(async ({ sessionId, questionId }) => (await aiInterviewsAPI.evaluateAnswer(sessionId, questionId)).data, 'Answer evaluation saved')
}

export function useGenerateAIInterviewFollowUp() {
  return useAssistantMutation(async ({ sessionId, questionId }) => (await aiInterviewsAPI.followUp(sessionId, questionId)).data, 'Follow-up question generated')
}

export function useAppendLiveAIInterviewFollowUp() {
  return useAssistantMutation(async ({ sessionId, questionId }) => (await aiInterviewsAPI.appendLiveFollowUp(sessionId, questionId)).data, 'Live follow-up added to the interview')
}

export function useUpdateAIInterviewReview() {
  return useAssistantMutation(async ({ sessionId, data }) => (await aiInterviewsAPI.review(sessionId, data)).data, 'Recruiter review saved')
}
