import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { accountsAPI } from '../services/api'
import {
  Plus,
  Edit2,
  Trash2,
  Wallet,
  CreditCard,
  PiggyBank,
  TrendingUp,
  X,
} from 'lucide-react'

// Account type icons and colors
const ACCOUNT_TYPES = {
  checking: { icon: Wallet, color: 'bg-blue-100 text-blue-600', label: 'Checking' },
  savings: { icon: PiggyBank, color: 'bg-green-100 text-green-600', label: 'Savings' },
  credit: { icon: CreditCard, color: 'bg-purple-100 text-purple-600', label: 'Credit Card' },
  investment: { icon: TrendingUp, color: 'bg-amber-100 text-amber-600', label: 'Investment' },
  loan: { icon: CreditCard, color: 'bg-red-100 text-red-600', label: 'Loan' },
  other: { icon: Wallet, color: 'bg-gray-100 text-gray-600', label: 'Other' },
}

/**
 * Accounts management page.
 * Lists all accounts and allows CRUD operations.
 */
function AccountsPage() {
  const queryClient = useQueryClient()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingAccount, setEditingAccount] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    account_type: 'checking',
    institution: '',
    balance: '0.00',
  })

  // Fetch accounts
  const { data: accounts = [], isLoading } = useQuery({
    queryKey: ['accounts'],
    queryFn: accountsAPI.list,
  })

  // Mutations
  const createMutation = useMutation({
    mutationFn: accountsAPI.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
      closeModal()
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => accountsAPI.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
      closeModal()
    },
  })

  const deleteMutation = useMutation({
    mutationFn: accountsAPI.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
    },
  })

  // Format currency
  const formatCurrency = (amount) => {
    const num = parseFloat(amount) || 0
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(num)
  }

  // Calculate total balance
  const totalBalance = accounts.reduce(
    (sum, acc) => sum + parseFloat(acc.balance || 0),
    0
  )

  // Modal handlers
  const openModal = (account = null) => {
    if (account) {
      setEditingAccount(account)
      setFormData({
        name: account.name,
        account_type: account.account_type,
        institution: account.institution || '',
        balance: account.balance?.toString() || '0.00',
      })
    } else {
      setEditingAccount(null)
      setFormData({
        name: '',
        account_type: 'checking',
        institution: '',
        balance: '0.00',
      })
    }
    setIsModalOpen(true)
  }

  const closeModal = () => {
    setIsModalOpen(false)
    setEditingAccount(null)
    setFormData({
      name: '',
      account_type: 'checking',
      institution: '',
      balance: '0.00',
    })
  }

  // Form submit
  const handleSubmit = (e) => {
    e.preventDefault()
    const data = {
      ...formData,
      balance: parseFloat(formData.balance) || 0,
    }

    if (editingAccount) {
      updateMutation.mutate({ id: editingAccount.id, data })
    } else {
      createMutation.mutate(data)
    }
  }

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Accounts</h1>
          <p className="text-sm text-gray-500">
            Total balance: {formatCurrency(totalBalance)}
          </p>
        </div>
        <button onClick={() => openModal()} className="btn-primary">
          <Plus size={20} className="mr-2" />
          Add Account
        </button>
      </div>

      {/* Accounts grid */}
      {isLoading ? (
        <div className="text-center py-12 text-gray-500">Loading...</div>
      ) : accounts.length === 0 ? (
        <div className="card text-center py-12">
          <Wallet className="h-12 w-12 mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No accounts yet
          </h3>
          <p className="text-gray-500 mb-4">
            Add your first account to start tracking your finances.
          </p>
          <button onClick={() => openModal()} className="btn-primary">
            <Plus size={20} className="mr-2" />
            Add Account
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {accounts.map((account) => {
            const typeConfig = ACCOUNT_TYPES[account.account_type] || ACCOUNT_TYPES.other
            const Icon = typeConfig.icon

            return (
              <div key={account.id} className="card">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`p-2.5 rounded-lg ${typeConfig.color}`}>
                      <Icon size={20} />
                    </div>
                    <div>
                      <h3 className="font-medium text-gray-900">{account.name}</h3>
                      <p className="text-sm text-gray-500">
                        {typeConfig.label}
                        {account.institution && ` • ${account.institution}`}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => openModal(account)}
                      className="p-1.5 text-gray-400 hover:text-gray-600 rounded"
                      title="Edit"
                    >
                      <Edit2 size={16} />
                    </button>
                    <button
                      onClick={() => {
                        if (confirm('Delete this account and all its transactions?')) {
                          deleteMutation.mutate(account.id)
                        }
                      }}
                      className="p-1.5 text-gray-400 hover:text-red-600 rounded"
                      title="Delete"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
                <div className="mt-4">
                  <p className="text-2xl font-bold text-gray-900">
                    {formatCurrency(account.balance)}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Add/Edit Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-black bg-opacity-50"
            onClick={closeModal}
          />
          <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">
                {editingAccount ? 'Edit Account' : 'Add Account'}
              </h2>
              <button
                onClick={closeModal}
                className="text-gray-400 hover:text-gray-600"
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="label">Account Name</label>
                <input
                  type="text"
                  required
                  className="input"
                  placeholder="e.g., Chase Checking"
                  value={formData.name}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, name: e.target.value }))
                  }
                />
              </div>

              <div>
                <label className="label">Account Type</label>
                <select
                  className="input"
                  value={formData.account_type}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      account_type: e.target.value,
                    }))
                  }
                >
                  {Object.entries(ACCOUNT_TYPES).map(([value, config]) => (
                    <option key={value} value={value}>
                      {config.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="label">Institution (Optional)</label>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g., Chase Bank"
                  value={formData.institution}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      institution: e.target.value,
                    }))
                  }
                />
              </div>

              <div>
                <label className="label">Current Balance</label>
                <input
                  type="number"
                  step="0.01"
                  className="input"
                  placeholder="0.00"
                  value={formData.balance}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, balance: e.target.value }))
                  }
                />
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={closeModal}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary"
                  disabled={createMutation.isPending || updateMutation.isPending}
                >
                  {editingAccount ? 'Save Changes' : 'Add Account'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default AccountsPage
