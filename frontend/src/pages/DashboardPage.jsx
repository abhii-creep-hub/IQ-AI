import { motion } from 'framer-motion'
import { useDashboardStats, useSkillAnalytics } from '../hooks/useQueries'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, CartesianGrid } from 'recharts'
import { HiUsers, HiBriefcase, HiDocumentCheck, HiStar, HiArrowTrendingUp } from 'react-icons/hi2'
import { getScoreColor } from '../utils/helpers'

const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#f43f5e', '#8b5cf6', '#06b6d4']

export default function DashboardPage() {
  const { data: stats, isLoading } = useDashboardStats()
  const { data: skillData } = useSkillAnalytics()

  if (isLoading) {
    return (
      <div className="page-container flex items-center justify-center min-h-[60vh]">
        <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  const funnelData = stats?.hiring_funnel || []
  const skillsList = skillData?.skills || []

  const statCards = [
    { label: 'Total Candidates', value: stats?.total_candidates || 0, icon: HiUsers, color: 'from-blue-500 to-primary-600' },
    { label: 'Total Jobs', value: stats?.total_jobs || 0, icon: HiBriefcase, color: 'from-emerald-500 to-green-600' },
    { label: 'Analyzed', value: stats?.analyzed_count || 0, icon: HiDocumentCheck, color: 'from-purple-500 to-violet-600' },
    { label: 'Gold Ranked', value: stats?.gold_count || 0, icon: HiStar, color: 'from-yellow-500 to-amber-600' },
  ]

  const rankPieData = [
    { name: 'Gold', value: stats?.gold_count || 0 },
    { name: 'Silver', value: stats?.silver_count || 0 },
    { name: 'Bronze', value: stats?.bronze_count || 0 },
    { name: 'Shortlisted', value: stats?.shortlisted_count || 0 },
    { name: 'Rejected', value: stats?.rejected_count || 0 },
    { name: 'Pending', value: stats?.pending_count || 0 },
  ].filter(d => d.value > 0)

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload?.length) {
      return (
        <div className="glass-card !p-3 text-sm">
          <p className="font-medium">{label || payload[0].name}</p>
          <p className="text-primary-400">Count: {payload[0].value}</p>
        </div>
      )
    }
    return null
  }

  return (
    <div className="page-container">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
        <div className="flex items-center gap-3 mb-8">
          <HiArrowTrendingUp className="w-7 h-7 text-primary-400" />
          <h1 className="text-2xl font-bold">Dashboard</h1>
        </div>

        {/* Stat Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
          {statCards.map((card, i) => (
            <motion.div
              key={card.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: i * 0.1 }}
              className="glass-card-hover p-5"
            >
              <div className="flex items-center justify-between mb-3">
                <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${card.color} flex items-center justify-center`}>
                  <card.icon className="w-5 h-5 text-white" />
                </div>
              </div>
              <p className="text-3xl font-bold">{card.value}</p>
              <p className="text-sm text-dark-400 mt-1">{card.label}</p>
            </motion.div>
          ))}
        </div>

        {/* Charts Row */}
        <div className="grid lg:grid-cols-2 gap-6 mb-8">
          {/* Hiring Funnel */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.2 }}
            className="glass-card p-6"
          >
            <h3 className="text-lg font-semibold mb-4">Hiring Funnel</h3>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={funnelData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                  <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                    {funnelData.map((_, index) => (
                      <Cell key={index} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </motion.div>

          {/* Rank Distribution */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.3 }}
            className="glass-card p-6"
          >
            <h3 className="text-lg font-semibold mb-4">Rank Distribution</h3>
            <div className="h-[300px] flex items-center justify-center">
              {rankPieData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={rankPieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={4}
                      dataKey="value"
                    >
                      {rankPieData.map((_, index) => (
                        <Cell key={index} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <p className="text-dark-500">No data yet</p>
              )}
            </div>
            <div className="flex flex-wrap gap-3 mt-2 justify-center">
              {rankPieData.map((d, i) => (
                <div key={d.name} className="flex items-center gap-2 text-xs">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                  <span className="text-dark-400">{d.name}: {d.value}</span>
                </div>
              ))}
            </div>
          </motion.div>
        </div>

        {/* Skills & Top Candidates */}
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Top Skills */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.4 }}
            className="glass-card p-6"
          >
            <h3 className="text-lg font-semibold mb-4">Top Skills</h3>
            <div className="space-y-3">
              {skillsList.length > 0 ? skillsList.slice(0, 8).map((skill, i) => (
                <div key={skill.name} className="flex items-center gap-3">
                  <span className="text-sm text-dark-300 w-32 truncate">{skill.name}</span>
                  <div className="flex-1 h-2 bg-dark-700 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${Math.min((skill.count / (skillsList[0]?.count || 1)) * 100, 100)}%` }}
                      transition={{ duration: 0.8, delay: i * 0.05 }}
                      className="h-full bg-gradient-to-r from-primary-500 to-primary-400 rounded-full"
                    />
                  </div>
                  <span className="text-xs text-dark-500 w-8 text-right">{skill.count}</span>
                </div>
              )) : (
                <p className="text-dark-500 text-sm">No skills data yet. Upload and analyze resumes to see skills.</p>
              )}
            </div>
          </motion.div>

          {/* Top Candidates */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.5 }}
            className="glass-card p-6"
          >
            <h3 className="text-lg font-semibold mb-4">Top Candidates</h3>
            <div className="space-y-3">
              {stats?.top_candidates?.length > 0 ? stats.top_candidates.map((c, i) => (
                <div key={c.id} className="flex items-center justify-between p-3 rounded-xl bg-dark-800/50 hover:bg-dark-700/50 transition-colors">
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-dark-500 w-5">#{i + 1}</span>
                    <div className="w-8 h-8 rounded-full bg-primary-500/20 flex items-center justify-center text-sm font-medium text-primary-400">
                      {c.name?.[0] || '?'}
                    </div>
                    <div>
                      <p className="text-sm font-medium">{c.name}</p>
                      <p className="text-xs text-dark-400 capitalize">{c.rank}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span
                      className="text-lg font-bold"
                      style={{ color: getScoreColor(c.ats_score) }}
                    >
                      {c.ats_score?.toFixed(1) || '0'}
                    </span>
                    <p className="text-[10px] text-dark-500">ATS Score</p>
                  </div>
                </div>
              )) : (
                <p className="text-dark-500 text-sm">No candidates analyzed yet.</p>
              )}
            </div>
          </motion.div>
        </div>
      </motion.div>
    </div>
  )
}
