'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';
import { useAuth } from '@/contexts/AuthProvider';
import { LoginForm } from '@/components/LoginForm';
import { ThemeProvider } from '@/components/theme-provider';
import { Sidebar } from '@/components/sidebar';
import { Header } from '@/components/header';
import Navbar from '@/components/Navbar';
import type { User } from '@/types';

// Componente de loading
function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
    </div>
  );
}

// Tipos para as páginas disponíveis no aplicativo
type AppPage = 'dashboard' | 'products' | 'sales' | 'customers' | 'reports' | 'settings';

// Interface para o estado da UI
interface UIState {
  sidebarCollapsed: boolean;
  notificationsOpen: boolean;
  notificationsPinned: boolean;
  mobileMenuOpen: boolean;
  mobileProfileOpen: boolean;
  mobileNotificationsOpen: boolean;
}

// Componente principal da aplicação
function MainApp() {
  // Estado para controlar a página atual
  const [currentPage, setCurrentPage] = useState<AppPage>('dashboard');
  
  // Estado para controlar a interface do usuário
  const [uiState, setUiState] = useState<UIState>({
    sidebarCollapsed: false,
    notificationsOpen: false,
    notificationsPinned: false,
    mobileMenuOpen: false,
    mobileProfileOpen: false,
    mobileNotificationsOpen: false,
  });

  const { logout, user } = useAuth() as { logout: () => void; user: User | null };
  const router = useRouter();

  // Redireciona para a raiz se tentar acessar /dashboard diretamente
  useEffect(() => {
    if (typeof window !== 'undefined' && window.location.pathname === '/dashboard') {
      window.history.replaceState({}, '', '/');
    }
  }, []);

  // Atualiza um estado específico da UI
  const updateUiState = (updates: Partial<UIState>) => {
    setUiState(prev => ({
      ...prev,
      ...updates,
    }));
  };

  // Função de logout
  const handleLogout = () => {
    logout();
    // Reseta o estado da aplicação
    setCurrentPage('dashboard');
    setUiState({
      sidebarCollapsed: false,
      notificationsOpen: false,
      notificationsPinned: false,
      mobileMenuOpen: false,
      mobileProfileOpen: false,
      mobileNotificationsOpen: false,
    });
  };

  // Navegação entre páginas
  const navigateTo = (page: AppPage) => {
    setCurrentPage(page);
    // Fecha o menu mobile após a navegação
    updateUiState({ mobileMenuOpen: false });
  };

  // Componente de carregamento para importações dinâmicas
  const LoadingSpinner = () => (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
    </div>
  );

  // Importação dinâmica dos componentes das páginas
  const Dashboard = dynamic(
    () => import('@/components/dashboard').then((mod) => mod.Dashboard),
    { ssr: false, loading: LoadingSpinner }
  );

  // Mapeamento de páginas para componentes
  const pageComponents: Record<AppPage, React.ReactNode> = {
    dashboard: <Dashboard />,
    products: <div className="p-6">Página de Produtos</div>,
    sales: <div className="p-6">Página de Vendas</div>,
    customers: <div className="p-6">Página de Clientes</div>,
    reports: <div className="p-6">Relatórios</div>,
    settings: <div className="p-6">Configurações</div>,
  };

  // Renderização condicional baseada na página atual
  const renderPage = () => {
    try {
      return (
        <div className="p-6">
          {pageComponents[currentPage]}
        </div>
      );
    } catch (error) {
      console.error(`Erro ao carregar a página ${currentPage}:`, error);
      return (
        <div className="p-6">
          <h2 className="text-xl font-bold text-red-600">Erro ao carregar a página</h2>
          <p className="text-gray-600">A página não pôde ser carregada. Verifique o console para mais detalhes.</p>
        </div>
      );
    }
  };

  // Desestruturação do estado para facilitar o uso
  const {
    sidebarCollapsed,
    notificationsOpen,
    mobileMenuOpen,
  } = uiState;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col">
      {/* Navbar */}
      <Navbar 
        currentPage={currentPage} 
        onPageChange={navigateTo} 
        onMenuToggle={() => updateUiState({ mobileMenuOpen: !uiState.mobileMenuOpen })}
      />
      
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar Desktop */}
        <div className="hidden md:flex">
          <Sidebar 
            currentPage={currentPage}
            onPageChange={navigateTo}
            isCollapsed={sidebarCollapsed}
            onToggleCollapse={() => updateUiState({ sidebarCollapsed: !sidebarCollapsed })}
          />
        </div>
        
        {/* Conteúdo principal */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Header */}
          <Header 
            onSidebarToggle={() => updateUiState({ sidebarCollapsed: !sidebarCollapsed })}
            onNotificationsToggle={() => updateUiState({ 
              notificationsOpen: !notificationsOpen,
              mobileNotificationsOpen: !uiState.mobileNotificationsOpen 
            })}
            unreadNotifications={0}
            onLogout={handleLogout}
          />
          
          {/* Conteúdo da página */}
          <main className="flex-1 overflow-y-auto p-4 md:p-6">
            {renderPage()}
          </main>
        </div>
      
        {/* Menu Mobile Overlay */}
        {mobileMenuOpen && (
          <div className="md:hidden fixed inset-0 z-40">
            <div 
              className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
              onClick={() => updateUiState({ mobileMenuOpen: false })}
            />
            <div className="fixed inset-y-0 left-0 max-w-xs w-full bg-white dark:bg-gray-800 shadow-lg transform transition-transform duration-300 ease-in-out">
              <Sidebar 
                currentPage={currentPage}
                onPageChange={navigateTo}
                isCollapsed={false}
                onToggleCollapse={() => {}}
              />
            </div>
          </div>
        )}

        {/* Notificações Mobile */}
        {uiState.mobileNotificationsOpen && (
          <div className="md:hidden fixed inset-0 z-40">
            <div 
              className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
              onClick={() => updateUiState({ mobileNotificationsOpen: false })}
            />
            <div className="fixed inset-y-0 right-0 max-w-xs w-full bg-white dark:bg-gray-800 shadow-lg transform transition-transform duration-300 ease-in-out">
              <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">Notificações</h3>
              </div>
              <div className="p-4">
                <p className="text-gray-600 dark:text-gray-300">Nenhuma notificação nova.</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function App() {
  const { isLoading, isAuthenticated } = useAuth();
  const [isClient, setIsClient] = useState(false);
  const router = useRouter();

  useEffect(() => {
    setIsClient(true);
  }, []);

  // Redireciona para o dashboard se estiver autenticado e tentar acessar a raiz
  useEffect(() => {
    if (isClient && isAuthenticated) {
      // Usando replace para evitar adicionar ao histórico de navegação
      window.history.replaceState({}, '', '/dashboard');
    }
  }, [isClient, isAuthenticated]);

  // Se ainda estiver carregando ou não for cliente, mostrar o spinner
  if (!isClient || isLoading) {
    return <LoadingSpinner />;
  }

  // Se não estiver autenticado, mostrar o formulário de login
  if (!isAuthenticated) {
    return (
      <ThemeProvider attribute="class" defaultTheme="light" enableSystem>
        <LoginForm onLoginSuccess={() => router.push('/dashboard')} />
      </ThemeProvider>
    );
  }

  // Se estiver autenticado, mostrar o aplicativo principal
  return (
    <ThemeProvider attribute="class" defaultTheme="light" enableSystem>
      <MainApp />
    </ThemeProvider>
  );
}
