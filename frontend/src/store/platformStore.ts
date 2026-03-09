import { create } from "zustand";
import type {
  CozeWorkspace,
  CozeWorkflowItem,
  DifyAppItem,
  DetectedService,
} from "../types/platform";

interface PlatformState {
  /* ── Coze ── */
  cozeToken: string;
  cozeApiBase: string;
  cozeConnected: boolean;
  cozeWorkspaces: CozeWorkspace[];
  cozeSelectedSpace: string;
  cozeWorkflows: CozeWorkflowItem[];

  /* ── Dify ── */
  difyApiBase: string;
  difyApiKey: string;
  difyConnected: boolean;
  difyApps: DifyAppItem[];

  /* ── DB ── */
  cozeDbUrl: string;
  cozeDbConnected: boolean;
  difyDbUrl: string;
  difyDbConnected: boolean;

  /* ── Dev Mode ── */
  devModeEnabled: boolean;
  detectedCoze: DetectedService[];
  detectedDify: DetectedService[];

  /* ── Active tab ── */
  activeTab: "coze" | "dify";

  /* ── Actions ── */
  setCozeCredentials: (token: string, apiBase: string) => void;
  setCozeConnected: (connected: boolean, workspaces: CozeWorkspace[]) => void;
  setCozeSelectedSpace: (spaceId: string) => void;
  setCozeWorkflows: (workflows: CozeWorkflowItem[]) => void;

  setDifyCredentials: (apiBase: string, apiKey: string) => void;
  setDifyConnected: (connected: boolean) => void;
  setDifyApps: (apps: DifyAppItem[]) => void;

  setCozeDb: (url: string, connected: boolean) => void;
  setDifyDb: (url: string, connected: boolean) => void;

  setDevMode: (enabled: boolean, coze: DetectedService[], dify: DetectedService[]) => void;

  setActiveTab: (tab: "coze" | "dify") => void;
  reset: () => void;
}

export const usePlatformStore = create<PlatformState>((set) => ({
  cozeToken: "",
  cozeApiBase: "https://api.coze.com",
  cozeConnected: false,
  cozeWorkspaces: [],
  cozeSelectedSpace: "",
  cozeWorkflows: [],

  difyApiBase: "",
  difyApiKey: "",
  difyConnected: false,
  difyApps: [],

  cozeDbUrl: "",
  cozeDbConnected: false,
  difyDbUrl: "",
  difyDbConnected: false,

  devModeEnabled: false,
  detectedCoze: [],
  detectedDify: [],

  activeTab: "coze",

  setCozeCredentials: (token, apiBase) =>
    set({ cozeToken: token, cozeApiBase: apiBase }),

  setCozeConnected: (connected, workspaces) =>
    set({ cozeConnected: connected, cozeWorkspaces: workspaces }),

  setCozeSelectedSpace: (spaceId) => set({ cozeSelectedSpace: spaceId }),

  setCozeWorkflows: (workflows) => set({ cozeWorkflows: workflows }),

  setDifyCredentials: (apiBase, apiKey) =>
    set({ difyApiBase: apiBase, difyApiKey: apiKey }),

  setDifyConnected: (connected) => set({ difyConnected: connected }),

  setDifyApps: (apps) => set({ difyApps: apps }),

  setCozeDb: (url, connected) =>
    set({ cozeDbUrl: url, cozeDbConnected: connected }),

  setDifyDb: (url, connected) =>
    set({ difyDbUrl: url, difyDbConnected: connected }),

  setDevMode: (enabled, coze, dify) =>
    set({ devModeEnabled: enabled, detectedCoze: coze, detectedDify: dify }),

  setActiveTab: (tab) => set({ activeTab: tab }),

  reset: () =>
    set({
      cozeToken: "",
      cozeApiBase: "https://api.coze.com",
      cozeConnected: false,
      cozeWorkspaces: [],
      cozeSelectedSpace: "",
      cozeWorkflows: [],
      difyApiBase: "",
      difyApiKey: "",
      difyConnected: false,
      difyApps: [],
      cozeDbUrl: "",
      cozeDbConnected: false,
      difyDbUrl: "",
      difyDbConnected: false,
      devModeEnabled: false,
      detectedCoze: [],
      detectedDify: [],
      activeTab: "coze",
    }),
}));
