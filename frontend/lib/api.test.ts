import { describe, expect, it } from "vitest";

import { effectiveToggles, emptyToggles, formatBytes } from "./api";

describe("API helpers", () => {
  it("desativa toggles incompatíveis quando o perfil muda", () => {
    const result = effectiveToggles(
      { ...emptyToggles(), exercicios: true, linha_do_tempo: true },
      ["linha_do_tempo"],
    );

    expect(result.exercicios).toBe(false);
    expect(result.linha_do_tempo).toBe(true);
  });

  it("formata tamanhos para a lista de fontes", () => {
    expect(formatBytes(12)).toBe("12 B");
    expect(formatBytes(2048)).toBe("2.0 KB");
    expect(formatBytes(2 * 1024 ** 2)).toBe("2.0 MB");
  });
});
