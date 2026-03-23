"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useAuthStore } from "@/lib/store"
import { Home, PlusCircle, List, Folders, MapPin, Database, Activity, ShieldAlert } from "lucide-react"
import { cn } from "@/lib/utils"

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: Home },
  { href: "/batch/create", label: "Create Batch", icon: PlusCircle },
  { href: "/batch/jobs", label: "Jobs Queue", icon: List },
  { href: "/categories", label: "Categories", icon: Folders },
  { href: "/cities", label: "Cities", icon: MapPin },
]

const adminItems = [
  { href: "/admin/control", label: "Master Control", icon: Activity },
  { href: "/admin/tenants", label: "Tenants", icon: Database },
  { href: "/admin/logs", label: "System Logs", icon: ShieldAlert },
]

function NavItem({ href, label, Icon }: { href: string; label: string; Icon: React.ElementType }) {
  const pathname = usePathname()
  const isActive = pathname === href

  return (
    <li>
      <Link
        href={href}
        className={cn(
          "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
          isActive
            ? "bg-sidebar-accent text-sidebar-accent-foreground"
            : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
        )}
      >
        <Icon className="h-4 w-4 shrink-0" />
        <span>{label}</span>
      </Link>
    </li>
  )
}

export function AppSidebar() {
  const user = useAuthStore((state) => state.user)

  return (
    <aside className="hidden md:flex h-screen w-64 flex-col border-r border-border bg-sidebar text-sidebar-foreground shrink-0">
      {/* Brand */}
      <div className="flex items-center gap-2 px-4 py-4 border-b border-border">
        <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-blue-600 text-white font-bold text-sm">
          B
        </div>
        <div className="flex flex-col gap-0.5 leading-none">
          <span className="font-semibold tracking-tight text-white">Bastion Core</span>
          <span className="text-xs text-blue-400">Prospector B2B</span>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto p-2 space-y-4">
        <div>
          <p className="px-3 py-1 text-xs font-medium text-sidebar-foreground/50 uppercase tracking-wider">
            Menu
          </p>
          <ul className="mt-1 space-y-0.5">
            {navItems.map(({ href, label, icon: Icon }) => (
              <NavItem key={href} href={href} label={label} Icon={Icon} />
            ))}
          </ul>
        </div>

        {user?.role === "admin" && (
          <div>
            <p className="px-3 py-1 text-xs font-medium text-sidebar-foreground/50 uppercase tracking-wider">
              Administration
            </p>
            <ul className="mt-1 space-y-0.5">
              {adminItems.map(({ href, label, icon: Icon }) => (
                <NavItem key={href} href={href} label={label} Icon={Icon} />
              ))}
            </ul>
          </div>
        )}
      </nav>
    </aside>
  )
}
