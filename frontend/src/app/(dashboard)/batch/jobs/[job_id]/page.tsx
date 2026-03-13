"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
// Progress import removed — using custom div-based progress bars to avoid Turbopack selector issues
import { MapPin, Briefcase, Clock, CheckCircle2, AlertCircle, Loader2, Activity } from "lucide-react"

// Mock detail data
const MOCK_JOB = {
  id: "job_123",
  category: "Dentists",
  city: "Monterrey, NL",
  status: "running",
  progress: 45,
  startedAt: "10:01 AM",
  resultsFound: 14,
  timeline: [
    { time: "10:01 AM", event: "Job started, inserted into worker queue", type: "info" },
    { time: "10:02 AM", event: "Playwright Chromium browser launched instance", type: "info" },
    { time: "10:04 AM", event: "Navigated to Google Maps & engaged search", type: "info" },
    { time: "10:05 AM", event: "Scraped 7 records from Page 1", type: "success" },
    { time: "10:07 AM", event: "Scrolling & scraping Page 2", type: "info" },
  ]
}

export default function JobDetailPage({ params }: { params: { job_id: string } }) {
  // Real app: fetch job details using params.job_id
  
  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
            Job Details 
            <Badge variant="outline" className="text-xs font-mono bg-slate-800 text-slate-400 border-none">
              #{params.job_id || MOCK_JOB.id}
            </Badge>
          </h1>
        </div>
        <Badge variant="outline" className="px-3 py-1 text-sm border-blue-500/50 text-blue-400 bg-blue-500/10">
          <Loader2 className="w-3 h-3 mr-2 animate-spin" /> RUNNING
        </Badge>
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
              <p className="text-lg text-slate-200 font-semibold">{MOCK_JOB.category}</p>
            </div>
            
            <div>
              <p className="text-sm font-medium text-slate-500 flex items-center gap-2 mb-1">
                <MapPin className="w-4 h-4" /> City
              </p>
              <p className="text-lg text-slate-200 font-semibold">{MOCK_JOB.city}</p>
            </div>

            <div>
              <p className="text-sm font-medium text-slate-500 flex items-center gap-2 mb-1">
                <Clock className="w-4 h-4" /> Started At
              </p>
              <p className="text-lg text-slate-200 font-semibold">{MOCK_JOB.startedAt}</p>
            </div>

            <div className="pt-4 border-t border-slate-800">
              <p className="text-sm font-medium text-blue-400 flex items-center gap-2 mb-1">
                <CheckCircle2 className="w-4 h-4" /> Results Found
              </p>
              <p className="text-4xl text-white font-bold">{MOCK_JOB.resultsFound}</p>
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
                  <span className="text-slate-400">Scraping in progress...</span>
                  <span className="text-blue-400 font-bold">{MOCK_JOB.progress}%</span>
                </div>
                <div className="relative h-4 w-full overflow-hidden rounded-full bg-slate-800">
                  <div className="h-full bg-blue-600 transition-all" style={{ width: `${MOCK_JOB.progress}%` }} />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-900 border-slate-800">
            <CardHeader>
              <CardTitle className="text-white text-lg flex items-center gap-2">
                <Activity className="w-5 h-5" /> Live Event Timeline
              </CardTitle>
              <CardDescription className="text-slate-400">Real-time log stream from the worker</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="relative border-l border-slate-800 ml-3 space-y-6 pb-4">
                {MOCK_JOB.timeline.map((item, i) => (
                  <div key={i} className="mb-6 ml-6 relative">
                    <span className={`absolute -left-8 top-1 h-4 w-4 rounded-full border-4 border-slate-900 ${
                      item.type === 'success' ? 'bg-green-500' : 'bg-blue-500'
                    }`} />
                    <span className="text-xs px-2 py-1 rounded bg-slate-800 text-slate-400 font-mono">
                      {item.time}
                    </span>
                    <p className="mt-2 text-slate-300">
                      {item.event}
                    </p>
                  </div>
                ))}
                
                <div className="mb-6 ml-6 relative">
                  <span className="absolute -left-[33px] top-1 h-5 w-5 rounded-full border-4 border-slate-900 bg-blue-600 animate-pulse flex items-center justify-center" />
                  <span className="text-xs px-2 py-1 rounded bg-blue-900/30 text-blue-400 font-mono font-semibold">
                    Live
                  </span>
                  <p className="mt-2 text-slate-400 italic">
                    Waiting for next event...
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
