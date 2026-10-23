import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";

import { server } from "../../test/mswServer";
import { AdminSummaries } from "./AdminSummaries";
import { adminBook } from "./test/adminBooks";
import { renderAdmin } from "./test/renderAdmin";

const summarized = adminBook({ id: 7, title: "Sistemas Distribuídos" });
const unsummarized = adminBook({ id: 8, title: "Redes", description: null });

function serveBooks() {
  server.use(
    http.get("*/api/config", () => HttpResponse.json({ llm_summary_pages: 10, llm_enabled: true })),
    http.get("*/api/books", () =>
      HttpResponse.json({ items: [summarized, unsummarized], total: 2 }),
    ),
  );
}

describe("AdminSummaries", () => {
  it("summarizes only the books still missing a summary", async () => {
    const user = userEvent.setup();
    serveBooks();
    let sent: unknown;
    server.use(
      http.post("*/api/admin/summaries/batch", async ({ request }) => {
        sent = await request.json();
        return HttpResponse.json({ book_ids: [8] }, { status: 202 });
      }),
    );
    renderAdmin(<AdminSummaries />);

    await screen.findByRole("checkbox", { name: /Redes/ });
    await user.click(screen.getByRole("button", { name: "Marcar sem resumo" }));
    await user.click(screen.getByRole("button", { name: "Resumir marcados (1)" }));

    await screen.findByText(/Processando/);
    expect(sent).toEqual({ book_ids: [8], pages: 10 });
  });

  it("marks which books already have a summary", async () => {
    serveBooks();
    renderAdmin(<AdminSummaries />);

    expect(await screen.findByRole("checkbox", { name: /Feito.*Sistemas/ })).toBeInTheDocument();
    expect(screen.getByRole("checkbox", { name: /Pendente.*Redes/ })).toBeInTheDocument();
  });
});
