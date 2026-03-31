"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { toast } from "sonner"
import { useRouter } from "next/navigation"
import api from "@/lib/api"
import { Info, Rocket } from "lucide-react"

interface Country { id: number; name: string }
interface State { id: number; name: string; country_id: number }
interface City { id: number; name: string; state_id: number }

export default function CreateBatchPage() {
  const router = useRouter()
  const [categories, setCategories] = useState<Array<{ id: number, name: string }>>([])
  const [selectedCategory, setSelectedCategory] = useState<string>("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [loadingCats, setLoadingCats] = useState(false)

  const [newCatName, setNewCatName] = useState("")
  const [isCreatingCat, setIsCreatingCat] = useState(false)

  // Scope Settings
  const [scope, setScope] = useState<'city' | 'state' | 'global'>('city')

  // Location Data
  const [countries, setCountries] = useState<Country[]>([])
  const [states, setStates] = useState<State[]>([])
  const [cities, setCities] = useState<City[]>([])

  const [selectedCountry, setSelectedCountry] = useState<string>("")
  const [selectedState, setSelectedState] = useState<string>("")
  const [selectedCity, setSelectedCity] = useState<string>("")

  // State mode (all or manual)
  const [stateMode, setStateMode] = useState<'all' | 'manual'>('all')
  const [manualCities, setManualCities] = useState<number[]>([])

  // Global mode confirmed
  const [globalConfirmed, setGlobalConfirmed] = useState(false)
  const [totalCitiesDB, setTotalCitiesDB] = useState<number>(0)

  // Load total cities for accurate global counts
  useEffect(() => {
    api.get<City[]>('/api/cities?limit=10000')
      .then(res => setTotalCitiesDB(res?.length || 0))
      .catch(() => { })
  }, [])

  // Load Categories on mount
  useEffect(() => {
    setLoadingCats(true)
    api.get<Array<{ id: number, name: string }>>('/api/categories?limit=100')
      .then(res => setCategories(res || []))
      .catch(() => toast.error("Failed to load categories"))
      .finally(() => setLoadingCats(false))
  }, [])

  // Load Countries on mount
  useEffect(() => {
    api.get<Country[]>("/api/countries")
      .then(res => setCountries(res || []))
      .catch(() => toast.error("Failed to load countries"))
  }, [])

  // Load States whenever country changes
  useEffect(() => {
    if (!selectedCountry) {
      setStates([]); setSelectedState(""); setCities([]); setSelectedCity("");
      return
    }
    api.get<State[]>(`/api/states?country_id=${selectedCountry}`)
      .then(res => {
        setStates(res || [])
      })
      .catch(() => toast.error("Failed to load states"))
  }, [selectedCountry])

  // Load Cities whenever state changes
  useEffect(() => {
    if (!selectedState) {
      setCities([]); setSelectedCity(""); setManualCities([]);
      return
    }
    api.get<City[]>(`/api/cities?state_id=${selectedState}`)
      .then(res => {
        setCities(res || [])
        setManualCities((res || []).map(c => c.id))
      })
      .catch(() => toast.error("Failed to load cities"))
  }, [selectedState])

  const handleCreateCategory = async () => {
    if (!newCatName.trim()) return
    setIsCreatingCat(true)
    try {
      const res = await api.post<{ id: number, name: string }>('/api/categories', { name: newCatName.trim() })
      setCategories([...categories, res])
      setSelectedCategory(res.id.toString())
      setNewCatName("")
      toast.success("Category created and selected")
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Failed to create category"
      toast.error(msg)
    } finally {
      setIsCreatingCat(false)
    }
  }

  const toggleCityCheck = (cityId: number) => {
    if (manualCities.includes(cityId)) {
      setManualCities(prev => prev.filter(id => id !== cityId))
    } else {
      setManualCities(prev => [...prev, cityId])
    }
  }

  const calculateTotalJobs = () => {
    if (scope === 'city') return selectedCity ? 1 : 0
    if (scope === 'state') return stateMode === 'all' ? cities.length : manualCities.length
    if (scope === 'global') return globalConfirmed ? totalCitiesDB : 0
    return 0
  }

  const isFormValid = () => {
    if (!selectedCategory) return false
    const count = calculateTotalJobs()
    if (count === 0) return false
    if (scope === 'city' && !selectedCity) return false
    if (scope === 'state' && !selectedState) return false
    if (scope === 'global' && !globalConfirmed) return false
    return true
  }

  const handleSubmit = async () => {
    if (!isFormValid()) return
    setIsSubmitting(true)
    const catId = Number(selectedCategory)

    try {
      if (scope === 'city') {
        await api.post("/api/jobs", { category_id: catId, city_id: Number(selectedCity) })
        toast.success("Job queued successfully!")
      }
      else if (scope === 'state') {
        if (stateMode === 'all') {
          await api.post("/api/jobs/batch", { category_id: catId, state_id: Number(selectedState) })
          toast.success("State-wide batch jobs queued!")
        } else {
          // Manual mode: call individual POST /api/jobs
          await Promise.all(manualCities.map(cId =>
            api.post("/api/jobs", { category_id: catId, city_id: cId })
          ))
          toast.success(`${manualCities.length} jobs queued!`)
        }
      }
      else if (scope === 'global') {
        await api.post("/api/jobs/batch", { category_id: catId, all_cities: true })
        toast.success("National batch jobs queued!")
      }

      router.push("/batch/jobs")
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to create jobs")
      setIsSubmitting(false)
    }
  }

  const categoryName = categories.find(c => c.id.toString() === selectedCategory)?.name || "None"
  const totalJobs = calculateTotalJobs()
  const targetLabel = scope === 'city'
    ? (cities.find(c => c.id.toString() === selectedCity)?.name || "Select city...")
    : scope === 'state'
      ? (stateMode === 'all' ? `All cities in ${states.find(s => s.id.toString() === selectedState)?.name || 'state'}` : `${manualCities.length} selected in ${states.find(s => s.id.toString() === selectedState)?.name || 'state'}`)
      : (globalConfirmed ? `All ${totalCitiesDB} cities mapping the database` : "Confirm national scope")

  return (
    <div className="max-w-6xl mx-auto mb-10 text-slate-50 font-sans">
      <div className="flex flex-col md:flex-row justify-between items-end mb-8 space-y-4 md:space-y-0">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight bg-clip-text text-transparent bg-linear-to-r from-white to-slate-400">
            Create Batch Builder
          </h1>
          <p className="text-slate-400 mt-2 font-medium">Deploy scraping jobs across multiple targets for a single category.</p>
        </div>
        <div>
          <span className="bg-linear-to-r from-blue-500 to-violet-500 text-white px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider shadow-lg shadow-blue-500/20">
            Pro Enterprise
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <div className="lg:col-span-8 space-y-6">

          {/* CATEGORY CARD */}
          <Card className="bg-[#0f172a] border-slate-800 shadow-xl shadow-black/20 rounded-2xl overflow-hidden">
            <CardHeader className="pb-4">
              <CardTitle className="text-lg flex items-center gap-3 text-white">
                <span className="flex items-center justify-center w-6 h-6 rounded-full bg-blue-500 text-xs text-white">1</span>
                Target Category
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label className="text-xs font-semibold text-slate-400 uppercase tracking-widest">Search & Select Category</Label>
                <Select value={selectedCategory} onValueChange={(value) => setSelectedCategory(value || "")}>
                  <SelectTrigger className="w-full bg-[#020617] border-slate-800 h-12 text-sm rounded-xl">
                    <SelectValue placeholder="Select a category..." />
                  </SelectTrigger>
                  <SelectContent className="bg-[#0f172a] border-slate-800 text-white rounded-xl">
                    {loadingCats ? (
                      <SelectItem value="loading" disabled>Loading categories...</SelectItem>
                    ) : (
                      categories.map(c => (
                        <SelectItem key={c.id} value={c.id.toString()} className="hover:bg-slate-800/50 cursor-pointer py-2">
                          {c.name}
                        </SelectItem>
                      ))
                    )}
                  </SelectContent>
                </Select>
              </div>

              <div className="pt-5 border-t border-slate-800/50 space-y-3">
                <Label className="text-xs font-semibold text-slate-400 uppercase tracking-widest">Or create new</Label>
                <div className="flex space-x-2">
                  <Input
                    placeholder="New Category Name..."
                    value={newCatName}
                    onChange={e => setNewCatName(e.target.value)}
                    className="bg-[#020617] border-slate-800 h-11 text-sm rounded-xl px-4"
                  />
                  <Button
                    onClick={handleCreateCategory}
                    disabled={isCreatingCat || !newCatName}
                    className="h-11 px-6 rounded-xl bg-slate-700 hover:bg-slate-600 font-semibold"
                  >
                    {isCreatingCat ? "..." : "Add"}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* TARGETING CARD */}
          <Card className="bg-[#0f172a] border-slate-800 shadow-xl shadow-black/20 rounded-2xl overflow-hidden">
            <CardHeader className="pb-4">
              <CardTitle className="text-lg flex items-center gap-3 text-white">
                <span className="flex items-center justify-center w-6 h-6 rounded-full bg-blue-500 text-xs text-white">2</span>
                Targeting Scope
              </CardTitle>
            </CardHeader>
            <CardContent>

              <div className="flex p-1 space-x-1 bg-[#020617] border border-slate-800 rounded-xl mb-8">
                {['city', 'state', 'global'].map(tab => (
                  <button
                    key={tab}
                    onClick={() => setScope(tab as 'city' | 'state' | 'global')}
                    className={`flex-1 py-2.5 text-sm font-semibold rounded-lg transition-all duration-200 ${scope === tab
                        ? 'bg-[#0f172a] text-white shadow-md border border-slate-800/80'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
                      }`}
                  >
                    {tab === 'city' ? 'Specific City' : tab === 'state' ? 'State-wide Selection' : 'National Coverage'}
                  </button>
                ))}
              </div>

              <div className="space-y-6">
                {scope !== 'global' && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label className="text-xs font-semibold text-slate-400 uppercase tracking-widest">Country</Label>
                      <Select value={selectedCountry} onValueChange={(val) => setSelectedCountry(val || "")}>
                        <SelectTrigger className="w-full bg-[#020617] border-slate-800 h-11 text-sm rounded-xl">
                          <SelectValue placeholder="Select country..." />
                        </SelectTrigger>
                        <SelectContent className="bg-[#0f172a] border-slate-800 text-white rounded-xl">
                          {countries.map(c => (
                            <SelectItem key={c.id} value={c.id.toString()}>{c.name}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label className="text-xs font-semibold text-slate-400 uppercase tracking-widest">
                        {scope === 'city' ? "State" : "Target State"}
                      </Label>
                      <Select value={selectedState} onValueChange={(val) => setSelectedState(val || "")} disabled={!selectedCountry}>
                        <SelectTrigger className="w-full bg-[#020617] border-slate-800 h-11 text-sm rounded-xl">
                          <SelectValue placeholder="Select state..." />
                        </SelectTrigger>
                        <SelectContent className="bg-[#0f172a] border-slate-800 text-white rounded-xl">
                          {states.map(s => (
                            <SelectItem key={s.id} value={s.id.toString()}>{s.name}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                )}

                {/* Scope = City */}
                {scope === 'city' && (
                  <div className="space-y-2 pt-2">
                    <Label className="text-xs font-semibold text-slate-400 uppercase tracking-widest">City</Label>
                    <Select value={selectedCity} onValueChange={(val) => setSelectedCity(val || "")} disabled={!selectedState}>
                      <SelectTrigger className="w-full bg-[#020617] border-slate-800 h-11 text-sm rounded-xl">
                        <SelectValue placeholder="Select city..." />
                      </SelectTrigger>
                      <SelectContent className="bg-[#0f172a] border-slate-800 text-white rounded-xl">
                        {cities.map(c => (
                          <SelectItem key={c.id} value={c.id.toString()}>{c.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}

                {/* Scope = State */}
                {scope === 'state' && selectedState && (
                  <div className="pt-4 border-t border-slate-800/50">
                    <Label className="text-xs font-semibold text-slate-400 uppercase tracking-widest block mb-4">Choose Selection Mode</Label>
                    <div className="flex gap-6 mb-6">
                      <label className="flex items-center gap-3 cursor-pointer text-sm font-medium">
                        <input
                          type="radio"
                          className="w-4 h-4 text-blue-500 border-slate-700 bg-black"
                          checked={stateMode === 'all'}
                          onChange={() => setStateMode('all')}
                        />
                        All cities in state
                      </label>
                      <label className="flex items-center gap-3 cursor-pointer text-sm font-medium">
                        <input
                          type="radio"
                          className="w-4 h-4 text-blue-500 border-slate-700 bg-black"
                          checked={stateMode === 'manual'}
                          onChange={() => setStateMode('manual')}
                        />
                        Manual selection
                      </label>
                    </div>

                    {stateMode === 'manual' && (
                      <div className="bg-[#020617] border border-slate-800 rounded-xl overflow-hidden mt-2">
                        <div className="bg-blue-900/10 px-4 py-3 border-b border-slate-800 flex justify-between items-center">
                          <span className="text-sm font-medium text-slate-300">Select cities to include:</span>
                          <button
                            type="button"
                            onClick={() => setManualCities(manualCities.length === cities.length ? [] : cities.map(c => c.id))}
                            className="text-xs font-bold text-blue-400 hover:text-blue-300 transition-colors uppercase"
                          >
                            {manualCities.length === cities.length ? 'Deselect All' : 'Select All'}
                          </button>
                        </div>
                        <div className="max-h-56 overflow-y-auto custom-scrollbar">
                          {cities.map(city => (
                            <label key={city.id} className="flex items-center gap-3 px-4 py-3 border-b border-slate-800/60 hover:bg-slate-900/80 cursor-pointer transition-colors">
                              <input
                                type="checkbox"
                                className="w-4 h-4 rounded text-blue-500"
                                checked={manualCities.includes(city.id)}
                                onChange={() => toggleCityCheck(city.id)}
                              />
                              <span className="text-sm">{city.name}</span>
                            </label>
                          ))}
                          {cities.length === 0 && <div className="p-4 text-slate-500 text-sm text-center">No cities available in this state.</div>}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Scope = Global */}
                {scope === 'global' && (
                  <div className="space-y-6 pt-2">
                    <div className="bg-amber-900/10 border border-amber-900/30 rounded-xl flex gap-4 p-4">
                      <Rocket className="text-amber-500 w-6 h-6 shrink-0 mt-0.5" />
                      <div>
                        <h4 className="font-bold text-amber-500 text-sm">Full National Deployment</h4>
                        <p className="text-slate-300 text-sm mt-1">This will automatically select all <strong>{totalCitiesDB}</strong> cities verified in the database.</p>
                      </div>
                    </div>

                    <div className="bg-blue-900/10 border border-slate-800 rounded-xl p-5">
                      <label className="flex items-center gap-4 cursor-pointer">
                        <input
                          type="checkbox"
                          className="w-5 h-5 rounded border-slate-700"
                          checked={globalConfirmed}
                          onChange={(e) => setGlobalConfirmed(e.target.checked)}
                        />
                        <span className="text-sm font-medium text-slate-200">
                          <strong className="text-white">Confirm:</strong> Target every available city in the database for this category.
                        </span>
                      </label>
                    </div>
                  </div>
                )}

              </div>
            </CardContent>
          </Card>
        </div>

        {/* SUMMARY SIDEBAR */}
        <div className="lg:col-span-4">
          <Card className="bg-linear-to-b from-[#0f172a] to-[#020617] border-slate-800 sticky top-6 shadow-xl shadow-black/30 rounded-2xl overflow-hidden">
            <CardHeader className="pb-2">
              <CardTitle className="text-xl font-bold text-white">Deployment Summary</CardTitle>
              <CardDescription className="text-slate-400">Estimated results</CardDescription>
            </CardHeader>
            <CardContent className="space-y-5 pt-4">

              <div className="bg-blue-500/5 border border-blue-500/20 rounded-xl p-5 relative overflow-hidden">
                <div className="absolute -right-4 -top-4 w-24 h-24 bg-blue-500/10 rounded-full blur-2xl"></div>
                <Label className="text-[11px] font-bold text-blue-400 uppercase tracking-widest">Impact Volume</Label>
                <div className="text-5xl font-black mt-2 text-white font-serif tracking-tight">{totalJobs}</div>
                <div className="text-xs text-slate-400 mt-2 font-medium">Total independent jobs to queue</div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="bg-white/5 border border-white/5 rounded-xl p-3">
                  <Label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Category</Label>
                  <div className="text-sm font-bold text-slate-200 mt-1 truncate">{categoryName}</div>
                </div>
                <div className="bg-white/5 border border-white/5 rounded-xl p-3">
                  <Label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Scope</Label>
                  <div className="text-sm font-bold text-slate-200 mt-1">
                    {scope === 'city' ? 'Single City' : scope === 'state' ? 'State-wide' : 'National'}
                  </div>
                </div>
              </div>

              <div className="bg-white/5 border border-white/5 rounded-xl p-4">
                <Label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Target Area</Label>
                <div className="text-sm font-medium text-slate-300 mt-1.5 leading-snug">
                  {targetLabel}
                </div>
              </div>

              <div className="flex items-start gap-3 bg-emerald-500/5 border border-emerald-500/20 p-3 rounded-xl">
                <Info className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" />
                <p className="text-xs text-emerald-400/90 font-medium my-auto leading-relaxed">
                  Jobs are processed sequentially at a safe rate to avoid proxy bans.
                </p>
              </div>

            </CardContent>
            <CardFooter className="pt-2 pb-6">
              <Button
                onClick={handleSubmit}
                disabled={isSubmitting || !isFormValid()}
                className="w-full h-14 bg-blue-600 hover:bg-blue-500 text-white font-bold text-base shadow-lg shadow-blue-600/25 transition-all rounded-xl disabled:opacity-50"
              >
                {isSubmitting ? "Queueing Jobs..." : "Launch Batch Job"}
              </Button>
            </CardFooter>
          </Card>
        </div>
      </div>
    </div>
  )
}
