"use client";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main>
      <section className="intro">
        <span className="eyebrow">Algo deu errado</span>
        <h1>A página parou de responder.</h1>
        <p className="formError" role="alert">
          {error.message || "Ocorreu um erro inesperado ao carregar esta página."}
        </p>
        <button className="primaryAction" onClick={reset} type="button">
          Tentar novamente
        </button>
      </section>
    </main>
  );
}
