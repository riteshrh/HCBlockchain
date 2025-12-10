import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import Layout from '../components/Layout';

export default function Dashboard() {
  const { user } = useAuth();

  return (
    <Layout>
      <div className="px-4 py-6 sm:px-0">
        <div className="border-4 border-dashed border-gray-200 rounded-lg p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Welcome, {user?.name}!
          </h1>
          <p className="text-gray-600 mb-6">
            You are logged in as <span className="font-semibold">{user?.role}</span>
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-8">
            {user?.role === 'patient' && (
              <>
                <Link
                  to="/records"
                  className="block p-6 bg-white rounded-lg shadow hover:shadow-md transition"
                >
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">My Records</h3>
                  <p className="text-gray-600">View and manage your medical records</p>
                </Link>
                <Link
                  to="/consent"
                  className="block p-6 bg-white rounded-lg shadow hover:shadow-md transition"
                >
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Manage Consent</h3>
                  <p className="text-gray-600">Grant or revoke access to providers</p>
                </Link>
              </>
            )}

            {user?.role === 'provider' && (
              <Link
                to="/provider/records"
                className="block p-6 bg-white rounded-lg shadow hover:shadow-md transition"
              >
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Access Records</h3>
                <p className="text-gray-600">View patient records with consent</p>
              </Link>
            )}

            {user?.role === 'admin' && (
              <Link
                to="/admin"
                className="block p-6 bg-white rounded-lg shadow hover:shadow-md transition"
              >
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Admin Panel</h3>
                <p className="text-gray-600">System administration and monitoring</p>
              </Link>
            )}

            <Link
              to="/blockchain"
              className="block p-6 bg-white rounded-lg shadow hover:shadow-md transition"
            >
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Blockchain Explorer</h3>
              <p className="text-gray-600">View blockchain transactions and blocks</p>
            </Link>
          </div>
        </div>
      </div>
    </Layout>
  );
}

