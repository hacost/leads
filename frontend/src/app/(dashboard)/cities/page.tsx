/* eslint-disable react-hooks/exhaustive-deps */
"use client"

import { useState, useEffect } from "react"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Plus, Globe, Edit2, Trash2, Check, X, MapPin } from "lucide-react"
import { toast } from "sonner"
import api from "@/lib/api"

// --- TYPES ---
interface Country { id: number; name: string }
interface State { id: number; name: string; country_id: number }
interface City { id: number; name: string; state_id: number | null; state_name?: string; country_name?: string; status: number; created_at: string | null }


// --- SUBCOMPONENTS ---

function CountriesTab() {
  const [countries, setCountries] = useState<Country[]>([])
  const [loading,   setLoading]   = useState(true)
  const [search,    setSearch]    = useState("")
  const [newName,   setNewName]   = useState("")
  const [isCreating,setIsCreating] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editName,  setEditName]  = useState("")

  const load = async () => {
    setLoading(true)
    try {
      const res = await api.get<Country[]>("/api/countries")
      setCountries(res || [])
    } catch { toast.error("Failed to load countries") }
    finally { setLoading(false) }
  }
  useEffect(() => { load() }, [])

  const handleCreate = async () => {
    if (!newName.trim()) return
    setIsCreating(true)
    try {
      await api.post("/api/countries", { name: newName.trim() })
      toast.success("Country added")
      setNewName("")
      load()
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed")
    }
    finally { setIsCreating(false) }
  }

  const handleSaveEdit = async () => {
    if (!editName.trim() || !editingId) return
    try {
      await api.put(`/api/countries/${editingId}`, { name: editName.trim() })
      toast.success("Country updated")
      setEditingId(null)
      load()
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed")
    }
  }

  const filtered = countries.filter(c => c.name.toLowerCase().includes(search.toLowerCase()))

  return (
    <div className="space-y-4">
      <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex items-end gap-4">
        <div className="w-1/2">
          <label className="text-xs text-slate-500 uppercase tracking-widest mb-1 block">Add New Country</label>
          <Input placeholder="e.g. Canada" value={newName} onChange={e => setNewName(e.target.value)} className="bg-slate-950 border-slate-700 h-10" />
        </div>
        <Button onClick={handleCreate} disabled={!newName.trim() || isCreating} className="bg-blue-600 hover:bg-blue-700 h-10 w-32">
          {isCreating ? "..." : <><Plus className="w-4 h-4 mr-2" />Add</>}
        </Button>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden p-4">
        <Input placeholder="Search country..." value={search} onChange={e => setSearch(e.target.value)} className="bg-slate-950 border-slate-700 w-full max-w-sm mb-4" />
        <Table>
          <TableHeader className="bg-slate-950/50">
            <TableRow className="border-slate-800">
              <TableHead className="w-16">ID</TableHead>
              <TableHead>Country Name</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? <TableRow><TableCell colSpan={3} className="text-center py-8 text-slate-500">Loading...</TableCell></TableRow> : null}
            {!loading && filtered.length === 0 ? <TableRow><TableCell colSpan={3} className="text-center py-8 text-slate-500">No countries found.</TableCell></TableRow> : null}
            {filtered.map(c => (
              <TableRow key={c.id} className="border-slate-800 hover:bg-slate-800/50">
                <TableCell className="text-slate-500">{c.id}</TableCell>
                <TableCell>
                  {editingId === c.id ? (
                    <Input value={editName} onChange={e => setEditName(e.target.value)} className="bg-slate-950 border-slate-700 h-8 max-w-xs" />
                  ) : <span className="font-semibold text-slate-200">{c.name}</span>}
                </TableCell>
                <TableCell className="text-right">
                  {editingId === c.id ? (
                    <div className="flex justify-end gap-2">
                      <Button onClick={handleSaveEdit} size="icon" className="bg-green-600 hover:bg-green-700 h-8 w-8"><Check className="w-4 h-4" /></Button>
                      <Button onClick={() => setEditingId(null)} size="icon" variant="ghost" className="h-8 w-8 text-slate-400"><X className="w-4 h-4" /></Button>
                    </div>
                  ) : (
                    <div className="flex justify-end gap-2">
                      <Button onClick={() => {setEditingId(c.id); setEditName(c.name)}} variant="ghost" size="icon" className="h-8 w-8 text-slate-400 hover:text-white"><Edit2 className="w-4 h-4" /></Button>
                      {/* Delete restricted intentionally */}
                    </div>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}

function StatesTab() {
  const [countries, setCountries] = useState<Country[]>([])
  const [selectedCountryId, setSelectedCountryId] = useState<number | null>(null)
  
  const [states, setStates] = useState<State[]>([])
  const [loading, setLoading] = useState(false)
  const [newName, setNewName] = useState("")
  const [isCreating, setIsCreating] = useState(false)
  
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editName, setEditName] = useState("")

  const loadCountries = async () => {
    try {
      const res = await api.get<Country[]>("/api/countries")
      setCountries(res || [])
    } catch {}
  }
  
  const loadStates = async (cid: number) => {
    if (!cid) return setStates([])
    setLoading(true)
    try {
      const res = await api.get<State[]>(`/api/states?country_id=${cid}`)
      setStates(res || [])
    } catch { toast.error("Failed to load states") }
    finally { setLoading(false) }
  }

  useEffect(() => { loadCountries() }, [])
  useEffect(() => { if (selectedCountryId) loadStates(selectedCountryId) }, [selectedCountryId])

  const handleCreate = async () => {
    if (!newName.trim() || !selectedCountryId) return
    setIsCreating(true)
    try {
      await api.post("/api/states", { name: newName.trim(), country_id: selectedCountryId })
      toast.success("State added")
      setNewName("")
      loadStates(selectedCountryId)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed")
    }
    finally { setIsCreating(false) }
  }

  const handleSaveEdit = async () => {
    if (!editName.trim() || !editingId || !selectedCountryId) return
    try {
      await api.put(`/api/states/${editingId}`, { name: editName.trim(), country_id: selectedCountryId })
      toast.success("State updated")
      setEditingId(null)
      loadStates(selectedCountryId)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed")
    }
  }

  const handleDelete = async (id: number) => {
    if (!window.confirm("Soft-delete this state AND cascading cities?")) return
    try {
      await api.delete(`/api/states/${id}`)
      toast.success("State deleted cascade")
      loadStates(selectedCountryId!)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed")
    }
  }

  return (
    <div className="space-y-4">
      {/* Context Selector */}
      <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex items-end gap-4">
        <div className="w-1/2">
          <label className="text-xs text-slate-500 uppercase tracking-widest mb-1 block">Filter by Country</label>
          <select 
            className="bg-slate-950 border-slate-700 text-slate-200 h-10 px-3 py-2 w-full rounded-md border outline-none"
            value={selectedCountryId ?? ""}
            onChange={e => setSelectedCountryId(e.target.value ? Number(e.target.value) : null)}
          >
            <option value="">-- Select Country --</option>
            {countries.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>
      </div>

      {selectedCountryId && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden p-4 space-y-4">
          <div className="flex gap-4 items-end bg-slate-950/30 p-4 rounded-lg border border-slate-800/60">
            <div className="flex-1">
              <label className="text-xs text-slate-500 uppercase tracking-widest mb-1 block">Add New State (in selected country)</label>
              <Input placeholder="e.g. Ontario" value={newName} onChange={e => setNewName(e.target.value)} className="bg-slate-950 border-slate-700 h-10" />
            </div>
            <Button onClick={handleCreate} disabled={!newName.trim() || isCreating} className="bg-blue-600 hover:bg-blue-700 h-10 w-32">
              {isCreating ? "..." : <><Plus className="w-4 h-4 mr-2" />Add</>}
            </Button>
          </div>

          <Table>
            <TableHeader className="bg-slate-950/50">
              <TableRow className="border-slate-800">
                <TableHead className="w-16">ID</TableHead>
                <TableHead>State Name</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? <TableRow><TableCell colSpan={3} className="text-center py-8 text-slate-500">Loading...</TableCell></TableRow> : null}
              {!loading && states.length === 0 ? <TableRow><TableCell colSpan={3} className="text-center py-8 text-slate-500">No states found here.</TableCell></TableRow> : null}
              {states.map(s => (
                <TableRow key={s.id} className="border-slate-800 hover:bg-slate-800/50">
                  <TableCell className="text-slate-500">{s.id}</TableCell>
                  <TableCell>
                    {editingId === s.id ? (
                      <Input value={editName} onChange={e => setEditName(e.target.value)} className="bg-slate-950 border-slate-700 h-8 max-w-xs" />
                    ) : <span className="font-semibold text-slate-200">{s.name}</span>}
                  </TableCell>
                  <TableCell className="text-right">
                    {editingId === s.id ? (
                      <div className="flex justify-end gap-2">
                        <Button onClick={handleSaveEdit} size="icon" className="bg-green-600 hover:bg-green-700 h-8 w-8"><Check className="w-4 h-4" /></Button>
                        <Button onClick={() => setEditingId(null)} size="icon" variant="ghost" className="h-8 w-8 text-slate-400"><X className="w-4 h-4" /></Button>
                      </div>
                    ) : (
                      <div className="flex justify-end gap-2">
                        <Button onClick={() => {setEditingId(s.id); setEditName(s.name)}} variant="ghost" size="icon" className="h-8 w-8 text-slate-400 hover:text-white"><Edit2 className="w-4 h-4" /></Button>
                        <Button onClick={() => handleDelete(s.id)} variant="ghost" size="icon" className="h-8 w-8 text-red-500 hover:text-red-400 hover:bg-red-500/10"><Trash2 className="w-4 h-4" /></Button>
                      </div>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  )
}

function CitiesTab() {
  const [cities, setCities] = useState<City[]>([])
  const [search, setSearch] = useState("")
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [limit, setLimit] = useState(20)

  // Form creation logic (pure selects, no guessing IDs)
  const [countries, setCountries] = useState<Country[]>([])
  const [formCountryId, setFormCountryId] = useState<number | null>(null)
  const [formStates, setFormStates] = useState<State[]>([])
  const [formStateId, setFormStateId] = useState<number | null>(null)
  const [newName, setNewName] = useState("")
  const [isCreating, setIsCreating] = useState(false)

  // Inline edit (just name, avoiding massive selects in table cells)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editName, setEditName] = useState("")

  const fetchCities = async () => {
    setLoading(true)
    try {
      const offset = (page - 1) * limit
      const res = await api.get<City[]>(`/api/cities?limit=${limit}&offset=${offset}`)
      setCities(res || [])
    } catch { toast.error("Failed to load cities") }
    finally { setLoading(false) }
  }

  const loadCountries = async () => {
    try {
      const res = await api.get<Country[]>("/api/countries")
      setCountries(res || [])
    } catch {}
  }

  const loadFormStates = async (cid: number) => {
    if (!cid) return setFormStates([])
    try {
      const res = await api.get<State[]>(`/api/states?country_id=${cid}`)
      setFormStates(res || [])
    } catch {}
  }

  useEffect(() => { fetchCities(); loadCountries() }, [page, limit])

  useEffect(() => {
    setFormStateId(null)
    if (formCountryId) loadFormStates(formCountryId)
    else setFormStates([])
  }, [formCountryId])

  const handleCreate = async () => {
    if (!newName.trim() || !formStateId) return
    setIsCreating(true)
    try {
      await api.post("/api/cities", { name: newName.trim(), state_id: formStateId })
      toast.success("City added successfully")
      setNewName("")
      setFormCountryId(null)
      fetchCities()
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed")
    }
    finally { setIsCreating(false) }
  }

  const handleSaveEdit = async (originalStateId: number | null) => {
    if (!editName.trim() || !editingId || !originalStateId) return
    try {
      await api.put(`/api/cities/${editingId}`, { name: editName.trim(), state_id: originalStateId })
      toast.success("City updated")
      setEditingId(null)
      fetchCities()
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed")
    }
  }

  const handleDelete = async (id: number) => {
    if (!window.confirm("Soft delete this master city?")) return
    try {
      await api.delete(`/api/cities/${id}`)
      toast.success("City deleted successfully")
      fetchCities()
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed")
    }
  }

  const filteredCities = cities.filter(c =>
    (c.name || "").toLowerCase().includes(search.toLowerCase()) ||
    (c.state_name || "").toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-4">
      {/* ADD CITY (Visual Flow Select) */}
      <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl space-y-4">
        <p className="text-slate-400 text-sm font-medium uppercase tracking-wider mb-2">Create New City Master</p>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="space-y-1">
            <label className="text-slate-400 text-xs tracking-wider">1. Select Country</label>
            <select 
              className="bg-slate-950 border-slate-700 text-slate-200 h-10 w-full rounded-md border px-3"
              value={formCountryId ?? ""}
              onChange={e => setFormCountryId(e.target.value ? Number(e.target.value) : null)}
            >
              <option value="">-- Choose --</option>
              {countries.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div className="space-y-1">
            <label className="text-slate-400 text-xs tracking-wider">2. Select State</label>
            <select 
              className="bg-slate-950 border-slate-700 text-slate-200 h-10 w-full rounded-md border px-3 disabled:opacity-50"
              value={formStateId ?? ""}
              onChange={e => setFormStateId(e.target.value ? Number(e.target.value) : null)}
              disabled={!formCountryId}
            >
              <option value="">-- Choose --</option>
              {formStates.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </div>
          <div className="space-y-1">
            <label className="text-slate-400 text-xs tracking-wider">3. Type City Name</label>
            <Input
              placeholder="e.g. Toronto"
              value={newName}
              onChange={e => setNewName(e.target.value)}
              className="bg-slate-950 border-slate-700 h-10"
              disabled={!formStateId}
            />
          </div>
          <div className="space-y-1 flex items-end">
            <Button
              onClick={handleCreate}
              disabled={!newName.trim() || !formStateId || isCreating}
              className="bg-blue-600 hover:bg-blue-700 h-10 w-full"
            >
              {isCreating ? "..." : <><Plus className="w-4 h-4 mr-2" />Add City</>}
            </Button>
          </div>
        </div>
      </div>

      {/* FILTER & LIMIT */}
      <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex flex-col sm:flex-row justify-between items-center gap-4">
        <Input placeholder="Search by city or state..." value={search} onChange={e => setSearch(e.target.value)} className="bg-slate-950 border-slate-700 w-full max-w-sm" />
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500 whitespace-nowrap">Show:</span>
          <select value={limit} onChange={e => { setLimit(Number(e.target.value)); setPage(1) }} className="bg-slate-950 border-slate-700 text-sm p-2 rounded-md outline-none text-slate-200">
            {[10, 20, 50, 100].map(v => <option key={v} value={v}>{v}</option>)}
          </select>
        </div>
      </div>

      {/* CITIES TABLE */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <Table>
          <TableHeader className="bg-slate-950/50">
            <TableRow className="border-slate-800 hover:bg-transparent">
              <TableHead className="text-slate-400">City</TableHead>
              <TableHead className="text-slate-400">State / Region</TableHead>
              <TableHead className="text-slate-400">Country</TableHead>
              <TableHead className="text-slate-400 text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? <TableRow><TableCell colSpan={4} className="h-32 text-center text-slate-500">Loading...</TableCell></TableRow> : null}
            {!loading && filteredCities.length === 0 ? <TableRow><TableCell colSpan={4} className="h-32 text-center text-slate-500">No active cities found.</TableCell></TableRow> : null}
            {filteredCities.map(city => (
              <TableRow key={city.id} className="border-slate-800 hover:bg-slate-800/50">
                <TableCell>
                  {editingId === city.id ? (
                    <Input value={editName} onChange={e => setEditName(e.target.value)} className="bg-slate-950 border-slate-700 h-8 max-w-xs" />
                  ) : <span className="font-semibold text-slate-200 flex items-center gap-2"><MapPin className="w-4 h-4 text-slate-500"/>{city.name}</span>}
                </TableCell>
                <TableCell className="text-slate-400">{city.state_name}</TableCell>
                <TableCell className="text-slate-500">{city.country_name}</TableCell>
                <TableCell className="text-right">
                  {editingId === city.id ? (
                      <div className="flex justify-end gap-2">
                        <Button onClick={() => handleSaveEdit(city.state_id)} size="icon" className="bg-green-600 hover:bg-green-700 h-8 w-8"><Check className="w-4 h-4" /></Button>
                        <Button onClick={() => setEditingId(null)} size="icon" variant="ghost" className="h-8 w-8 text-slate-400"><X className="w-4 h-4" /></Button>
                      </div>
                  ) : (
                    <div className="flex justify-end gap-2">
                      <Button onClick={() => {setEditingId(city.id); setEditName(city.name)}} variant="ghost" size="icon" className="text-slate-400 hover:text-white"><Edit2 className="w-4 h-4" /></Button>
                      <Button onClick={() => handleDelete(city.id)} variant="ghost" size="icon" className="text-red-400 hover:text-red-300 hover:bg-red-400/10"><Trash2 className="w-4 h-4" /></Button>
                    </div>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <div className="flex justify-between items-center pt-2">
        <p className="text-xs text-slate-500">Showing {cities.length} results (Page {page})</p>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1 || loading} className="border-slate-800 bg-slate-900 text-slate-300">Previous</Button>
          <Button variant="outline" size="sm" onClick={() => setPage(p => p + 1)} disabled={cities.length < limit || loading} className="border-slate-800 bg-slate-900 text-slate-300">Next</Button>
        </div>
      </div>
    </div>
  )
}

// --- MAIN PAGE ---

export default function LocationManagerPage() {
  return (
    <div className="space-y-6 max-w-5xl mx-auto mt-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
            Location Manager
            <Badge className="bg-purple-600 hover:bg-purple-700 text-white border-none text-xs">ADMIN ONLY</Badge>
          </h1>
          <p className="text-slate-400 mt-2">Global Master Directory for Countries, States, and Cities.</p>
        </div>
      </div>

      <Tabs defaultValue="cities" className="w-full">
        <TabsList className="grid w-full grid-cols-3 bg-slate-900 border border-slate-800 mb-6">
          <TabsTrigger value="countries" className="data-[state=active]:bg-slate-800 data-[state=active]:text-white">Countries</TabsTrigger>
          <TabsTrigger value="states" className="data-[state=active]:bg-slate-800 data-[state=active]:text-white">States</TabsTrigger>
          <TabsTrigger value="cities" className="data-[state=active]:bg-slate-800 data-[state=active]:text-white">Cities</TabsTrigger>
        </TabsList>
        
        <TabsContent value="countries" className="focus-visible:outline-none"><CountriesTab /></TabsContent>
        <TabsContent value="states" className="focus-visible:outline-none"><StatesTab /></TabsContent>
        <TabsContent value="cities" className="focus-visible:outline-none"><CitiesTab /></TabsContent>
      </Tabs>
    </div>
  )
}
