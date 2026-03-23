"use client"

import { useState, useEffect } from "react"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Plus, Globe, Edit2, Trash2, Check, X } from "lucide-react"
import { toast } from "sonner"
import api from "@/lib/api"

export default function MasterCitiesPage() {
  const [search, setSearch] = useState("")
  const [cities, setCities] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  const [newName, setNewName] = useState("")
  const [newState, setNewState] = useState("")
  const [newCountry, setNewCountry] = useState("Mexico")
  const [isCreating, setIsCreating] = useState(false)

  const [editingId, setEditingId] = useState<number | null>(null)
  const [editName, setEditName] = useState("")
  const [editState, setEditState] = useState("")
  const [editCountry, setEditCountry] = useState("")

  const handleEditClick = (city: any) => {
    setEditingId(city.id)
    setEditName(city.name)
    setEditState(city.state)
    setEditCountry(city.country || "Mexico")
  }

  const handleSaveEdit = async () => {
    if (!editName.trim() || !editState.trim() || !editCountry.trim() || !editingId) return;
    try {
      await api.put(`/api/cities/${editingId}`, { 
        name: editName.trim(),
        state: editState.trim(),
        country: editCountry.trim()
      })
      toast.success("City updated successfully")
      setEditingId(null)
      fetchCities()
    } catch (e: any) {
      toast.error(e.message || "Failed to update city. Ensure you are an Admin.")
    }
  }

  const handleDelete = async (id: number) => {
    if (!window.confirm("Are you sure you want to delete this master city? It will remove access for all tenants using it.")) return;
    try {
      await api.delete(`/api/cities/${id}`)
      toast.success("City deleted successfully")
      fetchCities()
    } catch (e: any) {
      toast.error(e.message || "Failed to delete city. Ensure you are an Admin.")
    }
  }

  const fetchCities = async () => {
    try {
      const res = await api.get<any[]>('/api/cities')
      setCities(res || [])
    } catch (e) {
      toast.error("Failed to load cities")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCities()
  }, [])

  const handleCreate = async () => {
    if (!newName.trim() || !newState.trim() || !newCountry.trim()) return
    setIsCreating(true)
    try {
      await api.post('/api/cities', { 
        name: newName.trim(), 
        state: newState.trim(),
        country: newCountry.trim()
      })
      toast.success("City added successfully")
      setNewName("")
      setNewState("")
      setNewCountry("Mexico")
      fetchCities()
    } catch (e: any) {
      toast.error(e.message || "Failed to add city")
    } finally {
      setIsCreating(false)
    }
  }

  const filteredCities = cities.filter(c => 
    (c.name || "").toLowerCase().includes(search.toLowerCase()) || 
    (c.state || "").toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-6 max-w-5xl mx-auto mt-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
            Master Cities
            <Badge className="bg-purple-600 hover:bg-purple-700 text-white border-none text-xs">ADMIN ONLY</Badge>
          </h1>
          <p className="text-slate-400 mt-2">Global directory of target cities available to all tenants.</p>
        </div>
      </div>

      <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex flex-col sm:flex-row gap-4 justify-between items-center">
        <Input 
          placeholder="Search by city or state..." 
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="bg-slate-950 border-slate-700 max-w-sm"
        />
        <div className="flex w-full sm:w-auto gap-2">
            <Input 
              placeholder="City Name" 
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              className="bg-slate-950 border-slate-700 w-full sm:w-32"
            />
            <Input 
              placeholder="State (e.g TX)" 
              value={newState}
              onChange={(e) => setNewState(e.target.value)}
              className="bg-slate-950 border-slate-700 w-24"
            />
            <Input 
              placeholder="Country" 
              value={newCountry}
              onChange={(e) => setNewCountry(e.target.value)}
              className="bg-slate-950 border-slate-700 w-32"
            />
            <Button onClick={handleCreate} disabled={!newName.trim() || !newState.trim() || !newCountry.trim() || isCreating} className="bg-blue-600 hover:bg-blue-700 text-white whitespace-nowrap">
              {isCreating ? "..." : <><Plus className="w-4 h-4 mr-2" /> Add</>}
            </Button>
        </div>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <Table>
          <TableHeader className="bg-slate-950/50">
            <TableRow className="border-slate-800 hover:bg-transparent">
              <TableHead className="text-slate-400">City</TableHead>
              <TableHead className="text-slate-400">State / Region</TableHead>
              <TableHead className="text-slate-400">Creation Date</TableHead>
              <TableHead className="text-slate-400 text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={4} className="h-32 text-center text-slate-500">
                  Loading...
                </TableCell>
              </TableRow>
            ) : filteredCities.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="h-32 text-center text-slate-500">
                  No cities found.
                </TableCell>
              </TableRow>
            ) : (
              filteredCities.map((city) => (
                <TableRow key={city.id} className="border-slate-800 hover:bg-slate-800/50">
                  {editingId === city.id ? (
                    <TableCell colSpan={3}>
                      <div className="flex gap-2">
                        <Input value={editName} onChange={e => setEditName(e.target.value)} placeholder="City" className="bg-slate-950 border-slate-700 h-8 w-1/3" />
                        <Input value={editState} onChange={e => setEditState(e.target.value)} placeholder="State" className="bg-slate-950 border-slate-700 h-8 w-1/3" />
                        <Input value={editCountry} onChange={e => setEditCountry(e.target.value)} placeholder="Country" className="bg-slate-950 border-slate-700 h-8 w-1/3" />
                      </div>
                    </TableCell>
                  ) : (
                    <>
                      <TableCell className="font-semibold text-slate-200 flex items-center gap-2">
                        <Globe className="w-4 h-4 text-slate-500" /> {city.name}
                      </TableCell>
                      <TableCell className="text-slate-300">{city.state}</TableCell>
                      <TableCell className="text-slate-500 text-xs">{city.created_at || "Legacy"}</TableCell>
                    </>
                  )}
                  <TableCell className="text-right">
                    {editingId === city.id ? (
                      <div className="flex justify-end gap-2">
                        <Button onClick={handleSaveEdit} size="icon" className="bg-green-600 hover:bg-green-700 text-white h-8 w-8">
                          <Check className="w-4 h-4" />
                        </Button>
                        <Button onClick={() => setEditingId(null)} size="icon" variant="ghost" className="h-8 w-8 text-slate-400 hover:text-white">
                          <X className="w-4 h-4" />
                        </Button>
                      </div>
                    ) : (
                      <div className="flex justify-end gap-2">
                        <Button onClick={() => handleEditClick(city)} variant="ghost" size="icon" className="text-slate-400 hover:text-white hover:bg-slate-800">
                          <Edit2 className="w-4 h-4" />
                        </Button>
                        <Button onClick={() => handleDelete(city.id)} variant="ghost" size="icon" className="text-red-400 hover:text-red-300 hover:bg-red-400/10">
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    )}
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
