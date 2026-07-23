import { useState } from 'react'
import { motion } from 'framer-motion'
import { useRankingReport, useJobs } from '../hooks/useQueries'
import { HiDocumentChartBar, HiArrowDownTray } from 'react-icons/hi2'
import { RANK_COLORS, formatDate } from '../utils/helpers'

export default function ReportsPage() {
  const [selectedJob, setSelectedJob] = useState('')
  const { data: rankingData, isLoading } = useRankingReport(selectedJob || null)
  const { data: jobs } = useJobs()

  const handleExport = (format) => {
    const data = rankingData?.candidates || []
    if (data.length === 0) return

    if (format === 'csv') {
      const headers = ['Name', 'Email', 'Rank', 'ATS Score', 'Status', 'Recommendation']
      const rows = data.map((c) => [c.name, c.email || '', c.rank, c.ats_score || 0, c.status, c.hiring_recommendation || ''])
      const csv = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n')
      const blob = new Blob([csv], { type: 'text/csv' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `iq-ai-report-${new Date().toISOString().slice(0, 10)}.csv`
      a.click()
    }
  }

  return (
    <div className="page-container">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <HiDocumentChartBar className="w-7 h-7 text-primary-400" />
            <h1 className="text-2xl font-bold">Reports</h1>
          </div>
          <button
            onClick={() => handleExport('csv')}
            className="glass-button-secondary flex items-center gap-2 text-sm"
          >
            <HiArrowDownTray className="w-4 h-4" /> Export CSV
          </button>
        </div>

        {/* Filter */}
        <div className="glass-card p-4 mb-6">
          <label className="text-sm text-dark-300 mr-3">Filter by Job:</label>
          <select
            value={selectedJob}
            onChange={(e) => setSelectedJob(e.target.value)}
            className="glass-input w-64 inline-block"
          >
            <option value="">All Jobs</option>
            {jobs?.map((job) => (
              <option key={job.id} value={job.id}>{job.title}</option>
            ))}
          </select>
        </div>

        {/* Summary Cards */}
        {rankingData?.summary && (
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3 mb-6">
            {[
              { label: 'Total', value: rankingData.summary.total, color: 'text-white' },
              { label: 'Gold', value: rankingData.summary.gold, color: 'text-yellow-400' },
              { label: 'Silver', value: rankingData.summary.silver, color: 'text-gray-300' },
              { label: 'Bronze', value: rankingData.summary.bronze, color: 'text-orange-400' },
              { label: 'Shortlisted', value: rankingData.summary.shortlisted, color: 'text-emerald-400' },
              { label: 'Pending', value: rankingData.summary.pending, color: 'text-blue-400' },
              { label: 'Rejected', value: rankingData.summary.rejected, color: 'text-rose-400' },
            ].map((item) => (
              <div key={item.label} className="glass-card p-3 text-center">
                <p className={`text-2xl font-bold ${item.color}`}>{item.value}</p>
                <p className="text-xs text-dark-500">{item.label}</p>
              </div>
            ))}
          </div>
        )}

        {/* Ranking Table */}
        {isLoading ? (
          <div className="flex justify-center py-20">
            <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : rankingData?.candidates?.length > 0 ? (
          <div className="glass-card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-dark-700/50">
                    <th className="text-left text-xs font-semibold text-dark-400 uppercase tracking-wider p-4">#</th>
                    <th className="text-left text-xs font-semibold text-dark-400 uppercase tracking-wider p-4">Candidate</th>
                    <th className="text-left text-xs font-semibold text-dark-400 uppercase tracking-wider p-4">Rank</th>
                    <th className="text-left text-xs font-semibold text-dark-400 uppercase tracking-wider p-4">ATS Score</th>
                    <th className="text-left text-xs font-semibold text-dark-400 uppercase tracking-wider p-4">Status</th>
                    <th className="text-left text-xs font-semibold text-dark-400 uppercase tracking-wider p-4">Recommendation</th>
                  </tr>
                </thead>
                <tbody>
                  {rankingData.candidates.map((c, i) => (
                    <tr key={c.id} className="border-b border-dark-700/30 hover:bg-dark-800/50 transition-colors">
                      <td className="p-4 text-sm text-dark-500">{i + 1}</td>
                      <td className="p-4">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-primary-500/20 flex items-center justify-center text-sm font-semibold text-primary-400">
                            {c.name?.[0] || '?'}
                          </div>
                          <div>
                            <p className="font-medium text-sm">{c.name}</p>
                            <p className="text-xs text-dark-400">{c.email || 'N/A'}</p>
                          </div>
                        </div>
                      </td>
                      <td className="p-4">
                        <span className={`px-3 py-1 rounded-full text-xs font-medium capitalize rank-${c.rank}`}>
                          {c.rank}
                        </span>
                      </td>
                      <td className="p-4">
                        <span className="text-sm font-semibold">{c.ats_score?.toFixed(1) || 'N/A'}</span>
                      </td>
                      <td className="p-4 text-xs text-dark-400 capitalize">{c.status}</td>
                      <td className="p-4 text-xs text-dark-400 capitalize">{c.hiring_recommendation?.replace('_', ' ') || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="text-center py-20 glass-card">
            <HiDocumentChartBar className="w-12 h-12 text-dark-500 mx-auto mb-3" />
            <p className="text-dark-400">No ranking data available</p>
          </div>
        )}
      </motion.div>
    </div>
  )
}
