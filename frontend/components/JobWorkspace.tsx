"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import {
  apiRequest,
  Capabilities,
  effectiveToggles,
  emptyToggles,
  formatBytes,
  Job,
  Profile,
  toggleLabels,
  ToggleName,
  uploadDirectly,
} from "../lib/api";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const directUpload = process.env.NEXT_PUBLIC_DIRECT_UPLOAD === "true";
const profileNames: Record<Profile, string> = {
  estudo: "Estudo",
  organizacao: "Organização",
  backlog: "Backlog",
};
const profileOrder: Profile[] = ["estudo", "organizacao", "backlog"];

export function JobWorkspace() {
  const [capabilities, setCapabilities] = useState<Capabilities | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [profile, setProfile] = useState<Profile>("estudo");
  const [toggles, setToggles] = useState(emptyToggles);
  const [files, setFiles] = useState<File[]>([]);
  const [job, setJob] = useState<Job | null>(null);
  const [history, setHistory] = useState<Job[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Deferred to an effect (not a useState initializer) so the client's first render
    // matches the static export's server-rendered markup; sessionStorage is unavailable
    // during static generation and differs per browser tab, so reading it synchronously
    // during render would cause a hydration mismatch.
    const saved = sessionStorage.getItem("ataviva-job-history");
    if (!saved) return;
    try {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- syncing one-time from sessionStorage on mount
      setHistory(JSON.parse(saved));
    } catch {
      sessionStorage.removeItem("ataviva-job-history");
    }
  }, []);

  const remember = useCallback((updated: Job) => {
    setHistory((current) => {
      const next = [updated, ...current.filter((item) => item.id !== updated.id)].slice(0, 8);
      sessionStorage.setItem("ataviva-job-history", JSON.stringify(next));
      return next;
    });
  }, []);

  useEffect(() => {
    apiRequest<Capabilities>(apiBaseUrl, "/v1/capabilities")
      .then(setCapabilities)
      .catch((reason: Error) => setError(reason.message));
  }, []);

  useEffect(() => {
    if (!job || !apiKey || !["queued", "processing"].includes(job.status)) return;
    const timer = window.setTimeout(() => {
      apiRequest<Job>(apiBaseUrl, `/v1/jobs/${job.id}`, {}, apiKey)
        .then((updated) => { setJob(updated); remember(updated); })
        .catch((reason: Error) => setError(reason.message));
    }, 2000);
    return () => window.clearTimeout(timer);
  }, [job, apiKey, remember]);

  const profileDefinition = useMemo(
    () => capabilities?.perfis.find((item) => item.perfil === profile),
    [capabilities, profile],
  );

  function chooseProfile(next: Profile) {
    setProfile(next);
    const allowed = capabilities?.perfis.find((item) => item.perfil === next)?.toggles_permitidos || [];
    setToggles((current) => effectiveToggles(current, allowed));
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    if (!apiKey.trim()) return setError("Informe uma API Key para criar o job.");
    if (!files.length) return setError("Selecione ao menos uma fonte.");
    setBusy(true);
    try {
      let created: Job;
      if (directUpload) {
        const tickets = await Promise.all(
          files.map((file) => uploadDirectly(apiBaseUrl, file, apiKey)),
        );
        created = await apiRequest<Job>(apiBaseUrl, "/v1/jobs/from-uploads", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ perfil: profile, toggles, tickets }),
        }, apiKey);
      } else {
        const form = new FormData();
        form.set("perfil", profile);
        form.set("toggles", JSON.stringify(toggles));
        files.forEach((file) => form.append("fontes", file));
        created = await apiRequest<Job>(apiBaseUrl, "/v1/jobs", {
          method: "POST",
          body: form,
        }, apiKey);
      }
      setJob(created);
      remember(created);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Não foi possível criar o job.");
    } finally {
      setBusy(false);
    }
  }

  async function downloadHtml() {
    if (!job?.html_url) return;
    try {
      const response = await fetch(`${apiBaseUrl}${job.html_url}`, { headers: { "X-API-Key": apiKey } });
      if (!response.ok) throw new Error("O documento ainda não pôde ser baixado.");
      const url = URL.createObjectURL(await response.blob());
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `ataviva-${job.id}.html`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Falha no download.");
    }
  }

  async function viewHtml() {
    if (!job?.html_url) return;
    try {
      const response = await fetch(`${apiBaseUrl}${job.html_url}`, { headers: { "X-API-Key": apiKey } });
      if (!response.ok) throw new Error("O documento ainda não pôde ser visualizado.");
      const url = URL.createObjectURL(await response.blob());
      window.open(url, "_blank", "noopener,noreferrer");
      window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Falha na visualização.");
    }
  }

  return (
    <section className="workspace" aria-labelledby="workspace-title">
      <div className="sectionIndex">01 / ENTRADA</div>
      <h2 id="workspace-title">Monte a análise</h2>
      <form onSubmit={submit}>
        <div className="workGrid">
          <div className="panel sourcePanel">
            <label className="fieldLabel" htmlFor="api-key">API Key da sessão</label>
            <input id="api-key" type="password" value={apiKey} onChange={(event) => setApiKey(event.target.value)} autoComplete="off" placeholder="ataviva_…" />
            <p className="fieldHint">Mantida apenas em memória; desaparece ao recarregar.</p>
            <label className="dropzone" htmlFor="sources">
              <span className="dropTitle">Escolher fontes</span>
              <span>TXT, VTT, SRT, MD, DOCX, MP3, WAV, MP4 ou MOV</span>
              <input id="sources" type="file" multiple accept=".txt,.vtt,.srt,.md,.docx,.mp3,.wav,.mp4,.mov" onChange={(event) => setFiles(Array.from(event.target.files || []))} />
            </label>
            {files.length > 0 && <ul className="fileList">{files.map((file) => <li key={`${file.name}-${file.size}`}><span>{file.name}</span><small>{formatBytes(file.size)}</small></li>)}</ul>}
          </div>
          <div className="panel configPanel">
            <fieldset>
              <legend>Perfil do documento</legend>
              <div className="profileList">{profileOrder.map((item) => {
                const definition = capabilities?.perfis.find((candidate) => candidate.perfil === item);
                return <label className={`profileChoice ${profile === item ? "selected" : ""}`} key={item}><input type="radio" name="perfil" value={item} checked={profile === item} onChange={() => chooseProfile(item)} /><strong>{profileNames[item]}</strong><span>{definition?.foco || "Carregando regras…"}</span></label>;
              })}</div>
            </fieldset>
            <fieldset>
              <legend>Conteúdo adicional</legend>
              <div className="toggleGrid">{(Object.keys(toggleLabels) as ToggleName[]).map((name) => {
                const allowed = profileDefinition?.toggles_permitidos.includes(name) ?? false;
                return <label className={`toggle ${!allowed ? "disabled" : ""}`} key={name}><input type="checkbox" checked={toggles[name]} disabled={!allowed} onChange={(event) => setToggles((current) => ({ ...current, [name]: event.target.checked }))} /><span>{toggleLabels[name]}</span></label>;
              })}</div>
            </fieldset>
            <button className="primaryAction" disabled={busy || !capabilities}>{busy ? "Enviando…" : "Criar documento"}</button>
            {error && <p className="formError" role="alert">{error}</p>}
          </div>
        </div>
      </form>
      <JobStatus job={job} onDownload={downloadHtml} onView={viewHtml} />
      {history.length > 0 && <section className="history"><div className="sectionIndex">03 / SESSÃO</div><h2>Jobs recentes</h2><div className="historyList">{history.map((item) => <button key={item.id} onClick={() => setJob(item)}><span>{profileNames[item.perfil]}</span><code>{item.id.slice(0, 8)}</code><StatusLabel status={item.status} /></button>)}</div></section>}
    </section>
  );
}

function JobStatus({ job, onDownload, onView }: { job: Job | null; onDownload: () => void; onView: () => void }) {
  if (!job) return null;
  return <section className="statusPanel" aria-live="polite"><div className="sectionIndex">02 / PROCESSAMENTO</div><div className="statusHeader"><div><StatusLabel status={job.status} /><h2>{job.status === "done" ? "Documento pronto" : job.status === "failed" ? "O processamento falhou" : "Documento em preparação"}</h2>{job.fila_posicao && <p className="queuePosition">Posição atual na fila: <strong>{job.fila_posicao}</strong>{job.fila_estimativa_minutos && <> · estimativa de até <strong>{job.fila_estimativa_minutos} min</strong></>}</p>}</div><code>{job.id}</code></div><div className="sourceSummary">{job.fontes.map((source) => <span key={source.id}>{source.nome}</span>)}</div>{job.avisos.map((warning) => <p className="jobWarning" key={warning.toggle}>{warning.message}</p>)}{job.status === "done" && job.html_url && <div className="resultActions"><button className="downloadAction" onClick={onView}>Visualizar HTML</button><button className="downloadAction" onClick={onDownload}>Baixar HTML</button></div>}{job.status === "failed" && <p className="formError">Consulte o motivo no status da API e tente novamente.</p>}</section>;
}

function StatusLabel({ status }: { status: Job["status"] }) {
  const labels = { queued: "Na fila", processing: "Processando", done: "Pronto", failed: "Erro" };
  return <span className={`status status-${status}`}>{labels[status]}</span>;
}
