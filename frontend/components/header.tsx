"use client"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Bell, Menu, Sun, Moon, User, Settings, LogOut, Building } from "lucide-react"
import { useTheme } from "next-themes"
import { TenantIndicator } from "./tenant-indicator"
import { useAuth } from "@/contexts/AuthProvider"

interface HeaderProps {
  onSidebarToggle: () => void
  onNotificationsToggle: () => void
  unreadNotifications: number
  onLogout: () => void
}

export function Header({ onSidebarToggle, onNotificationsToggle, unreadNotifications, onLogout }: HeaderProps) {
  const { theme, setTheme } = useTheme()
  const { user } = useAuth()

  return (
    <header className="h-16 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-4 flex items-center justify-between">
      {/* Left side */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={onSidebarToggle} className="lg:hidden rounded-2xl">
          <Menu className="h-5 w-5" />
        </Button>
        <div className="hidden lg:flex items-center gap-3">
          <h1 className="text-xl font-bold text-gray-900 dark:text-white">Pet Shop Management</h1>
          <TenantIndicator />
        </div>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-2">
        {/* Tenant Indicator (mobile) */}
        <div className="lg:hidden">
          <TenantIndicator showDetails={true} />
        </div>
        
        {/* Theme Toggle */}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          className="rounded-2xl"
        >
          <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          <span className="sr-only">Toggle theme</span>
        </Button>

        {/* Notifications */}
        <Button variant="ghost" size="icon" onClick={onNotificationsToggle} className="rounded-2xl relative">
          <Bell className="h-5 w-5" />
          {unreadNotifications > 0 && (
            <Badge className="absolute -top-1 -right-1 h-5 w-5 rounded-full p-0 flex items-center justify-center bg-red-500 text-white text-xs">
              {unreadNotifications > 9 ? "9+" : unreadNotifications}
            </Badge>
          )}
        </Button>

        {/* User Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="rounded-2xl">
              <div className="w-8 h-8 bg-gradient-to-br from-cyan-500 to-orange-500 rounded-2xl flex items-center justify-center">
                <span className="text-white font-bold text-sm">
                  {user?.nome ? user.nome.charAt(0).toUpperCase() : 'A'}
                </span>
              </div>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56 rounded-2xl">
            <DropdownMenuLabel>
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-medium">{user?.nome || 'Admin Master'}</p>
                <p className="text-xs text-gray-500">{user?.email || 'admin@petshop.com'}</p>
                {user?.tenant && (
                  <div className="flex items-center gap-1 mt-1">
                    <Building className="h-3 w-3 text-gray-500" />
                    <span className="text-xs text-gray-500">{user.tenant.name}</span>
                  </div>
                )}
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="rounded-xl">
              <User className="mr-2 h-4 w-4" />
              Perfil
            </DropdownMenuItem>
            <DropdownMenuItem className="rounded-xl" asChild>
              <a href="/admin/tenant-config">
                <Settings className="mr-2 h-4 w-4" />
                Configurações
              </a>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={onLogout} className="rounded-xl text-red-600">
              <LogOut className="mr-2 h-4 w-4" />
              Sair
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}
