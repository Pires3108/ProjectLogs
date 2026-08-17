import { JobWorkspace } from "../components/JobWorkspace";

export default function Home() {
  return (
    <main>
      <header className="masthead">
        <div className="brand">AtaViva</div>
        <div className="mastheadMeta">Fontes → análise → documento</div>
      </header>
      <section className="intro">
        <span className="eyebrow">Mesa de documentação</span>
        <h1>A reunião termina.<br />O trabalho continua claro.</h1>
        <p>
          Reúna transcrições, documentos, áudio e vídeo. Escolha a leitura que você precisa e
          acompanhe a transformação em um documento navegável.
        </p>
      </section>
      <JobWorkspace />
    </main>
  );
}

