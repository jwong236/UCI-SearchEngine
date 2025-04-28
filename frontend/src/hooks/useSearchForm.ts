import { useState } from 'react';

export function useSearchForm() {
  const [query, setQuery] = useState('');

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Implement search functionality
    console.log('Searching for:', query);
  };

  return {
    query,
    setQuery,
    handleSearch
  };
} 