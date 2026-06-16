import { useMutation, useQueryClient } from "@tanstack/react-query";

import type { UploadInput } from "../../../api/upload";
import { uploadBook } from "../../../api/upload";

export function useUpload() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: UploadInput) => uploadBook(input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["books"] });
      queryClient.invalidateQueries({ queryKey: ["tags"] });
    },
  });
}
