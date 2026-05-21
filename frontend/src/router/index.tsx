import { createBrowserRouter, Navigate } from 'react-router-dom';
import ProtectedRoute from '../components/ProtectedRoute';
import AdminRoute from '../components/AdminRoute';
import Layout from '../components/Layout';
import LoginPage from '../pages/LoginPage';
import RegisterPage from '../pages/RegisterPage';
import NoticesPage from '../pages/public/NoticesPage';
import NoticeDetailPage from '../pages/public/NoticeDetailPage';
import DashboardPage from '../pages/user/DashboardPage';
import AlertsPage from '../pages/user/AlertsPage';
import NotificationsPage from '../pages/user/NotificationsPage';
import AdminDashboardPage from '../pages/admin/AdminDashboardPage';
import AdminInstitutionsPage from '../pages/admin/AdminInstitutionsPage';
import AdminSourcesPage from '../pages/admin/AdminSourcesPage';

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
            element: <DashboardPage />,
          },
          {
            path: '/alerts',
            element: <AlertsPage />,
          },
          {
            path: '/notifications',
            element: <NotificationsPage />,
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
            element: <AdminDashboardPage />,
          },
          {
            path: '/admin/institutions',
            element: <AdminInstitutionsPage />,
          },
          {
            path: '/admin/sources',
            element: <AdminSourcesPage />,
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
