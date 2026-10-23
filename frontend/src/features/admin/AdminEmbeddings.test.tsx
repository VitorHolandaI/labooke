import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";

import { server } from "../../test/mswServer";
import { AdminEmbeddings } from "./AdminEmbeddings";
import { adminBook } from "./test/adminBooks";
import { renderAdmin } from "./test/renderAdmin";

const embedded = adminBook({ id: 1, title: "Compiladores" });
const failed = adminBook({
  id: 2,
  title: "Sistemas Operacionais",
  status: "failed",
  ingest_error: "ollama timeout",
});
const running = adminBook({ id: 3, title: "Bancos de Dados", status: "reembedding" });

describe("AdminEmbeddings", () => {
  it("shows each book's embedding state and the failure reason", async () => {
    server.use(
      http.get("*/api/books", () =>
        HttpResponse.json({ items: [embedded, failed, running], total: 3 }),
      ),
    );
    renderAdmin(<AdminEmbeddings />);

    expect(
      await screen.findByRole("checkbox", { name: /Feito.*Compiladores/ }),
    ).toBeInTheDocument();
    expect(screen.getByRole("checkbox", { name: /Pendente.*Sistemas/ })).toBeInTheDocument();
    expect(screen.getByRole("checkbox", { name: /Em andamento.*Bancos/ })).toBeInTheDocument();
    expect(screen.getByText("ollama timeout")).toBeInTheDocument();
  });

  it("re-embeds only the marked books in one batch", async () => {
    const user = userEvent.setup();
    let sent: unknown;
    server.use(
      http.get("*/api/books", () =>
        HttpResponse.json({ items: [embedded, failed, running], total: 3 }),
      ),
      http.post("*/api/admin/reembed-batch", async ({ request }) => {
        sent = await request.json();
        return HttpResponse.json([{ book_id: 2, status: "reembedding" }], { status: 202 });
      }),
    );
    renderAdmin(<AdminEmbeddings />);

    await screen.findByRole("checkbox", { name: /Sistemas/ });
    await user.click(screen.getByRole("button", { name: "Marcar sem embedding" }));
    await user.click(screen.getByRole("button", { name: "Re-embedar marcados (1)" }));

    expect(await screen.findByText(/Re-embedding iniciado para 1 livro/)).toBeInTheDocument();
    expect(sent).toEqual({ book_ids: [2] });
  });
});
