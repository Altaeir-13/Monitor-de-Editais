import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useNotices } from '../../hooks/useNotices';
import Spinner from '../../components/ui/Spinner';
import EmptyState from '../../components/ui/EmptyState';
import ErrorMessage from '../../components/ui/ErrorMessage';
import { Search, Calendar, ChevronLeft, ChevronRight, FileText, X } from 'lucide-react';

const PAGE_SIZE = 20;

const STATES = [
  'AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG',
  'PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO',
];

const NOTICE_TYPES = [
  { value: 'concurso', label: 'Concurso' },
  { value: 'bolsa', label: 'Bolsa' },
  { value: 'edital', label: 'Edital' },
  { value: 'licitacao', label: 'Licitação' },
  { value: 'selecao', label: 'Seleção' },
  { value: 'outro', label: 'Outro' },
];

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

export default function NoticesPage() {
  // Filter state
  const [keyword, setKeyword] = useState('');
  const [state, setState] = useState('');
  const [noticeType, setNoticeType] = useState('');
  const [detectedAfter, setDetectedAfter] = useState('');
  const [detectedBefore, setDetectedBefore] = useState('');

  // Pagination
  const [page, setPage] = useState(0);
  const skip = page * PAGE_SIZE;

  // Applied filters (only sent on submit or filter change)
  const [appliedKeyword, setAppliedKeyword] = useState('');

  const { data, isLoading, isError, refetch } = useNotices({
    keyword: appliedKeyword || undefined,
    state: state || undefined,
    notice_type: noticeType || undefined,
    detected_after: detectedAfter ? `${detectedAfter}T00:00:00Z` : undefined,
    detected_before: detectedBefore ? `${detectedBefore}T23:59:59Z` : undefined,
    skip,
    limit: PAGE_SIZE,
  });

  const notices = data ?? [];
  const hasNextPage = notices.length === PAGE_SIZE;
  const currentPage = page + 1;

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setAppliedKeyword(keyword);
    setPage(0);
  };

  const handleFilterChange = () => {
    setPage(0);
  };

  const clearFilters = () => {
    setKeyword('');
    setAppliedKeyword('');
    setState('');
    setNoticeType('');
    setDetectedAfter('');
    setDetectedBefore('');
    setPage(0);
  };

  const hasActiveFilters = appliedKeyword || state || noticeType || detectedAfter || detectedBefore;

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary-100 rounded-lg">
              <FileText className="text-primary-600" size={24} />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Monitor de Editais</h1>
              <p className="text-sm text-gray-500">Editais públicos de instituições monitoradas</p>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Filters */}
        <div className="glass-panel rounded-2xl p-6 mb-6">
          {/* Search bar */}
          <form onSubmit={handleSearch} className="flex gap-2 mb-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
              <input
                type="text"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                placeholder="Buscar por palavra-chave..."
                className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm
                           focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
                           placeholder-gray-400"
              />
            </div>
            <button
              type="submit"
              className="btn-primary"
            >
              Buscar
            </button>
          </form>

          {/* Filter row */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Estado (UF)</label>
              <select
                value={state}
                onChange={(e) => { setState(e.target.value); handleFilterChange(); }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm
                           focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
                           bg-white"
              >
                <option value="">Todos os estados</option>
                {STATES.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Tipo de Edital</label>
              <select
                value={noticeType}
                onChange={(e) => { setNoticeType(e.target.value); handleFilterChange(); }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm
                           focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
                           bg-white"
              >
                <option value="">Todos os tipos</option>
                {NOTICE_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">
                <Calendar className="inline" size={12} /> Detectado a partir de
              </label>
              <input
                type="date"
                value={detectedAfter}
                onChange={(e) => { setDetectedAfter(e.target.value); handleFilterChange(); }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm
                           focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">
                <Calendar className="inline" size={12} /> Detectado até
              </label>
              <input
                type="date"
                value={detectedBefore}
                onChange={(e) => { setDetectedBefore(e.target.value); handleFilterChange(); }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm
                           focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Clear filters */}
          {hasActiveFilters && (
            <div className="mt-3 pt-3 border-t border-gray-100">
              <button
                onClick={clearFilters}
                className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 transition-colors"
              >
                <X size={14} />
                Limpar filtros
              </button>
            </div>
          )}
        </div>

        {/* Content */}
        {isLoading && <Spinner text="Carregando editais..." />}

        {isError && (
          <ErrorMessage
            message="Não foi possível carregar os editais. Verifique sua conexão."
            onRetry={() => refetch()}
          />
        )}

        {!isLoading && !isError && notices.length === 0 && (
          <EmptyState
            title="Nenhum edital encontrado"
            description={
              hasActiveFilters
                ? 'Sua combinação de filtros não retornou nenhum edital. Tente remover palavras-chave, alterar o tipo de edital ou mudar o período de detecção.'
                : 'O sistema ainda não capturou editais recentes em nossas fontes cadastradas. Volte em breve ou ative alertas para ser notificado.'
            }
            actionLabel={hasActiveFilters ? 'Limpar filtros' : undefined}
            onAction={hasActiveFilters ? clearFilters : undefined}
          />
        )}

        {!isLoading && !isError && notices.length > 0 && (
          <>
            {/* Cards grid */}
            <div className="grid gap-4">
              {notices.map((notice) => (
                <Link
                  key={notice.id}
                  to={`/notices/${notice.id}`}
                  className="block glass-panel rounded-2xl p-5
                             hover:border-primary-300 hover:shadow-md transition-all duration-200"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="inline-flex px-2.5 py-0.5 bg-primary-50 text-primary-700
                                         text-xs font-medium rounded-full capitalize">
                          {notice.notice_type}
                        </span>
                      </div>
                      <h3 className="text-base font-semibold text-gray-900 mb-1 line-clamp-2">
                        {notice.title}
                      </h3>
                      {notice.description && (
                        <p className="text-sm text-gray-500 line-clamp-2 mb-2">
                          {notice.description}
                        </p>
                      )}
                      <div className="flex flex-wrap items-center gap-3 text-xs text-gray-400">
                        <span>Detectado em {formatDate(notice.detected_at)}</span>
                        {notice.publication_date && (
                          <span>Publicado em {formatDate(notice.publication_date)}</span>
                        )}
                      </div>
                    </div>
                    <ChevronRight className="text-gray-300 flex-shrink-0 mt-1" size={20} />
                  </div>
                </Link>
              ))}
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
    </div>
  );
}
