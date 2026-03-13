"use client"

import { useState } from "react"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
// Progress import removed — using custom div-based progress bars to avoid Turbopack selector issues
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Eye, RotateCcw } from "lucide-react"
import Link from "next/link"

const MOCK_JOBS = [
  { id: "job_1", category: "Dentists", city: "Monterrey", status: "running", progress: 45, created: "2026-03-10 10:00" },
  { id: "job_2", category: "Hardware Stores", city: "Guadalajara", status: "pending", progress: 0, created: "2026-03-10 11:30" },
  { id: "job_3", category: "Plumbers", city: "Puebla", status: "completed", progress: 100, created: "2026-03-10 09:15" },
  { id: "job_4", category: "Spas", city: "Mexico City", status: "failed", progress: 12, created: "2026-03-10 08:00" },
  { id: "job_5", category: "Dentists", city: "Cancun", status: "pending", progress: 0, created: "2026-03-10 12:45" },
]

export default function JobsPage() {
  const [statusFilter, setStatusFilter] = useState("all")
  const [search, setSearch] = useState("")

  const filteredJobs = MOCK_JOBS.filter(job => {
    if (statusFilter !== "all" && job.status !== statusFilter) return false
    if (search && !job.category.toLowerCase().includes(search.toLowerCase()) && !job.city.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Scraping Queue Monitor</h1>
          <p className="text-slate-400 mt-2">Track and manage your batch scraping jobs in real-time.</p>
        </div>
        <Link href="/batch/create">
          <Button className="bg-blue-600 hover:bg-blue-700 text-white">Create New Batch</Button>
        </Link>
      </div>

      <div className="flex flex-col sm:flex-row gap-4 bg-slate-900 border border-slate-800 p-4 rounded-xl">
        <div className="flex-1">
          <Input 
            placeholder="Search by category or city..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-slate-950 border-slate-700 max-w-sm"
          />
        </div>
        <Select value={statusFilter} onValueChange={(value) => setStatusFilter(value || "all")}>
          <SelectTrigger className="w-[180px] bg-slate-950 border-slate-700">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent className="bg-slate-900 border-slate-800">
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="running">Running</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <Table>
          <TableHeader className="bg-slate-950/50">
            <TableRow className="border-slate-800">
              <TableHead className="text-slate-400 font-semibold">Category</TableHead>
              <TableHead className="text-slate-400 font-semibold">City</TableHead>
              <TableHead className="text-slate-400 font-semibold">Status</TableHead>
              <TableHead className="text-slate-400 font-semibold w-1/4">Progress</TableHead>
              <TableHead className="text-slate-400 font-semibold">Created</TableHead>
              <TableHead className="text-slate-400 font-semibold text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredJobs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="h-32 text-center text-slate-500">
                  No jobs found matching your filters.
                </TableCell>
              </TableRow>
            ) : (
              filteredJobs.map((job) => (
                <TableRow key={job.id} className="border-slate-800 hover:bg-slate-800/30 transition-colors">
                  <TableCell className="font-medium text-slate-200">{job.category}</TableCell>
                  <TableCell className="text-slate-300">{job.city}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className={
                      job.status === 'completed' ? 'border-green-500/50 text-green-400 bg-green-500/10' :
                      job.status === 'running' ? 'border-blue-500/50 text-blue-400 bg-blue-500/10' :
                      job.status === 'pending' ? 'border-yellow-500/50 text-yellow-500 bg-yellow-500/10' :
                      'border-red-500/50 text-red-400 bg-red-500/10'
                    }>
                      {job.status.toUpperCase()}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {job.status === 'running' ? (
                      <div className="flex items-center gap-3">
                        <div className="relative h-2 w-full overflow-hidden rounded-full bg-slate-800">
                          <div className="h-full bg-blue-500 transition-all" style={{ width: `${job.progress}%` }} />
                        </div>
                        <span className="text-xs text-blue-400 font-medium w-8">{job.progress}%</span>
                      </div>
                    ) : job.status === 'completed' ? (
                      <div className="relative h-2 w-full overflow-hidden rounded-full bg-slate-800">
                        <div className="h-full w-full bg-green-500" />
                      </div>
                    ) : job.status === 'failed' ? (
                      <div className="relative h-2 w-full overflow-hidden rounded-full bg-slate-800">
                        <div className="h-full bg-red-500 transition-all" style={{ width: `${job.progress}%` }} />
                      </div>
                    ) : (
                      <span className="text-xs text-slate-500 italic">Waiting...</span>
                    )}
                  </TableCell>
                  <TableCell className="text-slate-400 text-sm">{job.created}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      {job.status === 'failed' && (
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-orange-400 hover:text-orange-300 hover:bg-orange-400/10" title="Retry Job">
                          <RotateCcw className="h-4 w-4" />
                        </Button>
                      )}
                      <Link href={`/batch/jobs/${job.id}`}>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-slate-400 hover:text-white hover:bg-slate-800" title="View Details">
                          <Eye className="h-4 w-4" />
                        </Button>
                      </Link>
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
