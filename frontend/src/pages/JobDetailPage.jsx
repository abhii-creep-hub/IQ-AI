import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useJob } from '../hooks/useQueries'
import { HiBriefcase, HiArrowLeft } from 'react-icons/hi2'

export default function JobDetailPage() {
  const { id } = useParams()
  const { data: job, isLoading } = useJob(id)

  if (isLoading) {
    return (
      <div className="page-container flex justify-center py-20">
        <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!job) {
    return (
      <div className="page-container text-center py-20">
        <p className="text-dark-400">Job not found</p>
        <Link to="/dashboard/jobs" className="glass-button mt-4 text-sm inline-block">Back to Jobs</Link>
      </div>
    )
  }

  return (
    <div className="page-container">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <Link to="/dashboard/jobs" className="inline-flex items-center gap-2 text-dark-400 hover:text-white mb-6 transition-colors">
          <HiArrowLeft className="w-4 h-4" /> Back to Jobs
        </Link>

        <div className="glass-card p-8">
          <div className="flex items-start gap-4 mb-6">
            <div className="w-12 h-12 rounded-xl bg-primary-500/10 flex items-center justify-center">
              <HiBriefcase className="w-6 h-6 text-primary-400" />
            </div>
            <div className="flex-1">
              <h1 className="text-2xl font-bold mb-1">{job.title}</h1>
              <div className="flex flex-wrap gap-3 text-sm text-dark-400">
                {job.location && <span>📍 {job.location}</span>}
                {job.job_type && <span>💼 {job.job_type}</span>}
                {job.experience_min && <span>📊 {job.experience_min}-{job.experience_max || '+'} years</span>}
                <span className={`px-2 py-0.5 rounded-full text-xs ${job.status === 'active' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-dark-600'}`}>{job.status}</span>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div>
              <h3 className="text-sm font-semibold text-dark-300 mb-2">Description</h3>
              <p className="text-dark-400 leading-relaxed whitespace-pre-line">{job.description}</p>
            </div>

            {job.requirements && (
              <div>
                <h3 className="text-sm font-semibold text-dark-300 mb-2">Requirements</h3>
                <p className="text-dark-400 leading-relaxed whitespace-pre-line">{job.requirements}</p>
              </div>
            )}

            {job.responsibilities && (
              <div>
                <h3 className="text-sm font-semibold text-dark-300 mb-2">Responsibilities</h3>
                <p className="text-dark-400 leading-relaxed whitespace-pre-line">{job.responsibilities}</p>
              </div>
            )}

            {job.required_skills?.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-dark-300 mb-2">Required Skills</h3>
                <div className="flex flex-wrap gap-2">
                  {job.required_skills.map((s) => (
                    <span key={s} className="px-3 py-1.5 text-sm rounded-lg bg-primary-500/10 text-primary-400 border border-primary-500/20">{s}</span>
                  ))}
                </div>
              </div>
            )}

            {job.preferred_skills?.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-dark-300 mb-2">Preferred Skills</h3>
                <div className="flex flex-wrap gap-2">
                  {job.preferred_skills.map((s) => (
                    <span key={s} className="px-3 py-1.5 text-sm rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">{s}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </motion.div>
    </div>
  )
}
