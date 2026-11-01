import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { authAPI } from '../services/api'

export default function ForgotPasswordPage() {
  const [sent, setSent] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { register, handleSubmit, formState: { errors } } = useForm()

  const onSubmit = async ({ email }) => {
    setLoading(true)
    setError('')
    try {
      await authAPI.forgotPassword({ email })
      setSent(true)
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to request a reset link. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-dark-950 flex items-center justify-center px-4">
      <section className="glass-card w-full max-w-md p-8">
        <h1 className="text-2xl font-bold mb-2">Reset your password</h1>
        <p className="text-dark-400 text-sm mb-6">
          {sent ? 'If that email is registered, a reset link is on its way.' : 'Enter your account email and we’ll send you a reset link.'}
        </p>
        {!sent && (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <label className="block text-sm text-dark-300">
              Email
              <input type="email" className="glass-input mt-1.5" autoComplete="email" {...register('email', { required: 'Email is required' })} />
              {errors.email && <span className="text-rose-400 text-xs">{errors.email.message}</span>}
            </label>
            {error && <p role="alert" className="text-rose-400 text-sm">{error}</p>}
            <button className="glass-button w-full" disabled={loading}>{loading ? 'Sending…' : 'Send reset link'}</button>
          </form>
        )}
        <Link to="/login" className="block text-center text-primary-400 hover:text-primary-300 text-sm mt-6">Back to sign in</Link>
      </section>
    </main>
  )
}
