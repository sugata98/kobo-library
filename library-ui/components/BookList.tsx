'use client';

import { useState, useEffect } from 'react';
import { getBooks } from '@/lib/api';
import Link from 'next/link';

export default function BookList() {
  const [books, setBooks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getBooks()
      .then(setBooks)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>Loading books...</div>;
  if (error) return <div className="text-red-500">Error: {error}</div>;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {books.map((book) => (
        <Link href={`/books/${encodeURIComponent(book.ContentID)}`} key={book.ContentID}>
          <div className="border p-4 rounded hover:shadow-lg transition-shadow cursor-pointer bg-white dark:bg-gray-800">
            <h3 className="font-bold text-lg">{book.Title}</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">{book.Author}</p>
            <div className="mt-2 text-xs text-gray-500">
              Progress: {Math.round(book.___PercentRead || 0)}%
            </div>
          </div>
        </Link>
      ))}
    </div>
  );
}

