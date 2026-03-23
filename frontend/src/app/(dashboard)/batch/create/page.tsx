"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { toast } from "sonner"
import { useRouter } from "next/navigation"
import { useEffect } from "react"
import api from "@/lib/api"

export default function CreateBatchPage() {
  const router = useRouter()
  const [categories, setCategories] = useState<any[]>([])
  const [cities, setCities] = useState<any[]>([])
  const [selectedCategory, setSelectedCategory] = useState<string>("")
  const [searchCity, setSearchCity] = useState("")
  const [selectedCities, setSelectedCities] = useState<string[]>([])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [loading, setLoading] = useState(true)

  const [newCatName, setNewCatName] = useState("")
  const [isCreatingCat, setIsCreatingCat] = useState(false)
  
  const [newCityName, setNewCityName] = useState("")
  const [newCityState, setNewCityState] = useState("")
  const [newCityCountry, setNewCityCountry] = useState("Mexico")
  const [isCreatingCity, setIsCreatingCity] = useState(false)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [catsRes, citiesRes] = await Promise.all([
          api.get<any[]>('/api/categories'),
          api.get<any[]>('/api/cities')
        ])
        setCategories(catsRes || [])
        setCities(citiesRes || [])
      } catch (e: any) {
        toast.error("Failed to fetch initial data")
        setCategories([])
        setCities([])
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  const filteredCities = cities.filter(c => 
    (c.name || "").toLowerCase().includes(searchCity.toLowerCase()) ||
    (c.state || "").toLowerCase().includes(searchCity.toLowerCase())
  )

  const handleSelectAll = () => {
    if (selectedCities.length === filteredCities.length) {
      setSelectedCities([])
    } else {
      setSelectedCities(filteredCities.map(c => c.id))
    }
  }

  const handleClear = () => {
    setSelectedCities([])
    setSearchCity("")
  }

  const toggleCity = (id: string) => {
    setSelectedCities(prev => 
      prev.includes(id) ? prev.filter(c => c !== id) : [...prev, id]
    )
  }

  const handleSubmit = async () => {
    if (!selectedCategory) return toast.error("Please select a category")
    if (selectedCities.length === 0) return toast.error("Please select at least one city")

    setIsSubmitting(true)
    try {
      await Promise.all(
        selectedCities.map(cityId => 
          api.post("/api/jobs", {
            category_id: Number(selectedCategory),
            city_id: Number(cityId)
          })
        )
      )
      
      toast.success(`Successfully queued ${selectedCities.length} jobs!`)
      router.push("/batch/jobs")
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to create batch")
      setIsSubmitting(false)
    }
  }

  const handleCreateCategory = async () => {
    if (!newCatName.trim()) return
    setIsCreatingCat(true)
    try {
      const res = await api.post<any>('/api/categories', { name: newCatName.trim() })
      setCategories([...categories, res])
      setSelectedCategory(res.id.toString())
      setNewCatName("")
      toast.success("Category created and selected")
    } catch (e: any) {
      toast.error(e.message || "Failed to create category")
    } finally {
      setIsCreatingCat(false)
    }
  }

  const handleCreateCity = async () => {
    if (!newCityName.trim() || !newCityState.trim() || !newCityCountry.trim()) return toast.error("Name, State and Country required")
    setIsCreatingCity(true)
    try {
      const res = await api.post<any>('/api/cities', { 
        name: newCityName.trim(), 
        state: newCityState.trim(),
        country: newCityCountry.trim()
      })
      setCities([...cities, res])
      setSelectedCities([...selectedCities, res.id.toString()])
      setNewCityName("")
      setNewCityState("")
      setNewCityCountry("Mexico")
      toast.success("City created and selected")
    } catch (e: any) {
      toast.error(e.message || "Failed to create city")
    } finally {
      setIsCreatingCity(false)
    }
  }

  const categoryName = categories.find(c => c.id.toString() === selectedCategory)?.name || "Category"

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-white">Create Batch Builder</h1>
        <p className="text-slate-400 mt-2">Deploy scraping jobs across multiple cities for a single category.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-6">
          <Card className="bg-slate-900 border-slate-800">
            <CardHeader>
              <CardTitle className="text-white">1. Select Target Category</CardTitle>
            </CardHeader>
            <CardContent>
              <Select value={selectedCategory} onValueChange={(value) => setSelectedCategory(value || "")}>
                <SelectTrigger className="w-full bg-slate-950 border-slate-700">
                  <SelectValue placeholder="Select a category..." />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 border-slate-800 text-white">
                  {loading ? (
                    <SelectItem value="loading" disabled>Loading categories...</SelectItem>
                  ) : (
                    categories.map(c => (
                      <SelectItem key={c.id} value={c.id.toString()} className="hover:bg-slate-800/50 cursor-pointer">
                        {c.name}
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
              
              <div className="mt-6 pt-4 border-t border-slate-800 space-y-3">
                <Label className="text-slate-400 text-xs uppercase tracking-wider">Or create a new category</Label>
                <div className="flex space-x-2">
                  <Input 
                    placeholder="e.g. Restaurants" 
                    value={newCatName} 
                    onChange={e => setNewCatName(e.target.value)}
                    className="bg-slate-950 border-slate-700 h-9"
                  />
                  <Button onClick={handleCreateCategory} disabled={isCreatingCat || !newCatName} size="sm" variant="secondary" className="h-9">
                    {isCreatingCat ? "..." : "Add"}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-900 border-slate-800">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-white">2. Select Target Cities</CardTitle>
              <div className="space-x-2">
                <Button variant="outline" size="sm" onClick={handleSelectAll} className="border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-white">
                  {selectedCities.length === filteredCities.length && filteredCities.length > 0 ? 'Deselect All' : 'Select All'}
                </Button>
                <Button variant="ghost" size="sm" onClick={handleClear} className="text-slate-400 hover:text-red-400">
                  Clear
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <Input
                placeholder="Search existing cities..."
                value={searchCity}
                onChange={(e) => setSearchCity(e.target.value)}
                className="bg-slate-950 border-slate-700 focus-visible:ring-blue-500 mb-2"
              />
              
              <div className="flex space-x-2 bg-slate-900 p-3 rounded-md border border-slate-800 mb-4">
                <Input 
                  placeholder="New City Name" 
                  value={newCityName} 
                  onChange={e => setNewCityName(e.target.value)}
                  className="bg-slate-950 border-slate-700 h-9 flex-1"
                />
                <Input 
                  placeholder="State (e.g. TX, Guerrero)" 
                  value={newCityState} 
                  onChange={e => setNewCityState(e.target.value)}
                  className="bg-slate-950 border-slate-700 h-9 w-32"
                />
                <Input 
                  placeholder="Country" 
                  value={newCityCountry} 
                  onChange={e => setNewCityCountry(e.target.value)}
                  className="bg-slate-950 border-slate-700 h-9 w-32"
                />
                <Button onClick={handleCreateCity} disabled={isCreatingCity || !newCityName || !newCityState || !newCityCountry} size="sm" variant="secondary" className="h-9">
                  {isCreatingCity ? "..." : "Add"}
                </Button>
              </div>
              
              <div className="h-72 overflow-y-auto border border-slate-800 rounded-md p-4 space-y-3 bg-slate-950/50">
                    {loading ? (
                      <div className="flex items-center space-x-3 p-3 text-slate-500 italic">
                        Loading cities...
                      </div>
                    ) : filteredCities.length === 0 ? (
                  <p className="text-center text-slate-500 py-10">No cities match your search.</p>
                ) : (
                  filteredCities.map(city => (
                    <div key={city.id} className="flex items-center space-x-3 bg-slate-900 p-2 rounded hover:bg-slate-800/50 transition-colors">
                      <Checkbox 
                        id={`city-${city.id}`} 
                        checked={selectedCities.includes(city.id)}
                        onCheckedChange={() => toggleCity(city.id)}
                        className="border-slate-600 data-[state=checked]:bg-blue-600 data-[state=checked]:border-blue-600"
                      />
                      <Label 
                        htmlFor={`city-${city.id}`}
                        className="flex-1 cursor-pointer font-medium text-slate-200"
                      >
                        {city.name} <span className="text-slate-500 text-sm ml-2">{city.state}</span>
                      </Label>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="md:col-span-1">
          <Card className="bg-slate-900 border-slate-800 sticky top-6">
            <CardHeader>
              <CardTitle className="text-white">Deployment Summary</CardTitle>
              <CardDescription className="text-slate-400">Review your batch settings</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <Label className="text-slate-500 text-xs uppercase tracking-wider">Target Category</Label>
                <p className="font-medium text-lg text-white mt-1">
                  {selectedCategory ? categoryName : <span className="text-slate-600 italic">None selected</span>}
                </p>
              </div>
              
              <div className="border-t border-slate-800 pt-4">
                <Label className="text-slate-500 text-xs uppercase tracking-wider">Cities Targeted</Label>
                <p className="font-bold text-3xl text-blue-500 mt-1">{selectedCities.length}</p>
              </div>

              <div className="border-t border-slate-800 pt-4 bg-blue-950/20 p-4 rounded-lg">
                <Label className="text-blue-400/80 text-xs uppercase tracking-wider">Jobs to create</Label>
                <div className="flex items-baseline space-x-2 mt-1">
                  <span className="font-bold text-4xl text-white">
                    {selectedCategory && selectedCities.length > 0 ? selectedCities.length : 0}
                  </span>
                  <span className="text-blue-400 text-sm">jobs</span>
                </div>
              </div>
            </CardContent>
            <CardFooter>
              <Button 
                onClick={handleSubmit} 
                disabled={isSubmitting || !selectedCategory || selectedCities.length === 0}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-6"
              >
                {isSubmitting ? "Queueing Jobs..." : "Launch Batch Scraper"}
              </Button>
            </CardFooter>
          </Card>
        </div>
      </div>
    </div>
  )
}
