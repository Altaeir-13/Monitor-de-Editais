import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import {
  LayoutDashboard,
  Bell,
  AlertTriangle,
  LogOut,
  Shield,
  FileText,
  Menu,
  X,
  Sun,
  Moon,
} from 'lucide-react';
import { useState } from 'react';
import { useTheme } from '../contexts/ThemeContext';

const userNavItems = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/notices', label: 'Editais', icon: FileText },
  { to: '/alerts', label: 'Meus Alertas', icon: AlertTriangle },
  { to: '/notifications', label: 'Notificações', icon: Bell },
];

const adminNavItems = [
  { to: '/admin', label: 'Admin', icon: Shield },
  { to: '/admin/institutions', label: 'Instituições', icon: Shield },
  { to: '/admin/sources', label: 'Fontes', icon: Shield },
];

export default function Layout() {
  const { user, isAdmin, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="min-h-screen flex">
      {/* Mobile sidebar toggle */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-[var(--theme-surface)] rounded-lg shadow-md border border-[var(--theme-border)]"
        aria-label="Toggle menu"
      >
        {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      {/* Sidebar */}
      <aside
        className={`
          fixed inset-y-0 left-0 z-40 w-64 glass-panel border-r border-[var(--theme-border)]
          transform transition-transform duration-200 ease-in-out
          lg:translate-x-0 lg:static lg:inset-auto bg-[var(--theme-surface)]/80
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="h-16 flex items-center px-6 border-b border-[var(--theme-border)]">
            <Link to="/dashboard" className="flex items-center gap-2">
              <FileText className="text-[var(--theme-primary-600)]" size={24} />
              <span className="font-bold text-lg text-[var(--theme-text-primary)]">Monitor de Editais</span>
            </Link>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
            {userNavItems.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.to}
                  to={item.to}
                  onClick={() => setSidebarOpen(false)}
                  className={`
                    flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium
                    transition-colors duration-150
                    ${
                      isActive(item.to)
                        ? 'bg-[var(--theme-primary-50)] text-[var(--theme-primary-700)] border border-[var(--theme-primary-100)] shadow-sm'
                        : 'text-[var(--theme-text-secondary)] hover:bg-[var(--theme-background)] hover:text-[var(--theme-text-primary)]'
                    }
                  `}
                >
                  <Icon size={18} />
                  {item.label}
                </Link>
              );
            })}

            {isAdmin && (
              <>
                <div className="pt-4 pb-2">
                  <p className="px-3 text-xs font-semibold text-[var(--theme-muted)] uppercase tracking-wider">
                    Administração
                  </p>
                </div>
                {adminNavItems.map((item) => {
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.to}
                      to={item.to}
                      onClick={() => setSidebarOpen(false)}
                      className={`
                        flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium
                        transition-colors duration-150
                        ${
                          isActive(item.to)
                            ? 'bg-[var(--theme-primary-50)] text-[var(--theme-primary-700)] border border-[var(--theme-primary-100)] shadow-sm'
                            : 'text-[var(--theme-text-secondary)] hover:bg-[var(--theme-background)] hover:text-[var(--theme-text-primary)]'
                        }
                      `}
                    >
                      <Icon size={18} />
                      {item.label}
                    </Link>
                  );
                })}
              </>
            )}
          </nav>

          {/* Theme Toggle */}
          <div className="px-4 py-3 border-t border-[var(--theme-border)]">
            <button
              onClick={toggleTheme}
              className="flex items-center gap-3 w-full px-3 py-2 rounded-lg text-sm font-medium text-[var(--theme-text-secondary)] hover:bg-[var(--theme-background)] hover:text-[var(--theme-text-primary)] transition-colors"
              aria-label="Alternar tema"
            >
              {theme === 'dark' ? (
                <>
                  <Sun size={18} />
                  Modo claro
                </>
              ) : (
                <>
                  <Moon size={18} />
                  Modo escuro
                </>
              )}
            </button>
          </div>

          {/* User info + Logout */}
          <div className="border-t border-[var(--theme-border)] p-4">
            <div className="flex items-center justify-between">
              <div className="min-w-0">
                <p className="text-sm font-medium text-[var(--theme-text-primary)] truncate">
                  {user?.name}
                </p>
                <p className="text-xs text-[var(--theme-text-secondary)] truncate">
                  {user?.email}
                </p>
              </div>
              <button
                onClick={handleLogout}
                className="p-2 text-[var(--theme-muted)] hover:text-red-600 transition-colors"
                title="Sair"
              >
                <LogOut size={18} />
              </button>
            </div>
          </div>
        </div>
      </aside>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main content */}
      <main className="flex-1 min-h-screen lg:pl-0">
        <div className="p-6 pt-16 lg:p-8 max-w-7xl mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
