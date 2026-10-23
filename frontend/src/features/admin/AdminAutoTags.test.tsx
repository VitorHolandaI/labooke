import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";

import { server } from "../../test/mswServer";
import { AdminAutoTags } from "./AdminAutoTags";
import { adminBook } from "./test/adminBooks";
import { renderAdmin } from "./test/renderAdmin";

const tagged = adminBook({
  id: 1,
  title: "Compiladores",
  auto_tagged_at: "2026-10-23T12:00:00Z",
  tags: [{ id: 4, name: "Linguagens", slug: "linguagens", color: "#000" }],
});
const untagged = adminBook({ id: 7, title: "Sistemas Distribuídos" });
const noSummary = adminBook({ id: 9, title: "Redes", description: null });

function serve(llmEnabled = true) {
  server.use(
    http.get("*/api/config", () =>
      HttpResponse.json({ llm_summary_pages: 10, llm_enabled: llmEnabled }),
    ),
    http.get("*/api/books", () =>
      HttpResponse.json({ items: [tagged, untagged, noSummary], total: 3 }),
    ),
  );
}

describe("AdminAutoTags", () => {
  it("marks which books the LLM already classified, with their tags", async () => {
    serve();
    renderAdmin(<AdminAutoTags />);

    expect(
      await screen.findByRole("checkbox", { name: /Feito.*Compiladores/ }),
    ).toBeInTheDocument();
    expect(screen.getByRole("checkbox", { name: /Pendente.*Sistemas/ })).toBeInTheDocument();
    expect(screen.getByText("Linguagens")).toBeInTheDocument();
  });

  // Auto-tagging reads the summary, so books without one can't be sent.
  it("sends only marked books that have a summary", async () => {
    const user = userEvent.setup();
    serve();
    let sent: unknown;
    server.use(
      http.post("*/api/admin/tags/auto", async ({ request }) => {
        sent = await request.json();
        return HttpResponse.json({ book_ids: [7] }, { status: 202 });
      }),
    );
    renderAdmin(<AdminAutoTags />);

    await screen.findByRole("checkbox", { name: /Sistemas/ });
    await user.click(screen.getByRole("button", { name: "Marcar sem tag IA" }));
    expect(screen.getByText(/1 marcado sem resumo/)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Taguear marcados (1)" }));

    expect(await screen.findByText(/Tagueamento iniciado no servidor/)).toBeInTheDocument();
    expect(sent).toEqual({ book_ids: [7] });
  });

  it("disables tagging while no LLM is configured", async () => {
    serve(false);
    renderAdmin(<AdminAutoTags />);

    await screen.findByRole("checkbox", { name: /Sistemas/ });
    expect(screen.getByRole("button", { name: /Taguear marcados/ })).toBeDisabled();
  });
});
