"use client"

import { Button } from "@/components/ui/button"
import { PawPrint, Sun, Moon, ArrowLeft } from "lucide-react"
import { useTheme } from "next-themes"

interface MobileHeaderProps {
  currentPage: string
  onBack?: () => void
  showBackButton?: boolean
  title?: string
}

const pageLabels: Record<string, string> = {
  dashboard: "Dashboard",
  financeiro: "Financeiro",
  agenda: "Agenda",
  hotel: "Hotel",
  pets: "Pets",
  promocoes: "Promoções",
  relatorios: "Relatórios",
  configuracoes: "Configurações",
}

export function MobileHeader({ currentPage, onBack, showBackButton = false, title }: MobileHeaderProps) {
  const { theme, setTheme } = useTheme()

  const pageTitle = title || pageLabels[currentPage] || "Pet Shop"

  return (
    <header className="h-14 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-4 flex items-center justify-between lg:hidden">
      {/* Left side */}
      <div className="flex items-center gap-3">
        {showBackButton ? (
          <Button variant="ghost" size="icon" onClick={onBack} className="rounded-2xl">
            <ArrowLeft className="h-5 w-5" />
          </Button>
        ) : (
          <div className="w-8 h-8 bg-gradient-to-br from-cyan-500 to-orange-500 rounded-2xl flex items-center justify-center">
            <PawPrint className="w-4 h-4 text-white" />
          </div>
        )}
        <div>
          <h1 className="text-lg font-bold text-gray-900 dark:text-white">{pageTitle}</h1>
        </div>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-2">
        {/* Theme Toggle */}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          className="rounded-2xl"
        >
          <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
        </Button>
      </div>
    </header>
  )
}
