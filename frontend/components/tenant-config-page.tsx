"use client"

import { useState, useEffect, useRef } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useTenant } from "@/contexts/TenantProvider"
import { useTenantApi } from "@/hooks/useTenantApi"
import { toast } from "@/components/ui/use-toast"
import { Settings, Upload, Palette, Building } from "lucide-react"

export function TenantConfigPage() {
  const { tenant, setTenant } = useTenant()
  const { getTenantConfig, updateTenantConfig } = useTenantApi()
  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  // Form state
  const [tenantName, setTenantName] = useState(tenant?.name || "")
  const [primaryColor, setPrimaryColor] = useState(tenant?.theme?.primary_color || "#0ea5e9")
  const [secondaryColor, setSecondaryColor] = useState(tenant?.theme?.secondary_color || "#f97316")
  const [accentColor, setAccentColor] = useState(tenant?.theme?.accent_color || "#8b5cf6")
  const [logoPreview, setLogoPreview] = useState<string | null>(tenant?.logo_url || null)
  const [logoFile, setLogoFile] = useState<File | null>(null)

  // Load tenant config on mount
  useEffect(() => {
    const loadTenantConfig = async () => {
      if (!tenant) return
      
      setIsLoading(true)
      try {
        const config = await getTenantConfig()
        
        // Update form state with config values
        if (config) {
          setTenantName(config.name || tenant.name)
          setPrimaryColor(config.theme?.primary_color || tenant.theme?.primary_color || "#0ea5e9")
          setSecondaryColor(config.theme?.secondary_color || tenant.theme?.secondary_color || "#f97316")
          setAccentColor(config.theme?.accent_color || tenant.theme?.accent_color || "#8b5cf6")
          setLogoPreview(config.logo_url || tenant.logo_url || null)
        }
      } catch (error) {
        console.error("Error loading tenant config:", error)
        toast({
          title: "Erro ao carregar configurações",
          description: "Não foi possível carregar as configurações do tenant.",
          variant: "destructive"
        })
      } finally {
        setIsLoading(false)
      }
    }
    
    loadTenantConfig()
  }, [tenant, getTenantConfig])

  // Handle logo file selection
  const handleLogoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    
    // Validate file type
    if (!file.type.startsWith('image/')) {
      toast({
        title: "Tipo de arquivo inválido",
        description: "Por favor, selecione uma imagem (PNG, JPG, SVG).",
        variant: "destructive"
      })
      return
    }
    
    // Validate file size (max 2MB)
    if (file.size > 2 * 1024 * 1024) {
      toast({
        title: "Arquivo muito grande",
        description: "O tamanho máximo permitido é 2MB.",
        variant: "destructive"
      })
      return
    }
    
    // Create preview URL
    const previewUrl = URL.createObjectURL(file)
    setLogoPreview(previewUrl)
    setLogoFile(file)
  }

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!tenant) return
    
    setIsSaving(true)
    try {
      // Prepare updated config
      const updatedConfig = {
        name: tenantName,
        theme: {
          primary_color: primaryColor,
          secondary_color: secondaryColor,
          accent_color: accentColor
        }
      }
      
      // If we have a new logo file, we would upload it here
      // In a real implementation, this would be a separate API call to upload the file
      // For now, we'll simulate it by adding a fake URL
      let logoUrl = tenant.logo_url
      if (logoFile) {
        // In a real implementation, this would be an API call to upload the file
        // For now, we'll simulate it with a fake URL
        logoUrl = logoPreview // In real implementation, this would be the URL returned from the server
      }
      
      // Update the config
      const result = await updateTenantConfig({
        ...updatedConfig,
        logo_url: logoUrl
      })
      
      // Update the tenant context with the new values
      if (result) {
        setTenant({
          ...tenant,
          name: tenantName,
          logo_url: logoUrl,
          theme: {
            primary_color: primaryColor,
            secondary_color: secondaryColor,
            accent_color: accentColor
          }
        })
        
        toast({
          title: "Configurações salvas",
          description: "As configurações do tenant foram atualizadas com sucesso.",
        })
      }
    } catch (error) {
      console.error("Error saving tenant config:", error)
      toast({
        title: "Erro ao salvar configurações",
        description: "Não foi possível salvar as configurações do tenant.",
        variant: "destructive"
      })
    } finally {
      setIsSaving(false)
    }
  }

  // Preview theme changes in real-time
  useEffect(() => {
    if (typeof document === 'undefined') return
    
    const root = document.documentElement
    
    // Apply theme colors to CSS variables
    root.style.setProperty('--primary', primaryColor)
    root.style.setProperty('--secondary', secondaryColor)
    root.style.setProperty('--accent', accentColor)
    
    // Cleanup function to reset variables when component unmounts
    return () => {
      if (tenant?.theme) {
        root.style.setProperty('--primary', tenant.theme.primary_color || '')
        root.style.setProperty('--secondary', tenant.theme.secondary_color || '')
        root.style.setProperty('--accent', tenant.theme.accent_color || '')
      } else {
        root.style.removeProperty('--primary')
        root.style.removeProperty('--secondary')
        root.style.removeProperty('--accent')
      }
    }
  }, [primaryColor, secondaryColor, accentColor, tenant])

  if (!tenant) {
    return (
      <div className="p-6 text-center">
        <p>Nenhum tenant selecionado.</p>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Configurações do Tenant</h1>
          <p className="text-gray-600 dark:text-gray-400">Personalize as configurações do seu petshop</p>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <Tabs defaultValue="geral" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3 rounded-2xl">
            <TabsTrigger value="geral" className="rounded-2xl">
              Geral
            </TabsTrigger>
            <TabsTrigger value="aparencia" className="rounded-2xl">
              Aparência
            </TabsTrigger>
            <TabsTrigger value="avancado" className="rounded-2xl">
              Avançado
            </TabsTrigger>
          </TabsList>

          <TabsContent value="geral" className="space-y-6">
            <Card className="rounded-3xl border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Building className="w-5 h-5 text-cyan-600" />
                  Informações do Tenant
                </CardTitle>
                <CardDescription>Configure as informações básicas do seu petshop</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="tenant-name">Nome do Petshop</Label>
                  <Input 
                    id="tenant-name" 
                    value={tenantName} 
                    onChange={(e) => setTenantName(e.target.value)} 
                    placeholder="Nome do seu petshop" 
                    className="rounded-2xl"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="tenant-subdomain">Subdomínio</Label>
                  <Input 
                    id="tenant-subdomain" 
                    value={tenant.subdomain} 
                    disabled
                    className="rounded-2xl bg-gray-50"
                  />
                  <p className="text-xs text-gray-500">O subdomínio não pode ser alterado após a criação.</p>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="tenant-plan">Plano Atual</Label>
                  <Input 
                    id="tenant-plan" 
                    value={tenant.plan_type.charAt(0).toUpperCase() + tenant.plan_type.slice(1)} 
                    disabled
                    className="rounded-2xl bg-gray-50"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="tenant-created">Data de Criação</Label>
                  <Input 
                    id="tenant-created" 
                    value={new Date(tenant.created_at).toLocaleDateString('pt-BR')} 
                    disabled
                    className="rounded-2xl bg-gray-50"
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="aparencia" className="space-y-6">
            <Card className="rounded-3xl border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Palette className="w-5 h-5 text-orange-600" />
                  Personalização Visual
                </CardTitle>
                <CardDescription>Personalize as cores e o logo do seu petshop</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Logo Upload */}
                  <div className="space-y-4">
                    <Label>Logo do Petshop</Label>
                    <div className="flex flex-col items-center justify-center p-6 border-2 border-dashed border-gray-300 rounded-2xl bg-gray-50 dark:bg-gray-800 dark:border-gray-700">
                      {logoPreview ? (
                        <div className="relative w-full max-w-xs">
                          <img 
                            src={logoPreview} 
                            alt="Logo preview" 
                            className="w-full h-auto object-contain rounded-lg mb-4"
                            style={{ maxHeight: '150px' }}
                          />
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            className="mt-2 w-full rounded-2xl"
                            onClick={() => fileInputRef.current?.click()}
                          >
                            Alterar Logo
                          </Button>
                        </div>
                      ) : (
                        <div className="text-center">
                          <Upload className="mx-auto h-12 w-12 text-gray-400" />
                          <div className="mt-4 flex text-sm leading-6 text-gray-600">
                            <label
                              htmlFor="file-upload"
                              className="relative cursor-pointer rounded-md bg-white font-semibold text-cyan-600 focus-within:outline-none focus-within:ring-2 focus-within:ring-cyan-600 focus-within:ring-offset-2 hover:text-cyan-500"
                            >
                              <span>Enviar um arquivo</span>
                              <input
                                id="file-upload"
                                name="file-upload"
                                type="file"
                                className="sr-only"
                                ref={fileInputRef}
                                onChange={handleLogoChange}
                                accept="image/*"
                              />
                            </label>
                            <p className="pl-1">ou arraste e solte</p>
                          </div>
                          <p className="text-xs text-gray-500">PNG, JPG, SVG até 2MB</p>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {/* Color Pickers */}
                  <div className="space-y-6">
                    <div className="space-y-2">
                      <Label htmlFor="primary-color">Cor Primária</Label>
                      <div className="flex gap-2">
                        <div 
                          className="w-10 h-10 rounded-lg border border-gray-300" 
                          style={{ backgroundColor: primaryColor }}
                        />
                        <Input
                          id="primary-color"
                          type="color"
                          value={primaryColor}
                          onChange={(e) => setPrimaryColor(e.target.value)}
                          className="w-full rounded-2xl h-10"
                        />
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="secondary-color">Cor Secundária</Label>
                      <div className="flex gap-2">
                        <div 
                          className="w-10 h-10 rounded-lg border border-gray-300" 
                          style={{ backgroundColor: secondaryColor }}
                        />
                        <Input
                          id="secondary-color"
                          type="color"
                          value={secondaryColor}
                          onChange={(e) => setSecondaryColor(e.target.value)}
                          className="w-full rounded-2xl h-10"
                        />
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="accent-color">Cor de Destaque</Label>
                      <div className="flex gap-2">
                        <div 
                          className="w-10 h-10 rounded-lg border border-gray-300" 
                          style={{ backgroundColor: accentColor }}
                        />
                        <Input
                          id="accent-color"
                          type="color"
                          value={accentColor}
                          onChange={(e) => setAccentColor(e.target.value)}
                          className="w-full rounded-2xl h-10"
                        />
                      </div>
                    </div>
                    
                    <div className="p-4 mt-4 rounded-2xl bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        As alterações de cores são visualizadas em tempo real. Clique em Salvar para aplicar permanentemente.
                      </p>
                    </div>
                  </div>
                </div>
                
                {/* Preview Section */}
                <div className="mt-8 p-6 rounded-2xl border border-gray-200 dark:border-gray-700">
                  <h3 className="text-lg font-medium mb-4">Visualização</h3>
                  <div className="flex flex-wrap gap-4">
                    <Button className="rounded-2xl">Botão Primário</Button>
                    <Button variant="outline" className="rounded-2xl">Botão Secundário</Button>
                    <Button variant="ghost" className="rounded-2xl">Botão Ghost</Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="avancado" className="space-y-6">
            <Card className="rounded-3xl border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="w-5 h-5 text-purple-600" />
                  Configurações Avançadas
                </CardTitle>
                <CardDescription>Configurações avançadas do tenant</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="p-4 rounded-2xl bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 mb-6">
                  <p className="text-sm text-yellow-700 dark:text-yellow-400">
                    ⚠️ As configurações avançadas podem afetar o funcionamento do sistema. Altere apenas se souber o que está fazendo.
                  </p>
                </div>
                
                <div className="space-y-6">
                  <div className="space-y-2">
                    <Label htmlFor="tenant-id">ID do Tenant</Label>
                    <Input 
                      id="tenant-id" 
                      value={tenant.id} 
                      disabled
                      className="rounded-2xl bg-gray-50"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="schema-name">Nome do Schema</Label>
                    <Input 
                      id="schema-name" 
                      value={tenant.schema_name} 
                      disabled
                      className="rounded-2xl bg-gray-50"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
        
        <div className="flex justify-end mt-6 gap-4">
          <Button
            type="button"
            variant="outline"
            className="rounded-2xl"
            onClick={() => {
              // Reset to original values
              setTenantName(tenant.name)
              setPrimaryColor(tenant.theme?.primary_color || "#0ea5e9")
              setSecondaryColor(tenant.theme?.secondary_color || "#f97316")
              setAccentColor(tenant.theme?.accent_color || "#8b5cf6")
              setLogoPreview(tenant.logo_url)
              setLogoFile(null)
              
              // Reset CSS variables
              if (typeof document !== 'undefined') {
                const root = document.documentElement
                root.style.setProperty('--primary', tenant.theme?.primary_color || '')
                root.style.setProperty('--secondary', tenant.theme?.secondary_color || '')
                root.style.setProperty('--accent', tenant.theme?.accent_color || '')
              }
            }}
          >
            Cancelar
          </Button>
          <Button 
            type="submit" 
            className="rounded-2xl bg-gradient-to-r from-cyan-500 to-orange-500"
            disabled={isSaving}
          >
            {isSaving ? "Salvando..." : "Salvar Configurações"}
          </Button>
        </div>
      </form>
    </div>
  )
}