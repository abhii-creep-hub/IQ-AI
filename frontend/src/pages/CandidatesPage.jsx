import { useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useCandidates, useDeleteCandidate } from '../hooks/useQueries'
import { HiUsers, HiMagnifyingGlass, HiTrash, HiEye, HiFunnel } from 'react-icons/hi2'
import { formatDate, RANK_COLORS, getScoreColor } from '../utils/helpers'

export default function CandidatesPage() {
  const [search, setSearch] = useState('')
  const [rankFilter, setRankFilter] = useState('')
  const { data: candidates, isLoading } = useCandidates({ search: search || undefined })
  const deleteMutation = useDeleteCandidate()

  const filteredCandidates = candidates?.filter((c) => !rankFilter || c.rank === rankFilter) || []

  return (
    <div className="page-container">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center gap-3 mb-8">
          <HiUsers className="w-7 h-7 text-primary-400" />
          <h1 className="text-2xl font-bold">Candidates</h1>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-3 mb-6">
          <div className="relative flex-1">
            <HiMagnifyingGlass className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-400" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="glass-input pl-10"
              placeholder="Search candidates..."
            />
          </div>
          <div className="relative">
            <HiFunnel className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-400" />
            <select
              value={rankFilter}
              onChange={(e) => setRankFilter(e.target.value)}
              className="glass-input pl-9 pr-4 w-44"
            >
              <option value="">All Ranks</option>
              <option value="gold">Gold</option>
              <option value="silver">Silver</option>
              <option value="bronze">Bronze</option>
              <option value="shortlisted">Shortlisted</option>
              <option value="pending">Pending</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>
        </div>

        {/* Table */}
        {isLoading ? (
          <div className="flex justify-center py-20">
            <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : filteredCandidates.length > 0 ? (
          <div className="glass-card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-dark-700/50">
                    <th className="text-left text-xs font-semibold text-dark-400 uppercase tracking-wider p-4">Candidate</th>
                    <th className="text-left text-xs font-semibold text-dark-400 uppercase tracking-wider p-4">Rank</th>
                    <th className="text-left text-xs font-semibold text-dark-400 uppercase tracking-wider p-4">Status</th>
                    <th className="text-left text-xs font-semibold text-dark-400 uppercase tracking-wider p-4">Recommendation</th>
                    <th className="text-left text-xs font-semibold text-dark-400 uppercase tracking-wider p-4">Experience</th>
                    <th className="text-left text-xs font-semibold text-dark-400 uppercase tracking-wider p-4">Uploaded</th>
                    <th className="text-right text-xs font-semibold text-dark-400 uppercase tracking-wider p-4">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredCandidates.map((c) => (
                    <tr key={c.id} className="border-b border-dark-700/30 hover:bg-dark-800/50 transition-colors">
                      <td className="p-4">
                        <div className="flex items-center gap-3">
                          <div className="w-9 h-9 rounded-full bg-primary-500/20 flex items-center justify-center text-sm font-semibold text-primary-400">
                            {c.name?.[0] || '?'}
                          </div>
                          <div>
                            <p className="font-medium text-sm">{c.name}</p>
                            <p className="text-xs text-dark-400">{c.email || 'No email'}</p>
                          </div>
                        </div>
                      </td>
                      <td className="p-4">
                        <span className={`px-3 py-1 rounded-full text-xs font-medium capitalize rank-${c.rank}`}>
                          {c.rank}
                        </span>
                      </td>
                      <td className="p-4">
                        <span className={`text-xs px-2 py-1 rounded-full ${c.status === 'analyzed' ? 'bg-emerald-500/20 text-emerald-400' : c.status === 'error' ? 'bg-rose-500/20 text-rose-400' : 'bg-dark-600 text-dark-400'}`}>
                          {c.status}
                        </span>
                      </td>
                      <td className="p-4 text-sm text-dark-400 capitalize">{c.hiring_recommendation || '-'}</td>
                      <td className="p-4 text-sm text-dark-400">{c.total_experience_years || 0}y</td>
                      <td className="p-4 text-xs text-dark-500">{formatDate(c.created_at)}</td>
                      <td className="p-4">
                        <div className="flex items-center justify-end gap-2">
                          <Link
                            to={`/dashboard/candidates/${c.id}`}
                            className="p-2 rounded-lg hover:bg-dark-700/50 text-dark-400 hover:text-primary-400 transition-colors"
                          >
                            <HiEye className="w-4 h-4" />
                          </Link>
                          <button
                            onClick={() => {
                              if (confirm('Delete this candidate?')) deleteMutation.mutate(c.id)
                            }}
                            className="p-2 rounded-lg hover:bg-dark-700/50 text-dark-400 hover:text-rose-400 transition-colors"
                          >
                            <HiTrash className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="text-center py-20 glass-card">
            <HiUsers className="w-12 h-12 text-dark-500 mx-auto mb-3" />
            <p className="text-dark-400">No candidates found</p>
            <Link to="/dashboard/upload" className="glass-button mt-4 text-sm inline-block">Upload resumes</Link>
          </div>
        )}
      </motion.div>
    </div>
  )
}
