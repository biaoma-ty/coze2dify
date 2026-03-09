import client from "./client";
import type { ConversionResult } from "../types/ir";

export async function convertWorkflow(file: File): Promise<ConversionResult> {
  const form = new FormData();
  form.append("file", file);
  const resp = await client.post<ConversionResult>("/convert", form);
  return resp.data;
}

export async function downloadDSL(conversionId: string): Promise<Blob> {
  const resp = await client.get(`/convert/${conversionId}/dsl`, { responseType: "blob" });
  return resp.data;
}

export async function getReport(conversionId: string) {
  const resp = await client.get(`/convert/${conversionId}/report`);
  return resp.data;
}
