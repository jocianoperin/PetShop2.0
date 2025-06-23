'use client';

import { Fragment } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthProvider';
import { Menu, Transition } from '@headlessui/react';
import { Bars3Icon, XMarkIcon } from '@heroicons/react/24/outline';

type NavItem = {
  name: string;
  id: string;
  icon?: React.ComponentType<{ className?: string }>;
};

const navigation: NavItem[] = [
  { name: 'Dashboard', id: 'dashboard' },
  { name: 'Clientes', id: 'clientes' },
  { name: 'Agendamentos', id: 'agendamentos' },
  { name: 'Produtos', id: 'produtos' },
];

const adminNavigation: NavItem[] = [
  { name: 'Admin', id: 'admin/usuarios' },
];

interface NavbarProps {
  currentPage: string;
  onPageChange: (page: string) => void;
  onMenuToggle?: () => void;
  className?: string;
}

export default function Navbar({ 
  currentPage, 
  onPageChange, 
  onMenuToggle,
  className = '' 
}: NavbarProps) {
  const router = useRouter();
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const handleNavigation = (e: React.MouseEvent, pageId: string) => {
    e.preventDefault();
    onPageChange(pageId);
  };

  // Estilo base para itens de navegação
  const navItemClass = (isActive: boolean) =>
    `${
      isActive
        ? 'border-indigo-500 text-gray-900 dark:text-white'
        : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
    } inline-flex items-center px-3 py-2 border-b-2 text-sm font-medium transition-colors duration-200`;

  return (
    <nav className={`bg-white dark:bg-gray-800 shadow-sm ${className}`}>
      <div className="max-w-7xl mx-auto px-2 sm:px-4 lg:px-6">
        <div className="flex justify-between h-16">
          {/* Lado esquerdo - Logo e navegação desktop */}
          <div className="flex items-center">
            {/* Botão de menu móvel */}
            <div className="flex-shrink-0 flex items-center sm:hidden">
              <button
                type="button"
                onClick={onMenuToggle}
                className="inline-flex items-center justify-center p-2 rounded-md text-gray-500 hover:text-gray-700 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-500"
                aria-expanded="false"
              >
                <span className="sr-only">Abrir menu principal</span>
                <Bars3Icon className="block h-6 w-6" aria-hidden="true" />
              </button>
            </div>

            {/* Logo */}
            <div className="flex-shrink-0 flex items-center ml-2 sm:ml-0">
              <a 
                href="#" 
                onClick={(e) => handleNavigation(e, 'dashboard')}
                className="text-xl font-bold text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300 transition-colors duration-200"
              >
                PetShop
              </a>
            </div>

            {/* Navegação desktop */}
            <div className="hidden sm:ml-6 sm:flex sm:space-x-2">
              {navigation.map((item) => (
                <a
                  key={item.id}
                  href="#"
                  onClick={(e) => handleNavigation(e, item.id)}
                  className={navItemClass(currentPage === item.id)}
                  aria-current={currentPage === item.id ? 'page' : undefined}
                >
                  {item.name}
                </a>
              ))}
              {user?.is_staff && adminNavigation.map((item) => (
                <a
                  key={item.id}
                  href="#"
                  onClick={(e) => handleNavigation(e, item.id)}
                  className={navItemClass(currentPage === item.id)}
                  aria-current={currentPage === item.id ? 'page' : undefined}
                >
                  {item.name}
                </a>
              ))}
            </div>
          </div>

          {/* Lado direito - Perfil e ações do usuário */}
          <div className="flex items-center">
            {user ? (
              <Menu as="div" className="ml-3 relative">
                <div className="flex items-center space-x-2 sm:space-x-4">
                  <div className="hidden sm:block text-right">
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {user.username}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {user.is_staff ? 'Administrador' : 'Usuário'}
                    </p>
                  </div>
                  
                  <Menu.Button className="flex items-center max-w-xs rounded-full bg-white dark:bg-gray-700 text-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                    <span className="sr-only">Abrir menu de usuário</span>
                    <div className="h-8 w-8 rounded-full bg-indigo-100 dark:bg-indigo-800 flex items-center justify-center">
                      <span className="text-indigo-600 dark:text-indigo-200 font-medium">
                        {user.username.charAt(0).toUpperCase()}
                      </span>
                    </div>
                  </Menu.Button>
                </div>

                <Transition
                  as={Fragment}
                  enter="transition ease-out duration-100"
                  enterFrom="transform opacity-0 scale-95"
                  enterTo="transform opacity-100 scale-100"
                  leave="transition ease-in duration-75"
                  leaveFrom="transform opacity-100 scale-100"
                  leaveTo="transform opacity-0 scale-95"
                >
                  <Menu.Items className="origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg py-1 bg-white dark:bg-gray-800 ring-1 ring-black ring-opacity-5 focus:outline-none z-50">
                    <Menu.Item>
                      {({ active }) => (
                        <a
                          href="#"
                          className={`${
                            active ? 'bg-gray-100 dark:bg-gray-700' : ''
                          } block px-4 py-2 text-sm text-gray-700 dark:text-gray-200`}
                        >
                          Seu perfil
                        </a>
                      )}
                    </Menu.Item>
                    <Menu.Item>
                      {({ active }) => (
                        <a
                          href="#"
                          className={`${
                            active ? 'bg-gray-100 dark:bg-gray-700' : ''
                          } block px-4 py-2 text-sm text-gray-700 dark:text-gray-200`}
                        >
                          Configurações
                        </a>
                      )}
                    </Menu.Item>
                    <Menu.Item>
                      {({ active }) => (
                        <button
                          onClick={handleLogout}
                          className={`${
                            active ? 'bg-gray-100 dark:bg-gray-700' : ''
                          } w-full text-left block px-4 py-2 text-sm text-gray-700 dark:text-gray-200`}
                        >
                          Sair
                        </button>
                      )}
                    </Menu.Item>
                  </Menu.Items>
                </Transition>
              </Menu>
            ) : (
              <a
                href="#"
                onClick={(e) => {
                  e.preventDefault();
                  router.push('/login');
                }}
                className="text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300 transition-colors duration-200 px-3 py-2"
              >
                Entrar
              </a>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
