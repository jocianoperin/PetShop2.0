'use client';

import { useAuth } from '@/hooks/useAuth';

export default function DashboardPage() {
  const { user, logout } = useAuth();

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <div className="text-sm text-muted-foreground">
          Olá, {user?.nome}!
        </div>
      </div>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {/* Estatísticas podem ser adicionadas aqui */}
        <div className="rounded-lg border bg-card text-card-foreground shadow-sm p-6">
          <h3 className="text-sm font-medium">Total de Clientes</h3>
          <p className="text-2xl font-bold">0</p>
        </div>
        <div className="rounded-lg border bg-card text-card-foreground shadow-sm p-6">
          <h3 className="text-sm font-medium">Total de Animais</h3>
          <p className="text-2xl font-bold">0</p>
        </div>
        <div className="rounded-lg border bg-card text-card-foreground shadow-sm p-6">
          <h3 className="text-sm font-medium">Hospedagens Ativas</h3>
          <p className="text-2xl font-bold">0</p>
        </div>
        <div className="rounded-lg border bg-card text-card-foreground shadow-sm p-6">
          <h3 className="text-sm font-medium">Agendamentos Hoje</h3>
          <p className="text-2xl font-bold">0</p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <div className="rounded-lg border bg-card text-card-foreground shadow-sm p-6 col-span-4">
          <h3 className="text-lg font-semibold mb-4">Atividades Recentes</h3>
          <div className="text-sm text-muted-foreground">
            Nenhuma atividade recente.
          </div>
        </div>
        <div className="rounded-lg border bg-card text-card-foreground shadow-sm p-6 col-span-3">
          <h3 className="text-lg font-semibold mb-4">Próximos Agendamentos</h3>
          <div className="text-sm text-muted-foreground">
            Nenhum agendamento agendado.
          </div>
        </div>
      </div>
    </div>
  );
}
