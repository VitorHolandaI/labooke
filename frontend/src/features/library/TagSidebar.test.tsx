import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { server } from "../../test/mswServer";
import { TagSidebar } from "./TagSidebar";
import type { LibraryFilters } from "./hooks/useLibraryFilters";

function setup(filtersOverride: Partial<LibraryFilters> = {}) {
  const onToggle = vi.fn();
  const onTagModeChange = vi.fn();
  const filters: LibraryFilters = {
    q: "",
    mode: "lexical",
    tags: [],
    exclude: [],
    tag_mode: "all",
    ...filtersOverride,
  };
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <TagSidebar filters={filters} onToggle={onToggle} onTagModeChange={onTagModeChange} />
      </MemoryRouter>
    </QueryClientProvider>,
  );
  return { onToggle, onTagModeChange };
}

const mockTags = [
  { tag: { id: 1, name: "fiction", slug: "fiction", color: "#aaa" }, count: 3 },
  { tag: { id: 2, name: "tech", slug: "tech", color: "#bbb" }, count: 7 },
];

describe("TagSidebar", () => {
  it("renders tags with counts after fetch", async () => {
    server.use(http.get("*/api/tags", () => HttpResponse.json(mockTags)));
    setup();
    await waitFor(() => expect(screen.getByText("fiction")).toBeInTheDocument());
    expect(screen.getByText("7")).toBeInTheDocument();
  });

  it("plain click toggles include", async () => {
    server.use(http.get("*/api/tags", () => HttpResponse.json(mockTags)));
    const user = userEvent.setup();
    const { onToggle } = setup();
    await waitFor(() => expect(screen.getByText("fiction")).toBeInTheDocument());
    await user.click(screen.getByText("fiction"));
    expect(onToggle).toHaveBeenCalledWith(1, { exclude: false });
  });

  it("alt-click toggles exclude", async () => {
    server.use(http.get("*/api/tags", () => HttpResponse.json(mockTags)));
    const user = userEvent.setup();
    const { onToggle } = setup();
    await waitFor(() => expect(screen.getByText("tech")).toBeInTheDocument());
    await user.keyboard("{Alt>}");
    await user.click(screen.getByText("tech"));
    await user.keyboard("{/Alt}");
    expect(onToggle).toHaveBeenCalledWith(2, { exclude: true });
  });

  it("switches tag_mode via ALL/ANY toggle", async () => {
    server.use(http.get("*/api/tags", () => HttpResponse.json(mockTags)));
    const user = userEvent.setup();
    const { onTagModeChange } = setup();
    await waitFor(() => expect(screen.getByText("fiction")).toBeInTheDocument());
    await user.click(screen.getByRole("button", { name: "ANY" }));
    expect(onTagModeChange).toHaveBeenCalledWith("any");
  });

  it("filters tags by the search input", async () => {
    server.use(http.get("*/api/tags", () => HttpResponse.json(mockTags)));
    const user = userEvent.setup();
    setup();
    await waitFor(() => expect(screen.getByText("fiction")).toBeInTheDocument());
    await user.type(screen.getByRole("searchbox", { name: /filter tags/i }), "tech");
    expect(screen.queryByText("fiction")).toBeNull();
    expect(screen.getByText("tech")).toBeInTheDocument();
  });
});
