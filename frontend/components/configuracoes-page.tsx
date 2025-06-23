"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  Plus,
  Users,
  Shield,
  Database,
  Bell,
  Mail,
  Phone,
  Settings,
  Edit,
  Trash2,
  Key,
  Download,
  Upload,
} from "lucide-react"

const usuarios = [
  {
    id: 1,
    nome: "Admin Master",
    email: "admin@petshop.com",
    perfil: "ADMIN",
    status: "ativo",
    ultimoAcesso: "2025-06-18T10:30:00",
    criadoEm: "2025-01-01",
  },
  {
    id: 2,
    nome: "Ana Costa",
    email: "ana@petshop.com",
    perfil: "ATENDENTE",
    status: "ativo",
    ultimoAcesso: "2025-06-18T09:15:00",
    criadoEm: "2025-02-15",
  },
  {
    id: 3,
    nome: "Pedro Oliveira",
    email: "pedro@petshop.com",
    perfil: "GROOMER",
    status: "ativo",
    ultimoAcesso: "2025-06-17T16:45:00",
    criadoEm: "2025-03-01",
  },
  {
    id: 4,
    nome: "Carla Santos",
    email: "carla@petshop.com",
    perfil: "ATENDENTE",
    status: "inativo",
    ultimoAcesso: "2025-06-10T14:20:00",
    criadoEm: "2025-04-10",
  },
]

const perfis = [
  {
    id: "ADMIN",
    nome: "Administrador",
    descricao: "Acesso total ao sistema",
    permissoes: ["dashboard", "financeiro", "agenda", "hotel", "pets", "promocoes", "relatorios", "configuracoes"],
    cor: "bg-red-100 text-red-800 border-red-200",
  },
  {
    id: "ATENDENTE",
    nome: "Atendente",
    descricao: "Acesso a agenda, pets e hotel",
    permissoes: ["dashboard", "agenda", "hotel", "pets"],
    cor: "bg-blue-100 text-blue-800 border-blue-200",
  },
  {
    id: "GROOMER",
    nome: "Tosador",
    descricao: "Acesso apenas à agenda",
    permissoes: ["dashboard", "agenda"],
    cor: "bg-green-100 text-green-800 border-green-200",
  },
  {
    id: "VETERINARIO",
    nome: "Veterinário",
    descricao: "Acesso a pets e vacinas",
    permissoes: ["dashboard", "pets"],
    cor: "bg-purple-100 text-purple-800 border-purple-200",
  },
]

const integracoes = [
  {
    id: "whatsapp",
    nome: "WhatsApp Business",
    descricao: "Envio de mensagens e lembretes",
    status: "conectado",
    configurado: true,
    icon: Phone,
  },
  {
    id: "email",
    nome: "E-mail Marketing",
    descricao: "Campanhas promocionais por e-mail",
    status: "conectado",
    configurado: true,
    icon: Mail,
  },
  {
    id: "banco",
    nome: "Integração Bancária",
    descricao: "Importação automática de extratos OFX",
    status: "desconectado",
    configurado: false,
    icon: Database,
  },
  {
    id: "push",
    nome: "Notificações Push",
    descricao: "Firebase Cloud Messaging",
    status: "conectado",
    configurado: true,
    icon: Bell,
  },
]

export function ConfiguracoesPage() {
  const [isUserDialogOpen, setIsUserDialogOpen] = useState(false)
  const [selectedUser, setSelectedUser] = useState<(typeof usuarios)[0] | null>(null)

  const getStatusColor = (status: string) => {
    switch (status) {
      case "ativo":
        return "bg-green-100 text-green-800 border-green-200"
      case "inativo":
        return "bg-red-100 text-red-800 border-red-200"
      default:
        return "bg-gray-100 text-gray-800 border-gray-200"
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case "ativo":
        return "Ativo"
      case "inativo":
        return "Inativo"
      default:
        return "Indefinido"
    }
  }

  const getIntegrationStatusColor = (status: string) => {
    switch (status) {
      case "conectado":
        return "bg-green-100 text-green-800 border-green-200"
      case "desconectado":
        return "bg-red-100 text-red-800 border-red-200"
      default:
        return "bg-gray-100 text-gray-800 border-gray-200"
    }
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Configurações</h1>
          <p className="text-gray-600 dark:text-gray-400">Gerencie usuários, perfis e integrações do sistema</p>
        </div>
      </div>

      <Tabs defaultValue="usuarios" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4 rounded-2xl">
          <TabsTrigger value="usuarios" className="rounded-2xl">
            Usuários
          </TabsTrigger>
          <TabsTrigger value="perfis" className="rounded-2xl">
            Perfis
          </TabsTrigger>
          <TabsTrigger value="integracoes" className="rounded-2xl">
            Integrações
          </TabsTrigger>
          <TabsTrigger value="backup" className="rounded-2xl">
            Backup
          </TabsTrigger>
        </TabsList>

        <TabsContent value="usuarios" className="space-y-6">
          <Card className="rounded-3xl border-0 shadow-lg">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Users className="w-5 h-5 text-cyan-600" />
                    Usuários do Sistema
                  </CardTitle>
                  <CardDescription>Gerencie os usuários e suas permissões</CardDescription>
                </div>
                <Dialog open={isUserDialogOpen} onOpenChange={setIsUserDialogOpen}>
                  <DialogTrigger asChild>
                    <Button className="rounded-2xl bg-gradient-to-r from-cyan-500 to-orange-500">
                      <Plus className="w-4 h-4 mr-2" />
                      Novo Usuário
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="rounded-3xl">
                    <DialogHeader>
                      <DialogTitle>Novo Usuário</DialogTitle>
                      <DialogDescription>Adicione um novo usuário ao sistema</DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label htmlFor="nome">Nome Completo</Label>
                          <Input id="nome" placeholder="Nome do usuário" className="rounded-2xl" />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="email">E-mail</Label>
                          <Input id="email" type="email" placeholder="email@exemplo.com" className="rounded-2xl" />
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label htmlFor="perfil">Perfil</Label>
                          <Select>
                            <SelectTrigger className="rounded-2xl">
                              <SelectValue placeholder="Selecione o perfil" />
                            </SelectTrigger>
                            <SelectContent>
                              {perfis.map((perfil) => (
                                <SelectItem key={perfil.id} value={perfil.id}>
                                  {perfil.nome}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="senha">Senha Temporária</Label>
                          <Input id="senha" type="password" placeholder="Senha temporária" className="rounded-2xl" />
                        </div>
                      </div>
                      <div className="flex justify-end gap-2 pt-4">
                        <Button variant="outline" onClick={() => setIsUserDialogOpen(false)} className="rounded-2xl">
                          Cancelar
                        </Button>
                        <Button className="rounded-2xl bg-gradient-to-r from-cyan-500 to-orange-500">
                          Criar Usuário
                        </Button>
                      </div>
                    </div>
                  </DialogContent>
                </Dialog>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {usuarios.map((usuario) => (
                  <div
                    key={usuario.id}
                    className="p-4 rounded-2xl bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-gradient-to-br from-cyan-500 to-orange-500 rounded-2xl flex items-center justify-center">
                          <span className="text-white font-bold">{usuario.nome.charAt(0)}</span>
                        </div>
                        <div>
                          <p className="font-medium text-gray-900 dark:text-white">{usuario.nome}</p>
                          <p className="text-sm text-gray-600 dark:text-gray-400">{usuario.email}</p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            Último acesso: {new Date(usuario.ultimoAcesso).toLocaleString("pt-BR")}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <Badge className={perfis.find((p) => p.id === usuario.perfil)?.cor || ""}>
                          {perfis.find((p) => p.id === usuario.perfil)?.nome}
                        </Badge>
                        <Badge className={`rounded-xl ${getStatusColor(usuario.status)}`}>
                          {getStatusText(usuario.status)}
                        </Badge>
                        <div className="flex gap-2">
                          <Button variant="ghost" size="sm" className="rounded-xl">
                            <Edit className="w-4 h-4" />
                          </Button>
                          <Button variant="ghost" size="sm" className="rounded-xl">
                            <Key className="w-4 h-4" />
                          </Button>
                          <Button variant="ghost" size="sm" className="rounded-xl text-red-600">
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="perfis" className="space-y-6">
          <Card className="rounded-3xl border-0 shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5 text-orange-600" />
                Perfis de Acesso
              </CardTitle>
              <CardDescription>Configure os níveis de permissão do sistema</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {perfis.map((perfil) => (
                  <Card key={perfil.id} className="rounded-2xl">
                    <CardContent className="p-6">
                      <div className="flex items-start justify-between mb-4">
                        <div>
                          <h3 className="font-bold text-lg text-gray-900 dark:text-white">{perfil.nome}</h3>
                          <p className="text-sm text-gray-600 dark:text-gray-400">{perfil.descricao}</p>
                        </div>
                        <Badge className={perfil.cor}>{perfil.id}</Badge>
                      </div>
                      <div className="space-y-2">
                        <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Permissões:</p>
                        <div className="flex flex-wrap gap-2">
                          {perfil.permissoes.map((permissao) => (
                            <Badge key={permissao} variant="outline" className="rounded-xl text-xs">
                              {permissao}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <div className="flex gap-2 mt-4">
                        <Button variant="outline" size="sm" className="rounded-xl flex-1">
                          <Edit className="w-4 h-4 mr-2" />
                          Editar
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="integracoes" className="space-y-6">
          <Card className="rounded-3xl border-0 shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="w-5 h-5 text-purple-600" />
                Integrações Externas
              </CardTitle>
              <CardDescription>Configure conexões com serviços externos</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {integracoes.map((integracao) => {
                  const Icon = integracao.icon
                  return (
                    <div
                      key={integracao.id}
                      className="p-6 rounded-2xl border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className="p-3 rounded-2xl bg-gray-100 dark:bg-gray-800">
                            <Icon className="w-6 h-6 text-gray-600 dark:text-gray-400" />
                          </div>
                          <div>
                            <h3 className="font-bold text-gray-900 dark:text-white">{integracao.nome}</h3>
                            <p className="text-sm text-gray-600 dark:text-gray-400">{integracao.descricao}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <Badge className={`rounded-xl ${getIntegrationStatusColor(integracao.status)}`}>
                            {integracao.status === "conectado" ? "Conectado" : "Desconectado"}
                          </Badge>
                          <Switch checked={integracao.status === "conectado"} />
                          <Button variant="outline" size="sm" className="rounded-xl">
                            <Settings className="w-4 h-4 mr-2" />
                            Configurar
                          </Button>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="backup" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card className="rounded-3xl border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Download className="w-5 h-5 text-green-600" />
                  Backup dos Dados
                </CardTitle>
                <CardDescription>Faça backup dos dados do sistema</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <p className="text-sm text-gray-600 dark:text-gray-400">Último backup:</p>
                  <p className="font-medium">18/06/2025 às 02:00</p>
                </div>
                <div className="space-y-2">
                  <p className="text-sm text-gray-600 dark:text-gray-400">Tamanho do backup:</p>
                  <p className="font-medium">45.2 MB</p>
                </div>
                <Button className="w-full rounded-2xl bg-green-600 hover:bg-green-700">
                  <Download className="w-4 h-4 mr-2" />
                  Gerar Backup Agora
                </Button>
              </CardContent>
            </Card>

            <Card className="rounded-3xl border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Upload className="w-5 h-5 text-blue-600" />
                  Restaurar Dados
                </CardTitle>
                <CardDescription>Restaure dados de um backup anterior</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="backup-file">Arquivo de Backup</Label>
                  <Input id="backup-file" type="file" accept=".sql,.zip" className="rounded-2xl" />
                </div>
                <div className="p-4 rounded-2xl bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800">
                  <p className="text-sm text-yellow-700 dark:text-yellow-400">
                    ⚠️ A restauração irá sobrescrever todos os dados atuais. Esta ação não pode ser desfeita.
                  </p>
                </div>
                <Button variant="outline" className="w-full rounded-2xl">
                  <Upload className="w-4 h-4 mr-2" />
                  Restaurar Backup
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
