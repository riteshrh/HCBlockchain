import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import PatientRecords from './pages/PatientRecords';
import RecordDetail from './pages/RecordDetail';
import ConsentManagement from './pages/ConsentManagement';
import ProviderRecords from './pages/ProviderRecords';
import BlockchainExplorer from './pages/BlockchainExplorer';
import AdminDashboard from './pages/AdminDashboard';

function PrivateRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }

  return user ? children : <Navigate to="/login" />;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route
        path="/dashboard"
        element={
          <PrivateRoute>
            <Dashboard />
          </PrivateRoute>
        }
      />
      <Route
        path="/records"
        element={
          <PrivateRoute>
            <PatientRecords />
          </PrivateRoute>
        }
      />
      <Route
        path="/records/:recordId"
        element={
          <PrivateRoute>
            <RecordDetail />
          </PrivateRoute>
        }
      />
      <Route
        path="/consent"
        element={
          <PrivateRoute>
            <ConsentManagement />
          </PrivateRoute>
        }
      />
      <Route
        path="/provider/records"
        element={
          <PrivateRoute>
            <ProviderRecords />
          </PrivateRoute>
        }
      />
      <Route
        path="/blockchain"
        element={
          <PrivateRoute>
            <BlockchainExplorer />
          </PrivateRoute>
        }
      />
      <Route
        path="/admin"
        element={
          <PrivateRoute>
            <AdminDashboard />
          </PrivateRoute>
        }
      />
      <Route path="/" element={<Navigate to="/dashboard" />} />
    </Routes>
  );
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </Router>
  );
}

export default App;
