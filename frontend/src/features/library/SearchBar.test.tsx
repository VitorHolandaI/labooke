import { act, fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { SearchBar } from "./SearchBar";

describe("SearchBar", () => {
  it("debounces input changes and emits a single q patch", () => {
    vi.useFakeTimers();
    const onChange = vi.fn();
    render(<SearchBar q="" mode="lexical" onChange={onChange} debounceMs={200} />);

    fireEvent.change(screen.getByLabelText(/library search/i), { target: { value: "rust" } });
    expect(onChange).not.toHaveBeenCalled();
    act(() => {
      vi.advanceTimersByTime(250);
    });

    expect(onChange).toHaveBeenLastCalledWith({ q: "rust" });
    vi.useRealTimers();
  });

  it("toggles between lexical and semantic modes", () => {
    const onChange = vi.fn();
    render(<SearchBar q="" mode="lexical" onChange={onChange} />);
    fireEvent.click(screen.getByRole("button", { name: /semantic/i }));
    expect(onChange).toHaveBeenCalledWith({ mode: "semantic" });
  });

  it("placeholder reflects the current mode", () => {
    const { rerender } = render(
      <SearchBar q="" mode="lexical" onChange={() => {}} />,
    );
    expect(screen.getByPlaceholderText(/title or filename/i)).toBeInTheDocument();
    rerender(<SearchBar q="" mode="semantic" onChange={() => {}} />);
    expect(screen.getByPlaceholderText(/semantic/i)).toBeInTheDocument();
  });
});
