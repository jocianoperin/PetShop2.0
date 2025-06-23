"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { format } from "date-fns"
import { ptBR } from "date-fns/locale"
import {
  Plus,
  Megaphone,
  CalendarIcon,
  Users,
  Eye,
  Send,
  Edit,
  Trash2,
  Target,
  TrendingUp,
  BarChart3,
} from "lucide-react"

const promocoes = [
  {
    id: 1,
    titulo: "10% OFF Banho & Tosa",
    descricao: "Desconto especial para cães de grande porte",
    desconto: 10,
    tipoDesconto: "percentual",
    validade: "2025-06-30",
    segmento: {
      especie: "Canina",
      porte: "Grande",
      raca: null,
    },
    status: "ativa",
    visualizacoes: 245,
    cliques: 32,
    conversoes: 8,
    dataCriacao: "2025-06-01",
  },
  {
    id: 2,
    titulo: "Shampoo Pelos Sensíveis - R$ 15 OFF",
    descricao: "Desconto fixo para pets com pele sensível",
    desconto: 15,
    tipoDesconto: "fixo",
    validade: "2025-07-15",
    segmento: {
      especie: "Canina",
      porte: "Pequeno",
      raca: null,
    },
    status: "ativa",
    visualizacoes: 189,
    cliques: 28,
    conversoes: 12,
    dataCriacao: "2025-05-20",
  },
  {
    id: 3,
    titulo: "Hotel Pet - 3ª Diária Grátis",
    descricao: "Na hospedagem de 3 dias, a terceira diária é gratuita",
    desconto: 0,
    tipoDesconto: "especial",
    validade: "2025-08-31",
    segmento: {
      especie: null,
      porte: null,
      raca: null,
    },
    status: "pausada",
    visualizacoes: 156,
    cliques: 19,
    conversoes: 5,
    dataCriacao: "2025-06-10",
  },
  {
    id: 4,
    titulo: "Combo Gatos - Banho + Tosa",
    descricao: "Pacote especial para felinos",
    desconto: 20,
    tipoDesconto: "percentual",
    validade: "2025-06-25",
    segmento: {
      especie: "Felina",
      porte: null,
      raca: null,
    },
    status: "expirada",
    visualizacoes: 98,
    cliques: 15,
    conversoes: 3,
    dataCriacao: "2025-05-01",
  },
]

const segmentacaoOptions = {
  especies: ["Canina", "Felina", "Ave", "Roedor"],
  portes: ["Pequeno", "Médio", "Grande"],
  racas: ["Golden Retriever", "Labrador", "Poodle", "Bulldog", "Persa", "Siamês", "Maine Coon"],
}

export function PromocoesPage() {
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [selectedDate, setSelectedDate] = useState<Date>()
  const [searchTerm, setSearchTerm] = useState("")

  const filteredPromocoes = promocoes.filter(
    (promo) =>
      promo.titulo.toLowerCase().includes(searchTerm.toLowerCase()) ||
      promo.descricao.toLowerCase().includes(searchTerm.toLowerCase()),
  )

  const getStatusColor = (status: string) => {
    switch (status) {
      case "ativa":
        return "bg-green-100 text-green-800 border-green-200"
      case "pausada":
        return "bg-yellow-100 text-yellow-800 border-yellow-200"
      case "expirada":
        return "bg-red-100 text-red-800 border-red-200"
      default:
        return "bg-gray-100 text-gray-800 border-gray-200"
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case "ativa":
        return "Ativa"
      case "pausada":
        return "Pausada"
      case "expirada":
        return "Expirada"
      default:
        return "Indefinido"
    }
  }

  const calcularTaxaConversao = (conversoes: number, cliques: number) => {
    if (cliques === 0) return 0
    return ((conversoes / cliques) * 100).toFixed(1)
  }

  const calcularCTR = (cliques: number, visualizacoes: number) => {
    if (visualizacoes === 0) return 0
    return ((cliques / visualizacoes) * 100).toFixed(1)
  }

  const promocoesAtivas = promocoes.filter((p) => p.status === "ativa").length
  const totalVisualizacoes = promocoes.reduce((sum, p) => sum + p.visualizacoes, 0)
  const totalConversoes = promocoes.reduce((sum, p) => sum + p.conversoes, 0)

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Promoções</h1>
          <p className="text-gray-600 dark:text-gray-400">Gerencie campanhas promocionais segmentadas</p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button className="rounded-2xl bg-gradient-to-r from-cyan-500 to-orange-500 hover:from-cyan-600 hover:to-orange-600">
              <Plus className="w-4 h-4 mr-2" />
              Nova Promoção
            </Button>
          </DialogTrigger>
          <DialogContent className="rounded-3xl max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Nova Promoção</DialogTitle>
              <DialogDescription>Crie uma nova campanha promocional segmentada</DialogDescription>
            </DialogHeader>
            <div className="space-y-6">
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="titulo">Título da Promoção</Label>
                  <Input id="titulo" placeholder="Ex: 10% OFF Banho & Tosa" className="rounded-2xl" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="descricao">Descrição</Label>
                  <Textarea
                    id="descricao"
                    placeholder="Descreva os detalhes da promoção"
                    className="rounded-2xl"
                    rows={3}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="tipoDesconto">Tipo de Desconto</Label>
                  <Select>
                    <SelectTrigger className="rounded-2xl">
                      <SelectValue placeholder="Selecione o tipo" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="percentual">Percentual (%)</SelectItem>
                      <SelectItem value="fixo">Valor Fixo (R$)</SelectItem>
                      <SelectItem value="especial">Oferta Especial</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="desconto">Valor do Desconto</Label>
                  <Input id="desconto" type="number" placeholder="0" className="rounded-2xl" />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Data de Validade</Label>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button variant="outline" className="w-full justify-start text-left font-normal rounded-2xl">
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      {selectedDate ? format(selectedDate, "PPP", { locale: ptBR }) : "Selecionar data"}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0 rounded-2xl">
                    <Calendar mode="single" selected={selectedDate} onSelect={setSelectedDate} initialFocus />
                  </PopoverContent>
                </Popover>
              </div>

              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Segmentação</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="especie">Espécie</Label>
                    <Select>
                      <SelectTrigger className="rounded-2xl">
                        <SelectValue placeholder="Todas" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="todas">Todas</SelectItem>
                        {segmentacaoOptions.especies.map((especie) => (
                          <SelectItem key={especie} value={especie.toLowerCase()}>
                            {especie}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="porte">Porte</Label>
                    <Select>
                      <SelectTrigger className="rounded-2xl">
                        <SelectValue placeholder="Todos" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="todos">Todos</SelectItem>
                        {segmentacaoOptions.portes.map((porte) => (
                          <SelectItem key={porte} value={porte.toLowerCase()}>
                            {porte}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="raca">Raça</Label>
                    <Select>
                      <SelectTrigger className="rounded-2xl">
                        <SelectValue placeholder="Todas" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="todas">Todas</SelectItem>
                        {segmentacaoOptions.racas.map((raca) => (
                          <SelectItem key={raca} value={raca.toLowerCase()}>
                            {raca}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-4">
                <Button variant="outline" onClick={() => setIsDialogOpen(false)} className="rounded-2xl">
                  Cancelar
                </Button>
                <Button className="rounded-2xl bg-gradient-to-r from-cyan-500 to-orange-500">Criar Promoção</Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-6">
        <Card className="rounded-3xl border-0 shadow-lg">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Promoções Ativas</p>
                <p className="text-2xl font-bold text-green-600 mt-1">{promocoesAtivas}</p>
              </div>
              <div className="p-3 rounded-2xl bg-green-100 dark:bg-green-900">
                <Megaphone className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-3xl border-0 shadow-lg">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Visualizações</p>
                <p className="text-2xl font-bold text-cyan-600 mt-1">{totalVisualizacoes.toLocaleString()}</p>
              </div>
              <div className="p-3 rounded-2xl bg-cyan-100 dark:bg-cyan-900">
                <Eye className="w-6 h-6 text-cyan-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-3xl border-0 shadow-lg">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Conversões</p>
                <p className="text-2xl font-bold text-orange-600 mt-1">{totalConversoes}</p>
              </div>
              <div className="p-3 rounded-2xl bg-orange-100 dark:bg-orange-900">
                <TrendingUp className="w-6 h-6 text-orange-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-3xl border-0 shadow-lg">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Taxa Conversão Média</p>
                <p className="text-2xl font-bold text-purple-600 mt-1">
                  {calcularTaxaConversao(
                    totalConversoes,
                    promocoes.reduce((sum, p) => sum + p.cliques, 0),
                  )}
                  %
                </p>
              </div>
              <div className="p-3 rounded-2xl bg-purple-100 dark:bg-purple-900">
                <Target className="w-6 h-6 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Busca */}
      <Card className="rounded-3xl border-0 shadow-lg">
        <CardContent className="p-6">
          <div className="relative">
            <Input
              placeholder="Buscar promoções..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="rounded-2xl h-12"
            />
          </div>
        </CardContent>
      </Card>

      {/* Lista de Promoções */}
      <div className="space-y-6">
        {filteredPromocoes.map((promocao) => (
          <Card
            key={promocao.id}
            className="rounded-3xl border-0 shadow-lg hover:shadow-xl transition-shadow duration-200"
          >
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-start gap-4">
                    <div className="p-3 rounded-2xl bg-gradient-to-br from-cyan-100 to-orange-100 dark:from-cyan-900 dark:to-orange-900">
                      <Megaphone className="w-6 h-6 text-cyan-600" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-start justify-between">
                        <div>
                          <h3 className="text-xl font-bold text-gray-900 dark:text-white">{promocao.titulo}</h3>
                          <p className="text-gray-600 dark:text-gray-400 mt-1">{promocao.descricao}</p>
                          <div className="flex items-center gap-4 mt-3">
                            <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                              <CalendarIcon className="w-4 h-4" />
                              Válida até: {new Date(promocao.validade).toLocaleDateString("pt-BR")}
                            </div>
                            {promocao.segmento.especie && (
                              <Badge variant="outline" className="rounded-xl">
                                {promocao.segmento.especie}
                              </Badge>
                            )}
                            {promocao.segmento.porte && (
                              <Badge variant="outline" className="rounded-xl">
                                {promocao.segmento.porte}
                              </Badge>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge className={`rounded-xl ${getStatusColor(promocao.status)}`}>
                            {getStatusText(promocao.status)}
                          </Badge>
                          <Switch checked={promocao.status === "ativa"} disabled={promocao.status === "expirada"} />
                        </div>
                      </div>

                      {/* Estatísticas */}
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 p-4 rounded-2xl bg-gray-50 dark:bg-gray-800">
                        <div className="text-center">
                          <div className="flex items-center justify-center gap-1 text-sm text-gray-600 dark:text-gray-400">
                            <Eye className="w-4 h-4" />
                            Visualizações
                          </div>
                          <p className="text-lg font-bold text-gray-900 dark:text-white">{promocao.visualizacoes}</p>
                        </div>
                        <div className="text-center">
                          <div className="flex items-center justify-center gap-1 text-sm text-gray-600 dark:text-gray-400">
                            <Users className="w-4 h-4" />
                            Cliques
                          </div>
                          <p className="text-lg font-bold text-gray-900 dark:text-white">{promocao.cliques}</p>
                        </div>
                        <div className="text-center">
                          <div className="flex items-center justify-center gap-1 text-sm text-gray-600 dark:text-gray-400">
                            <TrendingUp className="w-4 h-4" />
                            Conversões
                          </div>
                          <p className="text-lg font-bold text-gray-900 dark:text-white">{promocao.conversoes}</p>
                        </div>
                        <div className="text-center">
                          <div className="flex items-center justify-center gap-1 text-sm text-gray-600 dark:text-gray-400">
                            <BarChart3 className="w-4 h-4" />
                            Taxa Conv.
                          </div>
                          <p className="text-lg font-bold text-gray-900 dark:text-white">
                            {calcularTaxaConversao(promocao.conversoes, promocao.cliques)}%
                          </p>
                        </div>
                      </div>

                      {/* Ações */}
                      <div className="flex gap-2 mt-4">
                        <Button variant="outline" size="sm" className="rounded-xl">
                          <Send className="w-4 h-4 mr-2" />
                          Enviar Push
                        </Button>
                        <Button variant="outline" size="sm" className="rounded-xl">
                          <Edit className="w-4 h-4 mr-2" />
                          Editar
                        </Button>
                        <Button variant="outline" size="sm" className="rounded-xl text-red-600 hover:text-red-700">
                          <Trash2 className="w-4 h-4 mr-2" />
                          Excluir
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Segmentação Rápida */}
      <Card className="rounded-3xl border-0 shadow-lg">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="w-5 h-5 text-purple-600" />
            Segmentação Rápida
          </CardTitle>
          <CardDescription>Crie promoções direcionadas para grupos específicos</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button
              variant="outline"
              className="h-20 rounded-2xl flex-col bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-blue-200 dark:border-blue-800"
            >
              <Users className="w-6 h-6 mb-2 text-blue-600" />
              <span className="text-sm font-medium">Cães Pequenos</span>
              <span className="text-xs text-gray-500">2 pets elegíveis</span>
            </Button>
            <Button
              variant="outline"
              className="h-20 rounded-2xl flex-col bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 border-green-200 dark:border-green-800"
            >
              <Users className="w-6 h-6 mb-2 text-green-600" />
              <span className="text-sm font-medium">Cães Grandes</span>
              <span className="text-xs text-gray-500">2 pets elegíveis</span>
            </Button>
            <Button
              variant="outline"
              className="h-20 rounded-2xl flex-col bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20 border-orange-200 dark:border-orange-800"
            >
              <Users className="w-6 h-6 mb-2 text-orange-600" />
              <span className="text-sm font-medium">Gatos</span>
              <span className="text-xs text-gray-500">1 pet elegível</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
