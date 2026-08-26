import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";

import { server } from "../../test/mswServer";
import { AdminSummaries } from "./AdminSummaries";

const summarizedBook = {
  id: 7,
  sha256: "book-7",
  title: "Sistemas Distribuídos",
  author: null,
  description: "Consenso, replicação e tolerância a falhas.",
  format: "pdf",
  page_count: 200,
  status: "ready",
  ingest_error: null,
  tags: [],
};

function renderSummaries() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <AdminSummaries />
    </QueryClientProvider>,
  );
}

describe("AdminSummaries", () => {
  it("schedules selected summarized books for auto-tagging", async () => {
    const user = userEvent.setup();
    server.use(
      http.get("*/api/config", () =>
        HttpResponse.json({ llm_summary_pages: 10, llm_enabled: true }),
      ),
      http.get("*/api/books", () => HttpResponse.json({ items: [summarizedBook], total: 1 })),
      http.post("*/api/admin/tags/auto", async ({ request }) => {
        expect(await request.json()).toEqual({ book_ids: [7] });
        return HttpResponse.json({ book_ids: [7] }, { status: 202 });
      }),
    );
    renderSummaries();

    await user.click(await screen.findByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: "Taguear com IA (1)" }));

    expect(await screen.findByText(/Tagueamento iniciado no servidor/)).toBeInTheDocument();
  });
});
