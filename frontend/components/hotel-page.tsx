"use client"

import { useState, useEffect } from "react"
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
import { format, differenceInDays } from "date-fns"
import { ptBR } from "date-fns/locale"
import { Plus, Hotel, CalendarIcon, User, Clock, MapPin, Phone, AlertCircle, CheckCircle, XCircle } from "lucide-react"
import { api } from "@/lib/api"

// Interfaces para tipar os dados
interface Pet {
  id: number;
  nome: string;
  tutor: string;
  especie: string;
  porte: string;
}

interface Box {
  id: number;
  nome: string;
  tipo: string;
  capacidade: number;
  ocupado: boolean;
}

interface Hospedagem {
  id: number;
  petId: number;
  petNome: string;
  petFoto?: string;
  tutorNome: string;
  tutorTelefone: string;
  checkIn: string;
  checkOut: string;
  boxId: number;
  status: string;
  observacoes: string;
  valorDiaria: number;
}

// Interface para o formulário de nova hospedagem
interface NovaHospedagemForm {
  pet: string;
  check_in: string;
  check_out: string;
  box: number;
  observacoes: string;
  valor_diaria: number;
}

const HotelPage = () => {
  // Estados para gerenciar os dados
  const [hospedagens, setHospedagens] = useState<Hospedagem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  // Estados para armazenar boxes e pets da API
  const [boxes, setBoxes] = useState<Box[]>([]);
  const [pets, setPets] = useState<Pet[]>([]);

  // Carrega os dados da API
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Busca paralela de todos os dados necessários
        const [hospedagensData, animaisData, clientesData] = await Promise.all([
          api.getHospedagens(),
          api.getAnimais(),
          api.getClientes()
        ]);

        // Mapear animais para incluir informações do tutor
        const petsComTutor = animaisData.map(animal => {
          const tutor = clientesData.find(c => c.id === animal.tutor);
          return {
            id: animal.id!,
            nome: animal.nome,
            tutor: tutor?.nome || 'Tutor não encontrado',
            especie: animal.especie,
            porte: animal.raca // Usando raca como porte temporariamente
          };
        });

        // Criar boxes baseados nas hospedagens ativas
        const boxesAtivos = [
          { id: 1, nome: "Box 1", tipo: "Pequeno", capacidade: 1, ocupado: false },
          { id: 2, nome: "Box 2", tipo: "Pequeno", capacidade: 1, ocupado: false },
          { id: 3, nome: "Box 3", tipo: "Médio", capacidade: 1, ocupado: false },
          { id: 4, nome: "Box 4", tipo: "Médio", capacidade: 1, ocupado: false },
          { id: 5, nome: "Box 5", tipo: "Grande", capacidade: 2, ocupado: false },
          { id: 6, nome: "Box 6", tipo: "Grande", capacidade: 2, ocupado: false },
          { id: 7, nome: "Box 7", tipo: "Grande", capacidade: 2, ocupado: false },
          { id: 8, nome: "Box 8", tipo: "Gatos", capacidade: 1, ocupado: false },
        ];

        // Atualizar status dos boxes com base nas hospedagens ativas
        const hospedagensAtivas = hospedagensData.filter(h => 
          h.status === 'ativo' || h.status === 'reservado'
        );
        
        const boxesAtualizados = boxesAtivos.map(box => ({
          ...box,
          ocupado: hospedagensAtivas.some(h => h.box === box.id)
        }));

        setHospedagens(hospedagensData);
        setBoxes(boxesAtualizados);
        setPets(petsComTutor);
      } catch (err) {
        console.error('Erro ao buscar dados:', err);
        setError('Erro ao carregar os dados. Tente novamente mais tarde.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Estado para o formulário de nova hospedagem
  const [novaHospedagem, setNovaHospedagem] = useState<NovaHospedagemForm>({
    pet: '',
    check_in: '',
    check_out: '',
    box: 1,
    observacoes: '',
    valor_diaria: 60.0
  });

  // Estado para controlar o diálogo de nova hospedagem
  const [dialogAberto, setDialogAberto] = useState(false);

  // Função para lidar com a criação de uma nova hospedagem
  const handleCriarHospedagem = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      // Usando o serviço api para criar a hospedagem
      const data = await api.createHospedagem({
        pet: parseInt(novaHospedagem.pet),
        check_in: novaHospedagem.check_in,
        check_out: novaHospedagem.check_out,
        box: novaHospedagem.box,
        observacoes: novaHospedagem.observacoes,
        valor_diaria: novaHospedagem.valor_diaria
      });
      
      // Atualizar a lista de hospedagens com a nova hospedagem
      setHospedagens([...hospedagens, {
        id: data.id || 0,
        petId: data.pet,
        petNome: pets.find(p => p.id === parseInt(novaHospedagem.pet))?.nome || 'Pet não encontrado',
        tutorNome: pets.find(p => p.id === parseInt(novaHospedagem.pet))?.tutor || 'Tutor não encontrado',
        tutorTelefone: '', // Preencher com telefone real se necessário
        checkIn: data.check_in,
        checkOut: data.check_out,
        boxId: data.box,
        status: data.status,
        observacoes: data.observacoes || '',
        valorDiaria: data.valor_diaria
      }]);
      
      // Atualizar status do box para ocupado
      setBoxes(boxes.map(box => 
        box.id === data.box ? { ...box, ocupado: true } : box
      ));
      
      // Fechar o diálogo e limpar o formulário
      setDialogAberto(false);
      setNovaHospedagem({
        pet: '',
        check_in: '',
        check_out: '',
        box: boxes.find(b => !b.ocupado)?.id || 1, // Selecionar o próximo box disponível
        observacoes: '',
        valor_diaria: 60.0
      });
      
    } catch (err) {
      console.error('Erro ao criar hospedagem:', err);
      const errorMessage = err instanceof Error ? err.message : 'Erro desconhecido';
      alert(`Erro ao criar hospedagem: ${errorMessage}`);
    }
  };

  // Estados para o diálogo de nova hospedagem
  const [selectedCheckIn, setSelectedCheckIn] = useState<Date>();
  const [selectedCheckOut, setSelectedCheckOut] = useState<Date>();
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const getStatusColor = (status: string): string => {
    switch (status) {
      case "ativo":
        return "bg-green-100 text-green-800 border-green-200"
      case "checkout_hoje":
        return "bg-yellow-100 text-yellow-800 border-yellow-200"
      case "cancelado":
        return "bg-red-100 text-red-800 border-red-200"
      default:
        return "bg-gray-100 text-gray-800 border-gray-200"
    }
  }

  const getBoxColor = (ocupado: boolean, tipo: string): string => {
    if (ocupado) return 'bg-red-100 border-red-200';
    
    switch (tipo) {
      case 'Pequeno':
        return 'bg-blue-50 border-blue-100';
      case 'Médio':
        return 'bg-purple-50 border-purple-100';
      case 'Grande':
        return 'bg-yellow-50 border-yellow-100';
      case 'Gatos':
        return 'bg-green-50 border-green-100';
      default:
        return 'bg-gray-50 border-gray-100';
    }
  }

  const calcularDias = (checkIn: string, checkOut: string): number => {
    try {
      const inicio = new Date(checkIn);
      const fim = new Date(checkOut);
      const dias = differenceInDays(fim, inicio);
      return dias > 0 ? dias : 1;
    } catch (error) {
      console.error('Erro ao calcular dias:', error);
      return 1;
    }
  }

  const calcularTotal = (checkIn: string, checkOut: string, valorDiaria: number): number => {
    try {
      const dias = calcularDias(checkIn, checkOut);
      return dias * valorDiaria;
    } catch (error) {
      console.error('Erro ao calcular total:', error);
      return 0;
    }
  }
  
  // Função auxiliar para formatar valores monetários
  const formatarMoeda = (valor: number): string => {
    return valor.toLocaleString('pt-BR', { 
      style: 'currency', 
      currency: 'BRL',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }

  const boxesDisponiveis: number = boxes.filter((box: Box) => !box.ocupado).length;
  const boxesOcupados: number = boxes.filter((box: Box) => box.ocupado).length;
  const checkoutsHoje: number = hospedagens.filter((h: Hospedagem) => h.status === "checkout_hoje").length;

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Hotel</h1>
          <p className="text-gray-600 dark:text-gray-400">Gerencie as hospedagens dos pets</p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button className="rounded-2xl bg-gradient-to-r from-cyan-500 to-orange-500 hover:from-cyan-600 hover:to-orange-600">
              <Plus className="w-4 h-4 mr-2" />
              Nova Hospedagem
            </Button>
          </DialogTrigger>
          <DialogContent className="rounded-3xl max-w-2xl">
            <DialogHeader>
              <DialogTitle>Nova Hospedagem</DialogTitle>
              <DialogDescription>Registre uma nova hospedagem no hotel</DialogDescription>
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
                          {pet.nome} - {pet.tutor} ({pet.porte})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="box">Box</Label>
                  <Select>
                    <SelectTrigger className="rounded-2xl">
                      <SelectValue placeholder="Selecione o box" />
                    </SelectTrigger>
                    <SelectContent>
                      {boxes
                        .filter((box) => !box.ocupado)
                        .map((box) => (
                          <SelectItem key={box.id} value={box.id.toString()}>
                            {box.nome} - {box.tipo}
                          </SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Check-in</Label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button variant="outline" className="w-full justify-start text-left font-normal rounded-2xl">
                        <CalendarIcon className="mr-2 h-4 w-4" />
                        {selectedCheckIn ? format(selectedCheckIn, "PPP", { locale: ptBR }) : "Selecionar data"}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0 rounded-2xl">
                      <Calendar mode="single" selected={selectedCheckIn} onSelect={setSelectedCheckIn} initialFocus />
                    </PopoverContent>
                  </Popover>
                </div>
                <div className="space-y-2">
                  <Label>Check-out</Label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button variant="outline" className="w-full justify-start text-left font-normal rounded-2xl">
                        <CalendarIcon className="mr-2 h-4 w-4" />
                        {selectedCheckOut ? format(selectedCheckOut, "PPP", { locale: ptBR }) : "Selecionar data"}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0 rounded-2xl">
                      <Calendar mode="single" selected={selectedCheckOut} onSelect={setSelectedCheckOut} initialFocus />
                    </PopoverContent>
                  </Popover>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="valor">Valor da Diária</Label>
                  <Input id="valor" type="number" placeholder="60,00" className="rounded-2xl" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="telefone">Telefone do Tutor</Label>
                  <Input id="telefone" placeholder="(11) 99999-9999" className="rounded-2xl" />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="observacoes">Observações</Label>
                <Input id="observacoes" placeholder="Observações especiais sobre o pet" className="rounded-2xl" />
              </div>
              {selectedCheckIn && selectedCheckOut && (
                <div className="p-4 rounded-2xl bg-cyan-50 dark:bg-cyan-900/20 border border-cyan-200 dark:border-cyan-800">
                  <p className="text-sm text-cyan-700 dark:text-cyan-400">
                    <strong>Período:</strong> {differenceInDays(selectedCheckOut, selectedCheckIn)} dias
                  </p>
                  <p className="text-sm text-cyan-700 dark:text-cyan-400">
                    <strong>Total estimado:</strong> R${" "}
                    {(differenceInDays(selectedCheckOut, selectedCheckIn) * 60).toFixed(2).replace(".", ",")}
                  </p>
                </div>
              )}
              <div className="flex justify-end gap-2 pt-4">
                <Button variant="outline" onClick={() => setIsDialogOpen(false)} className="rounded-2xl">
                  Cancelar
                </Button>
                <Button className="rounded-2xl bg-gradient-to-r from-cyan-500 to-orange-500">
                  Registrar Hospedagem
                </Button>
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
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Boxes Disponíveis</p>
                <p className="text-2xl font-bold text-green-600 mt-1">{boxesDisponiveis}</p>
              </div>
              <div className="p-3 rounded-2xl bg-green-100 dark:bg-green-900">
                <CheckCircle className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-3xl border-0 shadow-lg">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Boxes Ocupados</p>
                <p className="text-2xl font-bold text-red-600 mt-1">{boxesOcupados}</p>
              </div>
              <div className="p-3 rounded-2xl bg-red-100 dark:bg-red-900">
                <XCircle className="w-6 h-6 text-red-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-3xl border-0 shadow-lg">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Check-outs Hoje</p>
                <p className="text-2xl font-bold text-yellow-600 mt-1">{checkoutsHoje}</p>
              </div>
              <div className="p-3 rounded-2xl bg-yellow-100 dark:bg-yellow-900">
                <Clock className="w-6 h-6 text-yellow-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-3xl border-0 shadow-lg">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Taxa de Ocupação</p>
                <p className="text-2xl font-bold text-cyan-600 mt-1">
                  {Math.round((boxesOcupados / boxes.length) * 100)}%
                </p>
              </div>
              <div className="p-3 rounded-2xl bg-cyan-100 dark:bg-cyan-900">
                <Hotel className="w-6 h-6 text-cyan-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Mapa de Boxes */}
        <Card className="lg:col-span-2 rounded-3xl border-0 shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MapPin className="w-5 h-5 text-purple-600" />
              Mapa de Boxes
            </CardTitle>
            <CardDescription>Status atual de todos os boxes do hotel</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {boxes.map((box) => {
                const hospedagem = hospedagens.find((h) => h.boxId === box.id && h.status !== "cancelado")

                return (
                  <div
                    key={box.id}
                    className={`p-4 rounded-2xl border-2 transition-all duration-200 hover:shadow-lg ${getBoxColor(box.ocupado, box.tipo)}`}
                  >
                    <div className="text-center">
                      <div className="w-12 h-12 mx-auto mb-2 bg-white dark:bg-gray-800 rounded-2xl flex items-center justify-center shadow-sm">
                        <Hotel className="w-6 h-6 text-gray-600 dark:text-gray-400" />
                      </div>
                      <p className="font-medium text-gray-900 dark:text-white">{box.nome}</p>
                      <p className="text-xs text-gray-600 dark:text-gray-400">{box.tipo}</p>
                      {hospedagem && (
                        <div className="mt-2 p-2 bg-white dark:bg-gray-800 rounded-xl">
                          <p className="text-xs font-medium text-gray-900 dark:text-white">{hospedagem.petNome}</p>
                          <p className="text-xs text-gray-600 dark:text-gray-400">
                            {calcularDias(hospedagem.checkIn, hospedagem.checkOut)} dias
                          </p>
                        </div>
                      )}
                      <Badge
                        variant="outline"
                        className={`mt-2 text-xs ${box.ocupado ? "border-red-500 text-red-700" : "border-green-500 text-green-700"}`}
                      >
                        {box.ocupado ? "Ocupado" : "Disponível"}
                      </Badge>
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>

        {/* Check-outs Hoje */}
        <Card className="rounded-3xl border-0 shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-orange-600" />
              Check-outs Hoje
            </CardTitle>
            <CardDescription>Pets com saída prevista para hoje</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {hospedagens
              .filter((h) => h.status === "checkout_hoje")
              .map((hospedagem) => (
                <div
                  key={hospedagem.id}
                  className="p-4 rounded-2xl bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800"
                >
                  <div className="flex items-center gap-3">
                    <img
                      src={hospedagem.petFoto || "/placeholder.svg"}
                      alt={hospedagem.petNome}
                      className="w-12 h-12 rounded-2xl object-cover"
                    />
                    <div className="flex-1">
                      <p className="font-medium text-gray-900 dark:text-white">{hospedagem.petNome}</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">{hospedagem.tutorNome}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        Box {hospedagem.boxId} • {calcularDias(hospedagem.checkIn, hospedagem.checkOut)} dias
                      </p>
                    </div>
                  </div>
                  <div className="flex justify-between items-center mt-3">
                    <span className="text-sm font-medium text-yellow-700 dark:text-yellow-400">
                      Total: {formatarMoeda(calcularTotal(hospedagem.checkIn, hospedagem.checkOut, hospedagem.valorDiaria))}
                    </span>
                    <Button size="sm" className="rounded-xl bg-yellow-600 hover:bg-yellow-700">
                      Check-out
                    </Button>
                  </div>
                </div>
              ))}
          </CardContent>
        </Card>
      </div>

      {/* Lista de Hospedagens Ativas */}
      <Card className="rounded-3xl border-0 shadow-lg">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="w-5 h-5 text-cyan-600" />
            Hospedagens Ativas
          </CardTitle>
          <CardDescription>Todos os pets atualmente hospedados</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {hospedagens
              .filter((h) => h.status === "ativo")
              .map((hospedagem) => (
                <div
                  key={hospedagem.id}
                  className="p-6 rounded-2xl bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <img
                        src={hospedagem.petFoto || "/placeholder.svg"}
                        alt={hospedagem.petNome}
                        className="w-16 h-16 rounded-2xl object-cover"
                      />
                      <div>
                        <p className="font-bold text-lg text-gray-900 dark:text-white">{hospedagem.petNome}</p>
                        <p className="text-gray-600 dark:text-gray-400">{hospedagem.tutorNome}</p>
                        <div className="flex items-center gap-4 mt-1">
                          <div className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400">
                            <Phone className="w-4 h-4" />
                            {hospedagem.tutorTelefone}
                          </div>
                          <div className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400">
                            <MapPin className="w-4 h-4" />
                            Box {hospedagem.boxId}
                          </div>
                        </div>
                        {hospedagem.observacoes && (
                          <div className="flex items-center gap-1 mt-2">
                            <AlertCircle className="w-4 h-4 text-amber-500" />
                            <p className="text-sm text-amber-700 dark:text-amber-400">{hospedagem.observacoes}</p>
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge className={`rounded-xl ${getStatusColor(hospedagem.status)}`}>
                          {hospedagem.status === "ativo" ? "Ativo" : hospedagem.status}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Check-in: {new Date(hospedagem.checkIn).toLocaleDateString("pt-BR")}
                      </p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Check-out: {new Date(hospedagem.checkOut).toLocaleDateString("pt-BR")}
                      </p>
                      <p className="text-lg font-bold text-cyan-600 mt-1">
                        {formatarMoeda(calcularTotal(hospedagem.checkIn, hospedagem.checkOut, hospedagem.valorDiaria))}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {calcularDias(hospedagem.checkIn, hospedagem.checkOut)} dias
                      </p>
                    </div>
                  </div>
                </div>
              ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
