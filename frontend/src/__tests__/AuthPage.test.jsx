import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { AppProvider } from '../context/AppContext.jsx';
import AuthPage from '../pages/AuthPage.jsx';

function renderWithProvider(ui) {
  return render(<AppProvider>{ui}</AppProvider>);
}

describe('AuthPage', () => {
  it('toggles between login and register', () => {
    renderWithProvider(<AuthPage />);
    const toggle = screen.getByText(/Need an account/);
    fireEvent.click(toggle);
    expect(screen.getByText(/Have an account/)).toBeInTheDocument();
  });
});
