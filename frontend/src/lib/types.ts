/** ATLAS-014 API envelope types */

export type ApiErrorBody = {
  code: string;
  message: string;
};

export type ApiResponse<T> = {
  success: boolean;
  data: T | null;
  message: string | null;
  error?: ApiErrorBody | null;
};

export type HealthData = {
  status: string;
  database: string;
};

export type UserPublic = {
  id: string;
  name: string;
  email: string;
};

export type LoginData = {
  access_token: string;
  token_type: string;
  user: UserPublic;
};
