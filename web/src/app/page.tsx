"use client";

import { useState, useEffect } from "react";
import { useDuckDB } from "@/hooks/useDuckDB";
import { SqlConsole } from "@/components/SqlConsole";
import { TraceView } from "@/components/TraceView";

interface TraceRecord {
  emenda_id: string;
  emenda_autor: string;
  emenda_valor: number;
  municipio_nome: string;
  uf: string;
  cnpjs_encontrados: string;
  gazette_url?: string;
  link_status: string;
}

export default function Home() {
  const { loading, error, executeQuery, isReady } = useDuckDB();
  const [traceData, setTraceData] = useState<TraceRecord[]>([]);
  const [stats, setStats] = useState({
    totalEmendas: 0,
    totalValor: 0,
    totalMunicipios: 0,
    evidenciasEncontradas: 0,
  });
  const [activeTab, setActiveTab] = useState<"trace" | "sql">("trace");

  useEffect(() => {
    async function loadInitialData() {
      if (!isReady) return;

      try {
        // Load trace data
        const data = await executeQuery(`
          SELECT * FROM 'emendas.parquet' 
          ORDER BY emenda_valor DESC 
          LIMIT 20
        `);
        setTraceData(data as unknown as TraceRecord[]);

        // Load stats
        const statsQuery = await executeQuery(`
          SELECT 
            COUNT(*) as total_emendas,
            COALESCE(SUM(emenda_valor), 0) as total_valor,
            COUNT(DISTINCT municipio_nome) as total_municipios,
            SUM(CASE WHEN link_status = 'found' THEN 1 ELSE 0 END) as evidencias
          FROM 'emendas.parquet'
        `);

        if (statsQuery.length > 0) {
          const s = statsQuery[0];
          setStats({
            totalEmendas: Number(s.total_emendas) || 0,
            totalValor: Number(s.total_valor) || 0,
            totalMunicipios: Number(s.total_municipios) || 0,
            evidenciasEncontradas: Number(s.evidencias) || 0,
          });
        }
      } catch (err) {
        console.error("Failed to load initial data:", err);
      }
    }

    loadInitialData();
  }, [isReady, executeQuery]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-950/50 backdrop-blur-xl sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-500/25">
                <span className="text-xl">💰</span>
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-emerald-400 to-teal-400 bg-clip-text text-transparent">
                  RastraVerba
                </h1>
                <p className="text-xs text-slate-400">Rastreando Emendas Parlamentares</p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-800/50 rounded-lg">
                <div className={`w-2 h-2 rounded-full ${isReady ? "bg-emerald-500 animate-pulse" : "bg-amber-500"}`}></div>
                <span className="text-sm text-slate-400">
                  {loading ? "Carregando..." : isReady ? "Online" : "Offline"}
                </span>
              </div>

              <a
                href="https://github.com"
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
              >
                <svg className="w-5 h-5 text-slate-400" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
                </svg>
              </a>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Stats */}
      <section className="container mx-auto px-6 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard
            title="Total de Emendas"
            value={stats.totalEmendas.toLocaleString("pt-BR")}
            icon="📋"
            color="emerald"
          />
          <StatCard
            title="Valor Total"
            value={new Intl.NumberFormat("pt-BR", {
              style: "currency",
              currency: "BRL",
              notation: "compact",
            }).format(stats.totalValor)}
            icon="💰"
            color="blue"
          />
          <StatCard
            title="Municípios"
            value={stats.totalMunicipios.toLocaleString("pt-BR")}
            icon="🏛️"
            color="purple"
          />
          <StatCard
            title="Evidências"
            value={stats.evidenciasEncontradas.toLocaleString("pt-BR")}
            icon="✓"
            color="amber"
          />
        </div>
      </section>

      {/* Main Content */}
      <main className="container mx-auto px-6 pb-12">
        {/* Tab Navigation */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setActiveTab("trace")}
            className={`px-4 py-2 rounded-lg font-medium transition-all ${activeTab === "trace"
              ? "bg-emerald-500 text-white shadow-lg shadow-emerald-500/25"
              : "bg-slate-800 text-slate-400 hover:text-white"
              }`}
          >
            📊 Rastro do Dinheiro
          </button>
          <button
            onClick={() => setActiveTab("sql")}
            className={`px-4 py-2 rounded-lg font-medium transition-all ${activeTab === "sql"
              ? "bg-emerald-500 text-white shadow-lg shadow-emerald-500/25"
              : "bg-slate-800 text-slate-400 hover:text-white"
              }`}
          >
            💻 Console SQL
          </button>
        </div>

        {/* Error State */}
        {error && (
          <div className="mb-6 p-4 bg-red-900/30 border border-red-500/50 rounded-xl text-red-300">
            <strong>Erro:</strong> {error.message}
          </div>
        )}

        {/* Tab Content */}
        {activeTab === "trace" ? (
          <TraceView data={traceData} />
        ) : (
          <SqlConsole executeQuery={executeQuery} isReady={isReady} />
        )}

        {/* Footer Info */}
        <div className="mt-12 text-center">
          <p className="text-slate-500 text-sm">
            Dados processados com DuckDB-Wasm direto no navegador.
            <br />
            Fontes: Câmara dos Deputados, TransfereGov, Querido Diário
          </p>
        </div>
      </main>
    </div>
  );
}

function StatCard({
  title,
  value,
  icon,
  color,
}: {
  title: string;
  value: string;
  icon: string;
  color: "emerald" | "blue" | "purple" | "amber";
}) {
  const colorClasses = {
    emerald: "from-emerald-500/20 to-teal-500/20 border-emerald-500/30",
    blue: "from-blue-500/20 to-indigo-500/20 border-blue-500/30",
    purple: "from-purple-500/20 to-pink-500/20 border-purple-500/30",
    amber: "from-amber-500/20 to-orange-500/20 border-amber-500/30",
  };

  return (
    <div
      className={`bg-gradient-to-br ${colorClasses[color]} border rounded-xl p-5`}
    >
      <div className="flex items-center gap-3 mb-2">
        <span className="text-2xl">{icon}</span>
        <span className="text-slate-400 text-sm">{title}</span>
      </div>
      <div className="text-2xl font-bold text-white">{value}</div>
    </div>
  );
}
