import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { dashboardAPI, candidatesAPI, jobsAPI, reportsAPI } from '../services/api'
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
