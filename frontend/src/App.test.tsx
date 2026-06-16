import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import App from "./App";
import { ThemeProvider } from "./theme/ThemeProvider";

function renderAt(initialEntries: string[]) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={initialEntries}>
          <App />
        </MemoryRouter>
      </QueryClientProvider>
    </ThemeProvider>,
  );
}

describe("App routes", () => {
  it("renders the library on /", () => {
    renderAt(["/"]);
    expect(screen.getByRole("heading", { name: /library/i })).toBeInTheDocument();
  });

  it("renders the reader shell on /read/:id", () => {
    renderAt(["/read/42"]);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("renders the tags page on /tags", () => {
    renderAt(["/tags"]);
    expect(screen.getByRole("heading", { name: /tags/i })).toBeInTheDocument();
  });

  it("toggles the theme via the toolbar button", async () => {
    const user = userEvent.setup();
    renderAt(["/"]);
    const button = screen.getByRole("button", { name: /toggle color theme/i });
    const before = document.documentElement.dataset.theme;
    await user.click(button);
    expect(document.documentElement.dataset.theme).not.toBe(before);
  });
});
