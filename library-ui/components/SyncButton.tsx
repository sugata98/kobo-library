'use client';

import { useState } from 'react';
import { syncData } from '@/lib/api';

export default function SyncButton() {
  const [syncing, setSyncing] = useState(false);
  const [message, setMessage] = useState('');

  const handleSync = async () => {
    setSyncing(true);
    setMessage('');
    try {
      await syncData();
      setMessage('Sync successful!');
      window.location.reload(); // Reload to refresh data
    } catch (err) {
      setMessage('Sync failed.');
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={handleSync}
        disabled={syncing}
        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
      >
        {syncing ? 'Syncing...' : 'Sync Data'}
      </button>
      {message && <span className="text-sm">{message}</span>}
    </div>
  );
}

