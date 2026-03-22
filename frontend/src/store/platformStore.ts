import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";
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
  difySelectedAppId: string;

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
  setDifySelectedApp: (appId: string) => void;

  setCozeDb: (url: string, connected: boolean) => void;
  setDifyDb: (url: string, connected: boolean) => void;

  setDevMode: (enabled: boolean, coze: DetectedService[], dify: DetectedService[]) => void;

  setActiveTab: (tab: "coze" | "dify") => void;
  reset: () => void;
}

type PlatformStoreData = Omit<
  PlatformState,
  | "setCozeCredentials"
  | "setCozeConnected"
  | "setCozeSelectedSpace"
  | "setCozeWorkflows"
  | "setDifyCredentials"
  | "setDifyConnected"
  | "setDifyApps"
  | "setDifySelectedApp"
  | "setCozeDb"
  | "setDifyDb"
  | "setDevMode"
  | "setActiveTab"
  | "reset"
>;

type PersistedPlatformState = Pick<
  PlatformStoreData,
  "cozeApiBase" | "cozeSelectedSpace" | "difyApiBase" | "difySelectedAppId" | "activeTab"
>;

const initialState: PlatformStoreData = {
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
  difySelectedAppId: "",

  cozeDbUrl: "",
  cozeDbConnected: false,
  difyDbUrl: "",
  difyDbConnected: false,

  devModeEnabled: false,
  detectedCoze: [],
  detectedDify: [],

  activeTab: "coze",
};

function partializePlatformState(state: PlatformState): PersistedPlatformState {
  return {
    cozeApiBase: state.cozeApiBase,
    cozeSelectedSpace: state.cozeSelectedSpace,
    difyApiBase: state.difyApiBase,
    difySelectedAppId: state.difySelectedAppId,
    activeTab: state.activeTab,
  };
}

function migratePlatformState(persistedState: unknown): PlatformStoreData {
  const state = (persistedState ?? {}) as Partial<PlatformStoreData>;

  return {
    ...initialState,
    cozeApiBase:
      typeof state.cozeApiBase === "string" && state.cozeApiBase
        ? state.cozeApiBase
        : initialState.cozeApiBase,
    cozeSelectedSpace: typeof state.cozeSelectedSpace === "string" ? state.cozeSelectedSpace : "",
    difyApiBase: typeof state.difyApiBase === "string" ? state.difyApiBase : "",
    difySelectedAppId: typeof state.difySelectedAppId === "string" ? state.difySelectedAppId : "",
    activeTab: state.activeTab === "dify" ? "dify" : "coze",
  };
}

export const usePlatformStore = create<PlatformState>()(
  persist(
    (set) => ({
      ...initialState,
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
      setDifySelectedApp: (appId) => set({ difySelectedAppId: appId }),
      setCozeDb: (url, connected) =>
        set({ cozeDbUrl: url, cozeDbConnected: connected }),
      setDifyDb: (url, connected) =>
        set({ difyDbUrl: url, difyDbConnected: connected }),
      setDevMode: (enabled, coze, dify) =>
        set({ devModeEnabled: enabled, detectedCoze: coze, detectedDify: dify }),
      setActiveTab: (tab) => set({ activeTab: tab }),
      reset: () => set(initialState),
    }),
    {
      name: "coze2dify-platform",
      version: 1,
      storage: createJSONStorage(() => sessionStorage),
      partialize: partializePlatformState,
      migrate: migratePlatformState,
    },
  ),
);
