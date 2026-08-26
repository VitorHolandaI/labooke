import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { server } from "../../test/mswServer";
import { AskPanel } from "./AskPanel";

const recommendedBook = {
  id: 7,
  sha256: "book-7",
  title: "Sistemas Distribuídos",
  author: "Ana Autora",
  description: "Uma introdução prática.",
  format: "pdf",
  page_count: 200,
  status: "ready",
  ingest_error: null,
  tags: [],
};

function renderPanel() {
  const client = new QueryClient({ defaultOptions: { mutations: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <AskPanel />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("AskPanel", () => {
  it("renders ranked recommendations with their reasons", async () => {
    const user = userEvent.setup();
    server.use(
      http.post("*/api/ask", async ({ request }) => {
        expect(await request.json()).toEqual({ question: "quero aprender sistemas distribuídos" });
        return HttpResponse.json({
          answer: "Encontrei uma opção introdutória.",
          books: [recommendedBook],
          recommendations: [
            { book: recommendedBook, reason: "Explica consenso e tolerância a falhas." },
          ],
        });
      }),
    );
    renderPanel();

    await user.type(
      screen.getByRole("textbox", { name: /ask the library/i }),
      "quero aprender sistemas distribuídos",
    );
    await user.click(screen.getByRole("button", { name: /encontrar livros/i }));

    expect(await screen.findByText("Encontrei uma opção introdutória.")).toBeInTheDocument();
    expect(screen.getByText("Explica consenso e tolerância a falhas.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Sistemas Distribuídos/i })).toHaveAttribute(
      "href",
      "/book/7",
    );
  });
});
