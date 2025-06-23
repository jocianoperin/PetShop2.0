"use client"
import React from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { Calendar, Home, Hotel, PawPrint, Settings, FileText, Megaphone, DollarSign, Bell, Menu, X } from "lucide-react"

interface MobileNavigationProps {
  currentPage: string
  onPageChange: (page: string) => void
  unreadNotifications: number
  handleMobileNotificationsToggle: () => void
  onProfileToggle: () => void
  isOpen: boolean
  onToggle: () => void
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

export function MobileNavigation({
  currentPage,
  onPageChange,
  unreadNotifications,
  handleMobileNotificationsToggle,
  onProfileToggle,
  isOpen,
  onToggle,
}: MobileNavigationProps) {
  return (
    <>
      {/* Mobile Bottom Navigation - Always visible */}
      <div className="fixed bottom-0 left-0 right-0 z-50 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800 lg:hidden">
        <div className="grid grid-cols-5 h-16">
          {/* Dashboard */}
          <Button
            variant="ghost"
            className={cn(
              "h-full rounded-none flex-col gap-1 text-xs",
              currentPage === "dashboard" && "text-cyan-600 bg-cyan-50 dark:bg-cyan-900/20",
            )}
            onClick={() => onPageChange("dashboard")}
          >
            <Home className="w-5 h-5" />
            <span>Home</span>
          </Button>

          {/* Agenda */}
          <Button
            variant="ghost"
            className={cn(
              "h-full rounded-none flex-col gap-1 text-xs",
              currentPage === "agenda" && "text-cyan-600 bg-cyan-50 dark:bg-cyan-900/20",
            )}
            onClick={() => onPageChange("agenda")}
          >
            <Calendar className="w-5 h-5" />
            <span>Agenda</span>
          </Button>

          {/* Menu Central */}
          <Button variant="ghost" className="h-full rounded-none flex-col gap-1 text-xs relative" onClick={onToggle}>
            <div className="w-10 h-10 bg-gradient-to-r from-cyan-500 to-orange-500 rounded-2xl flex items-center justify-center">
              {isOpen ? <X className="w-5 h-5 text-white" /> : <Menu className="w-5 h-5 text-white" />}
            </div>
            <span className="text-xs">Menu</span>
          </Button>

          {/* Notifications */}
          <Button
            variant="ghost"
            className="h-full rounded-none flex-col gap-1 text-xs relative"
            onClick={handleMobileNotificationsToggle}
          >
            <div className="relative">
              <Bell className="w-5 h-5" />
              {unreadNotifications > 0 && (
                <Badge className="absolute -top-2 -right-2 h-4 w-4 rounded-full p-0 flex items-center justify-center bg-red-500 text-white text-xs">
                  {unreadNotifications > 9 ? "9+" : unreadNotifications}
                </Badge>
              )}
            </div>
            <span>Avisos</span>
          </Button>

          {/* Profile */}
          <Button variant="ghost" className="h-full rounded-none flex-col gap-1 text-xs" onClick={onProfileToggle}>
            <div className="w-6 h-6 bg-gradient-to-br from-cyan-500 to-orange-500 rounded-full flex items-center justify-center">
              <span className="text-white font-bold text-xs">A</span>
            </div>
            <span>Perfil</span>
          </Button>
        </div>
      </div>

      {/* Mobile Menu Overlay */}
      {isOpen && (
        <>
          <div className="fixed inset-0 bg-black/50 z-40 lg:hidden" onClick={onToggle} />
          <div className="fixed bottom-16 left-0 right-0 z-50 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800 lg:hidden">
            <div className="p-4">
              <div className="grid grid-cols-2 gap-3">
                {menuItems
                  .filter((item) => !["dashboard", "agenda"].includes(item.id))
                  .map((item) => {
                    const Icon = item.icon
                    const isActive = currentPage === item.id

                    return (
                      <Button
                        key={item.id}
                        variant={isActive ? "default" : "outline"}
                        className={cn(
                          "h-16 flex-col gap-2 rounded-2xl",
                          isActive
                            ? "bg-gradient-to-r from-cyan-500 to-orange-500 text-white"
                            : "hover:bg-gray-50 dark:hover:bg-gray-800",
                        )}
                        onClick={() => {
                          onPageChange(item.id)
                          onToggle()
                        }}
                      >
                        <Icon className="w-6 h-6" />
                        <span className="text-xs font-medium">{item.label}</span>
                      </Button>
                    )
                  })}
              </div>
            </div>
          </div>
        </>
      )}
    </>
  )
}
