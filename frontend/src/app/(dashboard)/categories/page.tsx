"use client"

import { useState, useEffect } from "react"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Plus, Edit2, Trash2, Check, X } from "lucide-react"
import { toast } from "sonner"
import api from "@/lib/api"

export default function CategoriesPage() {
  const [search, setSearch] = useState("")
  const [categories, setCategories] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [newCatName, setNewCatName] = useState("")
  const [isCreating, setIsCreating] = useState(false)
  
  const [page, setPage] = useState(1)
  const [limit, setLimit] = useState(20)
  
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editName, setEditName] = useState("")

  const handleEditClick = (cat: any) => {
    setEditingId(cat.id)
    setEditName(cat.name)
  }

  const handleSaveEdit = async () => {
    if (!editName.trim() || !editingId) return;
    try {
      await api.put(`/api/categories/${editingId}`, { name: editName.trim() })
      toast.success("Category updated successfully")
      setEditingId(null)
      fetchCategories()
    } catch (e: any) {
      toast.error(e.message || "Failed to update category")
    }
  }

  const handleDelete = async (id: number) => {
    if (!window.confirm("Are you sure you want to delete this category? This action cannot be undone.")) return;
    try {
      await api.delete(`/api/categories/${id}`)
      toast.success("Category deleted successfully")
      fetchCategories()
    } catch (e: any) {
      toast.error(e.message || "Failed to delete category")
    }
  }

  const fetchCategories = async () => {
    setLoading(true)
    try {
      const offset = (page - 1) * limit
      const res = await api.get<any[]>(`/api/categories?limit=${limit}&offset=${offset}`)
      setCategories(res || [])
    } catch (e) {
      toast.error("Failed to load categories")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCategories()
  }, [page, limit])

  const handleCreate = async () => {
    if (!newCatName.trim()) return
    setIsCreating(true)
    try {
      await api.post('/api/categories', { name: newCatName.trim() })
      toast.success("Category added successfully")
      setNewCatName("")
      fetchCategories()
    } catch (e: any) {
      toast.error(e.message || "Failed to add category")
    } finally {
      setIsCreating(false)
    }
  }

  const filteredCategories = categories.filter(c => 
    (c.name || "").toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-6 max-w-5xl mx-auto mt-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Your Categories</h1>
          <p className="text-slate-400 mt-2">Manage the business types you want to scrape leads for.</p>
        </div>
      </div>

      <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex flex-col sm:flex-row gap-4 justify-between items-center">
        <div className="flex items-center gap-4 w-full sm:w-auto">
          <Input 
            placeholder="Search categories..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-slate-950 border-slate-700 max-w-sm"
          />
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 whitespace-nowrap">Show:</span>
            <select 
              value={limit} 
              onChange={(e) => { setLimit(Number(e.target.value)); setPage(1); }}
              className="bg-slate-950 border-slate-700 text-slate-300 text-sm rounded-md p-2 outline-none focus:ring-1 focus:ring-blue-500"
            >
              {[10, 20, 30, 50, 100].map(v => (
                <option key={v} value={v}>{v}</option>
              ))}
            </select>
          </div>
        </div>
        <div className="flex w-full sm:w-auto gap-2">
            <Input 
              placeholder="New category name" 
              value={newCatName}
              onChange={(e) => setNewCatName(e.target.value)}
              className="bg-slate-950 border-slate-700 w-full sm:w-48"
            />
            <Button onClick={handleCreate} disabled={!newCatName.trim() || isCreating} className="bg-blue-600 hover:bg-blue-700 text-white whitespace-nowrap">
              {isCreating ? "..." : <><Plus className="w-4 h-4 mr-2" /> Add</>}
            </Button>
        </div>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <Table>
          <TableHeader className="bg-slate-950/50">
            <TableRow className="border-slate-800 hover:bg-transparent">
              <TableHead className="text-slate-400">ID / Source</TableHead>
              <TableHead className="text-slate-400">Category Name</TableHead>
              <TableHead className="text-slate-400 text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={3} className="h-32 text-center text-slate-500">
                  Loading...
                </TableCell>
              </TableRow>
            ) : filteredCategories.length === 0 ? (
              <TableRow>
                <TableCell colSpan={3} className="h-32 text-center text-slate-500">
                  No categories found. Start by adding one.
                </TableCell>
              </TableRow>
            ) : (
              filteredCategories.map((cat) => (
                <TableRow key={cat.id} className="border-slate-800 hover:bg-slate-800/50">
                  {editingId === cat.id ? (
                    <TableCell colSpan={2}>
                      <div className="flex gap-2 items-center">
                        <Input 
                          value={editName} 
                          onChange={e => setEditName(e.target.value)} 
                          className="bg-slate-950 border-slate-700 h-8" 
                          autoFocus
                          onKeyDown={(e) => e.key === 'Enter' && handleSaveEdit()}
                        />
                      </div>
                    </TableCell>
                  ) : (
                    <>
                      <TableCell className="text-slate-500 font-mono text-xs">#{cat.id} {cat.owner_id === 'auto_seed' && "(Global)"}</TableCell>
                      <TableCell className="font-semibold text-slate-200">{cat.name}</TableCell>
                    </>
                  )}
                  <TableCell className="text-right">
                    {editingId === cat.id ? (
                      <div className="flex justify-end gap-2">
                        <Button onClick={handleSaveEdit} size="icon" className="h-8 w-8 bg-green-600 hover:bg-green-700 text-white">
                          <Check className="w-4 h-4" />
                        </Button>
                        <Button onClick={() => setEditingId(null)} size="icon" variant="ghost" className="h-8 w-8 text-slate-400 hover:text-white">
                          <X className="w-4 h-4" />
                        </Button>
                      </div>
                    ) : (
                      <div className="flex justify-end gap-2">
                        {cat.owner_id !== 'auto_seed' && (
                          <Button onClick={() => handleEditClick(cat)} variant="ghost" size="icon" className="text-slate-400 hover:text-white hover:bg-slate-800">
                            <Edit2 className="w-4 h-4" />
                          </Button>
                        )}
                        {cat.owner_id !== 'auto_seed' && (
                          <Button onClick={() => handleDelete(cat.id)} variant="ghost" size="icon" className="text-red-400 hover:text-red-300 hover:bg-red-400/10">
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        )}
                      </div>
                    )}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
      <div className="flex justify-between items-center pt-2">
        <p className="text-xs text-slate-500">
          Showing {categories.length} results (Page {page})
        </p>
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1 || loading}
            className="border-slate-800 bg-slate-900 text-slate-300 hover:bg-slate-800"
          >
            Previous
          </Button>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => setPage(p => p + 1)}
            disabled={categories.length < limit || loading}
            className="border-slate-800 bg-slate-900 text-slate-300 hover:bg-slate-800"
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  )
}
