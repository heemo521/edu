import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { AppProvider } from '../context/AppContext.jsx';
import Chat from '../pages/Chat.jsx';
import * as api from '../services/api.js';

vi.mock('../services/api.js');

function setup() {
  return render(
    <AppProvider>
      <Chat />
    </AppProvider>
  );
}

describe('Chat', () => {
  it('sends message and renders reply', async () => {
    api.sendChatMessage.mockResolvedValue({ reply: 'hello back' });
    api.fetchHistory.mockResolvedValue([]);
    setup();
    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: 'hello' } });
    fireEvent.click(screen.getByText('Send'));
    await waitFor(() => screen.getByText('hello back'));
    expect(screen.getByText('hello')).toBeInTheDocument();
  });
});
