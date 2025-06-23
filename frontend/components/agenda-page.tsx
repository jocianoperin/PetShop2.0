"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
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
import { format, startOfWeek, endOfWeek, eachDayOfInterval } from "date-fns"
import { ptBR } from "date-fns/locale"
import { Plus, CalendarIcon, Clock, User, Scissors, Droplets, ChevronLeft, ChevronRight } from "lucide-react"

const agendamentos = [
  {
    id: 1,
    petId: 101,
    petNome: "Luna",
    tutorNome: "Maria Silva",
    servico: "Banho & Tosa",
    profissional: "Ana Costa",
    data: "2025-06-18",
    inicio: "09:00",
    fim: "10:00",
    preco: 90.0,
    status: "confirmado",
    observacoes: "Pet nervoso, usar focinheira",
  },
  {
    id: 2,
    petId: 102,
    petNome: "Thor",
    tutorNome: "João Santos",
    servico: "Banho",
    profissional: "Ana Costa",
    data: "2025-06-18",
    inicio: "10:30",
    fim: "11:00",
    preco: 50.0,
    status: "confirmado",
    observacoes: "",
  },
  {
    id: 3,
    petId: 103,
    petNome: "Bella",
    tutorNome: "Carlos Lima",
    servico: "Tosa",
    profissional: "Pedro Oliveira",
    data: "2025-06-18",
    inicio: "14:00",
    fim: "15:00",
    preco: 60.0,
    status: "pendente",
    observacoes: "Primeira vez no pet shop",
  },
  {
    id: 4,
    petId: 104,
    petNome: "Max",
    tutorNome: "Ana Rodrigues",
    servico: "Banho & Tosa",
    profissional: "Ana Costa",
    data: "2025-06-18",
    inicio: "15:30",
    fim: "16:30",
    preco: 90.0,
    status: "confirmado",
    observacoes: "",
  },
]

const pets = [
  { id: 101, nome: "Luna", tutor: "Maria Silva", especie: "Canina", raca: "Golden Retriever" },
  { id: 102, nome: "Thor", tutor: "João Santos", especie: "Canina", raca: "Labrador" },
  { id: 103, nome: "Bella", tutor: "Carlos Lima", especie: "Canina", raca: "Poodle" },
  { id: 104, nome: "Max", tutor: "Ana Rodrigues", especie: "Canina", raca: "Bulldog" },
  { id: 105, nome: "Mimi", tutor: "Lucia Ferreira", especie: "Felina", raca: "Persa" },
]

const profissionais = [
  { id: 1, nome: "Ana Costa", especialidade: "Banho & Tosa" },
  { id: 2, nome: "Pedro Oliveira", especialidade: "Tosa Especializada" },
  { id: 3, nome: "Carla Santos", especialidade: "Banho Terapêutico" },
]

const servicos = [
  { nome: "Banho", preco: 50.0, duracao: 30 },
  { nome: "Tosa", preco: 60.0, duracao: 60 },
  { nome: "Banho & Tosa", preco: 90.0, duracao: 60 },
  { nome: "Hidratação", preco: 40.0, duracao: 45 },
  { nome: "Corte de Unhas", preco: 20.0, duracao: 15 },
]

const horarios = [
  "08:00",
  "08:30",
  "09:00",
  "09:30",
  "10:00",
  "10:30",
  "11:00",
  "11:30",
  "13:00",
  "13:30",
  "14:00",
  "14:30",
  "15:00",
  "15:30",
  "16:00",
  "16:30",
  "17:00",
]

export function AgendaPage() {
  const [selectedDate, setSelectedDate] = useState(new Date())
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [viewMode, setViewMode] = useState<"day" | "week">("day")

  const agendamentosHoje = agendamentos.filter((agendamento) => agendamento.data === format(selectedDate, "yyyy-MM-dd"))

  const getStatusColor = (status: string) => {
    switch (status) {
      case "confirmado":
        return "bg-green-100 text-green-800 border-green-200"
      case "pendente":
        return "bg-yellow-100 text-yellow-800 border-yellow-200"
      case "cancelado":
        return "bg-red-100 text-red-800 border-red-200"
      default:
        return "bg-gray-100 text-gray-800 border-gray-200"
    }
  }

  const getServicoIcon = (servico: string) => {
    if (servico.includes("Banho")) return <Droplets className="w-4 h-4" />
    if (servico.includes("Tosa")) return <Scissors className="w-4 h-4" />
    return <User className="w-4 h-4" />
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Agenda</h1>
          <p className="text-gray-600 dark:text-gray-400">Gerencie os agendamentos de banho e tosa</p>
        </div>
        <div className="flex gap-2">
          <div className="flex rounded-2xl border border-gray-200 dark:border-gray-700">
            <Button
              variant={viewMode === "day" ? "default" : "ghost"}
              size="sm"
              onClick={() => setViewMode("day")}
              className="rounded-l-2xl rounded-r-none"
            >
              Dia
            </Button>
            <Button
              variant={viewMode === "week" ? "default" : "ghost"}
              size="sm"
              onClick={() => setViewMode("week")}
              className="rounded-r-2xl rounded-l-none"
            >
              Semana
            </Button>
          </div>
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button className="rounded-2xl bg-gradient-to-r from-cyan-500 to-orange-500 hover:from-cyan-600 hover:to-orange-600">
                <Plus className="w-4 h-4 mr-2" />
                Novo Agendamento
              </Button>
            </DialogTrigger>
            <DialogContent className="rounded-3xl max-w-2xl">
              <DialogHeader>
                <DialogTitle>Novo Agendamento</DialogTitle>
                <DialogDescription>Agende um novo serviço de banho e tosa</DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="pet">Pet</Label>
                    <Select>
                      <SelectTrigger className="rounded-2xl">
                        <SelectValue placeholder="Selecione o pet" />
                      </SelectTrigger>
                      <SelectContent>
                        {pets.map((pet) => (
                          <SelectItem key={pet.id} value={pet.id.toString()}>
                            {pet.nome} - {pet.tutor}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="servico">Serviço</Label>
                    <Select>
                      <SelectTrigger className="rounded-2xl">
                        <SelectValue placeholder="Selecione o serviço" />
                      </SelectTrigger>
                      <SelectContent>
                        {servicos.map((servico) => (
                          <SelectItem key={servico.nome} value={servico.nome}>
                            {servico.nome} - R$ {servico.preco.toFixed(2).replace(".", ",")}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="profissional">Profissional</Label>
                    <Select>
                      <SelectTrigger className="rounded-2xl">
                        <SelectValue placeholder="Selecione o profissional" />
                      </SelectTrigger>
                      <SelectContent>
                        {profissionais.map((prof) => (
                          <SelectItem key={prof.id} value={prof.id.toString()}>
                            {prof.nome} - {prof.especialidade}
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
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="horario">Horário</Label>
                    <Select>
                      <SelectTrigger className="rounded-2xl">
                        <SelectValue placeholder="Selecione o horário" />
                      </SelectTrigger>
                      <SelectContent>
                        {horarios.map((horario) => (
                          <SelectItem key={horario} value={horario}>
                            {horario}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="preco">Preço</Label>
                    <Input id="preco" type="number" placeholder="0,00" className="rounded-2xl" />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="observacoes">Observações</Label>
                  <Input
                    id="observacoes"
                    placeholder="Observações especiais sobre o pet ou serviço"
                    className="rounded-2xl"
                  />
                </div>
                <div className="flex justify-end gap-2 pt-4">
                  <Button variant="outline" onClick={() => setIsDialogOpen(false)} className="rounded-2xl">
                    Cancelar
                  </Button>
                  <Button className="rounded-2xl bg-gradient-to-r from-cyan-500 to-orange-500">Agendar</Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Calendário */}
        <Card className="lg:col-span-1 rounded-3xl border-0 shadow-lg">
          <CardHeader>
            <CardTitle className="text-lg">Calendário</CardTitle>
          </CardHeader>
          <CardContent>
            <Calendar
              mode="single"
              selected={selectedDate}
              onSelect={(date) => date && setSelectedDate(date)}
              className="rounded-2xl"
            />
          </CardContent>
        </Card>

        {/* Agenda do Dia */}
        <Card className="lg:col-span-3 rounded-3xl border-0 shadow-lg">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <CalendarIcon className="w-5 h-5 text-cyan-600" />
                  Agenda de {format(selectedDate, "dd 'de' MMMM", { locale: ptBR })}
                </CardTitle>
                <CardDescription>{agendamentosHoje.length} agendamentos para hoje</CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm" className="rounded-xl">
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                <Button variant="outline" size="sm" className="rounded-xl">
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {viewMode === "day" ? (
              <div className="space-y-4">
                {horarios.map((horario) => {
                  const agendamento = agendamentosHoje.find((a) => a.inicio === horario)

                  return (
                    <div
                      key={horario}
                      className="flex items-center gap-4 p-3 rounded-2xl border border-gray-200 dark:border-gray-700"
                    >
                      <div className="w-16 text-sm font-medium text-gray-600 dark:text-gray-400">{horario}</div>
                      <div className="flex-1">
                        {agendamento ? (
                          <div className="p-4 rounded-2xl bg-gradient-to-r from-cyan-50 to-orange-50 dark:from-cyan-900/20 dark:to-orange-900/20 border border-cyan-200 dark:border-cyan-800">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-3">
                                {getServicoIcon(agendamento.servico)}
                                <div>
                                  <p className="font-medium text-gray-900 dark:text-white">
                                    {agendamento.petNome} - {agendamento.servico}
                                  </p>
                                  <p className="text-sm text-gray-600 dark:text-gray-400">
                                    {agendamento.tutorNome} • {agendamento.profissional}
                                  </p>
                                  {agendamento.observacoes && (
                                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                      {agendamento.observacoes}
                                    </p>
                                  )}
                                </div>
                              </div>
                              <div className="flex items-center gap-2">
                                <Badge className={`rounded-xl ${getStatusColor(agendamento.status)}`}>
                                  {agendamento.status}
                                </Badge>
                                <span className="font-bold text-cyan-600">
                                  R$ {agendamento.preco.toFixed(2).replace(".", ",")}
                                </span>
                              </div>
                            </div>
                          </div>
                        ) : (
                          <div className="p-4 rounded-2xl bg-gray-50 dark:bg-gray-800 border-2 border-dashed border-gray-300 dark:border-gray-600">
                            <p className="text-sm text-gray-500 dark:text-gray-400 text-center">Horário disponível</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="grid grid-cols-7 gap-2">
                {eachDayOfInterval({
                  start: startOfWeek(selectedDate, { weekStartsOn: 0 }),
                  end: endOfWeek(selectedDate, { weekStartsOn: 0 }),
                }).map((day) => (
                  <div key={day.toISOString()} className="p-2 rounded-2xl border border-gray-200 dark:border-gray-700">
                    <div className="text-center">
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        {format(day, "EEE", { locale: ptBR })}
                      </p>
                      <p className="text-xs text-gray-600 dark:text-gray-400">{format(day, "dd")}</p>
                    </div>
                    <div className="mt-2 space-y-1">
                      {agendamentos
                        .filter((a) => a.data === format(day, "yyyy-MM-dd"))
                        .slice(0, 3)
                        .map((agendamento) => (
                          <div key={agendamento.id} className="p-1 rounded-lg bg-cyan-100 dark:bg-cyan-900/20 text-xs">
                            <p className="font-medium truncate">{agendamento.petNome}</p>
                            <p className="text-gray-600 dark:text-gray-400 truncate">{agendamento.inicio}</p>
                          </div>
                        ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Estatísticas Rápidas */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-6">
        <Card className="rounded-3xl border-0 shadow-lg">
          <CardContent className="p-6 text-center">
            <div className="w-12 h-12 mx-auto mb-3 bg-cyan-100 dark:bg-cyan-900 rounded-2xl flex items-center justify-center">
              <Calendar className="w-6 h-6 text-cyan-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">{agendamentosHoje.length}</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Hoje</p>
          </CardContent>
        </Card>

        <Card className="rounded-3xl border-0 shadow-lg">
          <CardContent className="p-6 text-center">
            <div className="w-12 h-12 mx-auto mb-3 bg-green-100 dark:bg-green-900 rounded-2xl flex items-center justify-center">
              <Clock className="w-6 h-6 text-green-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {agendamentosHoje.filter((a) => a.status === "confirmado").length}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Confirmados</p>
          </CardContent>
        </Card>

        <Card className="rounded-3xl border-0 shadow-lg">
          <CardContent className="p-6 text-center">
            <div className="w-12 h-12 mx-auto mb-3 bg-yellow-100 dark:bg-yellow-900 rounded-2xl flex items-center justify-center">
              <User className="w-6 h-6 text-yellow-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {agendamentosHoje.filter((a) => a.status === "pendente").length}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Pendentes</p>
          </CardContent>
        </Card>

        <Card className="rounded-3xl border-0 shadow-lg">
          <CardContent className="p-6 text-center">
            <div className="w-12 h-12 mx-auto mb-3 bg-orange-100 dark:bg-orange-900 rounded-2xl flex items-center justify-center">
              <Scissors className="w-6 h-6 text-orange-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              R${" "}
              {agendamentosHoje
                .reduce((sum, a) => sum + a.preco, 0)
                .toFixed(2)
                .replace(".", ",")}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Receita Hoje</p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
