import { Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { useAlerts } from '../../hooks/useAlerts';
import { useNotifications } from '../../hooks/useNotifications';
import Spinner from '../../components/ui/Spinner';
import ErrorMessage from '../../components/ui/ErrorMessage';
import {
  AlertTriangle,
  Bell,
  ChevronRight,
  Plus,
  FileText,
} from 'lucide-react';

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—';
  try {
    return new Intl.DateTimeFormat('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    }).format(new Date(dateStr));
  } catch {
    return '—';
  }
}

const STATUS_BADGES: Record<string, { label: string; classes: string }> = {
  pending: { label: 'Pendente', classes: 'bg-yellow-50 text-yellow-700' },
  sent: { label: 'Enviada', classes: 'bg-green-50 text-green-700' },
  failed: { label: 'Falhou', classes: 'bg-red-50 text-red-700' },
};

export default function DashboardPage() {
  const { user } = useAuth();
  const {
    data: alerts,
    isLoading: alertsLoading,
    isError: alertsError,
    refetch: refetchAlerts,
  } = useAlerts();
  const {
    data: notifications,
    isLoading: notifsLoading,
    isError: notifsError,
    refetch: refetchNotifs,
  } = useNotifications(0, 5);

  const activeAlerts = alerts?.filter((a) => a.is_active) ?? [];
  const recentNotifications = notifications ?? [];

  const isLoading = alertsLoading || notifsLoading;

  if (isLoading) {
    return <Spinner text="Carregando dashboard..." />;
  }

  return (
    <div>
      {/* Hero / Greeting */}
      <div className="mb-8 p-8 glass-panel rounded-2xl text-center md:text-left flex flex-col md:flex-row items-center justify-between gap-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 tracking-tight">
            Bem-vindo, {user?.name?.split(' ')[0] ?? 'Usuário'}!
          </h1>
          <p className="text-base text-gray-500 mt-2 max-w-xl leading-relaxed">
            Aqui você encontra o resumo das suas atividades. Acompanhe os editais mais recentes e gerencie seus alertas para não perder nenhuma oportunidade.
          </p>
        </div>
        <div className="flex gap-3">
          <Link to="/notices" className="btn-secondary">
            Explorar Editais
          </Link>
          <Link to="/alerts" className="btn-primary">
            <Plus size={18} /> Novo Alerta
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Alerts Card */}
        <div className="glass-panel rounded-2xl overflow-hidden flex flex-col">
          <div className="flex items-center justify-between p-5 border-b border-gray-100">
            <div className="flex items-center gap-2">
              <AlertTriangle className="text-primary-600" size={20} />
              <h2 className="font-semibold text-gray-900">Meus Alertas</h2>
            </div>
            <Link
              to="/alerts"
              className="text-xs text-primary-600 hover:text-primary-700 font-medium flex items-center gap-0.5"
            >
              Ver todos <ChevronRight size={14} />
            </Link>
          </div>
          <div className="p-5">
            {alertsError ? (
              <ErrorMessage
                message="Erro ao carregar alertas."
                onRetry={() => refetchAlerts()}
              />
            ) : activeAlerts.length === 0 ? (
              <div className="text-center py-6">
                <p className="text-sm text-gray-500 mb-4 px-4">
                  Crie alertas com palavras-chave para ser avisado automaticamente quando novos editais forem encontrados no diário oficial.
                </p>
                <Link
                  to="/alerts"
                  className="inline-flex items-center gap-1 btn-primary"
                >
                  <Plus size={16} />
                  Criar meu primeiro alerta
                </Link>
              </div>
            ) : (
              <div>
                <p className="text-3xl font-bold text-primary-600 mb-1">
                  {activeAlerts.length}
                </p>
                <p className="text-sm text-gray-500">
                  {activeAlerts.length === 1 ? 'alerta ativo' : 'alertas ativos'}
                </p>
                <div className="mt-3 space-y-2">
                  {activeAlerts.slice(0, 3).map((alert) => (
                    <div
                      key={alert.id}
                      className="flex items-center gap-2 text-sm text-gray-600"
                    >
                      <FileText size={14} className="text-gray-400" />
                      <span className="truncate">{alert.keyword}</span>
                      {alert.notice_type && (
                        <span className="text-xs bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded capitalize">
                          {alert.notice_type}
                        </span>
                      )}
                    </div>
                  ))}
                  {activeAlerts.length > 3 && (
                    <p className="text-xs text-gray-400">
                      e mais {activeAlerts.length - 3}...
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Notifications Card */}
        <div className="glass-panel rounded-2xl overflow-hidden flex flex-col">
          <div className="flex items-center justify-between p-5 border-b border-gray-100">
            <div className="flex items-center gap-2">
              <Bell className="text-primary-600" size={20} />
              <h2 className="font-semibold text-gray-900">Notificações Recentes</h2>
            </div>
            <Link
              to="/notifications"
              className="text-xs text-primary-600 hover:text-primary-700 font-medium flex items-center gap-0.5"
            >
              Ver todas <ChevronRight size={14} />
            </Link>
          </div>
          <div className="p-5">
            {notifsError ? (
              <ErrorMessage
                message="Erro ao carregar notificações."
                onRetry={() => refetchNotifs()}
              />
            ) : recentNotifications.length === 0 ? (
              <div className="text-center py-6">
                <p className="text-sm text-gray-500 mb-4 px-4">
                  Nenhuma notificação recebida ainda. Quando um de seus alertas encontrar correspondência em novos editais, ela aparecerá aqui.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {recentNotifications.map((notif) => {
                  const badge = STATUS_BADGES[notif.status] ?? {
                    label: notif.status,
                    classes: ' text-gray-600',
                  };
                  return (
                    <Link
                      key={notif.id}
                      to={`/notices/${notif.notice_id}`}
                      className="flex items-center justify-between p-3 rounded-lg hover: transition-colors"
                    >
                      <div className="min-w-0">
                        <p className="text-sm text-gray-700">
                          Edital #{notif.notice_id}
                        </p>
                        <p className="text-xs text-gray-400">
                          {formatDate(notif.created_at)}
                        </p>
                      </div>
                      <span
                        className={`text-xs font-medium px-2 py-0.5 rounded-full ${badge.classes}`}
                      >
                        {badge.label}
                      </span>
                    </Link>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
