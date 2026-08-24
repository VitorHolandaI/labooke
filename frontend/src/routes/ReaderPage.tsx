import { Suspense, lazy, useCallback, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { BookmarkDrawer } from "../features/reader/BookmarkDrawer";
import { TagsEditDialog } from "../features/library/TagsEditDialog";
import { useAttachTag, useDetachTag } from "../features/library/hooks/useBookActions";
import { useTags } from "../features/library/hooks/useTags";
import { useBook } from "../features/reader/hooks/useBook";
import { useBookmarks, useCreateBookmark } from "../features/reader/hooks/useBookmarks";

const PdfViewer = lazy(() =>
  import("../features/reader/viewers/PdfViewer").then((m) => ({ default: m.PdfViewer })),
);
const EpubViewer = lazy(() =>
  import("../features/reader/viewers/EpubViewer").then((m) => ({ default: m.EpubViewer })),
);
const TextViewer = lazy(() =>
  import("../features/reader/viewers/TextViewer").then((m) => ({ default: m.TextViewer })),
);

import { useDebouncedProgress, useProgress } from "../features/reader/hooks/useProgress";
import styles from "./ReaderPage.module.css";

export default function ReaderPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const bookId = Number(id);
  const book = useBook(bookId);
  const progress = useProgress(bookId);
  const [page, setPage] = useState<number | null>(null);
  const [jumpTarget, setJumpTarget] = useState<number | null>(null);
  const [editingTags, setEditingTags] = useState(false);

  const { data: tagCounts = [] } = useTags();
  const allTags = tagCounts.map((tc) => tc.tag);
  const attach = useAttachTag();
  const detach = useDetachTag();

  const currentPage = page ?? progress.data?.page_no ?? 1;
  useDebouncedProgress(bookId, currentPage);

  const bookmarks = useBookmarks(bookId);
  const createBookmark = useCreateBookmark(bookId);
  const isBookmarked = !!bookmarks.data?.find((bm) => bm.page_no === currentPage);
  const addBookmark = useCallback(() => {
    createBookmark.mutate({ page_no: currentPage, label: `Page ${currentPage}`, note: null });
  }, [createBookmark, currentPage]);

  const handlePageChange = useCallback((next: number) => {
    setPage(next);
  }, []);

  if (book.isLoading) return <p className={styles.loading}>Loading…</p>;
  if (book.isError || !book.data)
    return <p className={styles.error}>Failed to load book.</p>;

  const initial = jumpTarget ?? progress.data?.page_no ?? 1;
  const format = book.data.format;

  let viewer: React.ReactNode;
  if (format === "pdf") {
    viewer = (
      <PdfViewer
        key={`pdf-${bookId}-${jumpTarget ?? ""}`}
        bookId={bookId}
        initialPage={initial}
        onPageChange={handlePageChange}
        isBookmarked={isBookmarked}
        onAddBookmark={addBookmark}
      />
    );
  } else if (format === "epub") {
    viewer = (
      <EpubViewer
        key={`epub-${bookId}-${jumpTarget ?? ""}`}
        bookId={bookId}
        initialPage={initial}
        onPageChange={handlePageChange}
        isBookmarked={isBookmarked}
        onAddBookmark={addBookmark}
      />
    );
  } else if (format === "txt" || format === "md") {
    viewer = (
      <TextViewer
        key={`text-${bookId}-${jumpTarget ?? ""}`}
        bookId={bookId}
        format={format}
        initialPage={initial}
        onPageChange={handlePageChange}
        isBookmarked={isBookmarked}
        onAddBookmark={addBookmark}
      />
    );
  } else {
    viewer = (
      <div className={styles.unsupported}>Unsupported format: {format}</div>
    );
  }

  return (
    <div className={styles.layout}>
      <div className={styles.main}>
        <header className={styles.header}>
          <div>
            <h1 className={styles.title}>{book.data.title}</h1>
            {book.data.author && (
              <p className={styles.author}>{book.data.author}</p>
            )}
          </div>
          <div className={styles.tagBar}>
            {book.data.tags.map((tag) => (
              <button
                key={tag.id}
                type="button"
                className={styles.tagChip}
                onClick={() => navigate(`/?tags=${tag.id}`)}
              >
                {tag.name}
              </button>
            ))}
            <button
              type="button"
              className={styles.editTags}
              onClick={() => setEditingTags(true)}
            >
              Editar tags
            </button>
          </div>
        </header>
        <Suspense fallback={<p className={styles.loading}>Loading viewer…</p>}>
          {viewer}
        </Suspense>
      </div>
      <BookmarkDrawer
        bookId={bookId}
        currentPage={currentPage}
        onJump={(target) => {
          setJumpTarget(target);
          setPage(target);
        }}
      />
      {editingTags && (
        <TagsEditDialog
          book={book.data}
          allTags={allTags}
          isPending={attach.isPending || detach.isPending}
          onClose={() => setEditingTags(false)}
          onToggle={(tag, attached) => {
            if (attached) detach.mutate({ bookId, tagId: tag.id });
            else attach.mutate({ bookId, tagId: tag.id });
          }}
        />
      )}
    </div>
  );
}
