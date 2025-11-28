const API_BASE_URL = 'http://localhost:8000/api';

export interface ProcessSettings {
  languages: string;
  extractImages: boolean;
  extractTables: boolean;
  maxCharacters: number;
  newAfterNChars: number;
  combineTextUnderNChars: number;
}

export interface SearchQuery {
  query: string;
  document_id?: string;
  k?: number;
}

export interface Document {
  document_id: string;
  chunks_processed: number;
  images_extracted: number;
  processing_time: number;
  created_at: string;
}

class ApiService {
  async healthCheck() {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.json();
  }

  async getLanguages() {
    const response = await fetch(`${API_BASE_URL}/languages`);
    return response.json();
  }

  async uploadPDF(file: File, settings: ProcessSettings) {
    console.log('=== Upload Debug ===');
    console.log('Selected language code:', settings.languages);
    console.log('Full settings:', settings);
    
    // ✅ FIX: Build query parameters for the URL (like Swagger does)
    const queryParams = new URLSearchParams({
      max_characters: String(settings.maxCharacters),
      new_after_n_chars: String(settings.newAfterNChars),
      combine_text_under_n_chars: String(settings.combineTextUnderNChars),
      extract_images: String(settings.extractImages),
      extract_tables: String(settings.extractTables),
      languages: settings.languages || 'english', // ✅ Send as query parameter
    });

    console.log('🔗 Query params:', queryParams.toString());
    console.log('🌐 Language in URL:', settings.languages);

    // ✅ Create FormData with ONLY the file
    const formData = new FormData();
    formData.append('file', file);

    // ✅ FIX: Append query parameters to URL (like Swagger)
    const url = `${API_BASE_URL}/process-pdf?${queryParams.toString()}`;
    console.log('📤 POST URL:', url);

    const response = await fetch(url, {
      method: 'POST',
      body: formData,
      // Don't set Content-Type - browser will set it with boundary
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }

    const result = await response.json();
    console.log('✅ Upload response:', result);
    return result;
  }

  async search(query: SearchQuery) {
    const response = await fetch(`${API_BASE_URL}/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(query),
    });

    if (!response.ok) {
      throw new Error(`Search failed: ${response.statusText}`);
    }

    return response.json();
  }

  async getDocuments() {
    const response = await fetch(`${API_BASE_URL}/documents`);
    return response.json();
  }

  async downloadDocument(documentId: string) {
    const response = await fetch(`${API_BASE_URL}/documents?document_id=${documentId}`);
    const blob = await response.blob();
    
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `document_${documentId}.zip`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  }

  async downloadAllData() {
    const response = await fetch(`${API_BASE_URL}/download-all`);
    
    if (!response.ok) {
      throw new Error(`Download failed: ${response.statusText}`);
    }
    
    const blob = await response.blob();
    
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'project_data.zip';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  }

  async getDocumentChunks(documentId: string, includeImages: boolean = true): Promise<DocumentChunksResponse> {
    const response = await fetch(`${API_BASE_URL}/documents/${documentId}/chunks?include_images=${includeImages}`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch chunks: ${response.statusText}`);
    }
    
    return response.json();
  }

  async initializeChat(documentId: string) {
    const response = await fetch(`${API_BASE_URL}/chat/init/${documentId}`, {
      method: 'POST',
    });

    if (!response.ok) {
      throw new Error(`Failed to initialize chat: ${response.statusText}`);
    }

    return response.json();
  }

  async clearChatHistory(sessionId: string) {
    const response = await fetch(`${API_BASE_URL}/chat/clear/${sessionId}`, {
      method: 'POST',
    });

    if (!response.ok) {
      throw new Error(`Failed to clear chat history: ${response.statusText}`);
    }

    return response.json();
  }
}

export interface ChunkImage {
  filename: string;
  data?: string;
  path: string;
  error?: string;
}

export interface DocumentChunk {
  chunk_index: number;
  enhanced_content: string;
  original_text: string;
  raw_tables_html: string[];
  ai_questions: string;
  ai_summary: string;
  image_interpretation: string;
  table_interpretation: string;
  image_paths: string[];
  page_numbers: number[];
  content_types: string[];
  images_base64?: ChunkImage[];
}

export interface DocumentChunksResponse {
  success: boolean;
  document_id: string;
  file_path: string;
  file_size_kb: number;
  chunks_count: number;
  images_included: boolean;
  chunks: DocumentChunk[];
}

export const apiService = new ApiService();