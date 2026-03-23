"use client"

import { useState, useEffect } from "react"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Download, FileJson, Building2, MapPin, Phone, Star } from "lucide-react"
import api from "@/lib/api"

interface Lead {
  name: string
  phone: string
  address: string
  stars: number
  reviews: number
}

export default function JobResultsPage({ params }: { params: { job_id: string } }) {
  const [search, setSearch] = useState("")
  const [leads, setLeads] = useState<Lead[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchLeads = async () => {
      try {
        const data = await api.get<Lead[]>(`/api/leads/${params.job_id}`)
        setLeads(data)
      } catch (error) {
        console.error("Error fetching leads:", error)
      } finally {
        setLoading(false)
      }
    }
    fetchLeads()
  }, [params.job_id])

  const filteredResults = leads.filter(r => 
    r.name.toLowerCase().includes(search.toLowerCase()) || 
    r.phone.includes(search)
  )

  const handleExportCSV = () => {
    // Logic to download as CSV goes here
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Scraped Results</h1>
          <p className="text-slate-400 mt-2">Displaying leads obtained from Job #{params.job_id || "123"}</p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" className="border-slate-700 bg-slate-900 text-white hover:bg-slate-800" onClick={handleExportCSV}>
            <FileJson className="w-4 h-4 mr-2 text-yellow-500" /> Export JSON
          </Button>
          <Button className="bg-green-600 hover:bg-green-700 text-white" onClick={handleExportCSV}>
            <Download className="w-4 h-4 mr-2" /> Export CSV
          </Button>
        </div>
      </div>

      <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex items-center gap-4">
        <Input 
          placeholder="Search by business name or phone..." 
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="bg-slate-950 border-slate-700 max-w-md"
        />
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <Table>
          <TableHeader className="bg-slate-950/50">
            <TableRow className="border-slate-800 hover:bg-transparent">
              <TableHead className="text-slate-400 font-semibold w-1/3">Business Name</TableHead>
              <TableHead className="text-slate-400 font-semibold">Phone Number</TableHead>
              <TableHead className="text-slate-400 font-semibold">Address</TableHead>
              <TableHead className="text-slate-400 font-semibold text-right">Reputation</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={4} className="h-48 text-center text-slate-500">
                  Loading leads...
                </TableCell>
              </TableRow>
            ) : filteredResults.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="h-48 text-center text-slate-500">
                  No leads found. Job might still be running or encountered an error.
                </TableCell>
              </TableRow>
            ) : (
              filteredResults.map((result, idx) => (
                <TableRow key={idx} className="border-slate-800 hover:bg-slate-800/30">
                  <TableCell className="font-semibold text-slate-200">
                    <div className="flex items-start gap-3">
                      <Building2 className="w-5 h-5 text-blue-500 shrink-0 mt-0.5" />
                      <span>{result.name}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2 text-slate-300">
                      <Phone className="w-4 h-4 text-slate-500" />
                      {result.phone}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2 text-slate-400 text-sm">
                      <MapPin className="w-4 h-4 shrink-0" />
                      <span className="truncate max-w-[200px]">{result.address}</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1 text-slate-200">
                      <Star className="w-4 h-4 fill-yellow-500 text-yellow-500" />
                      <span className="font-bold">{(result.stars || 0).toFixed(1)}</span>
                      <span className="text-slate-500 text-xs ml-1">({result.reviews || 0})</span>
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
