import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from './App';
import { ApiService } from './services/api';
import { vi } from 'vitest';

// Mock the API service
vi.mock('./services/api', () => {
  return {
    ApiService: {
      getProviders: vi.fn().mockResolvedValue({
        default_provider: 'ollama',
        providers: [
          {
            id: 'ollama',
            name: 'Ollama (Local)',
            type: 'local',
            model: 'qwen3:4b',
            available: true,
            description: 'Local model'
          },
          {
            id: 'claude',
            name: 'Claude AI (Cloud)',
            type: 'cloud',
            model: 'claude-3-5-sonnet-20241022',
            available: false,
            description: 'Cloud model'
          }
        ]
      }),
      getSessions: vi.fn().mockResolvedValue([]),
      getSessionMessages: vi.fn().mockResolvedValue([]),
      getSessionArtifacts: vi.fn().mockResolvedValue([]),
      listDocuments: vi.fn().mockResolvedValue([]),
      sendMessage: vi.fn()
    }
  }
});

describe('App UI - Unified Chat & Automatic Artifact Viewer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the welcome screen with unified prompt suggestions by default', async () => {
    render(<App />);
    
    // Check for welcome heading
    expect(screen.getByText('The Lenny Growth Assistant')).toBeInTheDocument();
    
    // Check for unified suggested prompts covering Q&A, writing, and HTML
    expect(screen.getByText('How should a startup find product-market fit?')).toBeInTheDocument();
    expect(screen.getByText('Write a Ship 30 for 30 atomic essay about product-led growth')).toBeInTheDocument();
    expect(screen.getByText('Create a responsive HTML dashboard with KPI cards and charts')).toBeInTheDocument();
  });

  it('allows sending questions through the single unified chat input', async () => {
    vi.mocked(ApiService.sendMessage).mockResolvedValueOnce({
      session_id: 'sess-qa-1',
      response: {
        id: 'msg-qa-1',
        role: 'assistant',
        content: 'Product-market fit occurs when you have strong retention and pull from the market.',
        created_at: new Date().toISOString()
      }
    });

    render(<App />);
    
    // Click suggested question
    const questionCard = screen.getByText('How should a startup find product-market fit?');
    fireEvent.click(questionCard);
    
    // Welcome screen disappears and conversation displays
    await waitFor(() => {
      expect(screen.queryByText('The Lenny Growth Assistant')).not.toBeInTheDocument();
    });
    expect(screen.getByText('How should a startup find product-market fit?')).toBeInTheDocument();
  });

  it('automatically displays the Artifact Viewer when an HTML artifact is returned', async () => {
    vi.mocked(ApiService.sendMessage).mockResolvedValueOnce({
      session_id: 'sess-html-1',
      response: {
        id: 'msg-html-1',
        role: 'assistant',
        content: 'I have created the **SaaS Analytics Dashboard** (HTML) artifact for you!',
        created_at: new Date().toISOString()
      },
      artifact: {
        id: 'art-html-1',
        session_id: 'sess-html-1',
        title: 'SaaS Analytics Dashboard',
        artifact_type: 'html',
        content: '<!DOCTYPE html><html><head><style>body{background:#0f172a;color:#fff;}</style></head><body><h1>SaaS Analytics Dashboard</h1></body></html>',
        created_at: new Date().toISOString()
      }
    });

    render(<App />);

    const dashboardCard = screen.getByText('Create a responsive HTML dashboard with KPI cards and charts');
    fireEvent.click(dashboardCard);

    await waitFor(() => {
      expect(screen.queryByText('The Lenny Growth Assistant')).not.toBeInTheDocument();
    });

    // The Artifact Viewer should open automatically displaying the HTML artifact title and preview badge
    await waitFor(() => {
      expect(screen.getAllByText('SaaS Analytics Dashboard').length).toBeGreaterThan(0);
      expect(screen.getByText('Sandboxed HTML/CSS Preview')).toBeInTheDocument();
      expect(screen.getByText('Scripts Restricted')).toBeInTheDocument();
    });
  });

  it('allows user to type directly in unified composer without manual mode selection', async () => {
    vi.mocked(ApiService.sendMessage).mockResolvedValueOnce({
      session_id: 'sess-essay-1',
      response: {
        id: 'msg-essay-1',
        role: 'assistant',
        content: '# The Silent Killer of Growth: Retention Churn\n\nMost founders focus on acquisition...',
        created_at: new Date().toISOString()
      }
    });

    render(<App />);

    const textarea = screen.getByPlaceholderText(/Ask a question, request a Ship 30 atomic essay, or create an HTML dashboard/i);
    fireEvent.change(textarea, { target: { value: 'Write a Ship 30 for 30 atomic essay about retention' } });
    
    const sendButton = screen.getByTitle('Send Message');
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(ApiService.sendMessage).toHaveBeenCalledWith(
        'Write a Ship 30 for 30 atomic essay about retention',
        undefined,
        [],
        'chat',
        undefined,
        undefined,
        expect.any(String)
      );
    });
  });
});
