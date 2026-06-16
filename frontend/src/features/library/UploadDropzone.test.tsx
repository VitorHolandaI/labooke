import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import type { ReactNode } from "react";
import { describe, expect, it } from "vitest";

import { server } from "../../test/mswServer";
import { UploadDropzone } from "./UploadDropzone";

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe("UploadDropzone", () => {
  it("stages an accepted file before uploading", async () => {
    server.use(
      http.post("*/api/books", async () =>
        HttpResponse.json({ id: 1, status: "pending" }, { status: 202 }),
      ),
    );
    const user = userEvent.setup();
    const { container } = render(<UploadDropzone />, { wrapper });
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    await user.upload(input, new File(["%PDF-1"], "doc.pdf", { type: "application/pdf" }));

    // file appears in staging with its stem as title
    expect(screen.getByDisplayValue("doc")).toBeInTheDocument();
    expect(screen.getByText("doc.pdf")).toBeInTheDocument();
    // no queued text yet — not uploaded
    expect(screen.queryByText(/queued/i)).not.toBeInTheDocument();
  });

  it("sends file with edited title and tags after clicking upload", async () => {
    let receivedTitle: string | undefined;
    server.use(
      http.post("*/api/books", async ({ request }) => {
        const form = await request.formData();
        receivedTitle = form.get("title") as string | undefined;
        return HttpResponse.json({ id: 1, status: "pending" }, { status: 202 });
      }),
      http.get("*/api/tags", () => HttpResponse.json([])),
    );
    const user = userEvent.setup();
    const { container } = render(<UploadDropzone />, { wrapper });
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    await user.upload(input, new File(["%PDF-1"], "great-book.pdf", { type: "application/pdf" }));

    // edit the title
    const titleInput = screen.getByDisplayValue("great-book");
    await user.clear(titleInput);
    await user.type(titleInput, "Great Book");

    // click upload
    await user.click(screen.getByRole("button", { name: /upload/i }));

    await waitFor(() => expect(receivedTitle).toBe("Great Book"));
    await waitFor(() => expect(screen.getByText(/ingesting/i)).toBeInTheDocument(), {
      timeout: 3000,
    });
  });

  it("rejects unsupported file types without staging them for upload", async () => {
    let calls = 0;
    server.use(
      http.post("*/api/books", () => {
        calls += 1;
        return HttpResponse.json({ id: 1, status: "pending" }, { status: 202 });
      }),
    );
    const { container } = render(<UploadDropzone />, { wrapper });
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const png = new File(["x"], "image.png", { type: "image/png" });
    Object.defineProperty(input, "files", { value: [png], configurable: true });
    fireEvent.change(input);
    await waitFor(() => expect(screen.getByText(/unsupported file type/i)).toBeInTheDocument());
    expect(calls).toBe(0);
  });

  it("allows removing a staged file before uploading", async () => {
    const user = userEvent.setup();
    const { container } = render(<UploadDropzone />, { wrapper });
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    await user.upload(input, new File(["%PDF-1"], "book.pdf", { type: "application/pdf" }));

    expect(screen.getByText("book.pdf")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /remove book\.pdf/i }));
    expect(screen.queryByText("book.pdf")).not.toBeInTheDocument();
  });
});
