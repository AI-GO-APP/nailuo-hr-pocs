/* @ai-go-sdk */
/**
 * DB Proxy SDK — 供 Custom App 存取現有 SaaS 資料表
 * 透過 fetch 直接呼叫後端 API，操作已授權的現有資料表。
 */

const API_BASE = (window as any).__API_BASE__ || '/api/v1';

function _getHeaders(): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  const token = (window as any).__APP_TOKEN__ || '';
  if (token) headers['Authorization'] = 'Bearer ' + token;
  return headers;
}

async function _handleResponse(resp: Response): Promise<any> {
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new Error(body.detail || 'DB Proxy Error (' + resp.status + ')');
  }
  return resp.json();
}

interface FilterCondition {
  column: string;
  op: 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'like' | 'ilike' | 'in' | 'is_null' | 'is_not_null';
  value?: any;
}

interface OrderByOption {
  column: string;
  direction: 'asc' | 'desc';
}

interface QueryOptions {
  filters?: FilterCondition[];
  order_by?: OrderByOption[];
  search?: string;
  search_columns?: string[];
  select?: string[];
  limit?: number;
  offset?: number;
}

export async function query(table: string, options?: { limit?: number; offset?: number }) {
  const appId = (window as any).__APP_ID__ || '';
  const isExternal = !!(window as any).__IS_EXTERNAL__;
  const proxyBase = isExternal ? '/ext/proxy/' : '/proxy/' + appId + '/';
  
  const params = new URLSearchParams();
  if (options?.limit) params.set('limit', String(options.limit));
  if (options?.offset) params.set('offset', String(options.offset));
  const qs = params.toString() ? '?' + params.toString() : '';
  
  const resp = await fetch(API_BASE + proxyBase + table + qs, {
    headers: _getHeaders(),
    credentials: 'include',
  });
  return _handleResponse(resp);
}

export async function queryAdvanced(table: string, payload: QueryOptions) {
  const appId = (window as any).__APP_ID__ || '';
  const isExternal = !!(window as any).__IS_EXTERNAL__;
  const proxyBase = isExternal ? '/ext/proxy/' : '/proxy/' + appId + '/';
  
  const resp = await fetch(API_BASE + proxyBase + table + '/query', {
    method: 'POST',
    headers: _getHeaders(),
    credentials: 'include',
    body: JSON.stringify(payload),
  });
  return _handleResponse(resp);
}

export async function insert(table: string, data: Record<string, any>) {
  const appId = (window as any).__APP_ID__ || '';
  const isExternal = !!(window as any).__IS_EXTERNAL__;
  const proxyBase = isExternal ? '/ext/proxy/' : '/proxy/' + appId + '/';
  
  const resp = await fetch(API_BASE + proxyBase + table, {
    method: 'POST',
    headers: _getHeaders(),
    credentials: 'include',
    body: JSON.stringify(data),
  });
  return _handleResponse(resp);
}

export async function update(table: string, id: string, data: Record<string, any>) {
  const appId = (window as any).__APP_ID__ || '';
  const isExternal = !!(window as any).__IS_EXTERNAL__;
  const proxyBase = isExternal ? '/ext/proxy/' : '/proxy/' + appId + '/';
  
  const resp = await fetch(API_BASE + proxyBase + table + '/' + id, {
    method: 'PATCH',
    headers: _getHeaders(),
    credentials: 'include',
    body: JSON.stringify(data),
  });
  return _handleResponse(resp);
}

export async function remove(table: string, id: string) {
  const appId = (window as any).__APP_ID__ || '';
  const isExternal = !!(window as any).__IS_EXTERNAL__;
  const proxyBase = isExternal ? '/ext/proxy/' : '/proxy/' + appId + '/';
  
  const resp = await fetch(API_BASE + proxyBase + table + '/' + id, {
    method: 'DELETE',
    headers: _getHeaders(),
    credentials: 'include',
  });
  return _handleResponse(resp);
}
