import { act, renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { usePdfDocument, type PdfLoadingTask, type PdfSource } from "./usePdfDocument";

class FakePdf {
  constructor(readonly numPages: number) {}
}

/** Loading task whose outcome the test controls, counting destroy calls. */
class FakeLoadingTask implements PdfLoadingTask<FakePdf> {
  readonly promise: Promise<FakePdf>;
  destroyCalls = 0;
  resolve: (pdf: FakePdf) => void = () => {};
  reject: (error: Error) => void = () => {};

  constructor() {
    this.promise = new Promise<FakePdf>((resolve, reject) => {
      this.resolve = resolve;
      this.reject = reject;
    });
  }

  destroy(): Promise<void> {
    this.destroyCalls += 1;
    return Promise.resolve();
  }
}

class RecordingPdfOpener {
  readonly urls: string[] = [];
  readonly tasks: FakeLoadingTask[] = [];

  readonly open = (source: PdfSource): FakeLoadingTask => {
    this.urls.push(source.url);
    const task = new FakeLoadingTask();
    this.tasks.push(task);
    return task;
  };
}

describe("usePdfDocument", () => {
  it("starts loading and becomes ready with the page count", async () => {
    const opener = new RecordingPdfOpener();
    const { result } = renderHook(() => usePdfDocument("/api/books/3/file", opener.open));
    expect(result.current.state).toEqual({ phase: "loading" });

    const pdf = new FakePdf(12);
    await act(async () => opener.tasks[0].resolve(pdf));

    expect(opener.urls).toEqual(["/api/books/3/file"]);
    expect(result.current.state).toEqual({ phase: "ready", total: 12 });
    expect(result.current.pdf).toBe(pdf);
  });

  it("destroys the loading task on unmount (pdfjs 6 moved destroy there)", async () => {
    const opener = new RecordingPdfOpener();
    const { unmount } = renderHook(() => usePdfDocument("/a.pdf", opener.open));
    await act(async () => opener.tasks[0].resolve(new FakePdf(1)));

    unmount();

    expect(opener.tasks[0].destroyCalls).toBe(1);
  });

  it("destroys a task that is still loading and ignores its late result", async () => {
    const opener = new RecordingPdfOpener();
    const { result, unmount } = renderHook(() => usePdfDocument("/a.pdf", opener.open));

    unmount();
    await act(async () => opener.tasks[0].resolve(new FakePdf(5)));

    expect(opener.tasks[0].destroyCalls).toBe(1);
    expect(result.current.state).toEqual({ phase: "loading" });
  });

  it("reloads when the url changes, destroying the previous task", async () => {
    const opener = new RecordingPdfOpener();
    const { rerender } = renderHook(({ url }) => usePdfDocument(url, opener.open), {
      initialProps: { url: "/a.pdf" },
    });

    rerender({ url: "/b.pdf" });

    expect(opener.urls).toEqual(["/a.pdf", "/b.pdf"]);
    expect(opener.tasks[0].destroyCalls).toBe(1);
  });

  it("reports the load error message", async () => {
    const opener = new RecordingPdfOpener();
    const { result } = renderHook(() => usePdfDocument("/a.pdf", opener.open));

    await act(async () => opener.tasks[0].reject(new Error("Missing PDF")));

    await waitFor(() =>
      expect(result.current.state).toEqual({ phase: "error", message: "Missing PDF" }),
    );
  });
});
