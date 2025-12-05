"use client";

import * as duckdb from "@duckdb/duckdb-wasm";
import { useState, useEffect, useCallback } from "react";

type DuckDBState = {
    db: duckdb.AsyncDuckDB | null;
    loading: boolean;
    error: Error | null;
};

const PARQUET_URL = process.env.NEXT_PUBLIC_DATA_URL || "/data/emendas_rastreadas.parquet";

export function useDuckDB() {
    const [state, setState] = useState<DuckDBState>({
        db: null,
        loading: true,
        error: null,
    });

    useEffect(() => {
        let isMounted = true;

        async function initDuckDB() {
            try {
                // Get bundles - use jsdelivr CDN for production
                const JSDELIVR_BUNDLES = duckdb.getJsDelivrBundles();

                // Select best bundle for the browser
                const bundle = await duckdb.selectBundle(JSDELIVR_BUNDLES);

                // Instantiate worker
                const worker_url = URL.createObjectURL(
                    new Blob([`importScripts("${bundle.mainWorker!}");`], {
                        type: "text/javascript",
                    })
                );

                const worker = new Worker(worker_url);
                const logger = new duckdb.ConsoleLogger();
                const db = new duckdb.AsyncDuckDB(logger, worker);

                await db.instantiate(bundle.mainModule, bundle.pthreadWorker);

                // Register the parquet file
                await db.registerFileURL(
                    "emendas.parquet",
                    PARQUET_URL,
                    duckdb.DuckDBDataProtocol.HTTP,
                    false
                );

                if (isMounted) {
                    setState({ db, loading: false, error: null });
                }
            } catch (error) {
                console.error("Failed to initialize DuckDB:", error);
                if (isMounted) {
                    setState({
                        db: null,
                        loading: false,
                        error: error instanceof Error ? error : new Error(String(error)),
                    });
                }
            }
        }

        initDuckDB();

        return () => {
            isMounted = false;
        };
    }, []);

    const executeQuery = useCallback(
        async (sql: string): Promise<Record<string, unknown>[]> => {
            if (!state.db) {
                throw new Error("Database not initialized");
            }

            const conn = await state.db.connect();
            try {
                const result = await conn.query(sql);
                return result.toArray().map((row) => row.toJSON());
            } finally {
                await conn.close();
            }
        },
        [state.db]
    );

    return {
        db: state.db,
        loading: state.loading,
        error: state.error,
        executeQuery,
        isReady: state.db !== null && !state.loading,
    };
}
