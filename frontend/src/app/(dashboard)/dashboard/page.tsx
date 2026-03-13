"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Activity, CheckCircle, Clock, AlertTriangle, PlayCircle } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

export default function DashboardPage() {
  // In a real app, these would come from React Query `useQuery`
  const stats = {
    masterSwitch: "ON",
    pending: 142,
    running: 3,
    completed: 890,
    errors: 12
  }

  const recentJobs = [
    { id: "1", category: "Dentists", city: "Monterrey", status: "running", created: "10 mins ago" },
    { id: "2", category: "Hardware Stores", city: "Guadalajara", status: "pending", created: "1 hour ago" },
    { id: "3", category: "Plumbers", city: "Puebla", status: "completed", created: "3 hours ago" },
    { id: "4", category: "Spas", city: "Mexico City", status: "failed", created: "5 hours ago" },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight text-white">Dashboard Overview</h1>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-400">Master Switch</CardTitle>
            <Activity className={`h-4 w-4 ${stats.masterSwitch === 'ON' ? 'text-green-500' : 'text-slate-500'}`} />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${stats.masterSwitch === 'ON' ? 'text-green-500' : 'text-slate-500'}`}>
              {stats.masterSwitch}
            </div>
            <p className="text-xs text-slate-500 mt-1">Worker execution state</p>
          </CardContent>
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
                  <TableCell className="font-medium text-slate-200">{job.category}</TableCell>
                  <TableCell className="text-slate-300">{job.city}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className={
                      job.status === 'completed' ? 'border-green-500 text-green-500' :
                      job.status === 'running' ? 'border-blue-500 text-blue-500' :
                      job.status === 'pending' ? 'border-yellow-500 text-yellow-500' :
                      'border-red-500 text-red-500'
                    }>
                      {job.status.toUpperCase()}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right text-slate-400">{job.created}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
