"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { PawPrint, Eye, EyeOff, Building2 } from "lucide-react"
import { useTenant } from "@/contexts/TenantProvider"

interface LoginFormProps {
  onLogin: (username: string, password: string) => void
}

export function LoginForm({ onLogin }: LoginFormProps) {
  const [username, setUsername] = useState("admin")
  const [password, setPassword] = useState("123")
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState("")

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!username || !password) {
      setError("Por favor, preencha todos os campos")
      return
    }
    if (username !== "admin" || password !== "123") {
      setError("Credenciais inválidas")
      return
    }
    setError("")
    onLogin(username, password)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-cyan-50 to-orange-50 dark:from-gray-900 dark:to-gray-800 p-4">
      <Card className="w-full max-w-md rounded-3xl shadow-2xl border-0 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm">
        <CardHeader className="text-center space-y-4 pb-8">
          <div className="mx-auto w-16 h-16 bg-gradient-to-br from-cyan-500 to-orange-500 rounded-3xl flex items-center justify-center">
            <PawPrint className="w-8 h-8 text-white" />
          </div>
          <div>
            <CardTitle className="text-2xl font-bold bg-gradient-to-r from-cyan-600 to-orange-500 bg-clip-text text-transparent">
              Pet Shop Management
            </CardTitle>
            <CardDescription className="text-gray-600 dark:text-gray-400 mt-2">
              Sistema de Gestão Completa
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="username" className="text-sm font-medium">
                Usuário
              </Label>
              <Input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="rounded-2xl h-12 border-gray-200 dark:border-gray-700 focus:border-cyan-500 focus:ring-cyan-500"
                placeholder="Digite seu usuário"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password" className="text-sm font-medium">
                Senha
              </Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="rounded-2xl h-12 border-gray-200 dark:border-gray-700 focus:border-cyan-500 focus:ring-cyan-500 pr-12"
                  placeholder="Digite sua senha"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-2 top-1/2 -translate-y-1/2 h-8 w-8 p-0"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>
            </div>
            {error && (
              <Alert className="rounded-2xl border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20">
                <AlertDescription className="text-red-700 dark:text-red-400">{error}</AlertDescription>
              </Alert>
            )}
            <Button
              type="submit"
              className="w-full h-12 rounded-2xl bg-gradient-to-r from-cyan-500 to-orange-500 hover:from-cyan-600 hover:to-orange-600 text-white font-medium shadow-lg hover:shadow-xl transition-all duration-200"
            >
              Entrar
            </Button>
          </form>
          <div className="text-center">
            <p className="text-xs text-gray-500 dark:text-gray-400">💡 Altere sua senha após o primeiro acesso</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
