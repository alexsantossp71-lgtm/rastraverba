"use client";

import { useState } from "react";

interface SqlConsoleProps {
    executeQuery: (sql: string) => Promise<Record<string, unknown>[]>;
    isReady: boolean;
}

export function SqlConsole({ executeQuery, isReady }: SqlConsoleProps) {
    const [query, setQuery] = useState(
        "SELECT * FROM 'emendas.parquet' LIMIT 10"
    );
    const [results, setResults] = useState<Record<string, unknown>[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    const handleExecute = async () => {
        if (!isReady) return;

        setLoading(true);
        setError(null);

        try {
            const data = await executeQuery(query);
            setResults(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : String(err));
            setResults([]);
        } finally {
            setLoading(false);
        }
    };

    const columns = results.length > 0 ? Object.keys(results[0]) : [];

    return (
        <div className="bg-slate-900 rounded-xl p-6 shadow-2xl border border-slate-700">
            <div className="flex items-center gap-3 mb-4">
                <div className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse"></div>
                <h2 className="text-xl font-bold text-white">Console SQL</h2>
                <span className="text-xs text-slate-400 ml-auto">
                    {isReady ? "DuckDB Conectado" : "Carregando..."}
                </span>
            </div>

            <div className="space-y-4">
                <div className="relative">
                    <textarea
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        className="w-full h-32 bg-slate-800 text-emerald-400 font-mono text-sm p-4 rounded-lg border border-slate-600 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none resize-none"
                        placeholder="Digite sua query SQL..."
                        disabled={!isReady}
                    />
                    <button
                        onClick={handleExecute}
                        disabled={!isReady || loading}
                        className="absolute bottom-4 right-4 px-4 py-2 bg-gradient-to-r from-emerald-500 to-teal-500 text-white font-semibold rounded-lg hover:from-emerald-600 hover:to-teal-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? (
                            <span className="flex items-center gap-2">
                                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                                    <circle
                                        className="opacity-25"
                                        cx="12"
                                        cy="12"
                                        r="10"
                                        stroke="currentColor"
                                        strokeWidth="4"
                                        fill="none"
                                    />
                                    <path
                                        className="opacity-75"
                                        fill="currentColor"
                                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                                    />
                                </svg>
                                Executando...
                            </span>
                        ) : (
                            "▶ Executar"
                        )}
                    </button>
                </div>

                {error && (
                    <div className="p-4 bg-red-900/50 border border-red-500 rounded-lg text-red-200 text-sm">
                        <strong>Erro:</strong> {error}
                    </div>
                )}

                {results.length > 0 && (
                    <div className="overflow-x-auto">
                        <div className="text-sm text-slate-400 mb-2">
                            {results.length} resultado(s)
                        </div>
                        <table className="w-full text-sm text-left">
                            <thead className="bg-slate-800 text-slate-300">
                                <tr>
                                    {columns.map((col) => (
                                        <th key={col} className="px-4 py-3 font-medium border-b border-slate-700">
                                            {col}
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {results.map((row, idx) => (
                                    <tr
                                        key={idx}
                                        className="border-b border-slate-800 hover:bg-slate-800/50 transition-colors"
                                    >
                                        {columns.map((col) => (
                                            <td key={col} className="px-4 py-3 text-slate-300 max-w-xs truncate">
                                                {String(row[col] ?? "")}
                                            </td>
                                        ))}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}
