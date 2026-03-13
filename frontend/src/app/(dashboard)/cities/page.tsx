"use client"

import { useState } from "react"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Plus, Edit2, Trash2, Globe } from "lucide-react"

const MOCK_CITIES = [
  { id: "1", name: "Monterrey", state: "NL", country: "Mexico", active: true },
  { id: "2", name: "Guadalajara", state: "JAL", country: "Mexico", active: true },
  { id: "3", name: "Puebla", state: "PUE", country: "Mexico", active: true },
  { id: "4", name: "Mexico City", state: "CDMX", country: "Mexico", active: true },
  { id: "5", name: "Tijuana", state: "BC", country: "Mexico", active: false },
]

export default function MasterCitiesPage() {
  const [search, setSearch] = useState("")

  const filteredCities = MOCK_CITIES.filter(c => 
    c.name.toLowerCase().includes(search.toLowerCase()) || 
    c.state.toLowerCase().includes(search.toLowerCase())
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
        <Button className="bg-blue-600 hover:bg-blue-700 text-white">
          <Plus className="w-4 h-4 mr-2" /> Add Master City
        </Button>
      </div>

      <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex items-center gap-4">
        <Input 
          placeholder="Search by city or state..." 
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="bg-slate-950 border-slate-700 max-w-sm"
        />
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <Table>
          <TableHeader className="bg-slate-950/50">
            <TableRow className="border-slate-800 hover:bg-transparent">
              <TableHead className="text-slate-400">City</TableHead>
              <TableHead className="text-slate-400">State / Region</TableHead>
              <TableHead className="text-slate-400">Country</TableHead>
              <TableHead className="text-slate-400">Status</TableHead>
              <TableHead className="text-slate-400 text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredCities.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="h-32 text-center text-slate-500">
                  No cities found.
                </TableCell>
              </TableRow>
            ) : (
              filteredCities.map((city) => (
                <TableRow key={city.id} className="border-slate-800 hover:bg-slate-800/50">
                  <TableCell className="font-semibold text-slate-200 flex items-center gap-2">
                    <Globe className="w-4 h-4 text-slate-500" /> {city.name}
                  </TableCell>
                  <TableCell className="text-slate-300">{city.state}</TableCell>
                  <TableCell className="text-slate-400">{city.country}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className={city.active ? "border-green-500/50 text-green-400 bg-green-500/10" : "border-slate-500 text-slate-400"}>
                      {city.active ? "ACTIVE" : "INACTIVE"}
                    </Badge>
                  </TableCell>
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
