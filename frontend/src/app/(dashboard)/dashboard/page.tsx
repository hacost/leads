"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Activity, CheckCircle, Clock, AlertTriangle, PlayCircle, ToggleRight, ToggleLeft } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

import { useState, useEffect } from "react"
import api from "@/lib/api"
import { formatDistanceToNow } from "date-fns"

export default function DashboardPage() {
  const [jobs, setJobs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [masterSwitch, setMasterSwitch] = useState(true)
  const [workerHealth, setWorkerHealth] = useState({ status: 'offline', last_heartbeat: null })
  const [toggling, setToggling] = useState(false)
  const [isMounted, setIsMounted] = useState(false)
  const [lastSync, setLastSync] = useState<Date | null>(null)

  const fetchDashboardData = async () => {
    try {
      const results = await Promise.allSettled([
        api.get<any[]>('/api/jobs'),
        api.get<{is_enabled: boolean}>('/api/admin/worker'),
        api.get<{status: string, last_heartbeat: any}>('/api/admin/worker/health')
      ])
      
      if (results[0].status === 'fulfilled') setJobs(results[0].value || [])
      if (results[1].status === 'fulfilled') setMasterSwitch(results[1].value.is_enabled)
      if (results[2].status === 'fulfilled') setWorkerHealth(results[2].value)
      
      setLastSync(new Date())
      setError(null)
    } catch (err: any) {
      setError(err?.message || "Failed to load dashboard data")
    } finally {
      if (loading) setLoading(false)
    }
  }

  const toggleMasterSwitch = async () => {
    setToggling(true)
    try {
      const resp = await api.patch<{is_enabled: boolean}>('/api/admin/worker', { is_enabled: !masterSwitch })
      setMasterSwitch(resp.is_enabled)
      // Force immediate refresh of health status to show 'offline' faster
      await fetchDashboardData()
    } catch (err: any) {
      alert("Failed to toggle Master Switch: " + (err?.message || "Unknown error"))
    } finally {
      setToggling(false)
    }
  }

  useEffect(() => {
    setIsMounted(true)
    fetchDashboardData()
    const interval = setInterval(fetchDashboardData, 5000) // Reduced to 5s for real-time feel
    return () => clearInterval(interval)
  }, [])

  const stats = {
    pending: jobs.filter(j => j.status === 'pending').length,
    running: jobs.filter(j => j.status === 'processing' || j.status === 'running').length,
    completed: jobs.filter(j => j.status === 'completed').length,
    errors: jobs.filter(j => j.status === 'failed').length
  }

  const recentJobs = [...jobs].sort((a, b) => {
    return new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime()
  }).slice(0, 5)

  if (loading) {
    return <div className="p-8 text-center text-slate-400">Loading dashboard data...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight text-white">Dashboard Overview</h1>
        {lastSync && (
          <div className="flex items-center gap-2 text-[10px] text-slate-500 font-medium uppercase tracking-widest bg-slate-900/50 px-3 py-1.5 rounded-full border border-slate-800">
            <div className="h-1.5 w-1.5 rounded-full bg-green-500 animate-pulse" />
            Live Sync: {lastSync.toLocaleTimeString()}
          </div>
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <Card className="bg-slate-900 border-slate-800 relative overflow-hidden">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-400">Master Switch</CardTitle>
            <Activity className={`h-4 w-4 ${masterSwitch ? 'text-green-500 animate-pulse' : 'text-slate-600'}`} />
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className={`text-2xl font-bold ${masterSwitch ? 'text-green-500' : 'text-slate-500'}`}>
                {toggling ? '...' : (masterSwitch ? 'ON' : 'OFF')}
              </div>
              <button 
                onClick={toggleMasterSwitch} 
                disabled={toggling}
                className={`transition-all duration-300 transform active:scale-95 ${toggling ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                {masterSwitch ? (
                  <ToggleRight className="h-10 w-10 text-green-500 fill-green-500/20" />
                ) : (
                  <ToggleLeft className="h-10 w-10 text-slate-600" />
                )}
              </button>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              {masterSwitch ? "Worker is active and polling." : "Worker is currently paused."}
            </p>
            <div className="mt-3 pt-3 border-t border-slate-800 flex items-center justify-between">
              <span className="text-[10px] uppercase tracking-wider text-slate-500 font-bold">Worker Status</span>
              <Badge variant="outline" className={`text-[10px] ${
                (masterSwitch && workerHealth.status === 'online') ? 'border-green-500/50 text-green-400 bg-green-500/10' : 'border-red-500/50 text-red-400 bg-red-500/10'
              }`}>
                {(masterSwitch && workerHealth.status === 'online') ? 'ONLINE' : 'OFFLINE'}
              </Badge>
            </div>
          </CardContent>
          {masterSwitch && <div className="absolute bottom-0 left-0 h-1 w-full bg-green-500/20 animate-shimmer" />}
        </Card>

        <Card className="bg-slate-900 border-slate-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-400">Jobs Pending</CardTitle>
            <Clock className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{stats.pending}</div>
            <p className="text-xs text-slate-500 mt-1">In queue</p>
          </CardContent>
        </Card>

        <Card className="bg-slate-900 border-slate-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-400">Jobs Running</CardTitle>
            <PlayCircle className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{stats.running}</div>
            <p className="text-xs text-slate-500 mt-1">Active scrapers</p>
          </CardContent>
        </Card>

        <Card className="bg-slate-900 border-slate-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-400">Completed Today</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{stats.completed}</div>
            <p className="text-xs text-slate-500 mt-1">Successfully scraped</p>
          </CardContent>
        </Card>

        <Card className="bg-slate-900 border-slate-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-400">Errors Today</CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{stats.errors}</div>
            <p className="text-xs text-slate-500 mt-1">Failed execution</p>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-slate-900 border-slate-800">
        <CardHeader>
          <CardTitle className="text-white">Recent Activities</CardTitle>
        </CardHeader>
        <CardContent>
          {error ? (
            <div className="text-red-400 py-4">{error}</div>
          ) : recentJobs.length === 0 ? (
            <div className="text-slate-500 py-4">No jobs found. Create one.</div>
          ) : (
          <Table>
            <TableHeader>
              <TableRow className="border-slate-800 hover:bg-transparent">
                <TableHead className="text-slate-400">Category</TableHead>
                <TableHead className="text-slate-400">City</TableHead>
                <TableHead className="text-slate-400">Status</TableHead>
                <TableHead className="text-slate-400 text-right">Created</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {recentJobs.map((job) => (
                <TableRow key={job.id} className="border-slate-800 hover:bg-slate-800/50">
                  <TableCell className="font-medium text-slate-200">{job.category_name}</TableCell>
                  <TableCell className="text-slate-300">{job.city_name}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className={
                      job.status === 'completed' ? 'border-green-500 text-green-500' :
                      (job.status === 'running' || job.status === 'processing') ? 'border-blue-500 text-blue-500' :
                      job.status === 'pending' ? 'border-yellow-500 text-yellow-500' :
                      'border-red-500 text-red-500'
                    }>
                      {(job.status === 'processing' ? 'running' : job.status).toUpperCase()}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right text-slate-400">
                    {isMounted && job.created_at ? formatDistanceToNow(new Date(job.created_at + "Z"), { addSuffix: true }) : (!isMounted && job.created_at ? '...' : 'Unknown')}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
