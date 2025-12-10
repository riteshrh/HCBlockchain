import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { blockchainAPI, adminAPI } from '../services/api';
import Layout from '../components/Layout';

export default function AdminDashboard() {
  const { user } = useAuth();
  const [blockchainInfo, setBlockchainInfo] = useState(null);
  const [providers, setProviders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    if (user?.role === 'admin') {
      loadBlockchainInfo();
      loadProviders();
    }
  }, [user]);

  const loadProviders = async () => {
    try {
      const response = await adminAPI.getProviders();
      setProviders(response.data);
    } catch (error) {
      console.error('Failed to load providers:', error);
    }
  };

  const loadBlockchainInfo = async () => {
    try {
      const response = await blockchainAPI.getInfo();
      setBlockchainInfo(response.data);
    } catch (error) {
      console.error('Failed to load blockchain info:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleValidateBlockchain = async () => {
    try {
      const response = await blockchainAPI.validate();
      alert(`Blockchain validation: ${response.data.is_valid ? 'Valid' : 'Invalid'}\n${response.data.message}`);
    } catch (error) {
      alert('Failed to validate blockchain: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleApproveProvider = async (providerId) => {
    try {
      await adminAPI.approveProvider(providerId);
      await loadProviders();
      alert('Provider approved successfully!');
    } catch (error) {
      alert('Failed to approve provider: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleRejectProvider = async (providerId) => {
    if (!window.confirm('Are you sure you want to reject this provider?')) {
      return;
    }
    try {
      await adminAPI.rejectProvider(providerId);
      await loadProviders();
      alert('Provider rejected successfully!');
    } catch (error) {
      alert('Failed to reject provider: ' + (error.response?.data?.detail || error.message));
    }
  };

  if (user?.role !== 'admin') {
    return (
      <Layout>
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-red-800 mb-2">Access Denied</h2>
            <p className="text-red-600">You must be an administrator to access this page.</p>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="px-4 py-6 sm:px-0">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Admin Dashboard</h1>

        <div className="bg-white rounded-lg shadow mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              <button
                onClick={() => setActiveTab('overview')}
                className={`px-6 py-3 text-sm font-medium ${
                  activeTab === 'overview'
                    ? 'border-b-2 border-blue-500 text-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Overview
              </button>
              <button
                onClick={() => setActiveTab('providers')}
                className={`px-6 py-3 text-sm font-medium ${
                  activeTab === 'providers'
                    ? 'border-b-2 border-blue-500 text-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Provider Management
              </button>
            </nav>
          </div>

          <div className="p-6">
            {activeTab === 'overview' && (
              <>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500 mb-2">System Status</h3>
            <p className="text-2xl font-bold text-green-600">Operational</p>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Blockchain Status</h3>
            {loading ? (
              <p className="text-gray-400">Loading...</p>
            ) : blockchainInfo ? (
              <p className={`text-2xl font-bold ${blockchainInfo.is_valid ? 'text-green-600' : 'text-red-600'}`}>
                {blockchainInfo.is_valid ? 'Valid' : 'Invalid'}
              </p>
            ) : (
              <p className="text-gray-400">Unknown</p>
            )}
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Chain Length</h3>
            {loading ? (
              <p className="text-gray-400">Loading...</p>
            ) : blockchainInfo ? (
              <p className="text-2xl font-bold text-gray-900">{blockchainInfo.chain_length}</p>
            ) : (
              <p className="text-gray-400">-</p>
            )}
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Blockchain Information</h2>
          {loading ? (
            <p className="text-gray-500">Loading blockchain data...</p>
          ) : blockchainInfo ? (
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Chain Length:</span>
                <span className="font-semibold">{blockchainInfo.chain_length} blocks</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Pending Transactions:</span>
                <span className="font-semibold">{blockchainInfo.pending_transactions}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Difficulty:</span>
                <span className="font-semibold">{blockchainInfo.difficulty}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Chain Valid:</span>
                <span className={`font-semibold ${blockchainInfo.is_valid ? 'text-green-600' : 'text-red-600'}`}>
                  {blockchainInfo.is_valid ? 'Yes' : 'No'}
                </span>
              </div>
              {blockchainInfo.latest_block_hash && (
                <div className="mt-4 pt-4 border-t">
                  <span className="text-gray-600 block mb-2">Latest Block Hash:</span>
                  <code className="text-xs bg-gray-100 p-2 rounded block break-all">
                    {blockchainInfo.latest_block_hash}
                  </code>
                </div>
              )}
            </div>
          ) : (
            <p className="text-red-600">Failed to load blockchain information</p>
          )}
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Admin Actions</h2>
          <div className="space-y-4">
            <button
              onClick={handleValidateBlockchain}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 mr-4"
            >
              Validate Blockchain
            </button>
            <Link
              to="/blockchain"
              className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 inline-block"
            >
              View Blockchain Explorer
            </Link>
          </div>
        </div>

        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-800">
            <strong>Admin Panel:</strong> This is the system administration dashboard. 
            Use this panel to monitor blockchain health, validate the chain, and manage system settings.
          </p>
        </div>
              </>
            )}

            {activeTab === 'providers' && (
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Provider Management</h2>
                {providers.length === 0 ? (
                  <p className="text-gray-500">No providers found</p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {providers.map((provider) => (
                          <tr key={provider.user_id}>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                              {provider.name || 'N/A'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {provider.email}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span
                                className={`px-2 py-1 text-xs font-semibold rounded-full ${
                                  provider.is_approved
                                    ? 'bg-green-100 text-green-800'
                                    : 'bg-yellow-100 text-yellow-800'
                                }`}
                              >
                                {provider.is_approved ? 'Approved' : 'Pending'}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {new Date(provider.created_at).toLocaleDateString()}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm">
                              {!provider.is_approved ? (
                                <button
                                  onClick={() => handleApproveProvider(provider.user_id)}
                                  className="text-green-600 hover:text-green-900 mr-4"
                                >
                                  Approve
                                </button>
                              ) : (
                                <button
                                  onClick={() => handleRejectProvider(provider.user_id)}
                                  className="text-red-600 hover:text-red-900"
                                >
                                  Reject
                                </button>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}

