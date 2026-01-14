import { useState, useCallback } from 'react';
import ProfessionalForm from './components/ProfessionalForm';
import ProfessionalList from './components/ProfessionalList';
import BulkUpload from './components/BulkUpload';

function App() {
  // Counter to trigger list refresh after form submission
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleFormSuccess = useCallback(() => {
    setRefreshTrigger((prev) => prev + 1);
  }, []);

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Professional Sign-ups
          </h1>
          <p className="mt-2 text-gray-600">
            Manage professional sign-ups from multiple sources
          </p>
        </header>

        <main className="space-y-6">
          <ProfessionalForm onSuccess={handleFormSuccess} />
          <BulkUpload onSuccess={handleFormSuccess} />
          <ProfessionalList refreshTrigger={refreshTrigger} />
        </main>

        <footer className="mt-12 text-center text-sm text-gray-500">
          NewtonX Professional Management System
        </footer>
      </div>
    </div>
  );
}

export default App;
