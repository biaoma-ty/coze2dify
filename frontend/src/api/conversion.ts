import client from "./client";
import type { ConversionDetail, ConversionHistoryResponse, ConversionResult } from "../types/ir";

export async function convertWorkflow(file: File): Promise<ConversionResult> {
  const form = new FormData();
  form.append("file", file);
  const resp = await client.post<ConversionResult>("/convert", form);
  return resp.data;
}

export async function convertWorkflowFromApi(params: {
  access_token: string;
  workflow_id: string;
  api_base?: string;
}): Promise<ConversionResult> {
  const resp = await client.post<ConversionResult>("/convert/from-api", params);
  return resp.data;
}

export async function convertWorkflowFromDb(params: {
  db_url: string;
  workflow_id: string;
}): Promise<ConversionResult> {
  const resp = await client.post<ConversionResult>("/convert/from-db", params);
  return resp.data;
}

export async function getConversion(conversionId: string): Promise<ConversionDetail> {
  const resp = await client.get<ConversionDetail>(`/convert/${conversionId}`);
  return resp.data;
}

export async function listConversionHistory(params: {
  limit?: number;
  offset?: number;
} = {}): Promise<ConversionHistoryResponse> {
  const resp = await client.get<ConversionHistoryResponse>("/convert", { params });
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

export async function writeToDify(
  conversionId: string,
  payload: { db_url?: string; app_id?: string },
): Promise<{ conversion_id: string; app_id: string; mode: "create" | "update"; status: string }> {
  const resp = await client.post(`/convert/${conversionId}/write-to-dify`, payload);
  return resp.data;
}
