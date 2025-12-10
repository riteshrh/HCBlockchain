import { useState, useEffect } from 'react';
import { blockchainAPI } from '../services/api';
import Layout from '../components/Layout';

export default function BlockchainExplorer() {
  const [info, setInfo] = useState(null);
  const [blocks, setBlocks] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('info');

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'info') {
        const response = await blockchainAPI.getInfo();
        setInfo(response.data);
      } else if (activeTab === 'blocks') {
        const response = await blockchainAPI.getBlocks(20);
        setBlocks(response.data.blocks);
      } else if (activeTab === 'transactions') {
        const response = await blockchainAPI.getTransactions(null, 50);
        setTransactions(response.data.transactions);
      }
    } catch (error) {
      console.error('Failed to load blockchain data:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="px-4 py-6 sm:px-0">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Blockchain Explorer</h1>

        <div className="bg-white rounded-lg shadow">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              <button
                onClick={() => setActiveTab('info')}
                className={`px-6 py-3 text-sm font-medium ${
                  activeTab === 'info'
                    ? 'border-b-2 border-blue-500 text-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Chain Info
              </button>
              <button
                onClick={() => setActiveTab('blocks')}
                className={`px-6 py-3 text-sm font-medium ${
                  activeTab === 'blocks'
                    ? 'border-b-2 border-blue-500 text-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Blocks
              </button>
              <button
                onClick={() => setActiveTab('transactions')}
                className={`px-6 py-3 text-sm font-medium ${
                  activeTab === 'transactions'
                    ? 'border-b-2 border-blue-500 text-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Transactions
              </button>
            </nav>
          </div>

          <div className="p-6">
            {loading ? (
              <div className="text-center py-12">Loading...</div>
            ) : (
              <>
                {activeTab === 'info' && info && (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-gray-50 p-4 rounded">
                        <p className="text-sm text-gray-600">Chain Length</p>
                        <p className="text-2xl font-bold">{info.chain_length}</p>
                      </div>
                      <div className="bg-gray-50 p-4 rounded">
                        <p className="text-sm text-gray-600">Pending Transactions</p>
                        <p className="text-2xl font-bold">{info.pending_transactions}</p>
                      </div>
                      <div className="bg-gray-50 p-4 rounded">
                        <p className="text-sm text-gray-600">Difficulty</p>
                        <p className="text-2xl font-bold">{info.difficulty}</p>
                      </div>
                      <div className="bg-gray-50 p-4 rounded">
                        <p className="text-sm text-gray-600">Chain Valid</p>
                        <p className={`text-2xl font-bold ${info.is_valid ? 'text-green-600' : 'text-red-600'}`}>
                          {info.is_valid ? 'Yes' : 'No'}
                        </p>
                      </div>
                    </div>
                    {info.latest_block_hash && (
                      <div className="bg-gray-50 p-4 rounded">
                        <p className="text-sm text-gray-600">Latest Block Hash</p>
                        <p className="text-xs font-mono break-all">{info.latest_block_hash}</p>
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'blocks' && (
                  <div className="space-y-4">
                    {blocks.length === 0 ? (
                      <p className="text-gray-500">No blocks found</p>
                    ) : (
                      blocks.map((block, idx) => (
                        <div key={idx} className="border border-gray-200 rounded-lg p-4">
                          <div className="flex justify-between items-start mb-2">
                            <h3 className="font-semibold">Block #{block.index}</h3>
                            <span className="text-xs text-gray-500">
                              {new Date(block.timestamp * 1000).toLocaleString()}
                            </span>
                          </div>
                          <p className="text-xs text-gray-600 mb-2">
                            Hash: <code className="bg-gray-100 px-2 py-1 rounded">{block.hash.substring(0, 20)}...</code>
                          </p>
                          <p className="text-xs text-gray-600 mb-2">
                            Previous: <code className="bg-gray-100 px-2 py-1 rounded">{block.previous_hash.substring(0, 20)}...</code>
                          </p>
                          <p className="text-sm text-gray-700">
                            Transactions: {block.transactions.length}
                          </p>
                        </div>
                      ))
                    )}
                  </div>
                )}

                {activeTab === 'transactions' && (
                  <div className="space-y-4">
                    {transactions.length === 0 ? (
                      <p className="text-gray-500">No transactions found</p>
                    ) : (
                      transactions.map((tx, idx) => (
                        <div key={idx} className="border border-gray-200 rounded-lg p-4">
                          <div className="flex justify-between items-start mb-2">
                            <h3 className="font-semibold">
                              {tx.transaction?.asset?.data?.type || 'Transaction'}
                            </h3>
                            <span className="text-xs text-gray-500">
                              {tx.timestamp ? new Date(tx.timestamp * 1000).toLocaleString() : 'Pending'}
                            </span>
                          </div>
                          <p className="text-xs text-gray-600 mb-2">
                            TX ID: <code className="bg-gray-100 px-2 py-1 rounded">{tx.tx_id?.substring(0, 20)}...</code>
                          </p>
                          {tx.block_index !== undefined && (
                            <p className="text-xs text-gray-600">
                              Block: {tx.block_index}
                            </p>
                          )}
                          {tx.transaction?.asset?.data && (
                            <div className="mt-2 text-xs bg-gray-50 p-2 rounded">
                              <pre className="whitespace-pre-wrap">
                                {JSON.stringify(tx.transaction.asset.data, null, 2)}
                              </pre>
                            </div>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}

