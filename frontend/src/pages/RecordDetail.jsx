import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { recordsAPI } from '../services/api';
import Layout from '../components/Layout';

export default function RecordDetail() {
  const { recordId } = useParams();
  const navigate = useNavigate();
  const [record, setRecord] = useState(null);
  const [content, setContent] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRecord();
  }, [recordId]);

  const loadRecord = async () => {
    try {
      const response = await recordsAPI.getRecord(recordId);
      setRecord(response.data);
    } catch (error) {
      console.error('Failed to load record:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleViewContent = async () => {
    try {
      const response = await recordsAPI.getRecordContent(recordId);
      setContent(response.data.content);
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to load content');
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="text-center py-12">Loading record...</div>
      </Layout>
    );
  }

  if (!record) {
    return (
      <Layout>
        <div className="text-center py-12">
          <p className="text-gray-500 mb-4">Record not found</p>
          <button
            onClick={() => navigate('/records')}
            className="text-blue-600 hover:text-blue-900"
          >
            Back to Records
          </button>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="px-4 py-6 sm:px-0">
        <button
          onClick={() => navigate('/records')}
          className="text-blue-600 hover:text-blue-900 mb-4"
        >
          ← Back to Records
        </button>

        <div className="bg-white p-6 rounded-lg shadow">
          <h1 className="text-3xl font-bold text-gray-900 mb-6">{record.title}</h1>

          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-medium text-gray-500">Description</h3>
              <p className="mt-1 text-gray-900">{record.description}</p>
            </div>

            <div>
              <h3 className="text-sm font-medium text-gray-500">Type</h3>
              <p className="mt-1 text-gray-900 capitalize">{record.record_type}</p>
            </div>

            <div>
              <h3 className="text-sm font-medium text-gray-500">Created</h3>
              <p className="mt-1 text-gray-900">
                {new Date(record.created_at).toLocaleString()}
              </p>
            </div>

            <div>
              <h3 className="text-sm font-medium text-gray-500">Record Hash</h3>
              <p className="mt-1 text-xs font-mono bg-gray-100 p-2 rounded break-all">
                {record.hash}
              </p>
            </div>

            {record.blockchain_tx_id && (
              <div>
                <h3 className="text-sm font-medium text-gray-500">Blockchain Transaction</h3>
                <p className="mt-1 text-xs font-mono bg-gray-100 p-2 rounded break-all">
                  {record.blockchain_tx_id}
                </p>
              </div>
            )}

            <div className="pt-4 border-t">
              {content ? (
                <div>
                  <h3 className="text-sm font-medium text-gray-500 mb-2">Decrypted Content</h3>
                  <div className="bg-gray-50 p-4 rounded border">
                    <pre className="whitespace-pre-wrap text-sm">{content}</pre>
                  </div>
                </div>
              ) : (
                <button
                  onClick={handleViewContent}
                  className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
                >
                  View Decrypted Content
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}

