"use client"

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
// Progress import removed — using custom div-based progress bars to avoid Turbopack selector issues
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Eye, RotateCcw } from "lucide-react"
import Link from "next/link"
import { useEffect, useState } from "react"
import api from "@/lib/api"
import { formatDistanceToNow } from "date-fns"

export default function JobsPage() {
  const [jobs, setJobs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState("all")
  const [search, setSearch] = useState("")
  
  // Pagination State
  const [page, setPage] = useState(0)
  const [limit, setLimit] = useState(10)

  const fetchJobs = async () => {
    try {
      const offset = page * limit
      const data = await api.get<any[]>(`/api/jobs?limit=${limit}&offset=${offset}`)
      setJobs(data || [])
    } catch (err) {
      console.error(err)
    } finally {
      if (loading) setLoading(false)
    }
  }

  const handleRetry = async (jobId: number) => {
    try {
      await api.patch(`/api/jobs/${jobId}/retry`, {})
      fetchJobs() // Refresh list
    } catch (err) {
      console.error("Failed to retry job:", err)
    }
  }

  useEffect(() => {
    fetchJobs()
    const interval = setInterval(fetchJobs, 10000)
    return () => clearInterval(interval)
  }, [page, limit]) // Refetch on page or limit change

  const filteredJobs = jobs.filter(job => {
    const rawStatus = job.status === 'processing' ? 'running' : job.status;
    if (statusFilter !== "all" && rawStatus !== statusFilter) return false
    const matchStr = search.toLowerCase()
    if (search && !(job.category_name || '').toLowerCase().includes(matchStr) && !(job.city_name || '').toLowerCase().includes(matchStr)) return false
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
        <div className="flex-1 flex items-center gap-4">
          <Input 
            placeholder="Search by category or city..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-slate-950 border-slate-700 max-w-sm"
          />
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 whitespace-nowrap">Show:</span>
            <select 
              value={limit} 
              onChange={(e) => { setLimit(Number(e.target.value)); setPage(0); }}
              className="bg-slate-950 border-slate-700 text-slate-300 text-sm rounded-md p-2 outline-none focus:ring-1 focus:ring-blue-500"
            >
              {[10, 20, 30, 50, 100].map(v => (
                <option key={v} value={v}>{v}</option>
              ))}
            </select>
          </div>
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
            {loading ? (
              <TableRow>
                <TableCell colSpan={6} className="h-32 text-center text-slate-500">
                  Loading jobs from Bastion Core API...
                </TableCell>
              </TableRow>
            ) : filteredJobs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="h-32 text-center text-slate-500">
                  No jobs found matching your filters.
                </TableCell>
              </TableRow>
            ) : (
              filteredJobs.map((job) => {
                const uiStatus = job.status === 'processing' ? 'running' : job.status;
                return (
                <TableRow key={job.id} className="border-slate-800 hover:bg-slate-800/30 transition-colors">
                  <TableCell className="font-medium text-slate-200">{job.category_name}</TableCell>
                  <TableCell className="text-slate-300">{job.city_name}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className={
                      uiStatus === 'completed' ? 'border-green-500/50 text-green-400 bg-green-500/10' :
                      uiStatus === 'running' ? 'border-blue-500/50 text-blue-400 bg-blue-500/10' :
                      uiStatus === 'pending' ? 'border-yellow-500/50 text-yellow-500 bg-yellow-500/10' :
                      'border-red-500/50 text-red-400 bg-red-500/10'
                    }>
                      {uiStatus.toUpperCase()}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {uiStatus === 'running' ? (
                      <div className="flex items-center gap-3">
                        <div className="relative h-2 w-full overflow-hidden rounded-full bg-slate-800">
                          <div className="h-full bg-blue-500 w-full animate-pulse" />
                        </div>
                      </div>
                    ) : uiStatus === 'completed' ? (
                      <div className="relative h-2 w-full overflow-hidden rounded-full bg-slate-800">
                        <div className="h-full w-full bg-green-500" />
                      </div>
                    ) : uiStatus === 'failed' ? (
                      <div className="relative h-2 w-full overflow-hidden rounded-full bg-slate-800">
                        <div className="h-full bg-red-500 w-full" />
                      </div>
                    ) : (
                      <span className="text-xs text-slate-500 italic">Waiting...</span>
                    )}
                  </TableCell>
                  <TableCell className="text-slate-400 text-sm">
                    {job.created_at ? formatDistanceToNow(new Date(job.created_at + "Z"), { addSuffix: true }) : 'Unknown'}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      {uiStatus === 'failed' && (
                        <Button 
                          variant="ghost" 
                          size="icon" 
                          className="h-8 w-8 text-orange-400 hover:text-orange-300 hover:bg-orange-400/10" 
                          title="Retry Job"
                          onClick={() => handleRetry(job.id)}
                        >
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
              )})
            )}
          </TableBody>
        </Table>
      </div>

      <div className="flex items-center justify-between px-2">
        <p className="text-sm text-slate-500">
          Showing page {page + 1}
        </p>
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            size="sm" 
            className="bg-slate-900 border-slate-800 text-white disabled:opacity-50"
            onClick={() => setPage(p => Math.max(0, p - 1))}
            disabled={page === 0}
          >
            Previous
          </Button>
          <Button 
            variant="outline" 
            size="sm" 
            className="bg-slate-900 border-slate-800 text-white disabled:opacity-50"
            onClick={() => setPage(p => p + 1)}
            disabled={jobs.length < limit}
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  )
}
