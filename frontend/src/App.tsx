import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Layout from './components/layout/Layout';
import { HomePage } from './components/HomePage';
import LoginForm from './components/auth/LoginForm';
import RegisterForm from './components/auth/RegisterForm';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { ListenerDashboard } from './components/dashboard/ListenerDashboard';
import { ArtistDashboard } from './components/dashboard/ArtistDashboard';
import { AdminDashboard } from './components/dashboard/AdminDashboard';
import './index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
    },
  },
});

const AppRoutes: React.FC = () => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <Layout user={user}>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<HomePage />} />
        <Route 
          path="/login" 
          element={user ? <Navigate to={`/dashboard/${user.role}`} replace /> : <LoginForm />} 
        />
        <Route 
          path="/register" 
          element={user ? <Navigate to={`/dashboard/${user.role}`} replace /> : <RegisterForm />} 
        />

        {/* Protected Dashboard Routes */}
        <Route 
          path="/dashboard/listener" 
          element={
            <ProtectedRoute user={user} requiredRole="listener">
              <ListenerDashboard />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/dashboard/artist" 
          element={
            <ProtectedRoute user={user} requiredRole="artist">
              <ArtistDashboard />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/dashboard/admin" 
          element={
            <ProtectedRoute user={user} requiredRole="admin">
              <AdminDashboard />
            </ProtectedRoute>
          } 
        />

        {/* Default Dashboard Redirect */}
        <Route 
          path="/dashboard" 
          element={
            user ? (
              <Navigate to={`/dashboard/${user.role}`} replace />
            ) : (
              <Navigate to="/login" replace />
            )
          } 
        />

        {/* Catch all route */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
};

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </Router>
    </QueryClientProvider>
  );
};

export default App;
