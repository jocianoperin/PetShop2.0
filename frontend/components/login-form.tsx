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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

interface LoginFormProps {
  onLogin: (username: string, password: string, tenantId?: string) => void
}

export function LoginForm({ onLogin }: LoginFormProps) {
  const [username, setUsername] = useState("admin")
  const [password, setPassword] = useState("123")
  const [tenantId, setTenantId] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState("")
  const { tenantId: detectedTenantId, tenant } = useTenant()
  const [tenantInputType, setTenantInputType] = useState<"text" | "select">("text")
  const [availableTenants, setAvailableTenants] = useState<{id: string, name: string}[]>([
    { id: "tenant1", name: "Pet Shop Canino" },
    { id: "tenant2", name: "Clínica Veterinária Feliz" },
    { id: "tenant3", name: "Pet Care Premium" }
  ])

  useEffect(() => {
    // If tenant is detected from subdomain, use it
    if (detectedTenantId) {
      setTenantId(detectedTenantId)
    }
  }, [detectedTenantId])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!username || !password) {
      setError("Por favor, preencha todos os campos")
      return
    }
    
    // In a real app, we wouldn't validate credentials client-side
    // This is just for demo purposes
    if (username !== "admin" || password !== "123") {
      setError("Credenciais inválidas")
      return
    }
    
    // Validate tenant
    if (!detectedTenantId && !tenantId) {
      setError("Por favor, selecione ou digite o ID do tenant")
      return
    }
    
    setError("")
    onLogin(username, password, tenantId || detectedTenantId)
  }

  // Load recent tenants from local storage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      try {
        const recentTenantsJson = localStorage.getItem('recent_tenants');
        if (recentTenantsJson) {
          const recentTenants = JSON.parse(recentTenantsJson);
          if (Array.isArray(recentTenants) && recentTenants.length > 0) {
            // Convert to the format expected by the component
            const formattedTenants = recentTenants.map(t => ({
              id: t.subdomain,
              name: t.name
            }));
            
            // Merge with default tenants, removing duplicates
            const existingIds = new Set(formattedTenants.map(t => t.id));
            const mergedTenants = [
              ...formattedTenants,
              ...availableTenants.filter(t => !existingIds.has(t.id))
            ];
            
            setAvailableTenants(mergedTenants);
          }
        }
      } catch (e) {
        console.error('Error loading recent tenants:', e);
      }
    }
  }, []);

  // Validate tenant ID when entered
  useEffect(() => {
    if (tenantId && tenantId !== detectedTenantId && tenantInputType === "text") {
      // In a real implementation, we would validate the tenant ID against the API
      // For now, we'll just simulate a validation
      const isValidFormat = /^[a-z0-9-]+$/.test(tenantId);
      if (!isValidFormat) {
        setError("ID do tenant deve conter apenas letras minúsculas, números e hífens");
      } else {
        setError("");
      }
    }
  }, [tenantId, detectedTenantId, tenantInputType]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-cyan-50 to-orange-50 dark:from-gray-900 dark:to-gray-800 p-4">
      <Card className="w-full max-w-md rounded-3xl shadow-2xl border-0 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm">
        <CardHeader className="text-center space-y-4 pb-8">
          {tenant && tenant.logo_url ? (
            <div className="mx-auto w-16 h-16 rounded-3xl flex items-center justify-center">
              <img 
                src={tenant.logo_url} 
                alt={`${tenant.name} logo`} 
                className="w-16 h-16 object-contain"
              />
            </div>
          ) : (
            <div className="mx-auto w-16 h-16 bg-gradient-to-br from-cyan-500 to-orange-500 rounded-3xl flex items-center justify-center">
              <PawPrint className="w-8 h-8 text-white" />
            </div>
          )}
          <div>
            <CardTitle 
              className="text-2xl font-bold bg-gradient-to-r from-cyan-600 to-orange-500 bg-clip-text text-transparent"
              style={tenant?.theme?.primary_color ? {
                background: `linear-gradient(to right, ${tenant.theme.primary_color}, ${tenant.theme.secondary_color || '#f97316'})`,
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent'
              } : {}}
            >
              {tenant?.name || "Pet Shop Management"}
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
            
            {!detectedTenantId && (
              <div className="space-y-2">
                <Label htmlFor="tenantId" className="text-sm font-medium flex items-center gap-1">
                  <Building2 className="h-4 w-4" /> Tenant
                </Label>
                
                <div className="flex items-center gap-2 mb-2">
                  <Button
                    type="button"
                    variant={tenantInputType === "text" ? "default" : "outline"}
                    size="sm"
                    onClick={() => setTenantInputType("text")}
                    className="text-xs"
                  >
                    Digitar ID
                  </Button>
                  <Button
                    type="button"
                    variant={tenantInputType === "select" ? "default" : "outline"}
                    size="sm"
                    onClick={() => setTenantInputType("select")}
                    className="text-xs"
                  >
                    Selecionar
                  </Button>
                </div>
                
                {tenantInputType === "text" ? (
                  <Input
                    id="tenantId"
                    type="text"
                    value={tenantId}
                    onChange={(e) => setTenantId(e.target.value)}
                    className="rounded-2xl h-12 border-gray-200 dark:border-gray-700 focus:border-cyan-500 focus:ring-cyan-500"
                    placeholder="Digite o ID do tenant"
                  />
                ) : (
                  <Select value={tenantId} onValueChange={setTenantId}>
                    <SelectTrigger className="rounded-2xl h-12 border-gray-200 dark:border-gray-700 focus:border-cyan-500 focus:ring-cyan-500">
                      <SelectValue placeholder="Selecione seu Petshop" />
                    </SelectTrigger>
                    <SelectContent>
                      {availableTenants.map(tenant => (
                        <SelectItem key={tenant.id} value={tenant.id}>
                          {tenant.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
                
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {tenantInputType === "text" 
                    ? "Identificador do seu petshop no sistema" 
                    : "Selecione seu petshop na lista"}
                </p>
              </div>
            )}
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
