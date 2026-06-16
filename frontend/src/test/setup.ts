import "@testing-library/jest-dom";
import { File as NodeFile } from "node:buffer";
import { afterAll, afterEach, beforeAll } from "vitest";

import { server } from "./mswServer";

// Node 26 exposes window.localStorage as undefined (experimental, needs --localstorage-file).
// Provide an in-memory stub so ThemeProvider and other consumers work in jsdom tests.
const makeLocalStorageMock = () => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
};
Object.defineProperty(globalThis, "localStorage", {
  value: makeLocalStorageMock(),
  configurable: true,
  writable: true,
});

// fetch / FormData / Headers / Request / Response are native globals in Node 22+.
// Only File needs a stub: jsdom's File differs from the node:buffer one the API client expects.
Object.defineProperty(globalThis, "File", { value: NodeFile, configurable: true, writable: true });

beforeAll(() => server.listen({ onUnhandledRequest: "warn" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
