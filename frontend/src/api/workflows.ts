import client from "./client";
import type { UploadResult } from "../types/ir";

export async function uploadWorkflow(file: File): Promise<UploadResult> {
  const form = new FormData();
  form.append("file", file);
  const resp = await client.post<UploadResult>("/coze/upload", form);
  return resp.data;
}
