import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

import { server } from "../../test/mswServer";
import { BookmarkDrawer } from "./BookmarkDrawer";

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

const sampleBookmark = {
  id: 7,
  book_id: 4,
  page_no: 10,
  label: "Intro",
  note: null,
  created_at: "2026-01-01T00:00:00Z",
};

describe("BookmarkDrawer", () => {
  it("lists bookmarks and jumps on click", async () => {
    server.use(
      http.get("*/api/books/4/bookmarks", () => HttpResponse.json([sampleBookmark])),
    );
    const onJump = vi.fn();
    const user = userEvent.setup();
    render(
      <BookmarkDrawer bookId={4} currentPage={1} onJump={onJump} />,
      { wrapper },
    );
    await waitFor(() => expect(screen.getByText("Intro")).toBeInTheDocument());
    await user.click(screen.getByText("Intro"));
    expect(onJump).toHaveBeenCalledWith(10);
  });

  it("posts a bookmark for the current page", async () => {
    let received: { label: string; page_no: number } | undefined;
    server.use(
      http.get("*/api/books/4/bookmarks", () => HttpResponse.json([])),
      http.post("*/api/books/4/bookmarks", async ({ request }) => {
        received = (await request.json()) as { label: string; page_no: number };
        return HttpResponse.json(
          { ...sampleBookmark, page_no: 25, label: received.label },
          { status: 201 },
        );
      }),
    );
    const user = userEvent.setup();
    render(
      <BookmarkDrawer bookId={4} currentPage={25} onJump={() => {}} />,
      { wrapper },
    );
    await waitFor(() => expect(screen.getByText(/no bookmarks/i)).toBeInTheDocument());
    await user.click(screen.getByRole("button", { name: /bookmark page 25/i }));
    await waitFor(() => expect(received?.page_no).toBe(25));
    expect(received?.label).toBe("Page 25");
  });
});
