"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { useAuthStore } from "@/lib/store"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { toast } from "sonner"

export default function LoginPage() {
  const [chatId, setChatId] = useState("")
  const [otp, setOtp] = useState("")
  const [step, setStep] = useState<1 | 2>(1)
  const [loading, setLoading] = useState(false)
  const [timeLeft, setTimeLeft] = useState(120)
  const router = useRouter()
  const login = useAuthStore((state) => state.login)

  // Timer effect for OTP
  useState(() => {
    let timer: NodeJS.Timeout
    if (step === 2 && timeLeft > 0) {
      timer = setInterval(() => setTimeLeft((prev) => prev - 1), 1000)
    }
    return () => clearInterval(timer)
  })

  const requestOtp = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!chatId) return toast.error("Please enter your Telegram Chat ID")

    setLoading(true)
    try {
      const res = await fetch("http://localhost:8000/api/auth/request-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chat_id: chatId }),
      })
      
      if (!res.ok) {
        const errorData = await res.json()
        throw new Error(errorData.detail || "Failed to request OTP")
      }

      setStep(2)
      setTimeLeft(300) // 5 minutes validity 
      toast.success("OTP sent to your Telegram")
      setLoading(false)
    } catch (error: any) {
      toast.error(error.message || "Failed to request OTP")
      setLoading(false)
    }
  }

  const verifyOtp = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!otp) return toast.error("Please enter the OTP")

    setLoading(true)
    try {
      const res = await fetch("http://localhost:8000/api/auth/verify-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chat_id: chatId, code: otp }),
      })
      
      if (!res.ok) {
        const errorData = await res.json()
        throw new Error(errorData.detail || "Invalid OTP")
      }

      const data = await res.json()
      // Extract role from token parsing (mock behavior if needed, or proper JWT decode)
      // Usually role is decoded, but for state simplicity we assign 'tenant' or 'admin'
      const role = chatId === '987654321' ? 'admin' : 'tenant'
      
      login({ chat_id: chatId, role }, data.token)
      toast.success("Login successful")
      router.push("/dashboard")
      
    } catch (error: any) {
      toast.error(error.message || "Invalid OTP")
      setLoading(false)
    }
  }

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, "0")
    const s = (seconds % 60).toString().padStart(2, "0")
    return `${m}:${s}`
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-950 p-4">
      <Card className="w-full max-w-sm border-slate-800 bg-slate-900">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold tracking-tight text-center">
            Bastion Core
          </CardTitle>
          <CardDescription className="text-center text-slate-400">
            {step === 1
              ? "Enter your Telegram Chat ID to access the dashboard"
              : "We sent a code to your Telegram"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {step === 1 ? (
            <form onSubmit={requestOtp} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="chatId" className="text-slate-300">Telegram Chat ID</Label>
                <Input
                  id="chatId"
                  placeholder="e.g. 12839128"
                  value={chatId}
                  onChange={(e) => setChatId(e.target.value)}
                  className="bg-slate-950 border-slate-700 focus-visible:ring-blue-500"
                  disabled={loading}
                />
              </div>
              <Button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white" disabled={loading}>
                {loading ? "Sending..." : "Send Code"}
              </Button>
            </form>
          ) : (
            <form onSubmit={verifyOtp} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="otp" className="text-slate-300">Enter OTP</Label>
                <Input
                  id="otp"
                  type="text"
                  placeholder="123456"
                  maxLength={6}
                  value={otp}
                  onChange={(e) => setOtp(e.target.value)}
                  className="bg-slate-950 border-slate-700 text-center tracking-widest text-lg focus-visible:ring-blue-500"
                  disabled={loading}
                />
                <p className="text-xs text-center mt-2 text-slate-400">
                  {timeLeft > 0 ? `Code expires in ${formatTime(timeLeft)}` : <span className="text-red-400">Code expired</span>}
                </p>
              </div>
              <Button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white" disabled={loading || timeLeft === 0}>
                {loading ? "Verifying..." : "Verify"}
              </Button>
              <Button type="button" variant="ghost" className="w-full text-slate-400 hover:text-white" onClick={() => setStep(1)} disabled={loading}>
                Back
              </Button>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
