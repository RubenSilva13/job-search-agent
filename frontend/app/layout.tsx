import type { Metadata } from "next";
import Link from "next/link";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Job Search Agent",
  description: "Painel de vagas analisadas por um agente de IA escrito à mão",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="pt-PT"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        {/* O cabeçalho aparece em todas as páginas */}
        <header className="border-b border-borda bg-superficie">
          <nav className="mx-auto flex max-w-3xl items-center justify-between px-8 py-3">
            <Link href="/" className="font-semibold">
              Job Search Agent
            </Link>
            <div className="flex gap-5 text-sm text-suave">
              <Link href="/" className="hover:text-foreground">
                Vagas
              </Link>
              <Link href="/nova" className="hover:text-foreground">
                Nova vaga
              </Link>
              <Link href="/custos" className="hover:text-foreground">
                Custos
              </Link>
            </div>
          </nav>
        </header>
        {children}
      </body>
    </html>
  );
}
