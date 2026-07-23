import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { motion, AnimatePresence } from 'framer-motion'
import { useUploadMultipleResumes, useParseAndAnalyze, useJobs } from '../hooks/useQueries'
import { HiArrowUpTray, HiDocument, HiXMark, HiCheckCircle, HiExclamationCircle } from 'react-icons/hi2'
import { formatFileSize } from '../utils/helpers'

export default function UploadPage() {
  const [files, setFiles] = useState([])
  const [selectedJob, setSelectedJob] = useState('')
  const [processing, setProcessing] = useState(false)
  const [results, setResults] = useState([])
  const uploadMutation = useUploadMultipleResumes()
  const analyzeMutation = useParseAndAnalyze()
  const { data: jobs } = useJobs()

  const onDrop = useCallback((acceptedFiles) => {
    setFiles((prev) => [...prev, ...acceptedFiles])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxSize: 20 * 1024 * 1024,
  })

  const removeFile = (index) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const handleUpload = async () => {
    if (files.length === 0) return
    setProcessing(true)
    setResults([])

    const formData = new FormData()
    files.forEach((f) => formData.append('files', f))
    if (selectedJob) formData.append('job_id', selectedJob)

    try {
      const uploaded = await uploadMutation.mutateAsync(formData)
      const newResults = []

      for (const item of uploaded) {
        try {
          const analysisResult = await analyzeMutation.mutateAsync({
            candidateId: item.candidate_id,
            jobId: selectedJob || null,
          })
          newResults.push({
            filename: item.filename,
            status: 'success',
            candidate_id: item.candidate_id,
            ats_score: analysisResult?.analysis?.ats_score || 0,
            rank: analysisResult?.analysis?.rank || 'pending',
          })
        } catch {
          newResults.push({
            filename: item.filename,
            status: 'partial',
            candidate_id: item.candidate_id,
          })
        }
      }

      setResults(newResults)
      setFiles([])
    } catch (err) {
      console.error('Upload failed:', err)
    } finally {
      setProcessing(false)
    }
  }

  return (
    <div className="page-container">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center gap-3 mb-8">
          <HiArrowUpTray className="w-7 h-7 text-primary-400" />
          <h1 className="text-2xl font-bold">Upload Resumes</h1>
        </div>

        {/* Job Selection */}
        <div className="glass-card p-6 mb-6">
          <label className="block text-sm font-medium text-dark-300 mb-2">Select Job (Optional)</label>
          <select
            value={selectedJob}
            onChange={(e) => setSelectedJob(e.target.value)}
            className="glass-input"
          >
            <option value="">No job selected - general screening</option>
            {jobs?.map((job) => (
              <option key={job.id} value={job.id}>{job.title}</option>
            ))}
          </select>
        </div>

        {/* Dropzone */}
        <div
          {...getRootProps()}
          className={`glass-card p-12 text-center cursor-pointer transition-all duration-300 ${
            isDragActive
              ? 'border-primary-500/50 bg-primary-500/5 shadow-glow'
              : 'hover:border-dark-500'
          }`}
        >
          <input {...getInputProps()} />
          <HiArrowUpTray className={`w-12 h-12 mx-auto mb-4 ${isDragActive ? 'text-primary-400' : 'text-dark-500'}`} />
          <p className="text-lg font-medium mb-2">
            {isDragActive ? 'Drop files here' : 'Drag & drop resumes here'}
          </p>
          <p className="text-sm text-dark-400">or click to browse. PDF, DOCX up to 20MB each</p>
        </div>

        {/* File List */}
        <AnimatePresence>
          {files.length > 0 && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="glass-card p-6 mt-6"
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold">{files.length} file(s) selected</h3>
                <button onClick={() => setFiles([])} className="text-sm text-dark-400 hover:text-rose-400">
                  Clear all
                </button>
              </div>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {files.map((file, i) => (
                  <div key={`${file.name}-${i}`} className="flex items-center justify-between p-3 rounded-xl bg-dark-800/50">
                    <div className="flex items-center gap-3">
                      <HiDocument className="w-5 h-5 text-primary-400" />
                      <div>
                        <p className="text-sm font-medium">{file.name}</p>
                        <p className="text-xs text-dark-400">{formatFileSize(file.size)}</p>
                      </div>
                    </div>
                    <button onClick={() => removeFile(i)} className="p-1 hover:bg-dark-700 rounded-lg transition-colors">
                      <HiXMark className="w-4 h-4 text-dark-400" />
                    </button>
                  </div>
                ))}
              </div>
              <button
                onClick={handleUpload}
                disabled={processing}
                className="glass-button w-full mt-4 flex items-center justify-center gap-2"
              >
                {processing ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Processing {files.length} files...
                  </>
                ) : (
                  `Upload & Analyze ${files.length} Resume(s)`
                )}
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Results */}
        <AnimatePresence>
          {results.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass-card p-6 mt-6"
            >
              <h3 className="font-semibold mb-4">Processing Results</h3>
              <div className="space-y-2">
                {results.map((r, i) => (
                  <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-dark-800/50">
                    <div className="flex items-center gap-3">
                      {r.status === 'success' ? (
                        <HiCheckCircle className="w-5 h-5 text-emerald-400" />
                      ) : (
                        <HiExclamationCircle className="w-5 h-5 text-yellow-400" />
                      )}
                      <div>
                        <p className="text-sm font-medium">{r.filename}</p>
                        <p className="text-xs text-dark-400 capitalize">{r.rank || 'Processing'}</p>
                      </div>
                    </div>
                    {r.ats_score > 0 && (
                      <span className="text-sm font-bold text-primary-400">{r.ats_score.toFixed(1)}</span>
                    )}
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  )
}
