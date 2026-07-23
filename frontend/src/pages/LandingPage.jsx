import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { HiSparkles, HiArrowRight, HiCheckBadge, HiBolt, HiShieldCheck, HiChartBar } from 'react-icons/hi2'

const features = [
  { icon: HiBolt, title: 'AI Resume Parsing', desc: 'Automatically extract structured data from resumes using GPT-4 and NLP.' },
  { icon: HiChartBar, title: 'ATS Scoring', desc: 'Get precise ATS compatibility scores with detailed breakdowns.' },
  { icon: HiCheckBadge, title: 'Smart Matching', desc: 'AI-powered job matching with skills gap analysis.' },
  { icon: HiShieldCheck, title: 'Enterprise Security', desc: 'JWT auth, RBAC, encrypted data, and rate limiting.' },
]

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-dark-950 overflow-hidden">
      {/* Nav */}
      <nav className="fixed top-0 w-full z-50 bg-dark-950/80 backdrop-blur-xl border-b border-dark-700/30">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center">
              <HiSparkles className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-gradient">IQ-AI</span>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/login" className="px-5 py-2.5 text-sm font-medium text-dark-300 hover:text-white transition-colors">
              Sign In
            </Link>
            <Link to="/register" className="glass-button text-sm !py-2.5">
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-32 pb-20 px-6 relative">
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-primary-600/10 rounded-full blur-[120px]" />
          <div className="absolute top-1/3 left-1/3 w-[400px] h-[400px] bg-primary-500/5 rounded-full blur-[100px]" />
        </div>
        <div className="max-w-5xl mx-auto text-center relative">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary-500/10 border border-primary-500/20 text-primary-400 text-sm font-medium mb-8">
              <HiSparkles className="w-4 h-4" />
              AI-Powered Recruitment
            </div>
          </motion.div>
          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.1 }}
            className="text-5xl md:text-7xl font-extrabold leading-tight mb-6"
          >
            <span className="text-gradient">Intelligent</span> Resume
            <br />
            Screening Platform
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.2 }}
            className="text-lg text-dark-400 max-w-2xl mx-auto mb-10"
          >
            Automate resume screening with AI. Parse, score, rank, and analyze candidates
            against job descriptions with enterprise-grade intelligence.
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.3 }}
            className="flex items-center justify-center gap-4"
          >
            <Link to="/register" className="glass-button flex items-center gap-2 text-lg">
              Start Free <HiArrowRight className="w-5 h-5" />
            </Link>
            <Link to="/login" className="glass-button-secondary">
              View Demo
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Built for Modern Recruiting</h2>
            <p className="text-dark-400 text-lg max-w-2xl mx-auto">
              Everything you need to screen, analyze, and hire the best talent with AI.
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, i) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.1 * i }}
                className="glass-card-hover p-6"
              >
                <div className="w-12 h-12 rounded-xl bg-primary-500/10 flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-primary-400" />
                </div>
                <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                <p className="text-dark-400 text-sm leading-relaxed">{feature.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-20 px-6 border-t border-dark-700/30">
        <div className="max-w-5xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
          {[
            { value: '98%', label: 'Parsing Accuracy' },
            { value: '5x', label: 'Faster Screening' },
            { value: '100+', label: 'Skills Tracked' },
            { value: '<2s', label: 'Analysis Time' },
          ].map((stat) => (
            <div key={stat.label}>
              <div className="text-3xl md:text-4xl font-extrabold text-gradient mb-2">{stat.value}</div>
              <div className="text-dark-400 text-sm">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-6 border-t border-dark-700/30">
        <div className="max-w-7xl mx-auto flex items-center justify-between text-dark-500 text-sm">
          <span>2024 IQ-AI. All rights reserved.</span>
          <span>Enterprise AI Recruitment Platform</span>
        </div>
      </footer>
    </div>
  )
}
