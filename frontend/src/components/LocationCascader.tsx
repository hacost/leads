/* eslint-disable react-hooks/set-state-in-effect, react-hooks/exhaustive-deps */
"use client"

import { useState, useEffect } from "react"
import { Label } from "@/components/ui/label"
import { toast } from "sonner"
import api from "@/lib/api"

interface Country { id: number; name: string }
interface State   { id: number; name: string; country_id: number }
interface City    { id: number; name: string; state_id: number; state_name?: string }

interface LocationCascaderProps {
  /** Callback invocado con el city_id seleccionado (o null si se deseleccionó) */
  onCitySelected: (cityId: number | null) => void
  /** ID de ciudad preseleccionada (opcional, para edición) */
  defaultCityId?: number | null
}

/**
 * LocationCascader — Selects encadenados País → Estado → Ciudad.
 * Llama a /api/countries al montar, luego /api/states?country_id=X,
 * luego /api/cities?state_id=Y conforme el usuario selecciona.
 */
export default function LocationCascader({ onCitySelected, defaultCityId }: LocationCascaderProps) {
  const [countries, setCountries] = useState<Country[]>([])
  const [states,    setStates]    = useState<State[]>([])
  const [cities,    setCities]    = useState<City[]>([])

  const [selectedCountry, setSelectedCountry] = useState<string>("")
  const [selectedState,   setSelectedState]   = useState<string>("")
  const [selectedCity,    setSelectedCity]     = useState<string>(defaultCityId?.toString() ?? "")

  const [loadingCountries, setLoadingCountries] = useState(true)
  const [loadingStates,    setLoadingStates]    = useState(false)
  const [loadingCities,    setLoadingCities]    = useState(false)

  // 1. Fetch countries on mount
  useEffect(() => {
    setLoadingCountries(true)
    api.get<Country[]>("/api/countries")
      .then(data => setCountries(data || []))
      .catch(() => toast.error("Failed to load countries"))
      .finally(() => setLoadingCountries(false))
  }, [])

  // 2. Fetch states when country changes
  useEffect(() => {
    if (!selectedCountry) { setStates([]); setSelectedState(""); return }
    setLoadingStates(true)
    setStates([])
    setSelectedState("")
    setCities([])
    setSelectedCity("")
    onCitySelected(null)
    api.get<State[]>(`/api/states?country_id=${selectedCountry}`)
      .then(data => setStates(data || []))
      .catch(() => toast.error("Failed to load states"))
      .finally(() => setLoadingStates(false))
  }, [selectedCountry])

  // 3. Fetch cities when state changes
  useEffect(() => {
    if (!selectedState) { setCities([]); setSelectedCity(""); return }
    setLoadingCities(true)
    setCities([])
    setSelectedCity("")
    onCitySelected(null)
    api.get<City[]>(`/api/cities?state_id=${selectedState}`)
      .then(data => setCities(data || []))
      .catch(() => toast.error("Failed to load cities"))
      .finally(() => setLoadingCities(false))
  }, [selectedState])

  const handleCityChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value
    setSelectedCity(val)
    onCitySelected(val ? Number(val) : null)
  }

  const selectClass = "w-full bg-slate-950 border border-slate-700 text-slate-300 text-sm rounded-md p-2 outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"

  return (
    <div className="space-y-3">
      {/* País */}
      <div className="space-y-1">
        <Label htmlFor="lc-country" className="text-slate-400 text-xs uppercase tracking-wider">
          Country
        </Label>
        <select
          id="lc-country"
          aria-label="country"
          value={selectedCountry}
          onChange={e => setSelectedCountry(e.target.value)}
          disabled={loadingCountries}
          className={selectClass}
        >
          <option value="">{loadingCountries ? "Loading..." : "Select country..."}</option>
          {countries.map(c => (
            <option key={c.id} value={c.id.toString()}>{c.name}</option>
          ))}
        </select>
      </div>

      {/* Estado */}
      <div className="space-y-1">
        <Label htmlFor="lc-state" className="text-slate-400 text-xs uppercase tracking-wider">
          State
        </Label>
        <select
          id="lc-state"
          aria-label="state"
          value={selectedState}
          onChange={e => setSelectedState(e.target.value)}
          disabled={!selectedCountry || loadingStates}
          className={selectClass}
        >
          <option value="">{loadingStates ? "Loading..." : "Select state..."}</option>
          {states.map(s => (
            <option key={s.id} value={s.id.toString()}>{s.name}</option>
          ))}
        </select>
      </div>

      {/* Ciudad */}
      <div className="space-y-1">
        <Label htmlFor="lc-city" className="text-slate-400 text-xs uppercase tracking-wider">
          City
        </Label>
        <select
          id="lc-city"
          aria-label="city"
          value={selectedCity}
          onChange={handleCityChange}
          disabled={!selectedState || loadingCities}
          className={selectClass}
        >
          <option value="">{loadingCities ? "Loading..." : "Select city..."}</option>
          {cities.map(c => (
            <option key={c.id} value={c.id.toString()}>{c.name}</option>
          ))}
        </select>
      </div>
    </div>
  )
}
