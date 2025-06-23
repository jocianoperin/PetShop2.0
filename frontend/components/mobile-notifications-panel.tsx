"use client"

import React from "react"
import { useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import {
  Bell,
  X,
  AlertTriangle,
  Calendar,
  DollarSign,
  Syringe,
  Hotel,
  CheckCircle,
  Clock,
  MoreVertical,
} from "lucide-react"

const notifications = [
  {
    id: 1,
    type: "alert",
    title: "Vacina Vencida",
    message: "Luna precisa renovar a vacina V8",
    time: "5 min atrás",
    priority: "high",
    icon: Syringe,
    color: "text-red-600",
    bgColor: "bg-red-50 dark:bg-red-900/20",
    borderColor: "border-red-200 dark:border-red-800",
    read: false,
  },
  {
    id: 2,
    type: "reminder",
    title: "Check-out Hoje",
    message: "Thor deve fazer check-out às 16:00",
    time: "30 min atrás",
    priority: "medium",
    icon: Hotel,
    color: "text-yellow-600",
    bgColor: "bg-yellow-50 dark:bg-yellow-900/20",
    borderColor: "border-yellow-200 dark:border-yellow-800",
    read: false,
  },
  {
    id: 3,
    type: "appointment",
    title: "Próximo Agendamento",
    message: "Bella - Banho & Tosa às 14:00",
    time: "1 hora atrás",
    priority: "medium",
    icon: Calendar,
    color: "text-blue-600",
    bgColor: "bg-blue-50 dark:bg-blue-900/20",
    borderColor: "border-blue-200 dark:border-blue-800",
    read: true,
  },
  {
    id: 4,
    type: "payment",
    title: "Pagamento Recebido",
    message: "R$ 90,00 - Banho & Tosa Luna",
    time: "2 horas atrás",
    priority: "low",
    icon: DollarSign,
    color: "text-green-600",
    bgColor: "bg-green-50 dark:bg-green-900/20",
    borderColor: "border-green-200 dark:border-green-800",
    read: true,
  },
  {
    id: 5,
    type: "system",
    title: "Backup Concluído",
    message: "Backup automático realizado com sucesso",
    time: "3 horas atrás",
    priority: "low",
    icon: CheckCircle,
    color: "text-cyan-600",
    bgColor: "bg-cyan-50 dark:bg-cyan-900/20",
    borderColor: "border-cyan-200 dark:border-cyan-800",
    read: true,
  },
  {
    id: 6,
    type: "alert",
    title: "Estoque Baixo",
    message: "Shampoo antipulgas com apenas 2 unidades",
    time: "4 horas atrás",
    priority: "medium",
    icon: AlertTriangle,
    color: "text-orange-600",
    bgColor: "bg-orange-50 dark:bg-orange-900/20",
    borderColor: "border-orange-200 dark:border-orange-800",
    read: false,
  },
]

interface MobileNotificationsPanelProps {
  isOpen: boolean
  onToggle: () => void
}

export function MobileNotificationsPanel({ isOpen, onToggle }: MobileNotificationsPanelProps) {
  const [notificationsList, setNotificationsList] = useState(notifications)
  const [filter, setFilter] = useState<"all" | "unread">("all")

  const unreadCount = notificationsList.filter((n: any) => !n.read).length

  const markAsRead = (id: number) => {
    setNotificationsList((prev: any[]) =>
      prev.map((notification: any) => (notification.id === id ? { ...notification, read: true } : notification)),
    )
  }

  const markAllAsRead = () => {
    setNotificationsList((prev: any[]) => prev.map((notification: any) => ({ ...notification, read: true })))
  }

  const removeNotification = (id: number) => {
    setNotificationsList((prev: any[]) => prev.filter((notification: any) => notification.id !== id))
  }

  const filteredNotifications = notificationsList.filter((n: any) => (filter === "unread" ? !n.read : true))

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "high":
        return "bg-red-500"
      case "medium":
        return "bg-yellow-500"
      case "low":
        return "bg-green-500"
      default:
        return "bg-gray-500"
    }
  }

  if (!isOpen) return null

  return (
    <>
      {/* Overlay */}
      <div className="fixed inset-0 bg-black/50 z-40 lg:hidden" onClick={onToggle} />

      {/* Notifications Panel */}
      <div className="fixed bottom-20 left-0 right-0 z-50 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800 lg:hidden max-h-[70vh] flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-800 flex-shrink-0">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              <div className="relative">
                <Bell className="w-5 h-5 text-gray-700 dark:text-gray-300" />
                {unreadCount > 0 && (
                  <Badge className="absolute -top-2 -right-2 h-4 w-4 rounded-full p-0 flex items-center justify-center bg-red-500 text-white text-xs">
                    {unreadCount}
                  </Badge>
                )}
              </div>
              <div>
                <h2 className="font-bold text-gray-900 dark:text-white">Notificações</h2>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {unreadCount} não {unreadCount === 1 ? "lida" : "lidas"}
                </p>
              </div>
            </div>
            <Button variant="ghost" size="icon" onClick={onToggle} className="rounded-2xl">
              <X className="w-5 h-5" />
            </Button>
          </div>

          {/* Filter Buttons */}
          <div className="flex gap-2">
            <Button
              variant={filter === "all" ? "default" : "outline"}
              size="sm"
              onClick={() => setFilter("all")}
              className="rounded-xl flex-1"
            >
              Todas ({notificationsList.length})
            </Button>
            <Button
              variant={filter === "unread" ? "default" : "outline"}
              size="sm"
              onClick={() => setFilter("unread")}
              className="rounded-xl flex-1"
            >
              Não lidas ({unreadCount})
            </Button>
            {unreadCount > 0 && (
              <Button variant="ghost" size="sm" onClick={markAllAsRead} className="rounded-xl">
                <CheckCircle className="w-4 h-4" />
              </Button>
            )}
          </div>
        </div>

        {/* Notifications List */}
        <ScrollArea className="flex-1">
          <div className="p-4 space-y-3">
            {filteredNotifications.length === 0 ? (
              <div className="text-center py-8">
                <Bell className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                <p className="text-gray-500 dark:text-gray-400">
                  {filter === "unread" ? "Nenhuma notificação não lida" : "Nenhuma notificação"}
                </p>
              </div>
            ) : (
              filteredNotifications.map((notification, index) => {
                const Icon = notification.icon
                return (
                  <div key={notification.id}>
                    <Card
                      className={`rounded-2xl border cursor-pointer transition-all duration-200 hover:shadow-md ${
                        notification.read ? "opacity-70" : ""
                      } ${notification.bgColor} ${notification.borderColor}`}
                      onClick={() => !notification.read && markAsRead(notification.id)}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start gap-3">
                          <div className="relative flex-shrink-0">
                            <div className="p-2 rounded-xl bg-white dark:bg-gray-800 shadow-sm">
                              <Icon className={`w-4 h-4 ${notification.color}`} />
                            </div>
                            {!notification.read && (
                              <div
                                className={`absolute -top-1 -right-1 w-3 h-3 rounded-full ${getPriorityColor(notification.priority)}`}
                              />
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between">
                              <div className="flex-1 min-w-0">
                                <p className="font-medium text-gray-900 dark:text-white text-sm truncate">
                                  {notification.title}
                                </p>
                                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">
                                  {notification.message}
                                </p>
                                <div className="flex items-center gap-2 mt-2">
                                  <Clock className="w-3 h-3 text-gray-400 flex-shrink-0" />
                                  <p className="text-xs text-gray-500 dark:text-gray-400">{notification.time}</p>
                                </div>
                              </div>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  removeNotification(notification.id)
                                }}
                                className="rounded-xl ml-2 flex-shrink-0"
                              >
                                <MoreVertical className="w-4 h-4" />
                              </Button>
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                    {index < filteredNotifications.length - 1 && <Separator className="my-2" />}
                  </div>
                )
              })
            )}
          </div>
        </ScrollArea>
      </div>
    </>
  )
}
