"use client"

import { useState, useEffect } from "react"
import { LoginForm } from "@/components/login-form"
import { Dashboard } from "@/components/dashboard"
import { FinanceiroPage } from "@/components/financeiro-page"
import { AgendaPage } from "@/components/agenda-page"
import { HotelPage } from "@/components/hotel-page"
import { PetsPage } from "@/components/pets-page"
import { PromocoesPage } from "@/components/promocoes-page"
import { RelatoriosPage } from "@/components/relatorios-page"
import { ConfiguracoesPage } from "@/components/configuracoes-page"
import { Sidebar } from "@/components/sidebar"
import { Header } from "@/components/header"
import { NotificationsPanel } from "@/components/notifications-panel"
import { MobileNavigation } from "@/components/mobile-navigation"
import { MobileHeader } from "@/components/mobile-header"
import { MobileProfilePanel } from "@/components/mobile-profile-panel"
import { MobileNotificationsPanel } from "@/components/mobile-notifications-panel"
import { MobileFab } from "@/components/mobile-fab"
import { ThemeProvider } from "@/components/theme-provider"
import { useMediaQuery } from "@/hooks/use-media-query"

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [currentPage, setCurrentPage] = useState("dashboard")
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [notificationsOpen, setNotificationsOpen] = useState(false)
  const [notificationsPinned, setNotificationsPinned] = useState(false)
  const [unreadNotifications, setUnreadNotifications] = useState(6)

  // Mobile states
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [mobileProfileOpen, setMobileProfileOpen] = useState(false)
  const [mobileNotificationsOpen, setMobileNotificationsOpen] = useState(false)

  const isMobile = useMediaQuery("(max-width: 1024px)")

  const handleLogin = (username: string, password: string) => {
    if (username === "admin" && password === "123") {
      setIsLoggedIn(true)
      setCurrentPage("dashboard")
    }
  }

  const handleLogout = () => {
    setIsLoggedIn(false)
    setCurrentPage("dashboard")
    setSidebarCollapsed(false)
    setNotificationsOpen(false)
    setNotificationsPinned(false)
    setMobileMenuOpen(false)
    setMobileProfileOpen(false)
    setMobileNotificationsOpen(false)
  }

  const toggleNotifications = () => {
    if (isMobile) {
      setMobileNotificationsOpen(!mobileNotificationsOpen)
      setMobileProfileOpen(false)
      setMobileMenuOpen(false)
    } else {
      setNotificationsOpen(!notificationsOpen)
    }
  }

  const toggleNotificationsPin = () => {
    setNotificationsPinned(!notificationsPinned)
    if (!notificationsPinned) {
      setNotificationsOpen(true)
    }
  }

  const handleMobileProfileToggle = () => {
    setMobileProfileOpen((open: boolean) => {
      if (!open) {
        setMobileMenuOpen(false)
        setMobileNotificationsOpen(false)
      }
      return !open
    })
  }

  const handleMobileMenuToggle = () => {
    setMobileMenuOpen((open: boolean) => {
      if (!open) {
        setMobileProfileOpen(false)
        setMobileNotificationsOpen(false)
      }
      return !open
    })
  }

  const handleMobileNotificationsToggle = () => {
    setMobileNotificationsOpen((open: boolean) => {
      if (!open) {
        setMobileMenuOpen(false)
        setMobileProfileOpen(false)
      }
      return !open
    })
  }

  const handlePageChange = (page: string) => {
    setCurrentPage(page)
    // Close mobile panels when navigating
    if (isMobile) {
      setMobileMenuOpen(false)
      setMobileProfileOpen(false)
      setMobileNotificationsOpen(false)
    }
  }

  const handleFabAction = (action: string) => {
    // Handle FAB actions based on the action type
    switch (action) {
      case "new-appointment":
        setCurrentPage("agenda")
        // Here you would typically open a new appointment dialog
        break
      case "new-pet":
        setCurrentPage("pets")
        // Here you would typically open a new pet dialog
        break
      case "new-checkin":
        setCurrentPage("hotel")
        // Here you would typically open a new check-in dialog
        break
      case "new-transaction":
        setCurrentPage("financeiro")
        // Here you would typically open a new transaction dialog
        break
    }
  }

  const renderPage = () => {
    switch (currentPage) {
      case "dashboard":
        return <Dashboard />
      case "financeiro":
        return <FinanceiroPage />
      case "agenda":
        return <AgendaPage />
      case "hotel":
        return <HotelPage />
      case "pets":
        return <PetsPage />
      case "promocoes":
        return <PromocoesPage />
      case "relatorios":
        return <RelatoriosPage />
      case "configuracoes":
        return <ConfiguracoesPage />
      default:
        return <Dashboard />
    }
  }

  // Close mobile panels when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (isMobile) {
        const target = event.target as Element
        if (
          !target.closest("[data-mobile-panel]") &&
          !target.closest("[data-mobile-trigger]") &&
          !target.closest("[data-mobile-fab]")
        ) {
          setMobileMenuOpen(false)
          setMobileProfileOpen(false)
          setMobileNotificationsOpen(false)
        }
      } else if (!notificationsPinned && notificationsOpen) {
        const target = event.target as Element
        if (!target.closest("[data-notifications-panel]") && !target.closest("[data-notifications-trigger]")) {
          setNotificationsOpen(false)
        }
      }
    }

    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [isMobile, notificationsOpen, notificationsPinned])

  // Auto-collapse sidebar on mobile
  useEffect(() => {
    if (isMobile) {
      setSidebarCollapsed(true)
      setNotificationsOpen(false)
      setNotificationsPinned(false)
    }
  }, [isMobile])

  if (!isLoggedIn) {
    return (
      <ThemeProvider attribute="class" defaultTheme="light" enableSystem>
        <LoginForm onLogin={handleLogin} />
      </ThemeProvider>
    )
  }

  return (
    <ThemeProvider attribute="class" defaultTheme="light" enableSystem>
      <div className="flex h-screen bg-gray-50 dark:bg-gray-950">
        {/* Desktop Sidebar */}
        {!isMobile && (
          <Sidebar
            currentPage={currentPage}
            onPageChange={handlePageChange}
            isCollapsed={sidebarCollapsed}
            onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
          />
        )}

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Desktop Header */}
          {!isMobile && (
            <Header
              onSidebarToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
              onNotificationsToggle={toggleNotifications}
              unreadNotifications={unreadNotifications}
              onLogout={handleLogout}
            />
          )}

          {/* Mobile Header */}
          {isMobile && <MobileHeader currentPage={currentPage} />}

          {/* Page Content */}
          <main
            className={`flex-1 overflow-auto transition-all duration-300 ${
              !isMobile && notificationsPinned ? "mr-80" : ""
            } ${isMobile ? "pb-16" : ""}`}
          >
            {renderPage()}
          </main>
        </div>

        {/* Desktop Notifications Panel */}
        {!isMobile && (
          <div data-notifications-panel>
            <NotificationsPanel
              isOpen={notificationsOpen}
              onToggle={toggleNotifications}
              isPinned={notificationsPinned}
              onPin={toggleNotificationsPin}
            />
          </div>
        )}

        {/* Mobile Navigation */}
        {isMobile && (
          <>
            <div data-mobile-trigger>
              <MobileNavigation
                currentPage={currentPage}
                onPageChange={handlePageChange}
                unreadNotifications={unreadNotifications}
                onNotificationsToggle={handleMobileNotificationsToggle}
                onProfileToggle={handleMobileProfileToggle}
                isOpen={mobileMenuOpen}
                onToggle={handleMobileMenuToggle}
              />
            </div>

            {/* Mobile Panels */}
            <div data-mobile-panel>
              <MobileProfilePanel
                isOpen={mobileProfileOpen}
                onToggle={handleMobileProfileToggle}
                onLogout={handleLogout}
                onNavigate={handlePageChange}
              />

              <MobileNotificationsPanel
                isOpen={mobileNotificationsOpen}
                onToggle={handleMobileNotificationsToggle}
              />
            </div>

            {/* Mobile FAB */}
            <div data-mobile-fab>
              <MobileFab currentPage={currentPage} onAction={handleFabAction} />
            </div>
          </>
        )}
      </div>
    </ThemeProvider>
  )
}
