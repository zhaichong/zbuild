/**
 * Shared safety helpers for IPC surfaces (SSRF / SQL).
 * Kept free of Electron imports so unit tests can require this file directly.
 */

'use strict';

const MOCK_HTTP_ALLOWED_METHODS = new Set(['GET', 'POST']);
const DB_ALLOWED_DATABASES = new Set(['YHDB']);
const DB_MAX_STATEMENTS = 500;
const DB_MAX_SQL_LENGTH = 64 * 1024;
const DB_INSERT_RE = /^\s*INSERT\s+(IGNORE\s+)?INTO\s+/i;
const DB_FORBIDDEN_RE = /\b(DROP|ALTER|TRUNCATE|DELETE|UPDATE|GRANT|REVOKE|CREATE|REPLACE|CALL|EXEC|EXECUTE|LOAD\s+DATA|INTO\s+OUTFILE|INTO\s+DUMPFILE|INFORMATION_SCHEMA|SLEEP\s*\(|BENCHMARK\s*\()(?!\w)/i;

function isPrivateOrLocalHost(hostname) {
  const h = String(hostname || '').toLowerCase().replace(/^\[|\]$/g, '');
  if (h === 'localhost' || h === '::1' || h === '0.0.0.0') return true;
  const m = h.match(/^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/);
  if (m) {
    const a = [+m[1], +m[2], +m[3], +m[4]];
    if (a.some((n) => n > 255)) return true;
    if (a[0] === 10) return true;
    if (a[0] === 127) return true;
    if (a[0] === 0) return true;
    if (a[0] === 169 && a[1] === 254) return true;
    if (a[0] === 192 && a[1] === 168) return true;
    if (a[0] === 172 && a[1] >= 16 && a[1] <= 31) return true;
    if (a[0] === 100 && a[1] >= 64 && a[1] <= 127) return true;
    return false;
  }
  if (h.startsWith('fc') || h.startsWith('fd') || h.startsWith('fe80')) return true;
  return false;
}

function assertSafeMockUrl(fullUrl, env = process.env) {
  if (!fullUrl || typeof fullUrl !== 'string') {
    throw new Error('无效的请求 URL');
  }
  let parsed;
  try {
    parsed = new URL(fullUrl);
  } catch {
    throw new Error('无效的请求 URL');
  }
  if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
    throw new Error(`不允许的协议: ${parsed.protocol}（仅支持 http/https）`);
  }
  if (parsed.username || parsed.password) {
    throw new Error('URL 中不允许嵌入用户名/密码');
  }
  const host = parsed.hostname.replace(/^\[|\]$/g, '').toLowerCase();
  if (host === '169.254.169.254' || host === 'metadata.google.internal') {
    throw new Error('禁止访问云元数据地址');
  }
  const allowlist = String(env.ZBUILD_HTTP_ALLOWLIST || '')
    .split(',')
    .map((s) => s.trim().toLowerCase())
    .filter(Boolean);
  if (allowlist.length && !allowlist.includes(host) && !isPrivateOrLocalHost(host)) {
    throw new Error(`主机不在允许列表中: ${host}`);
  }
  if (env.ZBUILD_HTTP_PRIVATE_ONLY === '1' && !isPrivateOrLocalHost(host)) {
    throw new Error(`严格模式仅允许内网地址，拒绝: ${host}`);
  }
  return parsed;
}

function assertDbHostAllowed(host, env = process.env) {
  const h = String(host || '').trim().toLowerCase();
  if (!h) throw new Error('数据库主机不能为空');
  if (h === '169.254.169.254' || h === 'metadata.google.internal') {
    throw new Error('禁止访问云元数据地址');
  }
  if (!isPrivateOrLocalHost(h)) {
    const allow = String(env.ZBUILD_DB_HOST_ALLOWLIST || '')
      .split(',')
      .map((s) => s.trim().toLowerCase())
      .filter(Boolean);
    if (!allow.includes(h)) {
      throw new Error(
        `数据库主机仅允许内网/本机地址，当前: ${h}（如需公网主机请设置环境变量 ZBUILD_DB_HOST_ALLOWLIST）`,
      );
    }
  }
  return h;
}

function assertSafeInsertSql(sql) {
  const text = String(sql || '').trim();
  if (!text) return null;
  if (text.startsWith('--')) return null;
  if (text.length > DB_MAX_SQL_LENGTH) {
    throw new Error(`单条 SQL 过长（>${DB_MAX_SQL_LENGTH} 字节）`);
  }
  const stripped = text.replace(/;+\s*$/, '');
  if (stripped.includes(';')) {
    throw new Error('禁止在一条语句中包含多个 SQL（多语句注入）');
  }
  if (!DB_INSERT_RE.test(stripped)) {
    throw new Error('仅允许 INSERT / INSERT IGNORE 语句');
  }
  // Strip string literals to avoid false positives on user data
  const sqlWithoutStrings = stripped.replace(/'(?:[^'\\]|\\.)*'/g, '').replace(/"(?:[^"\\]|\\.)*"/g, '');
  if (DB_FORBIDDEN_RE.test(sqlWithoutStrings)) {
    throw new Error('SQL 包含不允许的关键字');
  }
  return stripped;
}

module.exports = {
  MOCK_HTTP_ALLOWED_METHODS,
  DB_ALLOWED_DATABASES,
  DB_MAX_STATEMENTS,
  DB_MAX_SQL_LENGTH,
  isPrivateOrLocalHost,
  assertSafeMockUrl,
  assertDbHostAllowed,
  assertSafeInsertSql,
};
