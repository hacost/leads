"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Power, Activity, Server, ShieldAlert } from "lucide-react"
import { toast } from "sonner"

export default function MasterControlPage() {
  const [isEngineOn, setIsEngineOn] = useState(false)
  const [isToggling, setIsToggling] = useState(false)

  const stats = {
    pending: 142,
    running: 0,
    completed: 890,
  }

  const handleToggle = async () => {
    setIsToggling(true)
    try {
      // await api.post("/admin/engine", { status: !isEngineOn ? "START" : "STOP" })
      setTimeout(() => {
        setIsEngineOn(!isEngineOn)
        toast.success(
          !isEngineOn 
            ? "Scraping Engine STARTED. Workers are now consuming the queue." 
            : "Scraping Engine STOPPED. Workers will finish their current job and halt."
        )
        setIsToggling(false)
      }, 1000)
    } catch (error) {
      toast.error("Failed to toggle Master Engine")
      setIsToggling(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-8 mt-10">
      <div className="text-center space-y-2">
        <h1 className="text-4xl font-extrabold tracking-tight text-white uppercase flex items-center justify-center gap-3">
          <ShieldAlert className="text-red-500 h-8 w-8" />
          Master Control
          <ShieldAlert className="text-red-500 h-8 w-8" />
        </h1>
        <p className="text-slate-400">Global execution switch for the Bastion Core Scraping Engine</p>
      </div>

      <Card className={`border-2 transition-colors duration-500 ${isEngineOn ? 'border-green-500/50 bg-green-950/10' : 'border-slate-800 bg-slate-900'}`}>
        <CardContent className="pt-10 pb-10 flex flex-col items-center justify-center space-y-8">
          <div className="flex flex-col items-center justify-center space-y-4">
            <Button
              onClick={handleToggle}
              disabled={isToggling}
              className={`h-40 w-40 rounded-full flex flex-col items-center justify-center shadow-2xl transition-all duration-300 ${
                isEngineOn 
                  ? 'bg-red-600 hover:bg-red-700 shadow-red-500/20' 
                  : 'bg-green-600 hover:bg-green-700 shadow-green-500/20'
              }`}
            >
              <Power className={`h-16 w-16 mb-2 ${isToggling ? 'animate-pulse' : ''}`} />
              <span className="font-bold text-lg tracking-widest uppercase">
                {isToggling ? 'WAIT' : isEngineOn ? 'STOP' : 'START'}
              </span>
            </Button>
            <div className={`text-xl font-bold uppercase tracking-widest ${isEngineOn ? 'text-green-500' : 'text-slate-500'}`}>
              Engine is {isEngineOn ? 'ONLINE' : 'OFFLINE'}
            </div>
            {isEngineOn && (
              <p className="text-green-400/80 text-sm animate-pulse flex items-center gap-2">
                <Activity className="h-4 w-4" /> Workers are currently consuming the queue
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-3 gap-4">
        <Card className="bg-slate-900 border-slate-800 text-center">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs uppercase tracking-wider text-slate-500">Pending</CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-3xl font-bold text-yellow-500">{stats.pending}</span>
          </CardContent>
        </Card>
        
        <Card className="bg-slate-900 border-slate-800 text-center relative overflow-hidden">
          {isEngineOn && <div className="absolute inset-x-0 bottom-0 h-1 bg-blue-500 animate-pulse" />}
          <CardHeader className="pb-2">
            <CardTitle className="text-xs uppercase tracking-wider text-slate-500">Running</CardTitle>
          </CardHeader>
          <CardContent>
            <span className={`text-3xl font-bold ${isEngineOn ? 'text-blue-500' : 'text-slate-600'}`}>
              {isEngineOn ? 3 : 0}
            </span>
          </CardContent>
        </Card>

        <Card className="bg-slate-900 border-slate-800 text-center">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs uppercase tracking-wider text-slate-500">Completed Today</CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-3xl font-bold text-green-500">{stats.completed}</span>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
