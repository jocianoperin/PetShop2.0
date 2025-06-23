"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Plus, Calendar, PawPrint, Hotel, DollarSign, X } from "lucide-react"
import { cn } from "@/lib/utils"

interface MobileFabProps {
  currentPage: string
  onAction: (action: string) => void
}

const fabActions: Record<string, Array<{ id: string; label: string; icon: any; color: string }>> = {
  dashboard: [
    { id: "new-appointment", label: "Agendamento", icon: Calendar, color: "bg-blue-500" },
    { id: "new-pet", label: "Pet", icon: PawPrint, color: "bg-green-500" },
    { id: "new-checkin", label: "Check-in", icon: Hotel, color: "bg-purple-500" },
    { id: "new-transaction", label: "Transação", icon: DollarSign, color: "bg-orange-500" },
  ],
  agenda: [{ id: "new-appointment", label: "Agendamento", icon: Calendar, color: "bg-blue-500" }],
  pets: [{ id: "new-pet", label: "Novo Pet", icon: PawPrint, color: "bg-green-500" }],
  hotel: [{ id: "new-checkin", label: "Check-in", icon: Hotel, color: "bg-purple-500" }],
  financeiro: [{ id: "new-transaction", label: "Transação", icon: DollarSign, color: "bg-orange-500" }],
}

export function MobileFab({ currentPage, onAction }: MobileFabProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const actions = fabActions[currentPage] || []

  if (actions.length === 0) return null

  const handleAction = (actionId: string) => {
    onAction(actionId)
    setIsExpanded(false)
  }

  return (
    <div className="fixed bottom-20 right-4 z-40 lg:hidden">
      {/* Action Buttons */}
      {isExpanded && (
        <div className="flex flex-col gap-3 mb-3">
          {actions.map((action, index) => {
            const Icon = action.icon
            return (
              <div
                key={action.id}
                className="flex items-center gap-3 animate-in slide-in-from-bottom-2 duration-200"
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <div className="bg-white dark:bg-gray-800 px-3 py-2 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700">
                  <span className="text-sm font-medium text-gray-900 dark:text-white">{action.label}</span>
                </div>
                <Button
                  size="icon"
                  className={cn("w-12 h-12 rounded-2xl shadow-lg", action.color)}
                  onClick={() => handleAction(action.id)}
                >
                  <Icon className="w-5 h-5 text-white" />
                </Button>
              </div>
            )
          })}
        </div>
      )}

      {/* Main FAB */}
      <Button
        size="icon"
        className="w-14 h-14 rounded-2xl shadow-lg bg-gradient-to-r from-cyan-500 to-orange-500 hover:from-cyan-600 hover:to-orange-600"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        {isExpanded ? <X className="w-6 h-6 text-white" /> : <Plus className="w-6 h-6 text-white" />}
      </Button>
    </div>
  )
}
