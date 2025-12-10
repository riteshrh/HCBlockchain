import { useState, useEffect } from 'react';
import { recordsAPI } from '../services/api';
import Layout from '../components/Layout';

export default function ProviderRecords() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [recordId, setRecordId] = useState('');
  const [selectedRecord, setSelectedRecord] = useState(null);

  const handleAccess = async (e) => {
    e.preventDefault();
    if (!recordId) return;

    try {
      const response = await recordsAPI.getRecord(recordId);
      setSelectedRecord(response.data);
    } catch (error) {
      if (error.response?.status === 403) {
        alert('Access denied: You do not have consent to view this record');
      } else {
        alert(error.response?.data?.detail || 'Failed to access record');
      }
      setSelectedRecord(null);
    }
  };

  const handleViewContent = async (id) => {
    try {
      const response = await recordsAPI.getRecordContent(id);
      alert(`Record Content:\n\n${response.data.content}`);
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to load content');
    }
  };

  return (
    <Layout>
      <div className="px-4 py-6 sm:px-0">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Access Patient Records</h1>

        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <h2 className="text-xl font-semibold mb-4">Access Record by ID</h2>
          <p className="text-sm text-gray-600 mb-4">
            Enter a record ID to access. You must have consent from the patient.
          </p>
          <form onSubmit={handleAccess} className="flex gap-4">
            <input
              type="text"
              required
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md"
              value={recordId}
              onChange={(e) => setRecordId(e.target.value)}
              placeholder="Enter record ID"
            />
            <button
              type="submit"
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
            >
              Access
            </button>
          </form>
        </div>

        {selectedRecord && (
          <div className="bg-white p-6 rounded-lg shadow mb-6">
            <h2 className="text-xl font-semibold mb-4">Record Details</h2>
            <div className="space-y-2">
              <p><span className="font-semibold">Title:</span> {selectedRecord.title}</p>
              <p><span className="font-semibold">Description:</span> {selectedRecord.description}</p>
              <p><span className="font-semibold">Type:</span> {selectedRecord.record_type}</p>
              <p><span className="font-semibold">Created:</span> {new Date(selectedRecord.created_at).toLocaleString()}</p>
              <p><span className="font-semibold">Hash:</span> <code className="text-xs bg-gray-100 px-2 py-1 rounded">{selectedRecord.hash.substring(0, 20)}...</code></p>
              <button
                onClick={() => handleViewContent(selectedRecord.record_id)}
                className="mt-4 bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700"
              >
                View Decrypted Content
              </button>
            </div>
          </div>
        )}

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-800">
            <strong>Note:</strong> You can only access records for which the patient has granted you consent.
            If access is denied, contact the patient to grant consent.
          </p>
        </div>
      </div>
    </Layout>
  );
}

