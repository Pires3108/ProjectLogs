import "@testing-library/jest-dom/vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import Home from "./page";

const capabilities = {
  perfis: [
    { perfil: "estudo", toggles_permitidos: ["exercicios"], secoes_obrigatorias: [], foco: "Aprender" },
    { perfil: "organizacao", toggles_permitidos: ["linha_do_tempo"], secoes_obrigatorias: [], foco: "Organizar" },
    { perfil: "backlog", toggles_permitidos: [], secoes_obrigatorias: [], foco: "Executar" },
  ],
  formatos_planejados_v1: ["txt", "md"],
};

afterEach(() => vi.unstubAllGlobals());

describe("Home", () => {
  it("carrega os três perfis previstos pela API", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => capabilities }));

    render(<Home />);

    expect(screen.getByRole("heading", { name: /A reunião termina/ })).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("Aprender")).toBeInTheDocument());
    expect(screen.getByText("Organização")).toBeInTheDocument();
    expect(screen.getByText("Backlog")).toBeInTheDocument();
  });
});

