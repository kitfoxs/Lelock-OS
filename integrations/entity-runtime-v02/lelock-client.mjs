/** Thin browser client. Pair in trusted UI; keep agent/operator tokens separate and in memory. */
export class LelockClient {
  #base; #token;
  constructor(base, agentToken) {
    const url = new URL(base);
    if (url.protocol !== 'http:' || !['127.0.0.1', 'localhost'].includes(url.hostname) || !url.port || url.username || url.password || url.search || url.hash || url.pathname !== '/') {
      throw new Error('Only an explicitly paired loopback Entity daemon is supported.');
    }
    this.#base = url.origin;
    this.#token = agentToken;
  }
  async request(path, body) {
    const response = await fetch(this.#base + path, {
      method: body === undefined ? 'GET' : 'POST', mode: 'cors', credentials: 'omit', redirect: 'error',
      cache: 'no-store', headers: {Authorization: `Bearer ${this.#token}`, 'Content-Type': 'application/json'},
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.message || result.error || `HTTP ${response.status}`);
    return result;
  }
  status() { return this.request('/v1/status'); }
  tools() { return this.request('/v1/tools'); }
  invoke(tool, args, requestId = crypto.randomUUID()) {
    return this.request('/v1/invoke', {tool, arguments_json: JSON.stringify(args), request_id: requestId});
  }
}
/** Instantiate ONLY in an operator-owned approval panel. Never supply its token to a model. */
export class LelockOperatorClient extends LelockClient {
  actions() { return this.request('/v1/operator/actions'); }
  approve(actionId, reviewedDigest) { return this.request('/v1/operator/approve', {action_id: actionId, digest: reviewedDigest}); }
  reject(actionId) { return this.request('/v1/operator/reject', {action_id: actionId}); }
  stop() { return this.request('/v1/operator/stop', {}); }
}
