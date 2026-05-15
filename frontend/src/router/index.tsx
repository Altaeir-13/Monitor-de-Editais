import { createBrowserRouter, Navigate } from 'react-router-dom';
import ProtectedRoute from '../components/ProtectedRoute';
import AdminRoute from '../components/AdminRoute';
import Layout from '../components/Layout';
import LoginPage from '../pages/LoginPage';
import RegisterPage from '../pages/RegisterPage';
import NoticesPage from '../pages/public/NoticesPage';
import NoticeDetailPage from '../pages/public/NoticeDetailPage';

// ── Placeholder pages for future subetapas ──────────────────────────────────
// These are minimal placeholders. Real implementations come in 8C/8D.

function PlaceholderPage({ title }: { title: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-gray-400">
      <p className="text-lg font-medium">{title}</p>
      <p className="text-sm mt-1">Em breve</p>
    </div>
  );
}

const router = createBrowserRouter([
  // Public routes
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/register',
    element: <RegisterPage />,
  },
  {
    path: '/notices',
    element: <NoticesPage />,
  },
  {
    path: '/notices/:id',
    element: <NoticeDetailPage />,
  },

  // Protected routes (require authentication)
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <Layout />,
        children: [
          {
            path: '/dashboard',
            element: <PlaceholderPage title="Dashboard" />,
          },
          {
            path: '/alerts',
            element: <PlaceholderPage title="Meus Alertas" />,
          },
          {
            path: '/notifications',
            element: <PlaceholderPage title="Minhas Notificações" />,
          },
        ],
      },
    ],
  },

  // Admin routes (require authentication + admin role)
  {
    element: <AdminRoute />,
    children: [
      {
        element: <Layout />,
        children: [
          {
            path: '/admin',
            element: <PlaceholderPage title="Painel Administrativo" />,
          },
          {
            path: '/admin/institutions',
            element: <PlaceholderPage title="Instituições" />,
          },
          {
            path: '/admin/sources',
            element: <PlaceholderPage title="Fontes Monitoradas" />,
          },
        ],
      },
    ],
  },

  // Root redirect
  {
    path: '/',
    element: <Navigate to="/notices" replace />,
  },

  // Catch-all → redirect to notices
  {
    path: '*',
    element: <Navigate to="/notices" replace />,
  },
]);

export default router;
