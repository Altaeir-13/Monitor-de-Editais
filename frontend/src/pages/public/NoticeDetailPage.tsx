import { useParams, Link } from 'react-router-dom';
import { useNotice } from '../../hooks/useNotices';
import Spinner from '../../components/ui/Spinner';
import ErrorMessage from '../../components/ui/ErrorMessage';
import { ArrowLeft, ExternalLink, FileText, Building2, MapPin, Calendar, Tag } from 'lucide-react';

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

function formatDateTime(dateStr: string | null): string {
  if (!dateStr) return '—';
  try {
    return new Intl.DateTimeFormat('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(dateStr));
  } catch {
    return '—';
  }
}

export default function NoticeDetailPage() {
  const { id } = useParams<{ id: string }>();
  const noticeId = Number(id);

  const { data: notice, isLoading, isError, refetch } = useNotice(noticeId);

  if (isLoading) {
    return (
      <div className="min-h-screen">
        <Spinner text="Carregando edital..." />
      </div>
    );
  }

  if (isError || !notice) {
    return (
      <div className="min-h-screen">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Link
            to="/notices"
            className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700
                       transition-colors mb-6"
          >
            <ArrowLeft size={16} />
            Voltar para editais
          </Link>

          {isError ? (
            <ErrorMessage
              message="Não foi possível carregar este edital. Ele pode não existir ou estar inativo."
              onRetry={() => refetch()}
            />
          ) : (
            <ErrorMessage message="Edital não encontrado." />
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Back link */}
        <Link
          to="/notices"
          className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700
                     transition-colors mb-6"
        >
          <ArrowLeft size={16} />
          Voltar para editais
        </Link>

        {/* Main card */}
        <div className="glass-panel rounded-2xl overflow-hidden">
          {/* Header */}
          <div className="p-6 border-b border-gray-100">
            <div className="flex items-center gap-2 mb-3">
              <span className="badge badge-primary">
                {notice.notice_type}
              </span>
            </div>
            <h1 className="text-xl font-bold text-gray-900 mb-2">{notice.title}</h1>

            {/* Dates */}
            <div className="flex flex-wrap gap-4 text-sm text-gray-500">
              <span className="flex items-center gap-1">
                <Calendar size={14} />
                Detectado em {formatDateTime(notice.detected_at)}
              </span>
              {notice.publication_date && (
                <span className="flex items-center gap-1">
                  <Calendar size={14} />
                  Publicado em {formatDate(notice.publication_date)}
                </span>
              )}
            </div>
          </div>

          {/* Description */}
          {notice.description && (
            <div className="p-6 border-b border-gray-100">
              <h2 className="text-sm font-semibold text-gray-700 mb-2">Descrição</h2>
              <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-line">
                {notice.description}
              </p>
            </div>
          )}

          {/* Details */}
          <div className="p-6 border-b border-gray-100">
            <h2 className="text-sm font-semibold text-gray-700 mb-3">Informações</h2>
            <dl className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <dt className="flex items-center gap-1 text-xs text-gray-400">
                  <Tag size={12} /> Tipo
                </dt>
                <dd className="text-sm text-gray-700 capitalize">{notice.notice_type}</dd>
              </div>
              <div>
                <dt className="flex items-center gap-1 text-xs text-gray-400">
                  <FileText size={12} /> ID do Edital
                </dt>
                <dd className="text-sm text-gray-700">#{notice.id}</dd>
              </div>
            </dl>
          </div>

          {/* Institution */}
          {notice.institution && (
            <div className="p-6 border-b border-gray-100">
              <h2 className="text-sm font-semibold text-gray-700 mb-3">Instituição</h2>
              <div className="flex items-start gap-3">
                <div className="p-2 bg-gray-100 rounded-lg">
                  <Building2 className="text-gray-500" size={20} />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {notice.institution.name}
                    <span className="text-gray-400 ml-1">({notice.institution.initials})</span>
                  </p>
                  <p className="flex items-center gap-1 text-xs text-gray-500 mt-0.5">
                    <MapPin size={12} />
                    {notice.institution.state}
                  </p>
                  {notice.institution.official_site_url && (
                    <a
                      href={notice.institution.official_site_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-xs text-primary-600
                                 hover:text-primary-700 mt-1 transition-colors"
                    >
                      <ExternalLink size={12} />
                      Site oficial
                    </a>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Action */}
          <div className="p-6">
            <a
              href={notice.url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary px-5 py-2.5
                         transition-colors"
            >
              <ExternalLink size={16} />
              Ver edital original
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
