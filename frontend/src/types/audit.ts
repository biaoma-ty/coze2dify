export interface DatabaseTargetRef {
  scheme: string | null;
  host: string | null;
  port: number | null;
  database: string | null;
  display_url: string;
}
