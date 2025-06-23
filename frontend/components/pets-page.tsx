"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { format } from "date-fns"
import { ptBR } from "date-fns/locale"
import {
  Plus,
  Search,
  PawPrint,
  User,
  CalendarIcon,
  Phone,
  AlertTriangle,
  Heart,
  Syringe,
  FileText,
  Edit,
  Eye,
} from "lucide-react"

const pets = [
  {
    id: 101,
    nome: "Luna",
    foto: "/placeholder.svg?height=80&width=80",
    especie: "Canina",
    raca: "Golden Retriever",
    porte: "Grande",
    sexo: "Fêmea",
    nascimento: "2022-03-12",
    peso: "28.5 kg",
    cor: "Dourado",
    tutorId: 55,
    tutorNome: "Maria Silva",
    tutorTelefone: "(11) 99999-1111",
    tutorEmail: "maria@email.com",
    endereco: "Rua das Flores, 123",
    observacoes: "Pet nervoso, usar focinheira durante procedimentos",
    status: "ativo",
  },
  {
    id: 102,
    nome: "Thor",
    foto: "/placeholder.svg?height=80&width=80",
    especie: "Canina",
    raca: "Labrador",
    porte: "Grande",
    sexo: "Macho",
    nascimento: "2021-08-15",
    peso: "32.0 kg",
    cor: "Preto",
    tutorId: 56,
    tutorNome: "João Santos",
    tutorTelefone: "(11) 99999-2222",
    tutorEmail: "joao@email.com",
    endereco: "Av. Principal, 456",
    observacoes: "",
    status: "ativo",
  },
  {
    id: 103,
    nome: "Bella",
    foto: "/placeholder.svg?height=80&width=80",
    especie: "Canina",
    raca: "Poodle",
    porte: "Pequeno",
    sexo: "Fêmea",
    nascimento: "2023-01-20",
    peso: "8.2 kg",
    cor: "Branco",
    tutorId: 57,
    tutorNome: "Carlos Lima",
    tutorTelefone: "(11) 99999-3333",
    tutorEmail: "carlos@email.com",
    endereco: "Rua do Parque, 789",
    observacoes: "Primeira vez no pet shop, muito dócil",
    status: "ativo",
  },
  {
    id: 104,
    nome: "Max",
    foto: "/placeholder.svg?height=80&width=80",
    especie: "Canina",
    raca: "Bulldog",
    porte: "Médio",
    sexo: "Macho",
    nascimento: "2020-11-05",
    peso: "22.8 kg",
    cor: "Tigrado",
    tutorId: 58,
    tutorNome: "Ana Rodrigues",
    tutorTelefone: "(11) 99999-4444",
    tutorEmail: "ana@email.com",
    endereco: "Rua da Paz, 321",
    observacoes: "Dieta especial - ração hipoalergênica",
    status: "ativo",
  },
  {
    id: 105,
    nome: "Mimi",
    foto: "/placeholder.svg?height=80&width=80",
    especie: "Felina",
    raca: "Persa",
    porte: "Pequeno",
    sexo: "Fêmea",
    nascimento: "2022-06-30",
    peso: "4.1 kg",
    cor: "Cinza",
    tutorId: 59,
    tutorNome: "Lucia Ferreira",
    tutorTelefone: "(11) 99999-5555",
    tutorEmail: "lucia@email.com",
    endereco: "Rua dos Gatos, 654",
    observacoes: "Muito tímida, manter ambiente calmo",
    status: "ativo",
  },
]

const vacinas = [
  {
    id: 1,
    petId: 101,
    nome: "V8",
    dataAplicacao: "2024-07-15",
    dataVencimento: "2025-07-15",
    veterinario: "Dr. Carlos Vet",
    lote: "ABC123",
    status: "em_dia",
  },
  {
    id: 2,
    petId: 101,
    nome: "Antirrábica",
    dataAplicacao: "2024-08-10",
    dataVencimento: "2025-08-10",
    veterinario: "Dr. Carlos Vet",
    lote: "DEF456",
    status: "em_dia",
  },
  {
    id: 3,
    petId: 102,
    nome: "V8",
    dataAplicacao: "2024-06-20",
    dataVencimento: "2025-06-20",
    veterinario: "Dr. Ana Vet",
    lote: "GHI789",
    status: "vencendo",
  },
  {
    id: 4,
    petId: 103,
    nome: "V8",
    dataAplicacao: "2023-12-15",
    dataVencimento: "2024-12-15",
    veterinario: "Dr. Pedro Vet",
    lote: "JKL012",
    status: "vencida",
  },
]

const historico = [
  {
    id: 1,
    petId: 101,
    data: "2025-06-15",
    tipo: "Banho & Tosa",
    descricao: "Banho com shampoo antipulgas e tosa higiênica",
    profissional: "Ana Costa",
    valor: 90.0,
    observacoes: "Pet se comportou bem",
  },
  {
    id: 2,
    petId: 101,
    data: "2025-05-20",
    tipo: "Consulta Veterinária",
    descricao: "Check-up geral e aplicação de vacina",
    profissional: "Dr. Carlos Vet",
    valor: 150.0,
    observacoes: "Saúde em dia",
  },
  {
    id: 3,
    petId: 102,
    data: "2025-06-10",
    tipo: "Hotel",
    descricao: "Hospedagem por 3 dias",
    profissional: "Equipe Hotel",
    valor: 180.0,
    observacoes: "Pet adaptou-se bem",
  },
]

export function PetsPage() {
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedPet, setSelectedPet] = useState<(typeof pets)[0] | null>(null)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [isDetailDialogOpen, setIsDetailDialogOpen] = useState(false)
  const [selectedDate, setSelectedDate] = useState<Date>()

  const filteredPets = pets.filter(
    (pet) =>
      pet.nome.toLowerCase().includes(searchTerm.toLowerCase()) ||
      pet.tutorNome.toLowerCase().includes(searchTerm.toLowerCase()) ||
      pet.raca.toLowerCase().includes(searchTerm.toLowerCase()),
  )

  const getVacinaStatus = (status: string) => {
    switch (status) {
      case "em_dia":
        return "bg-green-100 text-green-800 border-green-200"
      case "vencendo":
        return "bg-yellow-100 text-yellow-800 border-yellow-200"
      case "vencida":
        return "bg-red-100 text-red-800 border-red-200"
      default:
        return "bg-gray-100 text-gray-800 border-gray-200"
    }
  }

  const getVacinaStatusText = (status: string) => {
    switch (status) {
      case "em_dia":
        return "Em dia"
      case "vencendo":
        return "Vencendo"
      case "vencida":
        return "Vencida"
      default:
        return "Indefinido"
    }
  }

  const calcularIdade = (nascimento: string) => {
    const hoje = new Date()
    const dataNascimento = new Date(nascimento)
    const anos = hoje.getFullYear() - dataNascimento.getFullYear()
    const meses = hoje.getMonth() - dataNascimento.getMonth()

    if (anos === 0) {
      return `${meses} meses`
    } else if (meses < 0) {
      return `${anos - 1} anos e ${12 + meses} meses`
    } else {
      return `${anos} anos e ${meses} meses`
    }
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Pets</h1>
          <p className="text-gray-600 dark:text-gray-400">Gerencie o cadastro completo dos pets</p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button className="rounded-2xl bg-gradient-to-r from-cyan-500 to-orange-500 hover:from-cyan-600 hover:to-orange-600">
              <Plus className="w-4 h-4 mr-2" />
              Novo Pet
            </Button>
          </DialogTrigger>
          <DialogContent className="rounded-3xl max-w-3xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Cadastrar Novo Pet</DialogTitle>
              <DialogDescription>Preencha as informações completas do pet</DialogDescription>
            </DialogHeader>
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="nome">Nome do Pet</Label>
                  <Input id="nome" placeholder="Nome do pet" className="rounded-2xl" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="especie">Espécie</Label>
                  <Select>
                    <SelectTrigger className="rounded-2xl">
                      <SelectValue placeholder="Selecione a espécie" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="canina">Canina</SelectItem>
                      <SelectItem value="felina">Felina</SelectItem>
                      <SelectItem value="ave">Ave</SelectItem>
                      <SelectItem value="roedor">Roedor</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="raca">Raça</Label>
                  <Input id="raca" placeholder="Raça do pet" className="rounded-2xl" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="porte">Porte</Label>
                  <Select>
                    <SelectTrigger className="rounded-2xl">
                      <SelectValue placeholder="Selecione o porte" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="pequeno">Pequeno</SelectItem>
                      <SelectItem value="medio">Médio</SelectItem>
                      <SelectItem value="grande">Grande</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="sexo">Sexo</Label>
                  <Select>
                    <SelectTrigger className="rounded-2xl">
                      <SelectValue placeholder="Selecione o sexo" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="macho">Macho</SelectItem>
                      <SelectItem value="femea">Fêmea</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>Data de Nascimento</Label>
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
                <div className="space-y-2">
                  <Label htmlFor="peso">Peso (kg)</Label>
                  <Input id="peso" type="number" placeholder="0.0" className="rounded-2xl" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="cor">Cor</Label>
                  <Input id="cor" placeholder="Cor do pet" className="rounded-2xl" />
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Dados do Tutor</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="tutorNome">Nome do Tutor</Label>
                    <Input id="tutorNome" placeholder="Nome completo" className="rounded-2xl" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="tutorTelefone">Telefone</Label>
                    <Input id="tutorTelefone" placeholder="(11) 99999-9999" className="rounded-2xl" />
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="tutorEmail">E-mail</Label>
                    <Input id="tutorEmail" type="email" placeholder="email@exemplo.com" className="rounded-2xl" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="endereco">Endereço</Label>
                    <Input id="endereco" placeholder="Endereço completo" className="rounded-2xl" />
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="observacoes">Observações</Label>
                <Input id="observacoes" placeholder="Observações especiais sobre o pet" className="rounded-2xl" />
              </div>

              <div className="flex justify-end gap-2 pt-4">
                <Button variant="outline" onClick={() => setIsDialogOpen(false)} className="rounded-2xl">
                  Cancelar
                </Button>
                <Button className="rounded-2xl bg-gradient-to-r from-cyan-500 to-orange-500">Cadastrar Pet</Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Busca */}
      <Card className="rounded-3xl border-0 shadow-lg">
        <CardContent className="p-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <Input
              placeholder="Buscar por nome do pet, tutor ou raça..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-12 rounded-2xl h-12"
            />
          </div>
        </CardContent>
      </Card>

      {/* Lista de Pets */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredPets.map((pet) => {
          const petVacinas = vacinas.filter((v) => v.petId === pet.id)
          const vacinasVencidas = petVacinas.filter((v) => v.status === "vencida").length
          const vacinasVencendo = petVacinas.filter((v) => v.status === "vencendo").length

          return (
            <Card
              key={pet.id}
              className="rounded-3xl border-0 shadow-lg hover:shadow-xl transition-shadow duration-200"
            >
              <CardContent className="p-6">
                <div className="flex items-start gap-4">
                  <img
                    src={pet.foto || "/placeholder.svg"}
                    alt={pet.nome}
                    className="w-20 h-20 rounded-2xl object-cover"
                  />
                  <div className="flex-1">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="text-xl font-bold text-gray-900 dark:text-white">{pet.nome}</h3>
                        <p className="text-gray-600 dark:text-gray-400">
                          {pet.raca} • {pet.porte}
                        </p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">{calcularIdade(pet.nascimento)}</p>
                      </div>
                      <Badge
                        variant="outline"
                        className={`rounded-xl ${pet.sexo === "Macho" ? "border-blue-500 text-blue-700" : "border-pink-500 text-pink-700"}`}
                      >
                        {pet.sexo}
                      </Badge>
                    </div>

                    <div className="mt-3 space-y-2">
                      <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                        <User className="w-4 h-4" />
                        {pet.tutorNome}
                      </div>
                      <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                        <Phone className="w-4 h-4" />
                        {pet.tutorTelefone}
                      </div>
                    </div>

                    {/* Alertas de Vacinas */}
                    {(vacinasVencidas > 0 || vacinasVencendo > 0) && (
                      <div className="mt-3 space-y-1">
                        {vacinasVencidas > 0 && (
                          <div className="flex items-center gap-2 text-sm text-red-600">
                            <AlertTriangle className="w-4 h-4" />
                            {vacinasVencidas} vacina{vacinasVencidas > 1 ? "s" : ""} vencida
                            {vacinasVencidas > 1 ? "s" : ""}
                          </div>
                        )}
                        {vacinasVencendo > 0 && (
                          <div className="flex items-center gap-2 text-sm text-yellow-600">
                            <AlertTriangle className="w-4 h-4" />
                            {vacinasVencendo} vacina{vacinasVencendo > 1 ? "s" : ""} vencendo
                          </div>
                        )}
                      </div>
                    )}

                    <div className="flex gap-2 mt-4">
                      <Button
                        variant="outline"
                        size="sm"
                        className="rounded-xl flex-1"
                        onClick={() => {
                          setSelectedPet(pet)
                          setIsDetailDialogOpen(true)
                        }}
                      >
                        <Eye className="w-4 h-4 mr-2" />
                        Ver Detalhes
                      </Button>
                      <Button variant="outline" size="sm" className="rounded-xl">
                        <Edit className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Dialog de Detalhes do Pet */}
      <Dialog open={isDetailDialogOpen} onOpenChange={setIsDetailDialogOpen}>
        <DialogContent className="rounded-3xl max-w-4xl max-h-[90vh] overflow-y-auto">
          {selectedPet && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-3">
                  <img
                    src={selectedPet.foto || "/placeholder.svg"}
                    alt={selectedPet.nome}
                    className="w-12 h-12 rounded-2xl object-cover"
                  />
                  <div>
                    <span className="text-2xl">{selectedPet.nome}</span>
                    <p className="text-sm text-gray-600 dark:text-gray-400 font-normal">
                      {selectedPet.raca} • {calcularIdade(selectedPet.nascimento)}
                    </p>
                  </div>
                </DialogTitle>
              </DialogHeader>

              <Tabs defaultValue="dados" className="space-y-6">
                <TabsList className="grid w-full grid-cols-4 rounded-2xl">
                  <TabsTrigger value="dados" className="rounded-2xl">
                    Dados
                  </TabsTrigger>
                  <TabsTrigger value="vacinas" className="rounded-2xl">
                    Vacinas
                  </TabsTrigger>
                  <TabsTrigger value="historico" className="rounded-2xl">
                    Histórico
                  </TabsTrigger>
                  <TabsTrigger value="observacoes" className="rounded-2xl">
                    Observações
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="dados" className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <Card className="rounded-2xl">
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <PawPrint className="w-5 h-5 text-cyan-600" />
                          Informações do Pet
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <p className="text-sm text-gray-600 dark:text-gray-400">Espécie</p>
                            <p className="font-medium">{selectedPet.especie}</p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-600 dark:text-gray-400">Porte</p>
                            <p className="font-medium">{selectedPet.porte}</p>
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <p className="text-sm text-gray-600 dark:text-gray-400">Peso</p>
                            <p className="font-medium">{selectedPet.peso}</p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-600 dark:text-gray-400">Cor</p>
                            <p className="font-medium">{selectedPet.cor}</p>
                          </div>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600 dark:text-gray-400">Data de Nascimento</p>
                          <p className="font-medium">{new Date(selectedPet.nascimento).toLocaleDateString("pt-BR")}</p>
                        </div>
                      </CardContent>
                    </Card>

                    <Card className="rounded-2xl">
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <User className="w-5 h-5 text-orange-600" />
                          Dados do Tutor
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <div>
                          <p className="text-sm text-gray-600 dark:text-gray-400">Nome</p>
                          <p className="font-medium">{selectedPet.tutorNome}</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600 dark:text-gray-400">Telefone</p>
                          <p className="font-medium">{selectedPet.tutorTelefone}</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600 dark:text-gray-400">E-mail</p>
                          <p className="font-medium">{selectedPet.tutorEmail}</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600 dark:text-gray-400">Endereço</p>
                          <p className="font-medium">{selectedPet.endereco}</p>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>

                <TabsContent value="vacinas" className="space-y-6">
                  <div className="flex justify-between items-center">
                    <h3 className="text-lg font-semibold">Cartão de Vacinas</h3>
                    <Button size="sm" className="rounded-xl bg-gradient-to-r from-cyan-500 to-orange-500">
                      <Plus className="w-4 h-4 mr-2" />
                      Nova Vacina
                    </Button>
                  </div>

                  <div className="space-y-4">
                    {vacinas
                      .filter((v) => v.petId === selectedPet.id)
                      .map((vacina) => (
                        <Card key={vacina.id} className="rounded-2xl">
                          <CardContent className="p-4">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-3">
                                <div className="p-2 rounded-xl bg-cyan-100 dark:bg-cyan-900">
                                  <Syringe className="w-5 h-5 text-cyan-600" />
                                </div>
                                <div>
                                  <p className="font-medium text-gray-900 dark:text-white">{vacina.nome}</p>
                                  <p className="text-sm text-gray-600 dark:text-gray-400">
                                    Aplicada em: {new Date(vacina.dataAplicacao).toLocaleDateString("pt-BR")}
                                  </p>
                                  <p className="text-sm text-gray-600 dark:text-gray-400">
                                    Vence em: {new Date(vacina.dataVencimento).toLocaleDateString("pt-BR")}
                                  </p>
                                  <p className="text-xs text-gray-500 dark:text-gray-400">
                                    {vacina.veterinario} • Lote: {vacina.lote}
                                  </p>
                                </div>
                              </div>
                              <Badge className={`rounded-xl ${getVacinaStatus(vacina.status)}`}>
                                {getVacinaStatusText(vacina.status)}
                              </Badge>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                  </div>
                </TabsContent>

                <TabsContent value="historico" className="space-y-6">
                  <h3 className="text-lg font-semibold">Histórico de Serviços</h3>

                  <div className="space-y-4">
                    {historico
                      .filter((h) => h.petId === selectedPet.id)
                      .map((item) => (
                        <Card key={item.id} className="rounded-2xl">
                          <CardContent className="p-4">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-3">
                                <div className="p-2 rounded-xl bg-orange-100 dark:bg-orange-900">
                                  <FileText className="w-5 h-5 text-orange-600" />
                                </div>
                                <div>
                                  <p className="font-medium text-gray-900 dark:text-white">{item.tipo}</p>
                                  <p className="text-sm text-gray-600 dark:text-gray-400">{item.descricao}</p>
                                  <p className="text-sm text-gray-600 dark:text-gray-400">
                                    {new Date(item.data).toLocaleDateString("pt-BR")} • {item.profissional}
                                  </p>
                                  {item.observacoes && (
                                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{item.observacoes}</p>
                                  )}
                                </div>
                              </div>
                              <div className="text-right">
                                <p className="font-bold text-cyan-600">R$ {item.valor.toFixed(2).replace(".", ",")}</p>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                  </div>
                </TabsContent>

                <TabsContent value="observacoes" className="space-y-6">
                  <Card className="rounded-2xl">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <AlertTriangle className="w-5 h-5 text-amber-600" />
                        Observações Especiais
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-gray-700 dark:text-gray-300">
                        {selectedPet.observacoes || "Nenhuma observação especial registrada."}
                      </p>
                    </CardContent>
                  </Card>
                </TabsContent>
              </Tabs>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Estatísticas */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-6">
        <Card className="rounded-3xl border-0 shadow-lg">
          <CardContent className="p-6 text-center">
            <div className="w-12 h-12 mx-auto mb-3 bg-cyan-100 dark:bg-cyan-900 rounded-2xl flex items-center justify-center">
              <PawPrint className="w-6 h-6 text-cyan-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">{pets.length}</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Total de Pets</p>
          </CardContent>
        </Card>

        <Card className="rounded-3xl border-0 shadow-lg">
          <CardContent className="p-6 text-center">
            <div className="w-12 h-12 mx-auto mb-3 bg-green-100 dark:bg-green-900 rounded-2xl flex items-center justify-center">
              <Syringe className="w-6 h-6 text-green-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {vacinas.filter((v) => v.status === "em_dia").length}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Vacinas em Dia</p>
          </CardContent>
        </Card>

        <Card className="rounded-3xl border-0 shadow-lg">
          <CardContent className="p-6 text-center">
            <div className="w-12 h-12 mx-auto mb-3 bg-yellow-100 dark:bg-yellow-900 rounded-2xl flex items-center justify-center">
              <AlertTriangle className="w-6 h-6 text-yellow-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {vacinas.filter((v) => v.status === "vencendo").length}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Vacinas Vencendo</p>
          </CardContent>
        </Card>

        <Card className="rounded-3xl border-0 shadow-lg">
          <CardContent className="p-6 text-center">
            <div className="w-12 h-12 mx-auto mb-3 bg-red-100 dark:bg-red-900 rounded-2xl flex items-center justify-center">
              <Heart className="w-6 h-6 text-red-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {pets.filter((p) => p.status === "ativo").length}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Pets Ativos</p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
