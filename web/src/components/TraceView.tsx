"use client";

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

interface TraceViewProps {
    data: TraceRecord[];
}

function formatCurrency(value: number): string {
    return new Intl.NumberFormat("pt-BR", {
        style: "currency",
        currency: "BRL",
    }).format(value);
}

function TraceCard({ record }: { record: TraceRecord }) {
    const cnpjs = record.cnpjs_encontrados
        ? record.cnpjs_encontrados.split(",").map((c) => c.trim()).filter(Boolean)
        : [];

    return (
        <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-6 border border-slate-700 hover:border-emerald-500/50 transition-all shadow-xl">
            {/* Flow visualization */}
            <div className="flex items-center gap-3 mb-6">
                {/* Author */}
                <div className="flex-1 text-center">
                    <div className="w-12 h-12 mx-auto bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center text-white font-bold text-lg shadow-lg shadow-blue-500/30">
                        👤
                    </div>
                    <p className="mt-2 text-sm font-medium text-slate-300 truncate max-w-[150px] mx-auto">
                        {record.emenda_autor || "Deputado"}
                    </p>
                    <p className="text-xs text-slate-500">Autor</p>
                </div>

                {/* Arrow + Value */}
                <div className="flex flex-col items-center">
                    <div className="text-emerald-400 font-bold text-sm">
                        {formatCurrency(record.emenda_valor || 0)}
                    </div>
                    <div className="flex items-center">
                        <div className="w-8 h-0.5 bg-gradient-to-r from-blue-500 to-purple-500"></div>
                        <svg className="w-4 h-4 text-purple-500" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" />
                        </svg>
                    </div>
                </div>

                {/* Municipality */}
                <div className="flex-1 text-center">
                    <div className="w-12 h-12 mx-auto bg-gradient-to-br from-purple-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold text-lg shadow-lg shadow-purple-500/30">
                        🏛️
                    </div>
                    <p className="mt-2 text-sm font-medium text-slate-300 truncate max-w-[150px] mx-auto">
                        {record.municipio_nome || "Município"}
                    </p>
                    <p className="text-xs text-slate-500">{record.uf || "UF"}</p>
                </div>

                {/* Arrow */}
                <div className="flex items-center">
                    <div className="w-8 h-0.5 bg-gradient-to-r from-purple-500 to-amber-500"></div>
                    <svg className="w-4 h-4 text-amber-500" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" />
                    </svg>
                </div>

                {/* Company */}
                <div className="flex-1 text-center">
                    <div className="w-12 h-12 mx-auto bg-gradient-to-br from-amber-500 to-orange-600 rounded-full flex items-center justify-center text-white font-bold text-lg shadow-lg shadow-amber-500/30">
                        🏢
                    </div>
                    <p className="mt-2 text-sm font-medium text-slate-300 truncate max-w-[150px] mx-auto">
                        {cnpjs.length > 0 ? cnpjs[0] : "Empresa"}
                    </p>
                    <p className="text-xs text-slate-500">
                        {cnpjs.length > 1 ? `+${cnpjs.length - 1} CNPJ(s)` : "CNPJ"}
                    </p>
                </div>
            </div>

            {/* Status and Evidence */}
            <div className="flex items-center justify-between pt-4 border-t border-slate-700">
                <div className="flex items-center gap-2">
                    <span
                        className={`px-2 py-1 rounded-full text-xs font-medium ${record.link_status === "found"
                                ? "bg-emerald-500/20 text-emerald-400"
                                : record.link_status === "no_gazette"
                                    ? "bg-amber-500/20 text-amber-400"
                                    : "bg-slate-500/20 text-slate-400"
                            }`}
                    >
                        {record.link_status === "found"
                            ? "✓ Evidência Encontrada"
                            : record.link_status === "no_gazette"
                                ? "⚠ Sem Diário Oficial"
                                : "○ Dados Incompletos"}
                    </span>
                </div>

                {record.gazette_url && (
                    <a
                        href={record.gazette_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 px-3 py-1.5 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 rounded-lg text-sm font-medium transition-colors"
                    >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                            />
                        </svg>
                        Ver Evidência
                    </a>
                )}
            </div>
        </div>
    );
}

export function TraceView({ data }: TraceViewProps) {
    if (!data || data.length === 0) {
        return (
            <div className="text-center py-12 text-slate-400">
                <p className="text-lg">Nenhum rastro encontrado</p>
                <p className="text-sm mt-2">Execute uma query no Console SQL para visualizar dados</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-white flex items-center gap-3">
                    <span className="w-3 h-3 rounded-full bg-purple-500"></span>
                    Rastro do Dinheiro
                </h2>
                <span className="text-sm text-slate-400">{data.length} transferência(s)</span>
            </div>

            <div className="grid gap-6">
                {data.map((record, idx) => (
                    <TraceCard key={record.emenda_id || idx} record={record} />
                ))}
            </div>
        </div>
    );
}
