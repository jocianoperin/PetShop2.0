"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { User, Settings, LogOut, Shield, Bell, HelpCircle, X } from "lucide-react"

interface MobileProfilePanelProps {
  isOpen: boolean
  onToggle: () => void
  onLogout: () => void
  onNavigate: (page: string) => void
}

export function MobileProfilePanel({ isOpen, onToggle, onLogout, onNavigate }: MobileProfilePanelProps) {
  if (!isOpen) return null

  const handleNavigation = (page: string) => {
    onNavigate(page)
    onToggle()
  }

  return (
    <>
      {/* Overlay */}
      <div className="fixed inset-0 bg-black/50 z-40 lg:hidden" onClick={onToggle} />

      {/* Profile Panel */}
      <div className="fixed bottom-20 left-0 right-0 z-50 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800 lg:hidden max-h-[70vh] overflow-y-auto">
        <div className="p-4">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-gray-900 dark:text-white">Perfil</h2>
            <Button variant="ghost" size="icon" onClick={onToggle} className="rounded-2xl">
              <X className="w-5 h-5" />
            </Button>
          </div>

          {/* User Info */}
          <Card className="rounded-2xl mb-4">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-gradient-to-br from-cyan-500 to-orange-500 rounded-2xl flex items-center justify-center">
                  <span className="text-white font-bold text-lg">A</span>
                </div>
                <div className="flex-1">
                  <p className="font-medium text-gray-900 dark:text-white">Admin Master</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">admin@petshop.com</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Administrador</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Menu Options */}
          <div className="space-y-2">
            <Button
              variant="ghost"
              className="w-full justify-start h-12 rounded-2xl"
              onClick={() => handleNavigation("configuracoes")}
            >
              <User className="w-5 h-5 mr-3" />
              Meu Perfil
            </Button>

            <Button
              variant="ghost"
              className="w-full justify-start h-12 rounded-2xl"
              onClick={() => handleNavigation("configuracoes")}
            >
              <Settings className="w-5 h-5 mr-3" />
              Configurações
            </Button>

            <Button variant="ghost" className="w-full justify-start h-12 rounded-2xl">
              <Shield className="w-5 h-5 mr-3" />
              Privacidade
            </Button>

            <Button variant="ghost" className="w-full justify-start h-12 rounded-2xl">
              <Bell className="w-5 h-5 mr-3" />
              Notificações
            </Button>

            <Button variant="ghost" className="w-full justify-start h-12 rounded-2xl">
              <HelpCircle className="w-5 h-5 mr-3" />
              Ajuda & Suporte
            </Button>

            <Separator className="my-4" />

            <Button
              variant="ghost"
              className="w-full justify-start h-12 rounded-2xl text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20"
              onClick={onLogout}
            >
              <LogOut className="w-5 h-5 mr-3" />
              Sair
            </Button>
          </div>

          {/* App Info */}
          <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
            <div className="text-center">
              <p className="text-xs text-gray-500 dark:text-gray-400">Pet Shop Management Suite</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Versão 1.0.0</p>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
