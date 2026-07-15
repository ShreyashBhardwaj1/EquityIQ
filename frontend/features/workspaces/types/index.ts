export interface Workspace {
  id: string;
  name: string;
  owner_id: string;
  created_at: string;
  updated_at: string;
}

export interface WorkspaceCreatePayload {
  name: string;
}

export interface WorkspacePatchPayload {
  name: string;
}

export interface SwitchResponse {
  detail: string;
  workspace_id: string;
}
