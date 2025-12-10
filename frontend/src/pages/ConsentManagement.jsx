import { useState, useEffect } from 'react';
import { consentAPI } from '../services/api';
import Layout from '../components/Layout';

export default function ConsentManagement() {
  const [consents, setConsents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showGrant, setShowGrant] = useState(false);
  const [grantData, setGrantData] = useState({
    provider_id: '',
    record_id: '',
  });

  useEffect(() => {
    loadConsents();
  }, []);

  const loadConsents = async () => {
    try {
      const response = await consentAPI.getMyConsents();
      setConsents(response.data);
    } catch (error) {
      console.error('Failed to load consents:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGrant = async (e) => {
    e.preventDefault();
    try {
      await consentAPI.grant(grantData);
      setShowGrant(false);
      setGrantData({ provider_id: '', record_id: '' });
      loadConsents();
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to grant consent');
    }
  };

  const handleRevoke = async (providerId, recordId) => {
    if (!window.confirm('Are you sure you want to revoke this consent?')) {
      return;
    }
    try {
      await consentAPI.revoke({ provider_id: providerId, record_id: recordId });
      loadConsents();
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to revoke consent');
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="text-center py-12">Loading consents...</div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="px-4 py-6 sm:px-0">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Consent Management</h1>
          <button
            onClick={() => setShowGrant(!showGrant)}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
          >
            {showGrant ? 'Cancel' : 'Grant Consent'}
          </button>
        </div>

        {showGrant && (
          <div className="bg-white p-6 rounded-lg shadow mb-6">
            <h2 className="text-xl font-semibold mb-4">Grant Consent to Provider</h2>
            <form onSubmit={handleGrant} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Provider ID</label>
                <input
                  type="text"
                  required
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                  value={grantData.provider_id}
                  onChange={(e) => setGrantData({ ...grantData, provider_id: e.target.value })}
                  placeholder="Enter provider user ID"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Record ID</label>
                <input
                  type="text"
                  required
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                  value={grantData.record_id}
                  onChange={(e) => setGrantData({ ...grantData, record_id: e.target.value })}
                  placeholder="Enter record ID"
                />
              </div>
              <button
                type="submit"
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
              >
                Grant Consent
              </button>
            </form>
          </div>
        )}

        <div className="bg-white shadow rounded-lg overflow-hidden">
          {consents.length === 0 ? (
            <div className="p-6 text-center text-gray-500">No consents found</div>
          ) : (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Provider ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Record ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {consents.map((consent) => (
                  <tr key={`${consent.provider_id}-${consent.record_id}`}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {consent.provider_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {consent.record_id.substring(0, 8)}...
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 text-xs font-semibold rounded-full ${
                          consent.status === 'granted'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {consent.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(consent.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {consent.status === 'granted' && (
                        <button
                          onClick={() => handleRevoke(consent.provider_id, consent.record_id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          Revoke
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </Layout>
  );
}

