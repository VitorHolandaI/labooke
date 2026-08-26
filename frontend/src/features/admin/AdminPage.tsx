import { useState } from "react";

import type { ScanResultOut } from "../../api/admin";
import { ConfirmDialog } from "../library/ConfirmDialog";
import { AdminSummaries } from "./AdminSummaries";
import { useConfig, useReembedAll, useScan, useUpdateConfig } from "./hooks/useAdmin";
import styles from "./AdminPage.module.css";

export function AdminPage() {
  const config = useConfig();
  const scan = useScan();
  const reembed = useReembedAll();
  const configUpdate = useUpdateConfig();

  const [scanResult, setScanResult] = useState<ScanResultOut | null>(null);
  const [reembedCount, setReembedCount] = useState<number | null>(null);
  const [confirmReembed, setConfirmReembed] = useState(false);
  const [ollamaDraft, setOllamaDraft] = useState<string | null>(null);

  function handleScan() {
    setScanResult(null);
    scan.mutate(undefined, {
      onSuccess: (result) => setScanResult(result),
    });
  }

  function handleReembedConfirmed() {
    setReembedCount(null);
    reembed.mutate(undefined, {
      onSuccess: (books) => {
        setReembedCount(books.length);
        setConfirmReembed(false);
      },
    });
  }

  function saveOllamaEndpoint() {
    const value = (ollamaDraft ?? config.data?.ollama_base_url ?? "").trim();
    if (!value) return;
    configUpdate.mutate({ ollama_base_url: value }, { onSuccess: () => setOllamaDraft(null) });
  }

  function resetOllamaEndpoint() {
    configUpdate.mutate({ ollama_base_url: null }, { onSuccess: () => setOllamaDraft(null) });
  }

  return (
    <section className={styles.page}>
      <h1 className={styles.heading}>Admin</h1>

      <div className={styles.card}>
        <h2 className={styles.cardTitle}>Runtime config</h2>
        {config.isLoading && <p className={styles.muted}>Loading…</p>}
        {config.isError && <p className={styles.error}>Failed to load config.</p>}
        {config.data && (
          <dl className={styles.dl}>
            <dt>Embed model</dt>
            <dd>{config.data.embed_model}</dd>
            <dt>LLM model</dt>
            <dd>{config.data.llm_model || "Disabled"}</dd>
            <dt>Chunk pages</dt>
            <dd>{config.data.chunk_pages}</dd>
            <dt>Data dir</dt>
            <dd className={styles.mono}>{config.data.data_dir}</dd>
          </dl>
        )}
      </div>

      <div className={styles.card}>
        <h2 className={styles.cardTitle}>Ollama endpoint</h2>
        <p className={styles.desc}>
          Troque temporariamente o host usado por embeddings e LLM. Sem override, o valor do
          <code> .env</code> é usado.
        </p>
        <label className={styles.endpointField}>
          URL raiz do Ollama
          <input
            type="url"
            className={styles.endpointInput}
            value={ollamaDraft ?? config.data?.ollama_base_url ?? ""}
            onChange={(event) => setOllamaDraft(event.target.value)}
            placeholder="URL raiz do servidor Ollama"
          />
        </label>
        <div className={styles.row}>
          <button
            type="button"
            className={styles.btn}
            onClick={saveOllamaEndpoint}
            disabled={configUpdate.isPending || !(ollamaDraft ?? config.data?.ollama_base_url)}
          >
            Salvar endpoint
          </button>
          <button
            type="button"
            className={styles.btn}
            onClick={resetOllamaEndpoint}
            disabled={configUpdate.isPending || !config.data?.ollama_overridden}
          >
            Usar valor do .env
          </button>
          {config.data && (
            <span className={styles.result}>
              {config.data.ollama_overridden ? "Override do Admin" : "Padrão do .env"}
            </span>
          )}
        </div>
        {configUpdate.isError && (
          <p className={styles.error}>{configUpdate.error?.message ?? "Endpoint inválido."}</p>
        )}
      </div>

      <div className={styles.card}>
        <h2 className={styles.cardTitle}>Import folder scan</h2>
        <p className={styles.desc}>
          Walk <code>LABOOKE_IMPORT_DIR</code> and ingest any supported files found there (PDF,
          EPUB, TXT, MD).
        </p>
        <div className={styles.row}>
          <button
            type="button"
            className={styles.btn}
            onClick={handleScan}
            disabled={scan.isPending}
          >
            {scan.isPending ? "Scanning…" : "Scan now"}
          </button>
          {scan.isError && (
            <span className={styles.error}>{scan.error?.message ?? "Scan failed."}</span>
          )}
          {scanResult && (
            <span className={styles.result}>
              {scanResult.ingested} ingested · {scanResult.skipped} skipped · {scanResult.failed}{" "}
              failed
            </span>
          )}
        </div>
      </div>

      <div className={styles.card}>
        <h2 className={styles.cardTitle}>Rebuild embeddings</h2>
        <p className={styles.desc}>
          Regenerate all book embeddings manually. Required after changing{" "}
          <code>LABOOKE_CHUNK_PAGES</code> or switching the embed model; migrations never start this
          job automatically.
        </p>
        <div className={styles.row}>
          <button
            type="button"
            className={`${styles.btn} ${styles.btnDanger}`}
            onClick={() => setConfirmReembed(true)}
            disabled={reembed.isPending}
          >
            {reembed.isPending ? "Working…" : "Redo all embeddings"}
          </button>
          {reembed.isError && (
            <span className={styles.error}>{reembed.error?.message ?? "Failed."}</span>
          )}
          {reembedCount !== null && !reembed.isPending && (
            <span className={styles.result}>
              Reembedding started for {reembedCount} book
              {reembedCount !== 1 ? "s" : ""}.
            </span>
          )}
        </div>
      </div>

      <AdminSummaries />

      {confirmReembed && (
        <ConfirmDialog
          title="Redo all embeddings"
          message="Rebuild vector embeddings for every book in the library. This may take several minutes."
          confirmLabel="Redo all"
          danger
          isPending={reembed.isPending}
          onClose={() => setConfirmReembed(false)}
          onConfirm={handleReembedConfirmed}
        />
      )}
    </section>
  );
}
