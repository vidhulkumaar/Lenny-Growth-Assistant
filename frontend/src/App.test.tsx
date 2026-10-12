import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from './App';
import { ApiService } from './services/api';
import { vi } from 'vitest';

// Mock the API service
vi.mock('./services/api', () => {
  return {
    ApiService: {
      getSessions: vi.fn().mockResolvedValue([]),
      getSessionMessages: vi.fn().mockResolvedValue([]),
      getSessionArtifacts: vi.fn().mockResolvedValue([]),
      listDocuments: vi.fn().mockResolvedValue([]),
      sendMessage: vi.fn()
    }
  }
});

describe('App UI', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the welcome screen by default', async () => {
    render(<App />);
    
    // Check for welcome heading
    expect(screen.getByText('The Lenny Growth Assistant')).toBeInTheDocument();
    
    // Check for suggested question
    expect(screen.getByText('What makes a successful product launch?')).toBeInTheDocument();
  });

  it('allows clicking a suggested question to send a message', async () => {
    // Setup mock response
    vi.mocked(ApiService.sendMessage).mockResolvedValueOnce({
      session_id: '123',
      response: {
        id: '456',
        role: 'assistant',
        content: 'Mock answer',
        created_at: new Date().toISOString()
      }
    });

    render(<App />);
    
    // Click suggested question
    const questionCard = screen.getByText('How should a startup find product-market fit?');
    fireEvent.click(questionCard);
    
    // The welcome screen should disappear, and user message should appear
    await waitFor(() => {
      expect(screen.queryByText('The Lenny Growth Assistant')).not.toBeInTheDocument();
    });
    expect(screen.getByText('How should a startup find product-market fit?')).toBeInTheDocument();
  });

  it('displays the artifact viewer when an artifact is returned', async () => {
    vi.mocked(ApiService.sendMessage).mockResolvedValueOnce({
      session_id: 'sess-artifact-1',
      response: {
        id: 'msg-art-1',
        role: 'assistant',
        content: 'I have created the **Viral Loops Report** (MARKDOWN) artifact for you!',
        created_at: new Date().toISOString()
      },
      artifact: {
        id: 'art-1',
        session_id: 'sess-artifact-1',
        title: 'Viral Loops Report',
        artifact_type: 'markdown',
        content: '# Viral Loops Report\nCompounding growth through referral loops.',
        created_at: new Date().toISOString()
      }
    });

    render(<App />);

    const questionCard = screen.getByText('What makes a successful product launch?');
    fireEvent.click(questionCard);

    await waitFor(() => {
      expect(screen.queryByText('The Lenny Growth Assistant')).not.toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getAllByText('Viral Loops Report').length).toBeGreaterThan(0);
      expect(screen.getByText(/compounding growth through referral loops/i)).toBeInTheDocument();
    });
  });
});

