import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { FileText, Eye, EyeOff } from 'lucide-react';
import type { AxiosError } from 'axios';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await login(email, password);
      navigate('/dashboard', { replace: true });
    } catch (err) {
      const axiosError = err as AxiosError<{ detail: string }>;
      setError(
        axiosError.response?.data?.detail || 'Erro ao fazer login. Tente novamente.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center  px-4">
      <div className="w-full max-w-md">
        {/* Header / Presentation */}
        <div className="text-center mb-8 px-2">
          <div className="flex justify-center mb-4">
            <div className="p-4 bg-primary-100 rounded-2xl shadow-sm">
              <FileText className="text-primary-600" size={36} />
            </div>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Monitor de Editais</h1>
          <p className="text-gray-500 mt-3 text-sm sm:text-base max-w-sm mx-auto leading-relaxed">
            Acompanhe editais públicos, configure alertas e receba notificações de oportunidades diretamente no seu e-mail.
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="glass-panel rounded-xl border border-gray-200 p-6 space-y-5">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              E-mail
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input-field"
              placeholder="seu@email.com"
              autoComplete="email"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
              Senha
            </label>
            <div className="relative">
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input-field pr-10"
                placeholder="••••••••"
                autoComplete="current-password"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                tabIndex={-1}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="btn-primary w-full py-2.5
                       disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? 'Entrando...' : 'Entrar'}
          </button>

          <p className="text-center text-sm text-gray-500">
            Não tem conta?{' '}
            <Link to="/register" className="text-primary-600 hover:text-primary-700 font-medium">
              Cadastre-se
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
