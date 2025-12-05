"use client";

interface EvidenceLinkProps {
    url: string;
    date?: string;
    territory?: string;
    excerpts?: string[];
}

export function EvidenceLink({ url, date, territory, excerpts }: EvidenceLinkProps) {
    return (
        <div className="bg-gradient-to-br from-emerald-900/30 to-teal-900/30 rounded-xl p-5 border border-emerald-500/30 hover:border-emerald-400/50 transition-all">
            <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-emerald-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                    <svg className="w-6 h-6 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                        />
                    </svg>
                </div>

                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                        <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-400 text-xs font-medium rounded">
                            Querido Diário
                        </span>
                        {date && (
                            <span className="text-slate-400 text-xs">
                                {new Date(date).toLocaleDateString("pt-BR")}
                            </span>
                        )}
                    </div>

                    <h4 className="text-white font-medium mb-1">
                        Diário Oficial {territory && `- ${territory}`}
                    </h4>

                    {excerpts && excerpts.length > 0 && (
                        <div className="mb-3">
                            {excerpts.slice(0, 2).map((excerpt, idx) => (
                                <p key={idx} className="text-slate-400 text-sm line-clamp-2 mb-1">
                                    &ldquo;...{excerpt.slice(0, 150)}...&rdquo;
                                </p>
                            ))}
                        </div>
                    )}

                    <a
                        href={url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white text-sm font-medium rounded-lg transition-colors"
                    >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                            />
                        </svg>
                        Acessar Documento Oficial
                    </a>
                </div>
            </div>
        </div>
    );
}

interface EvidenceListProps {
    evidences: {
        url: string;
        date?: string;
        territory?: string;
        excerpts?: string[];
    }[];
}

export function EvidenceList({ evidences }: EvidenceListProps) {
    if (!evidences || evidences.length === 0) {
        return (
            <div className="text-center py-8 text-slate-400">
                <p>Nenhuma evidência disponível</p>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                </svg>
                Evidências Documentadas
            </h3>

            <div className="space-y-3">
                {evidences.map((evidence, idx) => (
                    <EvidenceLink key={idx} {...evidence} />
                ))}
            </div>
        </div>
    );
}
