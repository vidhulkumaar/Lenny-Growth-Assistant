export interface Citation {
  source_key: string;
  title: string;
  source_url?: string;
  excerpt?: string;
  page_number?: number;
}

export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
  citations?: Citation[];
}

export interface Session {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface Artifact {
  id: string;
  session_id: string;
  title: string;
  artifact_type: "markdown" | "html";
  content: string;
  created_at: string;
  citations?: Citation[];
}

