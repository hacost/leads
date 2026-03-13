"use client"

import { useState } from "react"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Plus, Edit2, Trash2 } from "lucide-react"

const MOCK_CATEGORIES = [
  { id: "1", name: "Dentists", created: "2026-03-01", status: "active" },
  { id: "2", name: "Hardware Stores", created: "2026-03-05", status: "active" },
  { id: "3", name: "Plumbers", created: "2026-03-08", status: "active" },
  { id: "4", name: "Spas", created: "2026-03-10", status: "active" },
]

export default function CategoriesPage() {
  const [search, setSearch] = useState("")

  const filteredCategories = MOCK_CATEGORIES.filter(c => 
    c.name.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-6 max-w-5xl mx-auto mt-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Your Categories</h1>
          <p className="text-slate-400 mt-2">Manage the business types you want to scrape leads for.</p>
        </div>
        <Button className="bg-blue-600 hover:bg-blue-700 text-white">
          <Plus className="w-4 h-4 mr-2" /> Add Category
        </Button>
      </div>

      <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex items-center gap-4">
        <Input 
          placeholder="Search categories..." 
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="bg-slate-950 border-slate-700 max-w-sm"
        />
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <Table>
          <TableHeader className="bg-slate-950/50">
            <TableRow className="border-slate-800 hover:bg-transparent">
              <TableHead className="text-slate-400">Category Name</TableHead>
              <TableHead className="text-slate-400">Created Date</TableHead>
              <TableHead className="text-slate-400 text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredCategories.length === 0 ? (
              <TableRow>
                <TableCell colSpan={3} className="h-32 text-center text-slate-500">
                  No categories found. Start by adding one.
                </TableCell>
              </TableRow>
            ) : (
              filteredCategories.map((cat) => (
                <TableRow key={cat.id} className="border-slate-800 hover:bg-slate-800/50">
                  <TableCell className="font-semibold text-slate-200">{cat.name}</TableCell>
                  <TableCell className="text-slate-400">{cat.created}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button variant="ghost" size="icon" className="text-slate-400 hover:text-white hover:bg-slate-800">
                        <Edit2 className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="icon" className="text-red-400 hover:text-red-300 hover:bg-red-400/10">
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
