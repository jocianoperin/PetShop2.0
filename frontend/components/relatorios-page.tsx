"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { format, subDays, subMonths } from "date-fns"
import { ptBR } from "date-fns/locale"
import {
  Download,
  FileText,
  CalendarIcon,
  TrendingUp,
  DollarSign,
  Hotel,
  Syringe,
  BarChart3,
  PieChart,
  FileSpreadsheet,
} from "lucide-react"

const relatoriosDisponiveis = [
  {
    id: "fluxo-caixa",
    titulo: "Fluxo de Caixa",
    descricao: "Relatório detalhado de entradas e saídas financeiras",
    icon: DollarSign,
    formatos: ["PDF", "CSV", "Excel"],
    color: "text-green-600",
    bgColor: "bg-green-100 dark:bg-green-900",
  },
  {
    id: "ocupacao-hotel",
    titulo: "Ocupação do Hotel",
    descricao: "Taxa de ocupação e receita do hotel por período",
    icon: Hotel,
    formatos: ["PDF", "CSV"],
    color: "text-blue-600",
    bgColor: "bg-blue-100 dark:bg-blue-900",
  },
  {
    id: "vacinas-vencendo",
    titulo: "Vacinas Vencendo",
    descricao: "Lista de pets com vacinas próximas ao vencimento",
    icon: Syringe,
    formatos: ["PDF", "CSV"],
    color: "text-red-600",
    bgColor: "bg-red-100 dark:bg-red-900",
  },
  {
    id: "receita-servicos",
    titulo: "Receita por Serviço",
    descricao: "Análise de receita por tipo de serviço oferecido",
    icon: BarChart3,
    formatos: ["PDF", "Excel"],
    color: "text-purple-600",
    bgColor: "bg-purple-100 dark:bg-purple-900",
  },
  {
    id: "clientes-frequentes",
    titulo: "Clientes Frequentes",
    descricao: "Ranking dos clientes mais assíduos e rentáveis",
    icon: TrendingUp,
    formatos: ["PDF", "CSV"],
    color: "text-orange-600",
    bgColor: "bg-orange-100 dark:bg-orange-900",
  },
  {
    id: "performance-promocoes",
    titulo: "Performance de Promoções",
    descricao: "Análise de efetividade das campanhas promocionais",
    icon: PieChart,
    formatos: ["PDF", "Excel"],
    color: "text-cyan-600",
    bgColor: "bg-cyan-100 dark:bg-cyan-900",
  },
]

const periodosRapidos = [
  { label: "Últimos 7 dias", value: "7d", dataInicio: subDays(new Date(), 7) },
  { label: "Últimos 30 dias", value: "30d", dataInicio: subDays(new Date(), 30) },
  { label: "Último mês", value: "1m", dataInicio: subMonths(new Date(), 1) },
  { label: "Últimos 3 meses", value: "3m", dataInicio: subMonths(new Date(), 3) },
  { label: "Últimos 6 meses", value: "6m", dataInicio: subMonths(new Date(), 6) },
  { label: "Último ano", value: "1y", dataInicio: subMonths(new Date(), 12) },
]

const relatoriosRecentes = [
  {
    id: 1,
    nome: "Fluxo de Caixa - Junho 2025",
    tipo: "fluxo-caixa",
    formato: "PDF",
    dataGeracao: "2025-06-18T10:30:00",
    tamanho: "2.3 MB",
    status: "concluido",
  },
  {
    id: 2,
    nome: "Ocupação Hotel - Maio 2025",
    tipo: "ocupacao-hotel",
    formato: "CSV",
    dataGeracao: "2025-06-15T14:20:00",
    tamanho: "156 KB",
    status: "concluido",
  },
  {
    id: 3,
    nome: "Vacinas Vencendo - Próximos 30 dias",
    tipo: "vacinas-vencendo",
    formato: "PDF",
    dataGeracao: "2025-06-18T09:15:00",
    tamanho: "890 KB",
    status: "processando",
  },
]

export function RelatoriosPage() {
  const [selectedReport, setSelectedReport] = useState<string>("")
  const [selectedPeriod, setSelectedPeriod] = useState<string>("")
  const [selectedFormat, setSelectedFormat] = useState<string>("")
  const [dataInicio, setDataInicio] = useState<Date>()
  const [dataFim, setDataFim] = useState<Date>()
  const [isGenerating, setIsGenerating] = useState(false)

  const handlePeriodChange = (period: string) => {
    setSelectedPeriod(period)
    const periodoSelecionado = periodosRapidos.find((p) => p.value === period)
    if (periodoSelecionado) {
      setDataInicio(periodoSelecionado.dataInicio)
      setDataFim(new Date())
    }
  }

  const handleGenerateReport = async () => {
    if (!selectedReport || !selectedFormat) return

    setIsGenerating(true)
    // Simular geração do relatório
    await new Promise((resolve) => setTimeout(resolve, 2000))
    setIsGenerating(false)

    // Reset form
    setSelectedReport("")
    setSelectedPeriod("")
    setSelectedFormat("")
    setDataInicio(undefined)
    setDataFim(undefined)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "concluido":
        return "bg-green-100 text-green-800 border-green-200"
      case "processando":
        return "bg-yellow-100 text-yellow-800 border-yellow-200"
      case "erro":
        return "bg-red-100 text-red-800 border-red-200"
      default:
        return "bg-gray-100 text-gray-800 border-gray-200"
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case "concluido":
        return "Concluído"
      case "processando":
        return "Processando"
      case "erro":
        return "Erro"
      default:
        return "Indefinido"
    }
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Relatórios</h1>
          <p className="text-gray-600 dark:text-gray-400">Gere relatórios detalhados em PDF e CSV</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Gerador de Relatórios */}
        <Card className="lg:col-span-2 rounded-3xl border-0 shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-cyan-600" />
              Gerar Novo Relatório
            </CardTitle>
            <CardDescription>Selecione o tipo de relatório e período desejado</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Seleção de Relatório */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Tipo de Relatório</label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {relatoriosDisponiveis.map((relatorio) => {
                  const Icon = relatorio.icon
                  return (
                    <button
                      key={relatorio.id}
                      onClick={() => setSelectedReport(relatorio.id)}
                      className={`p-4 rounded-2xl border-2 text-left transition-all duration-200 ${
                        selectedReport === relatorio.id
                          ? "border-cyan-500 bg-cyan-50 dark:bg-cyan-900/20"
                          : "border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600"
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <div className={`p-2 rounded-xl ${relatorio.bgColor}`}>
                          <Icon className={`w-5 h-5 ${relatorio.color}`} />
                        </div>
                        <div className="flex-1">
                          <p className="font-medium text-gray-900 dark:text-white">{relatorio.titulo}</p>
                          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{relatorio.descricao}</p>
                        </div>
                      </div>
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Período */}
            <div className="space-y-4">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Período</label>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {periodosRapidos.map((periodo) => (
                  <Button
                    key={periodo.value}
                    variant={selectedPeriod === periodo.value ? "default" : "outline"}
                    size="sm"
                    className="rounded-xl"
                    onClick={() => handlePeriodChange(periodo.value)}
                  >
                    {periodo.label}
                  </Button>
                ))}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Data Início</label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button variant="outline" className="w-full justify-start text-left font-normal rounded-2xl">
                        <CalendarIcon className="mr-2 h-4 w-4" />
                        {dataInicio ? format(dataInicio, "PPP", { locale: ptBR }) : "Selecionar"}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0 rounded-2xl">
                      <Calendar mode="single" selected={dataInicio} onSelect={setDataInicio} initialFocus />
                    </PopoverContent>
                  </Popover>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Data Fim</label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button variant="outline" className="w-full justify-start text-left font-normal rounded-2xl">
                        <CalendarIcon className="mr-2 h-4 w-4" />
                        {dataFim ? format(dataFim, "PPP", { locale: ptBR }) : "Selecionar"}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0 rounded-2xl">
                      <Calendar mode="single" selected={dataFim} onSelect={setDataFim} initialFocus />
                    </PopoverContent>
                  </Popover>
                </div>
              </div>
            </div>

            {/* Formato */}
            {selectedReport && (
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Formato</label>
                <div className="flex gap-2">
                  {relatoriosDisponiveis
                    .find((r) => r.id === selectedReport)
                    ?.formatos.map((formato) => (
                      <Button
                        key={formato}
                        variant={selectedFormat === formato ? "default" : "outline"}
                        size="sm"
                        className="rounded-xl"
                        onClick={() => setSelectedFormat(formato)}
                      >
                        {formato === "PDF" && <FileText className="w-4 h-4 mr-2" />}
                        {formato === "CSV" && <FileSpreadsheet className="w-4 h-4 mr-2" />}
                        {formato === "Excel" && <FileSpreadsheet className="w-4 h-4 mr-2" />}
                        {formato}
                      </Button>
                    ))}
                </div>
              </div>
            )}

            {/* Botão Gerar */}
            <Button
              onClick={handleGenerateReport}
              disabled={!selectedReport || !selectedFormat || isGenerating}
              className="w-full rounded-2xl bg-gradient-to-r from-cyan-500 to-orange-500 hover:from-cyan-600 hover:to-orange-600"
            >
              {isGenerating ? (
                <>
                  <div className="w-4 h-4 mr-2 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Gerando Relatório...
                </>
              ) : (
                <>
                  <Download className="w-4 h-4 mr-2" />
                  Gerar Relatório
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Relatórios Recentes */}
        <Card className="rounded-3xl border-0 shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-orange-600" />
              Relatórios Recentes
            </CardTitle>
            <CardDescription>Últimos relatórios gerados</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {relatoriosRecentes.map((relatorio) => {
              const tipoRelatorio = relatoriosDisponiveis.find((r) => r.id === relatorio.tipo)
              const Icon = tipoRelatorio?.icon || FileText

              return (
                <div
                  key={relatorio.id}
                  className="p-4 rounded-2xl border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  <div className="flex items-start gap-3">
                    <div className={`p-2 rounded-xl ${tipoRelatorio?.bgColor || "bg-gray-100"}`}>
                      <Icon className={`w-4 h-4 ${tipoRelatorio?.color || "text-gray-600"}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900 dark:text-white truncate">{relatorio.nome}</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {new Date(relatorio.dataGeracao).toLocaleString("pt-BR")}
                      </p>
                      <div className="flex items-center gap-2 mt-2">
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {relatorio.formato} • {relatorio.tamanho}
                        </span>
                        <span
                          className={`px-2 py-1 rounded-lg text-xs font-medium ${getStatusColor(relatorio.status)}`}
                        >
                          {getStatusText(relatorio.status)}
                        </span>
                      </div>
                    </div>
                    {relatorio.status === "concluido" && (
                      <Button variant="ghost" size="sm" className="rounded-xl">
                        <Download className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                </div>
              )
            })}
          </CardContent>
        </Card>
      </div>

      {/* Relatórios Rápidos */}
      <Card className="rounded-3xl border-0 shadow-lg">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-purple-600" />
            Relatórios Rápidos
          </CardTitle>
          <CardDescription>Gere relatórios pré-configurados com um clique</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Button
              variant="outline"
              className="h-24 rounded-2xl flex-col bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 border-green-200 dark:border-green-800"
            >
              <DollarSign className="w-6 h-6 mb-2 text-green-600" />
              <span className="text-sm font-medium">Fluxo de Caixa</span>
              <span className="text-xs text-gray-500">Últimos 30 dias</span>
            </Button>

            <Button
              variant="outline"
              className="h-24 rounded-2xl flex-col bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-blue-200 dark:border-blue-800"
            >
              <Hotel className="w-6 h-6 mb-2 text-blue-600" />
              <span className="text-sm font-medium">Ocupação Hotel</span>
              <span className="text-xs text-gray-500">Mês atual</span>
            </Button>

            <Button
              variant="outline"
              className="h-24 rounded-2xl flex-col bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/20 border-red-200 dark:border-red-800"
            >
              <Syringe className="w-6 h-6 mb-2 text-red-600" />
              <span className="text-sm font-medium">Vacinas Vencendo</span>
              <span className="text-xs text-gray-500">Próximos 30 dias</span>
            </Button>

            <Button
              variant="outline"
              className="h-24 rounded-2xl flex-col bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 border-purple-200 dark:border-purple-800"
            >
              <BarChart3 className="w-6 h-6 mb-2 text-purple-600" />
              <span className="text-sm font-medium">Receita por Serviço</span>
              <span className="text-xs text-gray-500">Últimos 3 meses</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
