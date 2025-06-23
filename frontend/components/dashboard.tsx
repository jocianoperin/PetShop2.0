"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { TrendingUp, TrendingDown, DollarSign, Calendar, Hotel, PawPrint, AlertTriangle } from "lucide-react"
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from "recharts"

const kpiData = [
  {
    title: "Entradas Hoje",
    value: "R$ 1.240,00",
    change: "+12%",
    trend: "up",
    icon: TrendingUp,
    color: "text-green-600",
  },
  {
    title: "Saídas Hoje",
    value: "R$ 380,00",
    change: "-5%",
    trend: "down",
    icon: TrendingDown,
    color: "text-red-600",
  },
  {
    title: "Saldo Atual",
    value: "R$ 15.680,00",
    change: "+8%",
    trend: "up",
    icon: DollarSign,
    color: "text-cyan-600",
  },
  {
    title: "Vagas Hotel",
    value: "3/8",
    change: "62% ocupação",
    trend: "neutral",
    icon: Hotel,
    color: "text-orange-600",
  },
]

const fluxoCaixaData = [
  { dia: "01", entrada: 800, saida: 300 },
  { dia: "02", entrada: 1200, saida: 450 },
  { dia: "03", entrada: 900, saida: 200 },
  { dia: "04", entrada: 1500, saida: 600 },
  { dia: "05", entrada: 1100, saida: 400 },
  { dia: "06", entrada: 1300, saida: 350 },
  { dia: "07", entrada: 1240, saida: 380 },
]

const agendaHoje = [
  { horario: "09:00", pet: "Luna", servico: "Banho & Tosa", status: "confirmado" },
  { horario: "10:30", pet: "Thor", servico: "Banho", status: "confirmado" },
  { horario: "14:00", pet: "Bella", servico: "Tosa", status: "pendente" },
  { horario: "15:30", pet: "Max", servico: "Banho & Tosa", status: "confirmado" },
]

const alertas = [
  { tipo: "vacina", pet: "Luna", descricao: "Vacina V8 vence em 5 dias", urgencia: "alta" },
  { tipo: "hotel", pet: "Thor", descricao: "Check-out previsto para hoje", urgencia: "media" },
  { tipo: "pagamento", descricao: "3 faturas pendentes", urgencia: "baixa" },
]

export function Dashboard() {
  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
          <p className="text-gray-600 dark:text-gray-400">Visão geral do seu pet shop</p>
        </div>
        <div className="text-sm text-gray-500 dark:text-gray-400">
          Última atualização: {new Date().toLocaleString("pt-BR")}
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {kpiData.map((kpi, index) => {
          const Icon = kpi.icon
          return (
            <Card key={index} className="rounded-3xl border-0 shadow-lg hover:shadow-xl transition-shadow duration-200">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{kpi.title}</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{kpi.value}</p>
                    <p className={`text-sm mt-1 ${kpi.color}`}>{kpi.change}</p>
                  </div>
                  <div
                    className={`p-3 rounded-2xl bg-gradient-to-br ${
                      kpi.color.includes("green")
                        ? "from-green-100 to-green-200 dark:from-green-900 dark:to-green-800"
                        : kpi.color.includes("red")
                          ? "from-red-100 to-red-200 dark:from-red-900 dark:to-red-800"
                          : kpi.color.includes("cyan")
                            ? "from-cyan-100 to-cyan-200 dark:from-cyan-900 dark:to-cyan-800"
                            : "from-orange-100 to-orange-200 dark:from-orange-900 dark:to-orange-800"
                    }`}
                  >
                    <Icon className={`w-6 h-6 ${kpi.color}`} />
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Fluxo de Caixa */}
        <Card className="rounded-3xl border-0 shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-cyan-600" />
              Fluxo de Caixa (7 dias)
            </CardTitle>
            <CardDescription>Entradas vs Saídas dos últimos 7 dias</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={fluxoCaixaData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="dia" />
                <YAxis />
                <Tooltip formatter={(value, name) => [`R$ ${value}`, name === "entrada" ? "Entradas" : "Saídas"]} />
                <Bar dataKey="entrada" fill="#06b6d4" radius={[4, 4, 0, 0]} />
                <Bar dataKey="saida" fill="#f97316" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Agenda Hoje */}
        <Card className="rounded-3xl border-0 shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="w-5 h-5 text-orange-600" />
              Agenda de Hoje
            </CardTitle>
            <CardDescription>{agendaHoje.length} serviços agendados</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {agendaHoje.map((item, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 rounded-2xl bg-gray-50 dark:bg-gray-800"
              >
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-cyan-500"></div>
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">
                      {item.horario} - {item.pet}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">{item.servico}</p>
                  </div>
                </div>
                <Badge variant={item.status === "confirmado" ? "default" : "secondary"} className="rounded-xl">
                  {item.status}
                </Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* Alertas e Ocupação Hotel */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Alertas */}
        <Card className="rounded-3xl border-0 shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-600" />
              Alertas Importantes
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {alertas.map((alerta, index) => (
              <div
                key={index}
                className={`p-4 rounded-2xl border-l-4 ${
                  alerta.urgencia === "alta"
                    ? "border-red-500 bg-red-50 dark:bg-red-900/20"
                    : alerta.urgencia === "media"
                      ? "border-amber-500 bg-amber-50 dark:bg-amber-900/20"
                      : "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                }`}
              >
                <div className="flex items-start gap-3">
                  <div
                    className={`p-2 rounded-xl ${
                      alerta.urgencia === "alta"
                        ? "bg-red-100 dark:bg-red-800"
                        : alerta.urgencia === "media"
                          ? "bg-amber-100 dark:bg-amber-800"
                          : "bg-blue-100 dark:bg-blue-800"
                    }`}
                  >
                    {alerta.tipo === "vacina" && <PawPrint className="w-4 h-4" />}
                    {alerta.tipo === "hotel" && <Hotel className="w-4 h-4" />}
                    {alerta.tipo === "pagamento" && <DollarSign className="w-4 h-4" />}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">
                      {alerta.pet && `${alerta.pet}: `}
                      {alerta.descricao}
                    </p>
                    <Badge
                      variant="outline"
                      className={`mt-1 ${
                        alerta.urgencia === "alta"
                          ? "border-red-500 text-red-700"
                          : alerta.urgencia === "media"
                            ? "border-amber-500 text-amber-700"
                            : "border-blue-500 text-blue-700"
                      }`}
                    >
                      {alerta.urgencia}
                    </Badge>
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Ocupação Hotel */}
        <Card className="rounded-3xl border-0 shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Hotel className="w-5 h-5 text-purple-600" />
              Ocupação do Hotel
            </CardTitle>
            <CardDescription>Status atual das acomodações</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Ocupação Atual</span>
                <span className="font-medium">5/8 boxes</span>
              </div>
              <Progress value={62.5} className="h-3 rounded-xl" />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-4 rounded-2xl bg-green-50 dark:bg-green-900/20">
                <p className="text-2xl font-bold text-green-600">3</p>
                <p className="text-sm text-green-700 dark:text-green-400">Disponíveis</p>
              </div>
              <div className="text-center p-4 rounded-2xl bg-orange-50 dark:bg-orange-900/20">
                <p className="text-2xl font-bold text-orange-600">5</p>
                <p className="text-sm text-orange-700 dark:text-orange-400">Ocupados</p>
              </div>
            </div>

            <div className="space-y-2">
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Check-outs Hoje:</p>
              <div className="space-y-2">
                <div className="flex items-center justify-between p-2 rounded-xl bg-gray-50 dark:bg-gray-800">
                  <span className="text-sm">Thor - Box 3</span>
                  <Badge variant="outline" className="rounded-xl">
                    16:00
                  </Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
