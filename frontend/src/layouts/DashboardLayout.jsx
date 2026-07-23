import { useState } from 'react'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import {
  HiOutlineHome,
  HiOutlineArrowUpTray,
  HiOutlineBriefcase,
  HiOutlineUsers,
  HiOutlineDocumentChartBar,
  HiOutlineCog6Tooth,
  HiOutlineBars3,
  HiOutlineXMark,
  HiOutlineArrowRightOnRectangle,
  HiOutlineUser,
} from 'react-icons/hi2'
import { HiSparkles } from 'react-icons/hi'

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: HiOutlineHome, end: true },
  { path: '/dashboard/upload', label: 'Upload Resume', icon: HiOutlineArrowUpTray },
  { path: '/dashboard/jobs', label: 'Jobs', icon: HiOutlineBriefcase },
  { path: '/dashboard/candidates', label: 'Candidates', icon: HiOutlineUsers },
  { path: '/dashboard/reports', label: 'Reports', icon: HiOutlineDocumentChartBar },
  { path: '/dashboard/settings', label: 'Settings', icon: HiOutlineCog6Tooth },
]

export default function DashboardLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [mobileOpen, setMobileOpen] = useState(false)
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      <div className="p-6 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center shadow-glow">
          <HiSparkles className="w-6 h-6 text-white" />
        </div>
        {sidebarOpen && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col">
            <span className="text-lg font-bold text-gradient">IQ-AI</span>
            <span className="text-[10px] text-dark-400 tracking-wider">RECRUITMENT PLATFORM</span>
          </motion.div>
        )}
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.end}
            onClick={() => setMobileOpen(false)}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${
                isActive
                  ? 'bg-primary-600/20 text-primary-400 border border-primary-500/30 shadow-glow'
                  : 'text-dark-400 hover:text-white hover:bg-dark-700/50'
              }`
            }
          >
            <item.icon className="w-5 h-5 flex-shrink-0" />
            {sidebarOpen && <span>{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      <div className="p-3 border-t border-dark-700/50">
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-3 py-3 rounded-xl text-sm font-medium text-dark-400 hover:text-rose-400 hover:bg-rose-500/10 transition-all duration-200 w-full"
        >
          <HiOutlineArrowRightOnRectangle className="w-5 h-5" />
          {sidebarOpen && <span>Logout</span>}
        </button>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-dark-950 flex">
      {/* Desktop Sidebar */}
      <motion.aside
        animate={{ width: sidebarOpen ? 260 : 76 }}
        transition={{ duration: 0.3, ease: 'easeInOut' }}
        className="hidden lg:flex flex-col bg-dark-900/80 border-r border-dark-700/50 backdrop-blur-xl h-screen sticky top-0 z-30"
      >
        <SidebarContent />
      </motion.aside>

      {/* Mobile Sidebar Overlay */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/60 z-40 lg:hidden"
              onClick={() => setMobileOpen(false)}
            />
            <motion.aside
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ duration: 0.3, ease: 'easeInOut' }}
              className="fixed left-0 top-0 bottom-0 w-[260px] bg-dark-900 border-r border-dark-700/50 z-50 lg:hidden"
            >
              <SidebarContent />
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-h-screen">
        {/* Top Bar */}
        <header className="sticky top-0 z-20 bg-dark-950/80 backdrop-blur-xl border-b border-dark-700/50">
          <div className="flex items-center justify-between px-6 h-16">
            <div className="flex items-center gap-4">
              <button
                onClick={() => {
                  if (window.innerWidth < 1024) {
                    setMobileOpen(!mobileOpen)
                  } else {
                    setSidebarOpen(!sidebarOpen)
                  }
                }}
                className="p-2 rounded-lg hover:bg-dark-700/50 text-dark-400 hover:text-white transition-colors"
              >
                {mobileOpen ? <HiOutlineXMark className="w-5 h-5" /> : <HiOutlineBars3 className="w-5 h-5" />}
              </button>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center text-sm font-semibold">
                  {user?.full_name?.[0] || user?.username?.[0] || <HiOutlineUser />}
                </div>
                <div className="hidden sm:block">
                  <p className="text-sm font-medium">{user?.full_name || user?.username}</p>
                  <p className="text-xs text-dark-400 capitalize">{user?.role}</p>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
