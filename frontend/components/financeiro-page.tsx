"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
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
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { format } from "date-fns"
import { ptBR } from "date-fns/locale"
import {
  Plus,
  Search,
  Filter,
  Download,
  TrendingUp,
  TrendingDown,
  DollarSign,
  CalendarIcon,
  Edit,
  Trash2,
} from "lucide-react"

const transacoes = [
  {
    id: 1,
    data: "2025-06-18",
    descricao: "Banho & Tosa - Luna",
    tipo: "ENTRADA",
    valor: 90.0,
    categoria: "Serviços",
    status: "confirmado",
  },
  {
    id: 2,
    data: "2025-06-18",
    descricao: "Hotel - Thor (3 dias)",
    tipo: "ENTRADA",
    valor: 180.0,
    categoria: "Hotel",
    status: "confirmado",
  },
  {
    id: 3,
    data: "2025-06-17",
    descricao: "Compra de Shampoo",
    tipo: "SAIDA",
    valor: 45.0,
    categoria: "Produtos",
    status: "pago",
  },
  {
    id: 4,
    data: "2025-06-17",
    descricao: "Banho - Max",
    tipo: "ENTRADA",
    valor: 50.0,
    categoria: "Serviços",
    status: "confirmado",
  },
  {
    id: 5,
    data: "2025-06-16",
    descricao: "Energia Elétrica",
    tipo: "SAIDA",
    valor: 280.0,
    categoria: "Despesas Fixas",
    status: "pago",
  },
]

const categorias = [
  { nome: "Serviços", cor: "bg-cyan-500" },
  { nome: "Hotel", cor: "bg-orange-500" },
  { nome: "Produtos", cor: "bg-green-500" },
  { nome: "Despesas Fixas", cor: "bg-red-500" },
  { nome: "Marketing", cor: "bg-purple-500" },
]

export function FinanceiroPage() {
  const [selectedDate, setSelectedDate] = useState<Date>()
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedCategory, setSelectedCategory] = useState("todas")

  const filteredTransacoes = transacoes.filter((transacao) => {
    const matchesSearch = transacao.descricao.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesCategory = selectedCategory === "todas" || transacao.categoria === selectedCategory
    return matchesSearch && matchesCategory
  })

  const totalEntradas = transacoes.filter((t) => t.tipo === "ENTRADA").reduce((sum, t) => sum + t.valor, 0)

  const totalSaidas = transacoes.filter((t) => t.tipo === "SAIDA").reduce((sum, t) => sum + t.valor, 0)

  const saldoAtual = totalEntradas - totalSaidas

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Financeiro</h1>
          <p className="text-gray-600 dark:text-gray-400">Controle completo das finanças</p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button className="rounded-2xl bg-gradient-to-r from-cyan-500 to-orange-500 hover:from-cyan-600 hover:to-orange-600">
              <Plus className="w-4 h-4 mr-2" />
              Nova Transação
            </Button>
          </DialogTrigger>
          <DialogContent className="rounded-3xl">
            <DialogHeader>
              <DialogTitle>Nova Transação</DialogTitle>
              <DialogDescription>Adicione uma nova entrada ou saída financeira</DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="tipo">Tipo</Label>
                  <Select>
                    <SelectTrigger className="rounded-2xl">
                      <SelectValue placeholder="Selecione o tipo" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="entrada">Entrada</SelectItem>
                      <SelectItem value="saida">Saída</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="valor">Valor</Label>
                  <Input id="valor" type="number" placeholder="0,00" className="rounded-2xl" />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="descricao">Descrição</Label>
                <Input id="descricao" placeholder="Descrição da transação" className="rounded-2xl" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="categoria">Categoria</Label>
                  <Select>
                    <SelectTrigger className="rounded-2xl">
                      <SelectValue placeholder="Selecione a categoria" />
                    </SelectTrigger>
                    <SelectContent>
                      {categorias.map((categoria) => (
                        <SelectItem key={categoria.nome} value={categoria.nome}>
                          {categoria.nome}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Data</Label>
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
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <Button variant="outline" onClick={() => setIsDialogOpen(false)} className="rounded-2xl">
                  Cancelar
                </Button>
                <Button className="rounded-2xl bg-gradient-to-r from-cyan-500 to-orange-500">Salvar</Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* KPIs Financeiros */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <Card className="rounded-3xl border-0 shadow-lg">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Entradas</p>
                <p className="text-2xl font-bold text-green-600 mt-1">
                  R$ {totalEntradas.toFixed(2).replace(".", ",")}
                </p>
              </div>
              <div className="p-3 rounded-2xl bg-green-100 dark:bg-green-900">
                <TrendingUp className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-3xl border-0 shadow-lg">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Saídas</p>
                <p className="text-2xl font-bold text-red-600 mt-1">R$ {totalSaidas.toFixed(2).replace(".", ",")}</p>
              </div>
              <div className="p-3 rounded-2xl bg-red-100 dark:bg-red-900">
                <TrendingDown className="w-6 h-6 text-red-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-3xl border-0 shadow-lg">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Saldo Atual</p>
                <p className={`text-2xl font-bold mt-1 ${saldoAtual >= 0 ? "text-cyan-600" : "text-red-600"}`}>
                  R$ {saldoAtual.toFixed(2).replace(".", ",")}
                </p>
              </div>
              <div className="p-3 rounded-2xl bg-cyan-100 dark:bg-cyan-900">
                <DollarSign className="w-6 h-6 text-cyan-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="lancamentos" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3 rounded-2xl">
          <TabsTrigger value="lancamentos" className="rounded-2xl">
            Lançamentos
          </TabsTrigger>
          <TabsTrigger value="categorias" className="rounded-2xl">
            Categorias
          </TabsTrigger>
          <TabsTrigger value="relatorios" className="rounded-2xl">
            Relatórios
          </TabsTrigger>
        </TabsList>

        <TabsContent value="lancamentos" className="space-y-6">
          {/* Filtros */}
          <Card className="rounded-3xl border-0 shadow-lg">
            <CardContent className="p-6">
              <div className="flex flex-col sm:flex-row gap-4">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <Input
                      placeholder="Buscar transações..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10 rounded-2xl"
                    />
                  </div>
                </div>
                <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                  <SelectTrigger className="w-full sm:w-48 rounded-2xl">
                    <Filter className="w-4 h-4 mr-2" />
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="todas">Todas as categorias</SelectItem>
                    {categorias.map((categoria) => (
                      <SelectItem key={categoria.nome} value={categoria.nome}>
                        {categoria.nome}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button variant="outline" className="rounded-2xl">
                  <Download className="w-4 h-4 mr-2" />
                  Exportar
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Lista de Transações */}
          <Card className="rounded-3xl border-0 shadow-lg">
            <CardHeader>
              <CardTitle>Transações Recentes</CardTitle>
              <CardDescription>{filteredTransacoes.length} transações encontradas</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {filteredTransacoes.map((transacao) => (
                  <div
                    key={transacao.id}
                    className="flex items-center justify-between p-4 rounded-2xl bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      <div
                        className={`w-3 h-3 rounded-full ${
                          transacao.tipo === "ENTRADA" ? "bg-green-500" : "bg-red-500"
                        }`}
                      />
                      <div>
                        <p className="font-medium text-gray-900 dark:text-white">{transacao.descricao}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            {new Date(transacao.data).toLocaleDateString("pt-BR")}
                          </p>
                          <Badge variant="outline" className="rounded-xl text-xs">
                            {transacao.categoria}
                          </Badge>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <p className={`font-bold ${transacao.tipo === "ENTRADA" ? "text-green-600" : "text-red-600"}`}>
                        {transacao.tipo === "ENTRADA" ? "+" : "-"}R$ {transacao.valor.toFixed(2).replace(".", ",")}
                      </p>
                      <div className="flex gap-2">
                        <Button variant="ghost" size="sm" className="rounded-xl">
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button variant="ghost" size="sm" className="rounded-xl text-red-600 hover:text-red-700">
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="categorias" className="space-y-6">
          <Card className="rounded-3xl border-0 shadow-lg">
            <CardHeader>
              <CardTitle>Categorias</CardTitle>
              <CardDescription>Gerencie as categorias de transações</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {categorias.map((categoria) => (
                  <div
                    key={categoria.nome}
                    className="p-4 rounded-2xl border border-gray-200 dark:border-gray-700 hover:shadow-lg transition-shadow"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-4 h-4 rounded-full ${categoria.cor}`} />
                      <span className="font-medium">{categoria.nome}</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="relatorios" className="space-y-6">
          <Card className="rounded-3xl border-0 shadow-lg">
            <CardHeader>
              <CardTitle>Relatórios Financeiros</CardTitle>
              <CardDescription>Gere relatórios detalhados das suas finanças</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Button variant="outline" className="h-20 rounded-2xl flex-col">
                  <Download className="w-6 h-6 mb-2" />
                  Fluxo de Caixa Mensal
                </Button>
                <Button variant="outline" className="h-20 rounded-2xl flex-col">
                  <Download className="w-6 h-6 mb-2" />
                  Receita por Categoria
                </Button>
                <Button variant="outline" className="h-20 rounded-2xl flex-col">
                  <Download className="w-6 h-6 mb-2" />
                  Despesas Detalhadas
                </Button>
                <Button variant="outline" className="h-20 rounded-2xl flex-col">
                  <Download className="w-6 h-6 mb-2" />
                  Comparativo Anual
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
