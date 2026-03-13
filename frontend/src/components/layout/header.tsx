"use client"

import { useAuthStore } from "@/lib/store"
import { Button } from "@/components/ui/button"
import { LogOut } from "lucide-react"

export function Header() {
  const { user, logout } = useAuthStore()

  return (
    <header className="flex h-14 shrink-0 items-center justify-between gap-2 border-b border-border bg-card px-4">
      <div className="flex items-center gap-2">
        <h1 className="text-sm font-medium">Platform Dashboard</h1>
      </div>
      <div className="flex items-center gap-4">
        <span className="text-sm text-muted-foreground">
          Logged in as: <strong className="text-foreground">{user?.chat_id}</strong> ({user?.role})
        </span>
        <Button variant="ghost" size="icon" onClick={() => logout()}>
          <LogOut className="h-4 w-4" />
        </Button>
      </div>
    </header>
  )
}
