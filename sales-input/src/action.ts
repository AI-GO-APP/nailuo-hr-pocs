/* @ai-go-sdk */
/**
 * Server-Side Action SDK
 */

const API_BASE = (window as any).__API_BASE__ || '/api/v1';

function _getHeaders(): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  const token = (window as any).__APP_TOKEN__ || '';
  if (token) headers['Authorization'] = 'Bearer ' + token;
  return headers;
}

export async function runAction(
  actionName: string,
  params: Record<string, any> = {}
): Promise<any> {
  const appId = (window as any).__APP_ID__ || '';
  const isExternal = !!(window as any).__IS_EXTERNAL__;
  const actionUrl = isExternal
    ? API_BASE + '/ext/actions/run/' + actionName
    : API_BASE + '/actions/apps/' + appId + '/run/' + actionName;

  console.log('[Action] Calling:', actionUrl, 'params:', params);

  const resp = await fetch(actionUrl, {
    method: 'POST',
    headers: _getHeaders(),
    credentials: 'include',
    body: JSON.stringify({ params }),
  });

  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    console.error('[Action] Error:', resp.status, body);
    throw new Error(body.detail || 'Action Error (' + resp.status + ')');
  }

  const result = await resp.json();
  console.log('[Action] Result:', result);

  if (result && result.status === 'error') {
    throw new Error(result.error || result.message || 'Action Error');
  }

  return {
    data: result.result || result.data || result,
    file: result.file || undefined,
  };
}

export function downloadFile(file: any) {
  if (!file || !file.content_base64) return;
  const byteChars = atob(file.content_base64);
  const byteNumbers = new Array(byteChars.length);
  for (let i = 0; i < byteChars.length; i++) {
    byteNumbers[i] = byteChars.charCodeAt(i);
  }
  const byteArray = new Uint8Array(byteNumbers);
  const blob = new Blob([byteArray], { type: file.mime_type || 'application/octet-stream' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = file.filename || 'download';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 5000);
}
