import { useEffect, useRef, useState } from "react";

import type { PdfSearchDocument, PdfSearchHit } from "./pdfSearch";
import { searchPdfDocument } from "./pdfSearch";
import styles from "./PdfSearchControls.module.css";

interface Props {
  pdf: PdfSearchDocument;
  currentPage: number;
  onJump: (page: number) => void;
  onQueryChange: (query: string) => void;
}

/** Search controls for extracted PDF text with page-to-page navigation. */
export function PdfSearchControls({ pdf, currentPage, onJump, onQueryChange }: Props) {
  const [draft, setDraft] = useState("");
  const [hits, setHits] = useState<PdfSearchHit[]>([]);
  const [matches, setMatches] = useState(0);
  const [active, setActive] = useState(-1);
  const [searching, setSearching] = useState(false);
  const [searched, setSearched] = useState(false);
  const [failed, setFailed] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => () => abortRef.current?.abort(), []);
  async function runSearch() {
    const query = draft.trim();
    abortRef.current?.abort();
    if (!query) {
      setHits([]);
      setMatches(0);
      setActive(-1);
      setSearched(false);
      setSearching(false);
      setFailed(false);
      onQueryChange("");
      return;
    }

    const controller = new AbortController();
    abortRef.current = controller;
    setSearching(true);
    setSearched(false);
    setFailed(false);
    try {
      const summary = await searchPdfDocument(pdf, query, controller.signal);
      setHits(summary.hits);
      setMatches(summary.matches);
      setSearched(true);
      setActive(summary.hits.length ? 0 : -1);
      onQueryChange(query);
      if (summary.hits.length) onJump(summary.hits[0].page);
    } catch (error) {
      if (!(error instanceof DOMException && error.name === "AbortError")) {
        setHits([]);
        setMatches(0);
        setActive(-1);
        setSearched(true);
        setFailed(true);
      }
    } finally {
      if (!controller.signal.aborted) setSearching(false);
    }
  }

  function move(delta: number) {
    if (!hits.length) return;
    const current = hits.findIndex((hit) => hit.page === currentPage);
    const next = ((current >= 0 ? current : active) + delta + hits.length) % hits.length;
    setActive(next);
    onJump(hits[next].page);
  }

  const current = hits.findIndex((hit) => hit.page === currentPage);
  const displayedActive = current >= 0 ? current : active;

  const status = searching
    ? "Buscando…"
    : failed
      ? "Não foi possível buscar neste PDF"
      : searched && !matches
        ? "Nenhum texto encontrado (o PDF pode ser escaneado)"
        : matches
          ? `${matches} ocorrência${matches === 1 ? "" : "s"} em ${hits.length} página${hits.length === 1 ? "" : "s"}`
          : "";

  return (
    <form
      className={styles.search}
      onSubmit={(event) => {
        event.preventDefault();
        void runSearch();
      }}
    >
      <input
        type="search"
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
        placeholder="Buscar palavra no PDF"
        aria-label="Buscar palavra no PDF"
      />
      <button type="submit" disabled={searching || !draft.trim()}>
        Buscar
      </button>
      <span className={styles.status} aria-live="polite">
        {status}
      </span>
      {hits.length > 0 && (
        <span className={styles.navigation}>
          <button type="button" onClick={() => move(-1)} aria-label="Resultado anterior">
            ↑
          </button>
          <span>
            {displayedActive + 1} / {hits.length}
          </span>
          <button type="button" onClick={() => move(1)} aria-label="Próximo resultado">
            ↓
          </button>
        </span>
      )}
    </form>
  );
}
