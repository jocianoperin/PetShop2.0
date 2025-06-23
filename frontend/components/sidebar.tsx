"use client"

import { Button } from "@/components/ui/button"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { cn } from "@/lib/utils"
import {
  Calendar,
  Home,
  Hotel,
  PawPrint,
  Settings,
  FileText,
  Megaphone,
  DollarSign,
  ChevronLeft,
  ChevronRight,
} from "lucide-react"

interface SidebarProps {
  currentPage: string
  onPageChange: (page: string) => void
  isCollapsed: boolean
  onToggleCollapse: () => void
}

const menuItems = [
  { id: "dashboard", label: "Dashboard", icon: Home },
  { id: "financeiro", label: "Financeiro", icon: DollarSign },
  { id: "agenda", label: "Agenda", icon: Calendar },
  { id: "hotel", label: "Hotel", icon: Hotel },
  { id: "pets", label: "Pets", icon: PawPrint },
  { id: "promocoes", label: "Promoções", icon: Megaphone },
  { id: "relatorios", label: "Relatórios", icon: FileText },
  { id: "configuracoes", label: "Configurações", icon: Settings },
]

export function Sidebar({ currentPage, onPageChange, isCollapsed, onToggleCollapse }: SidebarProps) {
  return (
    <TooltipProvider>
      <aside
        className={cn(
          "bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 transition-all duration-300 flex flex-col",
          isCollapsed ? "w-16" : "w-64",
        )}
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className={cn("p-4 border-b border-gray-200 dark:border-gray-800", isCollapsed && "px-2")}>
            <div className="flex items-center justify-between">
              {!isCollapsed && (
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-orange-500 rounded-2xl flex items-center justify-center">
                    <PawPrint className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h2 className="font-bold text-gray-900 dark:text-white">Pet Shop</h2>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Management Suite</p>
                  </div>
                </div>
              )}
              {isCollapsed && (
                <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-orange-500 rounded-2xl flex items-center justify-center mx-auto">
                  <PawPrint className="w-5 h-5 text-white" />
                </div>
              )}
              <Button
                variant="ghost"
                size="icon"
                onClick={onToggleCollapse}
                className="rounded-xl hidden lg:flex"
                title={isCollapsed ? "Expandir sidebar" : "Recolher sidebar"}
              >
                {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
              </Button>
            </div>
          </div>

          {/* Navigation */}
          <nav className={cn("flex-1 p-2 space-y-1", isCollapsed && "px-1")}>
            {menuItems.map((item) => {
              const Icon = item.icon
              const isActive = currentPage === item.id

              const buttonContent = (
                <Button
                  key={item.id}
                  variant={isActive ? "default" : "ghost"}
                  className={cn(
                    "w-full transition-all duration-200 rounded-2xl",
                    isCollapsed ? "h-12 px-0" : "h-12 justify-start px-4",
                    isActive
                      ? "bg-gradient-to-r from-cyan-500 to-orange-500 text-white shadow-lg"
                      : "hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300",
                  )}
                  onClick={() => onPageChange(item.id)}
                >
                  <Icon className={cn("w-5 h-5", !isCollapsed && "mr-3")} />
                  {!isCollapsed && <span className="font-medium">{item.label}</span>}
                </Button>
              )

              if (isCollapsed) {
                return (
                  <Tooltip key={item.id}>
                    <TooltipTrigger asChild>{buttonContent}</TooltipTrigger>
                    <TooltipContent side="right" className="rounded-xl">
                      <p>{item.label}</p>
                    </TooltipContent>
                  </Tooltip>
                )
              }

              return buttonContent
            })}
          </nav>

          {/* Footer */}
          <div className={cn("p-2 border-t border-gray-200 dark:border-gray-800", isCollapsed && "px-1")}>
            {!isCollapsed && (
              <div className="p-3 rounded-2xl bg-gradient-to-r from-cyan-50 to-orange-50 dark:from-cyan-900/20 dark:to-orange-900/20">
                <p className="text-xs font-medium text-gray-700 dark:text-gray-300">Versão 1.0.0</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">© 2025 Pet Shop Suite</p>
              </div>
            )}
          </div>
        </div>
      </aside>
    </TooltipProvider>
  )
}
