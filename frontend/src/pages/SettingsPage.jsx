import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { motion } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { HiCog6Tooth } from 'react-icons/hi2'
import toast from 'react-hot-toast'

export default function SettingsPage() {
  const { user, updateProfile } = useAuth()
  const [loading, setLoading] = useState(false)
  const { register, handleSubmit, formState: { errors } } = useForm({
    defaultValues: {
      full_name: user?.full_name || '',
      phone: user?.phone || '',
      company: user?.company || '',
      designation: user?.designation || '',
    },
  })

  const onSubmit = async (data) => {
    setLoading(true)
    try {
      await updateProfile(data)
      toast.success('Profile updated')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Update failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-container max-w-2xl">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center gap-3 mb-8">
          <HiCog6Tooth className="w-7 h-7 text-primary-400" />
          <h1 className="text-2xl font-bold">Settings</h1>
        </div>

        {/* Profile */}
        <div className="glass-card p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Profile</h2>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-dark-300 mb-1">Full Name</label>
                <input className="glass-input" {...register('full_name')} />
              </div>
              <div>
                <label className="block text-sm text-dark-300 mb-1">Email</label>
                <input className="glass-input bg-dark-800/30" value={user?.email || ''} disabled />
              </div>
              <div>
                <label className="block text-sm text-dark-300 mb-1">Phone</label>
                <input className="glass-input" {...register('phone')} />
              </div>
              <div>
                <label className="block text-sm text-dark-300 mb-1">Company</label>
                <input className="glass-input" {...register('company')} />
              </div>
              <div>
                <label className="block text-sm text-dark-300 mb-1">Designation</label>
                <input className="glass-input" {...register('designation')} />
              </div>
              <div>
                <label className="block text-sm text-dark-300 mb-1">Role</label>
                <input className="glass-input bg-dark-800/30 capitalize" value={user?.role || ''} disabled />
              </div>
            </div>
            <button type="submit" disabled={loading} className="glass-button text-sm">
              {loading ? 'Saving...' : 'Save Changes'}
            </button>
          </form>
        </div>

        {/* Account Info */}
        <div className="glass-card p-6">
          <h2 className="text-lg font-semibold mb-4">Account Info</h2>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-dark-400">Username</span>
              <span>{user?.username}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-dark-400">Role</span>
              <span className="capitalize">{user?.role}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-dark-400">Account Status</span>
              <span className="text-emerald-400">{user?.is_active ? 'Active' : 'Inactive'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-dark-400">Member Since</span>
              <span>{user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}</span>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
