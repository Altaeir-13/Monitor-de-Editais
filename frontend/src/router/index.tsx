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
import AdminCoveragePage from '../pages/admin/AdminCoveragePage';
import AdminInstitutionsPage from '../pages/admin/AdminInstitutionsPage';
import AdminSourcesPage from '../pages/admin/AdminSourcesPage';
import AdminCrawlerPage from '../pages/admin/AdminCrawlerPage';

const router = createBrowserRouter([
  // Public routes (Auth)
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/register',
    element: <RegisterPage />,
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
            path: '/notices',
            element: <NoticesPage />,
          },
          {
            path: '/notices/:id',
            element: <NoticeDetailPage />,
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
            path: '/admin/coverage',
            element: <AdminCoveragePage />,
          },
          {
            path: '/admin/institutions',
            element: <AdminInstitutionsPage />,
          },
          {
            path: '/admin/sources',
            element: <AdminSourcesPage />,
          },
          {
            path: '/admin/crawler',
            element: <AdminCrawlerPage />,
          },
        ],
      },
    ],
  },

  // Root redirect
  {
    path: '/',
    element: <Navigate to="/dashboard" replace />,
  },

  // Catch-all → redirect to dashboard
  {
    path: '*',
    element: <Navigate to="/dashboard" replace />,
  },
]);

export default router;
