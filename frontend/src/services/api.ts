import type { Session, Message, Artifact } from '../types';

export interface DocumentInfo {
  id: string;
  filename: string;
  status: 'processing' | 'indexed' | 'failed';
  error_message?: string;
  created_at: string;
}

export class ApiService {
  static async getSessions(): Promise<Session[]> {
    const res = await fetch('/api/v1/chat/sessions');
    if (!res.ok) {
      console.error('Failed to load sessions');
      return [];
    }
    return await res.json();
  }

  static async getSessionMessages(sessionId: string): Promise<Message[]> {
    const res = await fetch(`/api/v1/chat/sessions/${sessionId}/messages`);
    if (!res.ok) {
      console.error('Failed to load session messages');
      return [];
    }
    return await res.json();
  }

  static async getSessionArtifacts(sessionId: string): Promise<Artifact[]> {
    const res = await fetch(`/api/v1/chat/sessions/${sessionId}/artifacts`);
    if (!res.ok) {
      console.error('Failed to load session artifacts');
      return [];
    }
    return await res.json();
  }

  static async getArtifact(artifactId: string): Promise<Artifact | null> {
    const res = await fetch(`/api/v1/chat/artifacts/${artifactId}`);
    if (!res.ok) {
      console.error(`Failed to load artifact ${artifactId}`);
      return null;
    }
    return await res.json();
  }

  static async sendMessage(
    content: string,
    sessionId?: string,
    documentIds: string[] = [],
    mode: "chat" | "ship30" | "artifact" = "chat",
    writingOptions?: Record<string, any>,
    artifactOptions?: Record<string, any>
  ): Promise<{ session_id: string; response: Message; artifact?: Artifact }> {
    const payload: any = {
      content,
      document_ids: documentIds,
      mode,
    };
    if (sessionId) {
      payload.session_id = sessionId;
    }
    if (writingOptions) {
      payload.writing_options = writingOptions;
    }
    if (artifactOptions) {
      payload.artifact_options = artifactOptions;
    }
    
    const res = await fetch('/api/v1/chat/message', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });
    
    if (!res.ok) {
      throw new Error("Failed to send message");
    }
    
    return await res.json();
  }

  static async uploadDocument(file: File): Promise<DocumentInfo> {
    const formData = new FormData();
    formData.append('file', file);
    
    const res = await fetch('/api/v1/documents/upload', {
      method: 'POST',
      body: formData
    });
    
    if (!res.ok) {
      throw new Error(`Failed to upload ${file.name}`);
    }
    
    return await res.json();
  }

  static async listDocuments(): Promise<DocumentInfo[]> {
    const res = await fetch('/api/v1/documents/');
    if (!res.ok) {
      throw new Error("Failed to list documents");
    }
    return await res.json();
  }

  static async deleteDocument(documentId: string): Promise<void> {
    const res = await fetch(`/api/v1/documents/${documentId}`, {
      method: 'DELETE'
    });
    if (!res.ok) {
      throw new Error("Failed to delete document");
    }
  }
}
