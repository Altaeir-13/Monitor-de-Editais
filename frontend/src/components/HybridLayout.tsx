import { Outlet, Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import Layout from './Layout';
import { FileText, LogIn, UserPlus } from 'lucide-react';

function PublicLayout() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Public Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link to="/notices" className="flex items-center gap-2">
              <div className="p-2 bg-primary-100 rounded-lg">
                <FileText className="text-primary-600" size={20} />
              </div>
              <span className="font-bold text-lg text-gray-900 hidden sm:block">Monitor de Editais</span>
            </Link>

            {/* Auth Buttons */}
            <div className="flex items-center gap-3">
              <Link 
                to="/login" 
                className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors flex items-center gap-1.5"
              >
                <LogIn size={16} />
                Entrar
              </Link>
              <Link 
                to="/register" 
                className="btn-primary py-1.5 px-4 text-sm flex items-center gap-1.5"
              >
                <UserPlus size={16} />
                Cadastrar
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Wrapper */}
      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  );
}

export default function HybridLayout() {
  const { isAuthenticated } = useAuth();

  // If user is authenticated, we render the standard full Layout (with Sidebar).
  // If not, we render the PublicLayout (header only).
  if (isAuthenticated) {
    return <Layout />;
  }

  return <PublicLayout />;
}
