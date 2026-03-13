"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Terminal, ShieldAlert } from "lucide-react"

const MOCK_LOGS = [
  { id: 1, time: "2026-03-10 10:05:22", level: "INFO", message: "Worker 1 acknowledged job batch #45", service: "worker" },
  { id: 2, time: "2026-03-10 10:04:10", level: "ERROR", message: "Timeout waiting for Chromium to launch (chat_id: scalio_bot)", service: "playwright" },
  { id: 3, time: "2026-03-10 10:01:45", level: "INFO", message: "Admin user 987654321 logged in via OTP", service: "auth" },
  { id: 4, time: "2026-03-10 09:55:00", level: "WARN", message: "City Monterrey has no active proxy assigned", service: "scraper" },
  { id: 5, time: "2026-03-10 09:00:00", level: "INFO", message: "Master Switch set to ON", service: "engine" },
]

export default function AdminLogsPage() {
  return (
    <div className="space-y-6 max-w-6xl mx-auto mt-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
            System Logs
            <Badge className="bg-purple-600 hover:bg-purple-700 text-white border-none text-xs">ADMIN ONLY</Badge>
          </h1>
          <p className="text-slate-400 mt-2">Live stream of all backend services, workers, and API events.</p>
        </div>
      </div>

      <Card className="bg-slate-950 border-slate-800 overflow-hidden shadow-2xl">
        <CardHeader className="bg-slate-900 border-b border-slate-800 pb-4">
          <CardTitle className="text-white text-lg flex items-center gap-2 font-mono">
            <Terminal className="w-5 h-5" /> bash (bastion-core-platform)
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="h-[600px] overflow-y-auto p-4 space-y-2 font-mono text-sm">
            {MOCK_LOGS.map(log => (
              <div key={log.id} className="flex items-start gap-4 hover:bg-slate-900/50 p-1 -mx-2 px-2 rounded">
                <span className="text-slate-500 shrink-0">{log.time}</span>
                <span className={`shrink-0 font-bold w-14 ${
                  log.level === 'ERROR' ? 'text-red-500' :
                  log.level === 'WARN' ? 'text-yellow-500' :
                  'text-blue-500'
                }`}>
                  [{log.level}]
                </span>
                <span className="text-slate-400 shrink-0 font-bold w-20">
                  {log.service}
                </span>
                <span className={log.level === 'ERROR' ? 'text-red-400' : 'text-slate-300'}>
                  {log.message}
                </span>
              </div>
            ))}
            <div className="flex items-center gap-4 p-1 mt-4">
              <span className="h-4 w-2 bg-slate-400 animate-pulse" />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
