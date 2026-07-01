import ErrorBoundary from './components/ErrorBoundary';
import MainPage from './pages/MainPage';

export default function App() {
  return (
    <ErrorBoundary>
      <MainPage />
    </ErrorBoundary>
  );
}
