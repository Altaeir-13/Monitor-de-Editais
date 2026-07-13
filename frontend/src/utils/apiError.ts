import axios from 'axios';

interface FastApiValidationError {
  loc?: Array<string | number>;
  msg?: string;
  type?: string;
}

interface ApiErrorData {
  detail?: string | FastApiValidationError[] | unknown;
}

const API_UNAVAILABLE_MESSAGE =
  'Não foi possível conectar à API. Verifique sua conexão e a disponibilidade do serviço.';

function formatStatusMessage(status: number | undefined, message: string): string {
  return status ? `Erro ${status}: ${message}` : message;
}

function formatValidationLocation(loc: Array<string | number> | undefined): string {
  if (!loc || loc.length === 0) {
    return 'payload';
  }

  const filtered = loc.filter((part) => part !== 'body');
  return filtered.length > 0 ? filtered.join('.') : 'payload';
}

function isValidationErrorList(detail: unknown): detail is FastApiValidationError[] {
  return Array.isArray(detail);
}

function formatValidationDetail(detail: FastApiValidationError[]): string {
  return detail
    .map((item) => {
      const location = formatValidationLocation(item.loc);
      const message = item.msg || item.type || 'valor inválido';
      return `${location}: ${message}`;
    })
    .join('; ');
}

function getTechnicalMessage(error: unknown): string {
  if (error instanceof Error && error.message) {
    return ` Mensagem técnica: ${error.message}`;
  }

  return '';
}

export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError<ApiErrorData>(error)) {
    const status = error.response?.status;
    const detail = error.response?.data?.detail;

    if (typeof detail === 'string' && detail.trim()) {
      return formatStatusMessage(status, detail);
    }

    if (isValidationErrorList(detail)) {
      return formatStatusMessage(status, formatValidationDetail(detail));
    }

    if (status) {
      return `Erro ${status}: resposta inesperada da API.`;
    }

    return `${API_UNAVAILABLE_MESSAGE}${getTechnicalMessage(error)}`;
  }

  if (error instanceof Error && error.message) {
    return `Erro inesperado. Mensagem técnica: ${error.message}`;
  }

  return 'Erro inesperado ao comunicar com a API.';
}
