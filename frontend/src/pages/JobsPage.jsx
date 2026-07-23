import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { motion, AnimatePresence } from 'framer-motion'
import { useJobs, useCreateJob, useDeleteJob } from '../hooks/useQueries'
import { HiBriefcase, HiPlus, HiTrash, HiEye, HiXMark } from 'react-icons/hi2'
import { formatDate } from '../utils/helpers'

export default function JobsPage() {
  const [showCreate, setShowCreate] = useState(false)
  const { data: jobs, isLoading } = useJobs()
  const createMutation = useCreateJob()
  const deleteMutation = useDeleteJob()
  const { register, handleSubmit, reset, formState: { errors } } = useForm()

  const onSubmit = async (data) => {
    const skills = data.required_skills ? data.required_skills.split(',').map(s => s.trim()).filter(Boolean) : []
    const preferred = data.preferred_skills ? data.preferred_skills.split(',').map(s => s.trim()).filter(Boolean) : []
    await createMutation.mutateAsync({
      ...data,
      required_skills: skills,
      preferred_skills: preferred,
      experience_min: data.experience_min ? parseInt(data.experience_min) : null,
      experience_max: data.experience_max ? parseInt(data.experience_max) : null,
      salary_min: data.salary_min ? parseInt(data.salary_min) : null,
      salary_max: data.salary_max ? parseInt(data.salary_max) : null,
    })
    reset()
    setShowCreate(false)
  }

  return (
    <div className="page-container">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <HiBriefcase className="w-7 h-7 text-primary-400" />
            <h1 className="text-2xl font-bold">Job Descriptions</h1>
          </div>
          <button onClick={() => setShowCreate(true)} className="glass-button flex items-center gap-2 text-sm">
            <HiPlus className="w-4 h-4" /> Create Job
          </button>
        </div>

        {/* Jobs Grid */}
        {isLoading ? (
          <div className="flex justify-center py-20">
            <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : jobs?.length > 0 ? (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
            {jobs.map((job, i) => (
              <motion.div
                key={job.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: i * 0.05 }}
                className="glass-card-hover p-6 flex flex-col"
              >
                <div className="flex-1">
                  <div className="flex items-start justify-between mb-3">
                    <h3 className="font-semibold text-lg">{job.title}</h3>
                    <span className={`text-xs px-2.5 py-1 rounded-full ${job.status === 'active' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-dark-600 text-dark-400'}`}>
                      {job.status}
                    </span>
                  </div>
                  <div className="space-y-2 text-sm text-dark-400 mb-4">
                    {job.location && <p>📍 {job.location}</p>}
                    {job.job_type && <p>💼 {job.job_type}</p>}
                    {job.experience_min && (
                      <p>📊 {job.experience_min}{job.experience_max ? `-${job.experience_max}` : '+'} years</p>
                    )}
                  </div>
                  {job.required_skills?.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mb-4">
                      {job.required_skills.slice(0, 5).map((skill) => (
                        <span key={skill} className="text-xs px-2 py-1 rounded-lg bg-primary-500/10 text-primary-400 border border-primary-500/20">
                          {skill}
                        </span>
                      ))}
                      {job.required_skills.length > 5 && (
                        <span className="text-xs px-2 py-1 rounded-lg bg-dark-700 text-dark-400">
                          +{job.required_skills.length - 5}
                        </span>
                      )}
                    </div>
                  )}
                </div>
                <div className="flex items-center justify-between pt-3 border-t border-dark-700/50">
                  <span className="text-xs text-dark-500">{formatDate(job.created_at)}</span>
                  <div className="flex items-center gap-2">
                    <Link
                      to={`/dashboard/jobs/${job.id}`}
                      className="p-2 rounded-lg hover:bg-dark-700/50 text-dark-400 hover:text-primary-400 transition-colors"
                    >
                      <HiEye className="w-4 h-4" />
                    </Link>
                    <button
                      onClick={() => deleteMutation.mutate(job.id)}
                      className="p-2 rounded-lg hover:bg-dark-700/50 text-dark-400 hover:text-rose-400 transition-colors"
                    >
                      <HiTrash className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="text-center py-20 glass-card">
            <HiBriefcase className="w-12 h-12 text-dark-500 mx-auto mb-3" />
            <p className="text-dark-400">No jobs created yet</p>
            <button onClick={() => setShowCreate(true)} className="glass-button mt-4 text-sm">
              Create your first job
            </button>
          </div>
        )}

        {/* Create Job Modal */}
        <AnimatePresence>
          {showCreate && (
            <>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 bg-black/60 z-40"
                onClick={() => setShowCreate(false)}
              />
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="fixed inset-4 md:inset-auto md:top-1/2 md:left-1/2 md:-translate-x-1/2 md:-translate-y-1/2 md:w-[600px] md:max-h-[80vh] glass-card p-6 z-50 overflow-y-auto"
              >
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-bold">Create Job</h2>
                  <button onClick={() => setShowCreate(false)} className="p-2 hover:bg-dark-700 rounded-lg">
                    <HiXMark className="w-5 h-5" />
                  </button>
                </div>
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                  <div>
                    <label className="block text-sm text-dark-300 mb-1">Title *</label>
                    <input className="glass-input" placeholder="Senior Backend Engineer" {...register('title', { required: true })} />
                  </div>
                  <div>
                    <label className="block text-sm text-dark-300 mb-1">Description *</label>
                    <textarea className="glass-input h-24 resize-none" {...register('description', { required: true })} />
                  </div>
                  <div>
                    <label className="block text-sm text-dark-300 mb-1">Required Skills (comma separated)</label>
                    <input className="glass-input" placeholder="Python, FastAPI, PostgreSQL" {...register('required_skills')} />
                  </div>
                  <div>
                    <label className="block text-sm text-dark-300 mb-1">Preferred Skills</label>
                    <input className="glass-input" placeholder="Docker, Kubernetes, AWS" {...register('preferred_skills')} />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm text-dark-300 mb-1">Min Experience (yrs)</label>
                      <input type="number" className="glass-input" {...register('experience_min')} />
                    </div>
                    <div>
                      <label className="block text-sm text-dark-300 mb-1">Max Experience (yrs)</label>
                      <input type="number" className="glass-input" {...register('experience_max')} />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm text-dark-300 mb-1">Location</label>
                      <input className="glass-input" placeholder="Remote" {...register('location')} />
                    </div>
                    <div>
                      <label className="block text-sm text-dark-300 mb-1">Job Type</label>
                      <select className="glass-input" {...register('job_type')}>
                        <option value="full-time">Full-time</option>
                        <option value="part-time">Part-time</option>
                        <option value="contract">Contract</option>
                        <option value="internship">Internship</option>
                      </select>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm text-dark-300 mb-1">Education Level</label>
                    <input className="glass-input" placeholder="Bachelor's in CS" {...register('education_level')} />
                  </div>
                  <button type="submit" disabled={createMutation.isPending} className="glass-button w-full">
                    {createMutation.isPending ? 'Creating...' : 'Create Job'}
                  </button>
                </form>
              </motion.div>
            </>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  )
}
