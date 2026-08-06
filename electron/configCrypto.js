/**
 * Encrypt/decrypt sensitive config fields with Electron safeStorage (OS keychain / DPAPI).
 * Values are stored as: zbuild-enc:v1:<base64>
 * When encryption is unavailable, plaintext is kept (dev / unsupported OS).
 */

'use strict';

const ENC_PREFIX = 'zbuild-enc:v1:';

function getSafeStorage() {
  try {
    // Lazy require so unit tests can inject a mock without loading electron
    const electron = require('electron');
    return electron.safeStorage || null;
  } catch {
    return null;
  }
}

function isEncrypted(value) {
  return typeof value === 'string' && value.startsWith(ENC_PREFIX);
}

function encryptSecret(plain, safeStorage = getSafeStorage()) {
  if (plain == null || plain === '') return '';
  const text = String(plain);
  if (isEncrypted(text)) return text;
  if (!safeStorage || typeof safeStorage.isEncryptionAvailable !== 'function') return text;
  if (!safeStorage.isEncryptionAvailable()) return text;
  try {
    const buf = safeStorage.encryptString(text);
    return ENC_PREFIX + Buffer.from(buf).toString('base64');
  } catch {
    return text;
  }
}

function decryptSecret(value, safeStorage = getSafeStorage()) {
  if (value == null || value === '') return '';
  const text = String(value);
  if (!isEncrypted(text)) return text;
  if (!safeStorage || typeof safeStorage.decryptString !== 'function') return '';
  if (typeof safeStorage.isEncryptionAvailable === 'function' && !safeStorage.isEncryptionAvailable()) {
    return '';
  }
  try {
    const b64 = text.slice(ENC_PREFIX.length);
    return safeStorage.decryptString(Buffer.from(b64, 'base64'));
  } catch {
    return '';
  }
}

/** Encrypt password fields on a Python-shaped config object (mutates a shallow copy). */
function encryptConfigSecrets(config, safeStorage = getSafeStorage()) {
  if (!config || typeof config !== 'object') return config;
  const out = { ...config };
  if (out.svn_credentials && typeof out.svn_credentials === 'object') {
    out.svn_credentials = { ...out.svn_credentials };
    if (out.svn_credentials.password != null) {
      out.svn_credentials.password = encryptSecret(out.svn_credentials.password, safeStorage);
    }
  }
  if (out.server && typeof out.server === 'object') {
    out.server = { ...out.server };
    if (out.server.password != null) {
      out.server.password = encryptSecret(out.server.password, safeStorage);
    }
  }
  return out;
}

/** Decrypt password fields on a Python-shaped config object. */
function decryptConfigSecrets(config, safeStorage = getSafeStorage()) {
  if (!config || typeof config !== 'object') return config;
  const out = { ...config };
  if (out.svn_credentials && typeof out.svn_credentials === 'object') {
    out.svn_credentials = { ...out.svn_credentials };
    if (out.svn_credentials.password != null) {
      out.svn_credentials.password = decryptSecret(out.svn_credentials.password, safeStorage);
    }
  }
  if (out.server && typeof out.server === 'object') {
    out.server = { ...out.server };
    if (out.server.password != null) {
      out.server.password = decryptSecret(out.server.password, safeStorage);
    }
  }
  return out;
}

module.exports = {
  ENC_PREFIX,
  isEncrypted,
  encryptSecret,
  decryptSecret,
  encryptConfigSecrets,
  decryptConfigSecrets,
};
