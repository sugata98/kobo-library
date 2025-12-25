const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export async function syncData() {
  const res = await fetch(`${API_BASE_URL}/sync`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to sync data');
  return res.json();
}

export async function getBooks() {
  const res = await fetch(`${API_BASE_URL}/books`);
  if (!res.ok) throw new Error('Failed to fetch books');
  return res.json();
}

export async function getBookHighlights(bookId: string) {
  const res = await fetch(`${API_BASE_URL}/books/${encodeURIComponent(bookId)}/highlights`);
  if (!res.ok) throw new Error('Failed to fetch highlights');
  return res.json();
}

export async function getBookMarkups(bookId: string) {
  const res = await fetch(`${API_BASE_URL}/books/${encodeURIComponent(bookId)}/markups`);
  if (!res.ok) throw new Error('Failed to fetch markups');
  return res.json();
}

