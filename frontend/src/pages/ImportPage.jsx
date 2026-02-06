import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { importAPI, accountsAPI } from '../services/api'
import {
  Upload,
  FileText,
  CheckCircle,
  AlertCircle,
  Info,
  X,
} from 'lucide-react'

/**
 * Import page for uploading CSV and OFX files.
 */
function ImportPage() {
  const queryClient = useQueryClient()
  const fileInputRef = useRef(null)
  const [selectedFile, setSelectedFile] = useState(null)
  const [selectedAccount, setSelectedAccount] = useState('')
  const [fileType, setFileType] = useState('csv')
  const [importResult, setImportResult] = useState(null)

  // Fetch accounts
  const { data: accounts = [] } = useQuery({
    queryKey: ['accounts'],
    queryFn: accountsAPI.list,
  })

  // Import mutation
  const importMutation = useMutation({
    mutationFn: async () => {
      if (fileType === 'csv') {
        return importAPI.importCSV(selectedFile, selectedAccount)
      } else {
        return importAPI.importOFX(selectedFile, selectedAccount)
      }
    },
    onSuccess: (data) => {
      setImportResult(data)
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] })
    },
    onError: (error) => {
      setImportResult({
        error: error.response?.data?.detail || 'Import failed',
      })
    },
  })

  // Handle file selection
  const handleFileChange = (e) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      // Auto-detect file type
      if (file.name.toLowerCase().endsWith('.ofx') || file.name.toLowerCase().endsWith('.qfx')) {
        setFileType('ofx')
      } else {
        setFileType('csv')
      }
      setImportResult(null)
    }
  }

  // Handle drag and drop
  const handleDrop = (e) => {
    e.preventDefault()
    const file = e.dataTransfer.files?.[0]
    if (file) {
      setSelectedFile(file)
      if (file.name.toLowerCase().endsWith('.ofx') || file.name.toLowerCase().endsWith('.qfx')) {
        setFileType('ofx')
      } else {
        setFileType('csv')
      }
      setImportResult(null)
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
  }

  // Handle import
  const handleImport = () => {
    if (!selectedFile || !selectedAccount) return
    importMutation.mutate()
  }

  // Reset form
  const resetForm = () => {
    setSelectedFile(null)
    setSelectedAccount('')
    setImportResult(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="space-y-6 max-w-2xl">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Import Transactions</h1>
        <p className="text-sm text-gray-500">
          Upload CSV or OFX files from your bank
        </p>
      </div>

      {/* Import form */}
      <div className="card space-y-6">
        {/* File upload area */}
        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            selectedFile
              ? 'border-primary-500 bg-primary-50'
              : 'border-gray-300 hover:border-gray-400'
          }`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,.ofx,.qfx"
            onChange={handleFileChange}
            className="hidden"
          />

          {selectedFile ? (
            <div className="flex items-center justify-center gap-3">
              <FileText className="h-8 w-8 text-primary-600" />
              <div className="text-left">
                <p className="font-medium text-gray-900">{selectedFile.name}</p>
                <p className="text-sm text-gray-500">
                  {(selectedFile.size / 1024).toFixed(1)} KB •{' '}
                  {fileType.toUpperCase()}
                </p>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  resetForm()
                }}
                className="ml-4 text-gray-400 hover:text-gray-600"
              >
                <X size={20} />
              </button>
            </div>
          ) : (
            <>
              <Upload className="h-10 w-10 mx-auto text-gray-400 mb-4" />
              <p className="font-medium text-gray-900 mb-1">
                Drop your file here, or click to browse
              </p>
              <p className="text-sm text-gray-500">
                Supports CSV, OFX, and QFX files
              </p>
            </>
          )}
        </div>

        {/* Account selection */}
        <div>
          <label className="label">Import to Account</label>
          <select
            className="input"
            value={selectedAccount}
            onChange={(e) => setSelectedAccount(e.target.value)}
          >
            <option value="">Select an account</option>
            {accounts.map((account) => (
              <option key={account.id} value={account.id}>
                {account.name} ({account.institution || account.account_type})
              </option>
            ))}
          </select>
          {accounts.length === 0 && (
            <p className="mt-1 text-sm text-amber-600">
              You need to create an account first before importing transactions.
            </p>
          )}
        </div>

        {/* Import button */}
        <button
          onClick={handleImport}
          disabled={!selectedFile || !selectedAccount || importMutation.isPending}
          className="btn-primary w-full"
        >
          {importMutation.isPending ? 'Importing...' : 'Import Transactions'}
        </button>

        {/* Import result */}
        {importResult && (
          <div
            className={`p-4 rounded-lg ${
              importResult.error
                ? 'bg-red-50 border border-red-200'
                : 'bg-green-50 border border-green-200'
            }`}
          >
            {importResult.error ? (
              <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-red-800">Import Failed</p>
                  <p className="text-sm text-red-700 mt-1">{importResult.error}</p>
                </div>
              </div>
            ) : (
              <div className="flex items-start gap-3">
                <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-green-800">Import Complete</p>
                  <ul className="text-sm text-green-700 mt-1 space-y-1">
                    <li>Total transactions: {importResult.total}</li>
                    <li>Imported: {importResult.imported}</li>
                    <li>Skipped (duplicates): {importResult.skipped}</li>
                    {importResult.errors?.length > 0 && (
                      <li className="text-amber-700">
                        Errors: {importResult.errors.length}
                      </li>
                    )}
                  </ul>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Help section */}
      <div className="card bg-gray-50">
        <div className="flex items-start gap-3">
          <Info className="h-5 w-5 text-gray-400 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-gray-600">
            <p className="font-medium text-gray-900 mb-2">Supported Banks</p>
            <ul className="space-y-1 list-disc list-inside">
              <li>Chase (Checking, Savings, Credit Cards)</li>
              <li>Capital One</li>
              <li>Discover</li>
              <li>Synovus</li>
              <li>Associated Credit Union</li>
              <li>Any bank with standard CSV exports</li>
            </ul>
            <p className="mt-3">
              <strong>Tip:</strong> Transactions are automatically categorized based
              on common keywords. You can always recategorize them later.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ImportPage
