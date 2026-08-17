import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: "AtaViva",
  description: "Documentação inteligente para reuniões",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}

