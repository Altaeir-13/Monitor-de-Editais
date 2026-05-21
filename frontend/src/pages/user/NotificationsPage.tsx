import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useNotifications } from '../../hooks/useNotifications';
import Spinner from '../../components/ui/Spinner';
import EmptyState from '../../components/ui/EmptyState';
import ErrorMessage from '../../components/ui/ErrorMessage';
import { Bell, ChevronLeft, ChevronRight, ExternalLink } from 'lucide-react';

const PAGE_SIZE = 20;

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
  pending: { label: 'Pendente', classes: 'app-badge app-badge-warning' },
  sent: { label: 'Enviada', classes: 'app-badge app-badge-success' },
  failed: { label: 'Falhou', classes: 'app-badge app-badge-danger' },
};

export default function NotificationsPage() {
  const [page, setPage] = useState(0);
  const skip = page * PAGE_SIZE;

  const { data, isLoading, isError, refetch } = useNotifications(skip, PAGE_SIZE);

  const notifications = data ?? [];
  const hasNextPage = notifications.length === PAGE_SIZE;
  const currentPage = page + 1;

  if (isLoading) {
    return <Spinner text="Carregando notificações..." />;
  }

  if (isError) {
    return (
      <ErrorMessage
        message="Não foi possível carregar suas notificações."
        onRetry={() => refetch()}
      />
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Minhas Notificações</h1>
        <p className="text-sm text-gray-500 mt-1">
          Editais que corresponderam aos seus alertas.
        </p>
      </div>

      {notifications.length === 0 && page === 0 ? (
        <EmptyState
          icon={<Bell className="text-gray-400" size={32} />}
          title="Nenhuma notificação"
          description="Quando novos editais corresponderem aos seus alertas, eles aparecerão aqui."
        />
      ) : (
        <>
          <div className="grid gap-3">
            {notifications.map((notif) => {
              const badge = STATUS_BADGES[notif.status] ?? {
                label: notif.status,
                classes: ' text-gray-600',
              };
              return (
                <div
                  key={notif.id}
                  className="glass-panel rounded-2xl p-5
                             flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className={`text-xs font-medium px-2 py-0.5 rounded-full ${badge.classes}`}
                      >
                        {badge.label}
                      </span>
                    </div>
                    <p className="text-sm font-medium text-gray-900">
                      Edital #{notif.notice_id}
                    </p>
                    <div className="flex flex-wrap gap-3 text-xs text-gray-400 mt-0.5">
                      <span>Criada em {formatDate(notif.created_at)}</span>
                      {notif.sent_at && (
                        <span>Enviada em {formatDate(notif.sent_at)}</span>
                      )}
                    </div>
                  </div>

                  <Link
                    to={`/notices/${notif.notice_id}`}
                    className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium
                               text-primary-600 bg-primary-50 rounded-lg hover:bg-primary-100 transition-colors
                               flex-shrink-0"
                  >
                    <ExternalLink size={14} />
                    Ver edital
                  </Link>
                </div>
              );
            })}
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between mt-6 glass-panel rounded-2xl p-4">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="flex items-center gap-1 px-3 py-2 text-sm font-medium rounded-lg
                         text-gray-600 hover:bg-gray-100 transition-colors
                         disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-transparent"
            >
              <ChevronLeft size={16} />
              Anterior
            </button>

            <span className="text-sm text-gray-500">
              Página {currentPage}
            </span>

            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={!hasNextPage}
              className="flex items-center gap-1 px-3 py-2 text-sm font-medium rounded-lg
                         text-gray-600 hover:bg-gray-100 transition-colors
                         disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-transparent"
            >
              Próximo
              <ChevronRight size={16} />
            </button>
          </div>
        </>
      )}
    </div>
  );
}
