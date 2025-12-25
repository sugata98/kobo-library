import SyncButton from '@/components/SyncButton';
import BookList from '@/components/BookList';

export default function Home() {
  return (
    <main className="min-h-screen p-8 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      <header className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Kobo Library</h1>
        <SyncButton />
      </header>
      
      <section>
        <h2 className="text-2xl font-semibold mb-4">My Books</h2>
        <BookList />
      </section>
    </main>
  );
}
