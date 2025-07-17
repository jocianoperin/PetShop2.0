'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthProvider';
import { useTenant } from '@/contexts/TenantProvider';
import { LoginForm } from '@/components/login-form';
import { buildTenantUrl } from '@/lib/tenant';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();
  const { tenantId: detectedTenantId, tenant } = useTenant();
  const router = useRouter();
  const [isRedirecting, setIsRedirecting] = useState(false);

  // If we already have tenant information in the URL (subdomain),
  // we don't need to show the tenant input field
  useEffect(() => {
    // Check if we're on a tenant subdomain
    if (detectedTenantId && typeof window !== 'undefined') {
      // Update the page title with tenant name if available
      if (tenant?.name) {
        document.title = `${tenant.name} - Login`;
      }
    }
  }, [detectedTenantId, tenant]);

  const handleLogin = async (username: string, password: string, tenantId?: string) => {
    setError('');
    
    try {
      // Use the tenant from the login form, or the detected tenant from the subdomain
      const providedTenantId = tenantId || detectedTenantId;
      
      if (!providedTenantId) {
        setError('Por favor, forneça um ID de tenant');
        return;
      }
      
      // If we're not already on a tenant subdomain, redirect to the tenant subdomain
      if (!detectedTenantId && providedTenantId && typeof window !== 'undefined') {
        setIsRedirecting(true);
        setError('');
        
        // Build the tenant URL with the provided tenant ID
        const tenantUrl = `${window.location.protocol}//${providedTenantId}.${window.location.host.split('.').slice(1).join('.')}/login`;
        
        // Show a message before redirecting
        setTimeout(() => {
          window.location.href = tenantUrl;
        }, 1000);
        
        return;
      }
      
      await login(username, password, providedTenantId);
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Usuário ou senha inválidos');
      console.error('Erro no login:', err);
      setIsRedirecting(false);
    }
  };

  return (
    <div>
      {error && (
        <div className="max-w-md mx-auto mt-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
          <span className="block sm:inline">{error}</span>
        </div>
      )}
      
      {isRedirecting && (
        <div className="max-w-md mx-auto mt-4 bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded relative" role="alert">
          <span className="block sm:inline">Redirecionando para o ambiente do tenant...</span>
        </div>
      )}
      
      <LoginForm onLogin={handleLogin} />
      
      <div className="text-center mt-4">
        <p className="text-sm text-gray-600">
          Ainda não tem uma conta?{' '}
          <Link href="/register" className="font-medium text-indigo-600 hover:text-indigo-500">
            Cadastre-se
          </Link>
        </p>
      </div>
    </div>
  );
}
