import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { categoriesAPI } from '../services/api'
import { Plus, Edit2, Trash2, Tags, X } from 'lucide-react'

/**
 * Categories management page.
 * Lists all categories and category rules.
 */
function CategoriesPage() {
  const queryClient = useQueryClient()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isRuleModalOpen, setIsRuleModalOpen] = useState(false)
  const [editingCategory, setEditingCategory] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    category_type: 'expense',
    color: '#3b82f6',
  })
  const [ruleForm, setRuleForm] = useState({
    pattern: '',
    category_id: '',
    priority: 0,
  })

  // Fetch data
  const { data: categories = [], isLoading } = useQuery({
    queryKey: ['categories'],
    queryFn: categoriesAPI.list,
  })

  const { data: rules = [] } = useQuery({
    queryKey: ['category-rules'],
    queryFn: categoriesAPI.listRules,
  })

  // Mutations
  const createMutation = useMutation({
    mutationFn: categoriesAPI.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      closeModal()
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => categoriesAPI.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      closeModal()
    },
  })

  const deleteMutation = useMutation({
    mutationFn: categoriesAPI.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] })
    },
  })

  const createRuleMutation = useMutation({
    mutationFn: categoriesAPI.createRule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['category-rules'] })
      closeRuleModal()
    },
  })

  const deleteRuleMutation = useMutation({
    mutationFn: categoriesAPI.deleteRule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['category-rules'] })
    },
  })

  // Modal handlers
  const openModal = (category = null) => {
    if (category) {
      setEditingCategory(category)
      setFormData({
        name: category.name,
        category_type: category.category_type,
        color: category.color || '#3b82f6',
      })
    } else {
      setEditingCategory(null)
      setFormData({
        name: '',
        category_type: 'expense',
        color: '#3b82f6',
      })
    }
    setIsModalOpen(true)
  }

  const closeModal = () => {
    setIsModalOpen(false)
    setEditingCategory(null)
  }

  const openRuleModal = () => {
    setRuleForm({ pattern: '', category_id: '', priority: 0 })
    setIsRuleModalOpen(true)
  }

  const closeRuleModal = () => {
    setIsRuleModalOpen(false)
  }

  // Form submits
  const handleSubmit = (e) => {
    e.preventDefault()
    if (editingCategory) {
      updateMutation.mutate({ id: editingCategory.id, data: formData })
    } else {
      createMutation.mutate(formData)
    }
  }

  const handleRuleSubmit = (e) => {
    e.preventDefault()
    createRuleMutation.mutate({
      ...ruleForm,
      category_id: parseInt(ruleForm.category_id),
      priority: parseInt(ruleForm.priority),
    })
  }

  // Predefined colors
  const colors = [
    '#ef4444', '#f97316', '#f59e0b', '#22c55e', '#14b8a6',
    '#0ea5e9', '#3b82f6', '#6366f1', '#8b5cf6', '#ec4899',
  ]

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Categories</h1>
          <p className="text-sm text-gray-500">
            Manage transaction categories and auto-categorization rules
          </p>
        </div>
        <button onClick={() => openModal()} className="btn-primary">
          <Plus size={20} className="mr-2" />
          Add Category
        </button>
      </div>

      {/* Categories grid */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Categories</h2>
        {isLoading ? (
          <div className="text-center py-8 text-gray-500">Loading...</div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {categories.map((category) => (
              <div
                key={category.id}
                className="flex items-center justify-between p-3 rounded-lg border border-gray-200 hover:border-gray-300"
              >
                <div className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: category.color || '#94a3b8' }}
                  />
                  <span className="text-sm font-medium text-gray-900">
                    {category.name}
                  </span>
                </div>
                {category.user_id && (
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => openModal(category)}
                      className="p-1 text-gray-400 hover:text-gray-600"
                    >
                      <Edit2 size={14} />
                    </button>
                    <button
                      onClick={() => {
                        if (confirm('Delete this category?')) {
                          deleteMutation.mutate(category.id)
                        }
                      }}
                      className="p-1 text-gray-400 hover:text-red-600"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Category rules */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              Auto-Categorization Rules
            </h2>
            <p className="text-sm text-gray-500">
              Custom rules to automatically categorize transactions
            </p>
          </div>
          <button onClick={openRuleModal} className="btn-secondary">
            <Plus size={18} className="mr-2" />
            Add Rule
          </button>
        </div>

        {rules.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Tags className="h-8 w-8 mx-auto mb-2 text-gray-400" />
            <p>No custom rules yet.</p>
            <p className="text-sm">
              Add rules to automatically categorize transactions based on keywords.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {rules.map((rule) => {
              const category = categories.find((c) => c.id === rule.category_id)
              return (
                <div
                  key={rule.id}
                  className="py-3 flex items-center justify-between"
                >
                  <div className="flex items-center gap-3">
                    <code className="px-2 py-1 bg-gray-100 rounded text-sm">
                      {rule.pattern}
                    </code>
                    <span className="text-gray-400">→</span>
                    <div className="flex items-center gap-1.5">
                      <div
                        className="w-2.5 h-2.5 rounded-full"
                        style={{ backgroundColor: category?.color || '#94a3b8' }}
                      />
                      <span className="text-sm text-gray-700">
                        {category?.name || 'Unknown'}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => deleteRuleMutation.mutate(rule.id)}
                    className="p-1 text-gray-400 hover:text-red-600"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Category Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-black bg-opacity-50"
            onClick={closeModal}
          />
          <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">
                {editingCategory ? 'Edit Category' : 'Add Category'}
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
                <label className="label">Name</label>
                <input
                  type="text"
                  required
                  className="input"
                  placeholder="e.g., Coffee Shops"
                  value={formData.name}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, name: e.target.value }))
                  }
                />
              </div>

              <div>
                <label className="label">Type</label>
                <select
                  className="input"
                  value={formData.category_type}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      category_type: e.target.value,
                    }))
                  }
                >
                  <option value="expense">Expense</option>
                  <option value="income">Income</option>
                </select>
              </div>

              <div>
                <label className="label">Color</label>
                <div className="flex flex-wrap gap-2">
                  {colors.map((color) => (
                    <button
                      key={color}
                      type="button"
                      className={`w-8 h-8 rounded-full border-2 ${
                        formData.color === color
                          ? 'border-gray-900'
                          : 'border-transparent'
                      }`}
                      style={{ backgroundColor: color }}
                      onClick={() =>
                        setFormData((prev) => ({ ...prev, color }))
                      }
                    />
                  ))}
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <button type="button" onClick={closeModal} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  {editingCategory ? 'Save Changes' : 'Add Category'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Rule Modal */}
      {isRuleModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-black bg-opacity-50"
            onClick={closeRuleModal}
          />
          <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">
                Add Categorization Rule
              </h2>
              <button
                onClick={closeRuleModal}
                className="text-gray-400 hover:text-gray-600"
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleRuleSubmit} className="space-y-4">
              <div>
                <label className="label">Pattern (keyword or regex)</label>
                <input
                  type="text"
                  required
                  className="input"
                  placeholder="e.g., starbucks or coffee.*"
                  value={ruleForm.pattern}
                  onChange={(e) =>
                    setRuleForm((prev) => ({ ...prev, pattern: e.target.value }))
                  }
                />
                <p className="mt-1 text-xs text-gray-500">
                  Matches transaction descriptions containing this pattern
                </p>
              </div>

              <div>
                <label className="label">Category</label>
                <select
                  required
                  className="input"
                  value={ruleForm.category_id}
                  onChange={(e) =>
                    setRuleForm((prev) => ({
                      ...prev,
                      category_id: e.target.value,
                    }))
                  }
                >
                  <option value="">Select a category</option>
                  {categories.map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {cat.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="label">Priority</label>
                <input
                  type="number"
                  className="input"
                  value={ruleForm.priority}
                  onChange={(e) =>
                    setRuleForm((prev) => ({ ...prev, priority: e.target.value }))
                  }
                />
                <p className="mt-1 text-xs text-gray-500">
                  Higher priority rules are matched first
                </p>
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={closeRuleModal}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Add Rule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default CategoriesPage
