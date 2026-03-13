"use client"

import { useState } from "react"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Server, Users } from "lucide-react"

const MOCK_TENANTS = [
  { id: "1", name: "Bastion Core", owner_id: "987654321", activeJobs: 3, totalCategories: 12 },
  { id: "2", name: "Scalio", owner_id: "scalio_bot", activeJobs: 0, totalCategories: 4 },
  { id: "3", name: "AmigoX", owner_id: "amigox_system", activeJobs: 1, totalCategories: 8 },
]

export default function AdminTenantsPage() {
  const [search, setSearch] = useState("")

  const filteredTenants = MOCK_TENANTS.filter(t => 
    t.name.toLowerCase().includes(search.toLowerCase()) ||
    t.owner_id.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-6 max-w-5xl mx-auto mt-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
            Registered Tenants
            <Badge className="bg-purple-600 hover:bg-purple-700 text-white border-none text-xs">ADMIN ONLY</Badge>
          </h1>
          <p className="text-slate-400 mt-2">Manage all active user workspaces and agents using the Bastion Engine.</p>
        </div>
      </div>

      <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex items-center gap-4">
        <Input 
          placeholder="Search by tenant name or owner ID..." 
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="bg-slate-950 border-slate-700 max-w-md"
        />
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <Table>
          <TableHeader className="bg-slate-950/50">
            <TableRow className="border-slate-800 hover:bg-transparent">
              <TableHead className="text-slate-400">Tenant Name</TableHead>
              <TableHead className="text-slate-400">Owner ID / Telegram Chat</TableHead>
              <TableHead className="text-slate-400 text-center">Owned Categories</TableHead>
              <TableHead className="text-slate-400 text-center">Active Jobs in Queue</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredTenants.map((tenant) => (
              <TableRow key={tenant.id} className="border-slate-800 hover:bg-slate-800/50">
                <TableCell className="font-semibold text-slate-200 flex items-center gap-2">
                  <Users className="w-4 h-4 text-slate-500" /> {tenant.name}
                </TableCell>
                <TableCell className="text-slate-400 font-mono text-xs">{tenant.owner_id}</TableCell>
                <TableCell className="text-center text-slate-300 font-bold">{tenant.totalCategories}</TableCell>
                <TableCell className="text-center">
                  <Badge variant="outline" className={tenant.activeJobs > 0 ? "border-blue-500/50 text-blue-400 bg-blue-500/10" : "border-slate-700 text-slate-500"}>
                    {tenant.activeJobs} Jobs
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
