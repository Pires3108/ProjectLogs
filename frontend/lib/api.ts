export type Profile = "estudo" | "organizacao" | "backlog";

export type ToggleName =
  | "fluxogramas"
  | "diagramas"
  | "exemplos"
  | "exercicios"
  | "glossario"
  | "linha_do_tempo"
  | "matriz_responsabilidade";

export type Capabilities = {
  perfis: Array<{
    perfil: Profile;
    toggles_permitidos: ToggleName[];
    secoes_obrigatorias: string[];
    foco: string;
  }>;
  formatos_planejados_v1: string[];
};

export type Job = {
  id: string;
  status: "queued" | "processing" | "done" | "failed";
  perfil: Profile;
  toggles: Record<ToggleName, boolean>;
  avisos: Array<{ code: string; message: string; toggle: ToggleName }>;
  fontes: Array<{
    id: string;
    nome: string;
    formato: string;
    tipo: string;
    tamanho_bytes: number;
    requer_transcricao: boolean;
  }>;
  provedor_llm: string | null;
  analise: Record<string, unknown> | null;
  erro: Record<string, unknown> | null;
  html_url: string | null;
  criado_em: string;
  atualizado_em: string;
  fila_posicao: number | null;
  fila_estimativa_minutos: number | null;
};

export type DirectUpload = {
  upload_url: string;
  metodo: "PUT";
  headers: Record<string, string>;
  ticket: string;
  expira_em: number;
};

export async function uploadDirectly(
  baseUrl: string,
  file: File,
  apiKey: string,
): Promise<string> {
  const upload = await apiRequest<DirectUpload>(baseUrl, "/v1/uploads", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      nome: file.name,
      tamanho_bytes: file.size,
      content_type: file.type || undefined,
    }),
  }, apiKey);
  const response = await fetch(upload.upload_url, {
    method: upload.metodo,
    headers: upload.headers,
    body: file,
  });
  if (!response.ok) throw new Error(`Falha ao enviar ${file.name} ao armazenamento.`);
  return upload.ticket;
}

type ApiErrorPayload = { error?: { code?: string; message?: string } };

export const toggleLabels: Record<ToggleName, string> = {
  fluxogramas: "Fluxogramas",
  diagramas: "Diagramas",
  exemplos: "Exemplos",
  exercicios: "Exercícios",
  glossario: "Glossário",
  linha_do_tempo: "Linha do tempo",
  matriz_responsabilidade: "Matriz de responsabilidade",
};

export const emptyToggles = (): Record<ToggleName, boolean> => ({
  fluxogramas: false,
  diagramas: false,
  exemplos: false,
  exercicios: false,
  glossario: false,
  linha_do_tempo: false,
  matriz_responsabilidade: false,
});

export function effectiveToggles(
  current: Record<ToggleName, boolean>,
  allowed: ToggleName[],
): Record<ToggleName, boolean> {
  const allowedSet = new Set(allowed);
  return Object.fromEntries(
    Object.entries(current).map(([name, enabled]) => [name, enabled && allowedSet.has(name as ToggleName)]),
  ) as Record<ToggleName, boolean>;
}

export async function apiRequest<T>(
  baseUrl: string,
  path: string,
  options: RequestInit = {},
  apiKey?: string,
): Promise<T> {
  const headers = new Headers(options.headers);
  if (apiKey) headers.set("X-API-Key", apiKey);
  const response = await fetch(`${baseUrl}${path}`, { ...options, headers });
  if (!response.ok) {
    let payload: ApiErrorPayload = {};
    try {
      payload = await response.json();
    } catch {
      // A resposta pode não ser JSON em falhas de infraestrutura.
    }
    throw new Error(payload.error?.message || `A API respondeu com status ${response.status}.`);
  }
  return response.json() as Promise<T>;
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
}
