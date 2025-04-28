import { useState } from 'react';

export function useTabNavigation() {
  const [currentTab, setCurrentTab] = useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  return {
    currentTab,
    handleTabChange
  };
} 