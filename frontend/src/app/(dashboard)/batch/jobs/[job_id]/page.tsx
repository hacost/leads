"use client"
import React, { useState, useEffect } from 'react'

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { MapPin, Briefcase, Clock, CheckCircle2, Loader2, Activity, AlertCircle } from "lucide-react"
import { formatDistanceToNow } from 'date-fns'
import api from '@/lib/api'

// Replicating basic type layout
interface JobDetail {
  id: number;
  category_id: number;
  city_id: number;
  status: string;
  created_at: string;
  category_name: string;
  city_name: string;
}

export default function JobDetailPage({ params }: { params: Promise<{ job_id: string }> }) {
  const unwrappedParams = React.use(params)
  const [job, setJob] = useState<JobDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isMounted, setIsMounted] = useState(false)

  const fetchJob = async () => {
    try {
      const res = await api.get<JobDetail>(`/api/jobs/${unwrappedParams.job_id}`)
      setJob(res)
      setError(null)
    } catch (e: any) {
      setError(e.message || "Failed to load job details")
    } finally {
      if (loading) setLoading(false)
    }
  }

  useEffect(() => {
    setIsMounted(true)
    fetchJob()
    // Poll every 10 seconds if not completed/failed
    const interval = setInterval(() => {
      if (job && (job.status === 'completed' || job.status === 'failed')) return;
      fetchJob();
    }, 10000)
    return () => clearInterval(interval)
  }, [unwrappedParams.job_id, job?.status])

  if (loading) {
    return <div className="p-8 text-center text-slate-400">Loading Job Data...</div>
  }

  if (error || !job) {
    return <div className="p-8 text-center text-red-500">Error: {error || "Job not found"}</div>
  }

  const isRunning = job.status === 'processing' || job.status === 'running'
  const isPending = job.status === 'pending'
  const isDone = job.status === 'completed'
  const isFailed = job.status === 'failed'

  let statusBadge
  if (isPending) statusBadge = <Badge variant="outline" className="px-3 py-1 text-sm border-yellow-500/50 text-yellow-400 bg-yellow-500/10"><Clock className="w-3 h-3 mr-2" /> PENDING</Badge>
  else if (isRunning) statusBadge = <Badge variant="outline" className="px-3 py-1 text-sm border-blue-500/50 text-blue-400 bg-blue-500/10"><Loader2 className="w-3 h-3 mr-2 animate-spin" /> RUNNING</Badge>
  else if (isDone) statusBadge = <Badge variant="outline" className="px-3 py-1 text-sm border-green-500/50 text-green-500 bg-green-500/10"><CheckCircle2 className="w-3 h-3 mr-2" /> COMPLETED</Badge>
  else statusBadge = <Badge variant="outline" className="px-3 py-1 text-sm border-red-500/50 text-red-500 bg-red-500/10"><AlertCircle className="w-3 h-3 mr-2" /> FAILED</Badge>

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
            Job Details 
            <Badge variant="outline" className="text-xs font-mono bg-slate-800 text-slate-400 border-none">
              #{job.id}
            </Badge>
          </h1>
        </div>
        {statusBadge}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="bg-slate-900 border-slate-800 md:col-span-1">
          <CardHeader>
            <CardTitle className="text-white text-lg">Metrics</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <p className="text-sm font-medium text-slate-500 flex items-center gap-2 mb-1">
                <Briefcase className="w-4 h-4" /> Category
              </p>
              <p className="text-lg text-slate-200 font-semibold">{job.category_name}</p>
            </div>
            
            <div>
              <p className="text-sm font-medium text-slate-500 flex items-center gap-2 mb-1">
                <MapPin className="w-4 h-4" /> City
              </p>
              <p className="text-lg text-slate-200 font-semibold">{job.city_name}</p>
            </div>

            <div>
              <p className="text-sm font-medium text-slate-500 flex items-center gap-2 mb-1">
                <Clock className="w-4 h-4" /> Started At
              </p>
              <p className="text-base text-slate-200 font-semibold">
                {isMounted && job.created_at ? new Date(job.created_at + "Z").toLocaleString() : (!isMounted && job.created_at ? '...' : 'N/A')}
              </p>
            </div>

            <div className="pt-4 border-t border-slate-800">
              <p className="text-sm font-medium text-slate-400 flex items-center gap-2 mb-1">
                 Results Delivered
              </p>
              <p className="text-lg text-white font-medium">Via Telegram</p>
              <p className="text-xs text-slate-500 mt-1">(Check chat for raw files)</p>
            </div>
          </CardContent>
        </Card>

        <div className="md:col-span-3 space-y-6">
          <Card className="bg-slate-900 border-slate-800">
            <CardHeader>
              <CardTitle className="text-white text-lg">Execution Progress</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">{isDone ? "Extraction Finished" : isFailed ? "Extraction Failed" : "Scraping in progress..."}</span>
                  <span className={isDone ? "text-green-500 font-bold" : isFailed ? "text-red-500 font-bold" : "text-blue-400 font-bold"}>
                    {isDone ? "100%" : isPending ? "0%" : isFailed ? "Halted" : "75%"}
                  </span>
                </div>
                <div className="relative h-4 w-full overflow-hidden rounded-full bg-slate-800">
                  <div className={`h-full transition-all ${isDone ? 'bg-green-500' : isFailed ? 'bg-red-500' : 'bg-blue-600'}`} style={{ width: isDone ? '100%' : isPending ? '5%' : isFailed ? '100%' : '75%' }} />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-900 border-slate-800">
            <CardHeader>
              <CardTitle className="text-white text-lg flex items-center gap-2">
                <Activity className="w-5 h-5" /> Live Event Timeline
              </CardTitle>
              <CardDescription className="text-slate-400">Status checkpoint stream</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="relative border-l border-slate-800 ml-3 space-y-6 pb-4">
                
                <div className="mb-6 ml-6 relative">
                  <span className="absolute -left-8 top-1 h-4 w-4 rounded-full border-4 border-slate-900 bg-slate-500" />
                  <span className="text-xs px-2 py-1 rounded bg-slate-800 text-slate-400 font-mono">
                    {isMounted && job.created_at ? formatDistanceToNow(new Date(job.created_at + "Z"), { addSuffix: true }) : (!isMounted && job.created_at ? '...' : 'N/A')}
                  </span>
                  <p className="mt-2 text-slate-300">
                    Job requested. Inserted into the Worker Database Queue.
                  </p>
                </div>

                {(isRunning || isDone || isFailed) && (
                  <div className="mb-6 ml-6 relative">
                    <span className="absolute -left-8 top-1 h-4 w-4 rounded-full border-4 border-slate-900 bg-blue-500" />
                    <span className="text-xs px-2 py-1 rounded bg-slate-800 text-slate-400 font-mono">
                      Running
                    </span>
                    <p className="mt-2 text-slate-300">
                      Job picked up by Scraper Worker. Chrome instance launched.
                    </p>
                  </div>
                )}

                {isDone && (
                  <div className="mb-6 ml-6 relative">
                    <span className="absolute -left-8 top-1 h-4 w-4 rounded-full border-4 border-slate-900 bg-green-500" />
                    <span className="text-xs px-2 py-1 rounded bg-slate-800 text-slate-400 font-mono">
                      Finished
                    </span>
                    <p className="mt-2 text-slate-300">
                      Files exported to disk and sent successfully via Telegram Bot. Job Concluded.
                    </p>
                  </div>
                )}

                {isFailed && (
                  <div className="mb-6 ml-6 relative">
                    <span className="absolute -left-8 top-1 h-4 w-4 rounded-full border-4 border-slate-900 bg-red-500" />
                    <span className="text-xs px-2 py-1 rounded bg-slate-800 text-slate-400 font-mono">
                      Terminated
                    </span>
                    <p className="mt-2 text-red-400">
                      An unhandled error occurred during Lead extraction in the Worker Loop.
                    </p>
                  </div>
                )}

                {isRunning && (
                  <div className="mb-6 ml-6 relative">
                    <span className="absolute -left-[33px] top-1 h-5 w-5 rounded-full border-4 border-slate-900 bg-blue-600 animate-pulse flex items-center justify-center" />
                    <span className="text-xs px-2 py-1 rounded bg-blue-900/30 text-blue-400 font-mono font-semibold">
                      Live
                    </span>
                    <p className="mt-2 text-slate-400 italic">
                      Waiting for the process to conclude...
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
