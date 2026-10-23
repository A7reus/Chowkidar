let apiToken: string | null = null;

export function setApiToken(token: string | null) {
  apiToken = token;
}

export function getApiToken() {
  return apiToken;
}
