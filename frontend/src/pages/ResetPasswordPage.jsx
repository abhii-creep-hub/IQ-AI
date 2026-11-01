import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { authAPI } from '../services/api'

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams()
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { register, handleSubmit, watch, formState: { errors } } = useForm()
  const password = watch('password')
  const token = searchParams.get('token')

  const onSubmit = async ({ password: new_password }) => {
    setLoading(true)
    setError('')
    try {
      await authAPI.resetPassword({ token, new_password })
      navigate('/login', { replace: true, state: { message: 'Password reset. Please sign in.' } })
    } catch (err) {
      setError(err.response?.data?.detail || 'The reset link is invalid or expired. Request a new one.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-dark-950 flex items-center justify-center px-4">
      <section className="glass-card w-full max-w-md p-8">
        <h1 className="text-2xl font-bold mb-2">Choose a new password</h1>
        <p className="text-dark-400 text-sm mb-6">Use at least 8 characters.</p>
        {!token ? (
          <p role="alert" className="text-rose-400 text-sm">This reset link is missing its token. <Link className="underline" to="/forgot-password">Request another link</Link>.</p>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <label className="block text-sm text-dark-300">
              New password
              <input type="password" className="glass-input mt-1.5" autoComplete="new-password" {...register('password', { required: 'Password is required', minLength: { value: 8, message: 'Use at least 8 characters' }, maxLength: { value: 128, message: 'Password is too long' } })} />
              {errors.password && <span className="text-rose-400 text-xs">{errors.password.message}</span>}
            </label>
            <label className="block text-sm text-dark-300">
              Confirm password
              <input type="password" className="glass-input mt-1.5" autoComplete="new-password" {...register('confirmPassword', { required: 'Please confirm your password', validate: (value) => value === password || 'Passwords do not match' })} />
              {errors.confirmPassword && <span className="text-rose-400 text-xs">{errors.confirmPassword.message}</span>}
            </label>
            {error && <p role="alert" className="text-rose-400 text-sm">{error}</p>}
            <button className="glass-button w-full" disabled={loading}>{loading ? 'Updating…' : 'Update password'}</button>
          </form>
        )}
        <Link to="/login" className="block text-center text-primary-400 hover:text-primary-300 text-sm mt-6">Back to sign in</Link>
      </section>
    </main>
  )
}
