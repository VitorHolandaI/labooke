import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { useBookSelection } from "./useBookSelection";

describe("useBookSelection", () => {
  it("toggles a single book on and off", () => {
    const { result } = renderHook(() => useBookSelection());
    act(() => result.current.toggle(3));
    expect([...result.current.selected]).toEqual([3]);
    act(() => result.current.toggle(3));
    expect(result.current.selected.size).toBe(0);
  });

  it("replaces, extends and clears the selection", () => {
    const { result } = renderHook(() => useBookSelection());
    act(() => result.current.selectIds([1, 2]));
    act(() => result.current.addIds([2, 5]));
    expect([...result.current.selected]).toEqual([1, 2, 5]);
    act(() => result.current.selectIds([9]));
    expect([...result.current.selected]).toEqual([9]);
    act(() => result.current.clear());
    expect(result.current.selected.size).toBe(0);
  });
});
