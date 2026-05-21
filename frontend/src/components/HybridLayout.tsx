import { Outlet, Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useTheme } from '../contexts/ThemeContext';
import Layout from './Layout';
import { FileText, LogIn, UserPlus, Sun, Moon } from 'lucide-react';

function PublicLayout() {
  const { theme, toggleTheme } = useTheme();
  return (
    <div className="min-h-screen bg-[var(--theme-background)] flex flex-col">
      {/* Public Header */}
      <header className="bg-[var(--theme-surface)] border-b border-[var(--theme-border)]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link to="/notices" className="flex items-center gap-2">
              <div className="p-2 bg-[var(--theme-primary-100)] rounded-lg">
                <FileText className="text-[var(--theme-primary-600)]" size={20} />
              </div>
              <span className="font-bold text-lg text-[var(--theme-text-primary)] hidden sm:block">Monitor de Editais</span>
            </Link>

            {/* Auth Buttons & Theme */}
            <div className="flex items-center gap-3">
              <button
                onClick={toggleTheme}
                className="p-2 text-[var(--theme-text-secondary)] hover:text-[var(--theme-text-primary)] transition-colors rounded-lg hover:bg-[var(--theme-background)]"
                aria-label="Alternar tema"
              >
                {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
              </button>
              
              <Link 
                to="/login" 
                className="text-sm font-medium text-[var(--theme-text-secondary)] hover:text-[var(--theme-text-primary)] transition-colors flex items-center gap-1.5"
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
