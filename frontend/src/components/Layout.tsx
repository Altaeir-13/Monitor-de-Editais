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
import { useState, useEffect } from 'react';
import { useTheme } from '../contexts/ThemeContext';

interface IconProps {
  size?: number;
  className?: string;
}

function CollapseSidebarIcon({ size = 18, className }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <line x1="5" y1="4" x2="5" y2="20" />
      <line x1="19" y1="12" x2="9" y2="12" />
      <polyline points="13 8 9 12 13 16" />
    </svg>
  );
}

function ExpandSidebarIcon({ size = 18, className }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <line x1="5" y1="4" x2="5" y2="20" />
      <line x1="9" y1="12" x2="19" y2="12" />
      <polyline points="15 8 19 12 15 16" />
    </svg>
  );
}

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
  const [isCollapsed, setIsCollapsed] = useState(() => {
    return localStorage.getItem('monitor_editais_sidebar_collapsed') === 'true';
  });

  useEffect(() => {
    localStorage.setItem('monitor_editais_sidebar_collapsed', String(isCollapsed));
  }, [isCollapsed]);

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  const isActive = (path: string) => {
    if (path === '/notices') return location.pathname.startsWith('/notices');
    return location.pathname === path;
  };

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
          fixed inset-y-0 left-0 z-40 glass-panel border-r border-[var(--theme-border)]
          transform transition-all duration-200 ease-in-out
          lg:translate-x-0 lg:sticky lg:top-0 lg:h-screen lg:shrink-0 bg-[var(--theme-surface)]/80
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
          w-64 ${isCollapsed ? 'lg:w-20' : 'lg:w-64'}
        `}
      >
        <div className="flex flex-col h-full relative">
          {/* Logo & Toggle */}
          <div className={`h-16 flex items-center ${isCollapsed ? 'justify-center gap-1 px-1' : 'justify-between px-4'} border-b border-[var(--theme-border)]`}>
            <Link to="/dashboard" className="flex items-center shrink-0" title="Monitor de Editais">
              <FileText className="text-[var(--theme-primary-600)]" size={24} />
            </Link>
            {!isCollapsed && (
              <span className="font-bold text-base text-[var(--theme-text-primary)] truncate ml-2 mr-auto">Monitor Editais</span>
            )}
            <button
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="hidden lg:flex items-center justify-center w-9 h-9 shrink-0 rounded-lg bg-[var(--theme-surface)] border border-[var(--theme-border)] shadow-sm text-[var(--theme-text-secondary)] hover:text-[var(--theme-primary-600)] hover:bg-[var(--theme-background)] hover:border-[var(--theme-primary-300)] focus:outline-none focus:ring-2 focus:ring-[var(--theme-primary-500)] transition-all duration-200"
              title={isCollapsed ? "Expandir sidebar" : "Recolher sidebar"}
              aria-label={isCollapsed ? "Expandir sidebar" : "Recolher sidebar"}
            >
              {isCollapsed ? <ExpandSidebarIcon size={18} /> : <CollapseSidebarIcon size={18} />}
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto overflow-x-hidden">
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
                    ${isCollapsed ? 'lg:justify-center lg:px-0' : ''}
                    ${
                      isActive(item.to)
                        ? 'bg-[var(--theme-primary-50)] text-[var(--theme-primary-700)] border border-[var(--theme-primary-100)] shadow-sm'
                        : 'text-[var(--theme-text-secondary)] hover:bg-[var(--theme-background)] hover:text-[var(--theme-text-primary)]'
                    }
                  `}
                  title={item.label}
                >
                  <Icon size={18} className="shrink-0" />
                  <span className={`${isCollapsed ? 'lg:hidden' : ''}`}>{item.label}</span>
                </Link>
              );
            })}

            {isAdmin && (
              <>
                <div className={`pt-4 pb-2 ${isCollapsed ? 'lg:flex lg:justify-center' : ''}`}>
                  <p className={`px-3 text-xs font-semibold text-[var(--theme-muted)] uppercase tracking-wider ${isCollapsed ? 'lg:hidden' : ''}`}>
                    Administração
                  </p>
                  <div className={`hidden ${isCollapsed ? 'lg:block' : ''} w-8 h-px bg-[var(--theme-border)]`} />
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
                        ${isCollapsed ? 'lg:justify-center lg:px-0' : ''}
                        ${
                          isActive(item.to)
                            ? 'bg-[var(--theme-primary-50)] text-[var(--theme-primary-700)] border border-[var(--theme-primary-100)] shadow-sm'
                            : 'text-[var(--theme-text-secondary)] hover:bg-[var(--theme-background)] hover:text-[var(--theme-text-primary)]'
                        }
                      `}
                      title={item.label}
                    >
                      <Icon size={18} className="shrink-0" />
                      <span className={`${isCollapsed ? 'lg:hidden' : ''}`}>{item.label}</span>
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
              className={`flex items-center gap-3 w-full px-3 py-2 rounded-lg text-sm font-medium text-[var(--theme-text-secondary)] hover:bg-[var(--theme-background)] hover:text-[var(--theme-text-primary)] transition-colors ${isCollapsed ? 'lg:justify-center lg:px-0' : ''}`}
              title={theme === 'dark' ? "Modo claro" : "Modo escuro"}
              aria-label="Alternar tema"
            >
              {theme === 'dark' ? <Sun size={18} className="shrink-0" /> : <Moon size={18} className="shrink-0" />}
              <span className={`${isCollapsed ? 'lg:hidden' : ''}`}>
                {theme === 'dark' ? 'Modo claro' : 'Modo escuro'}
              </span>
            </button>
          </div>

          {/* User info + Logout */}
          <div className={`border-t border-[var(--theme-border)] p-4 flex items-center ${isCollapsed ? 'lg:justify-center' : 'justify-between'}`}>
            <div className={`min-w-0 ${isCollapsed ? 'lg:hidden' : ''}`}>
              <p className="text-sm font-medium text-[var(--theme-text-primary)] truncate" title={user?.name}>
                {user?.name}
              </p>
              <p className="text-xs text-[var(--theme-text-secondary)] truncate" title={user?.email}>
                {user?.email}
              </p>
            </div>
            <button
              onClick={handleLogout}
              className="p-2 text-[var(--theme-muted)] hover:text-red-600 transition-colors shrink-0"
              title="Sair"
              aria-label="Sair"
            >
              <LogOut size={18} />
            </button>
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
      <main className="flex-1 min-h-screen min-w-0 overflow-y-auto lg:pl-0">
        <div className="p-6 pt-16 lg:p-8 max-w-7xl mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
