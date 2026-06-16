import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { TagOut } from "../../api/tags";
import { MergeTagsDialog } from "./MergeTagsDialog";

const TAG_A: TagOut = { id: 1, name: "fiction", slug: "fiction", color: "#f00" };
const TAG_B: TagOut = { id: 2, name: "linux", slug: "linux", color: "#0f0" };

describe("MergeTagsDialog", () => {
  it("renders both tags in each select", () => {
    render(
      <MergeTagsDialog tags={[TAG_A, TAG_B]} onMerge={vi.fn()} onClose={vi.fn()} />,
    );
    const selects = screen.getAllByRole("combobox");
    expect(selects).toHaveLength(2);
    expect(screen.getAllByRole("option", { name: "fiction" })).toHaveLength(2);
    expect(screen.getAllByRole("option", { name: "linux" })).toHaveLength(2);
  });

  it("Merge button is disabled until both selects have different values", async () => {
    const user = userEvent.setup();
    render(
      <MergeTagsDialog tags={[TAG_A, TAG_B]} onMerge={vi.fn()} onClose={vi.fn()} />,
    );
    const mergeBtn = screen.getByRole("button", { name: /merge/i });
    expect(mergeBtn).toBeDisabled();

    const [sourceSelect, targetSelect] = screen.getAllByRole("combobox");
    await user.selectOptions(sourceSelect, "1");
    expect(mergeBtn).toBeDisabled();

    await user.selectOptions(targetSelect, "2");
    expect(mergeBtn).not.toBeDisabled();
  });

  it("calls onMerge with sourceId and targetId when Merge is clicked", async () => {
    const user = userEvent.setup();
    const onMerge = vi.fn();
    render(
      <MergeTagsDialog tags={[TAG_A, TAG_B]} onMerge={onMerge} onClose={vi.fn()} />,
    );
    const [sourceSelect, targetSelect] = screen.getAllByRole("combobox");
    await user.selectOptions(sourceSelect, "1");
    await user.selectOptions(targetSelect, "2");
    await user.click(screen.getByRole("button", { name: /merge/i }));
    expect(onMerge).toHaveBeenCalledWith(1, 2);
  });

  it("calls onClose when Cancel is clicked", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(
      <MergeTagsDialog tags={[TAG_A, TAG_B]} onMerge={vi.fn()} onClose={onClose} />,
    );
    await user.click(screen.getByRole("button", { name: /cancel/i }));
    expect(onClose).toHaveBeenCalled();
  });
});
