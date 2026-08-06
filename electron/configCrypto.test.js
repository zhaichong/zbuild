const test = require('node:test');
const assert = require('node:assert/strict');
const {
  ENC_PREFIX,
  isEncrypted,
  encryptSecret,
  decryptSecret,
  encryptConfigSecrets,
  decryptConfigSecrets,
} = require('./configCrypto');

function mockSafeStorage() {
  const map = new Map();
  let n = 0;
  return {
    isEncryptionAvailable: () => true,
    encryptString(plain) {
      const id = `tok${n++}`;
      map.set(id, plain);
      return Buffer.from(id, 'utf8');
    },
    decryptString(buf) {
      const id = Buffer.from(buf).toString('utf8');
      if (!map.has(id)) throw new Error('bad token');
      return map.get(id);
    },
  };
}

test('encrypt/decrypt round-trip with mock safeStorage', () => {
  const ss = mockSafeStorage();
  const enc = encryptSecret('super-secret', ss);
  assert.equal(isEncrypted(enc), true);
  assert.ok(enc.startsWith(ENC_PREFIX));
  assert.equal(decryptSecret(enc, ss), 'super-secret');
});

test('encrypt is no-op when encryption unavailable', () => {
  const ss = { isEncryptionAvailable: () => false };
  assert.equal(encryptSecret('plain', ss), 'plain');
});

test('encryptConfigSecrets only touches password fields', () => {
  const ss = mockSafeStorage();
  const out = encryptConfigSecrets(
    {
      hospital_name: 'h',
      svn_credentials: { username: 'u', password: 'p1' },
      server: { host: '10.0.0.1', password: 'p2' },
    },
    ss,
  );
  assert.equal(out.hospital_name, 'h');
  assert.equal(out.svn_credentials.username, 'u');
  assert.equal(isEncrypted(out.svn_credentials.password), true);
  assert.equal(isEncrypted(out.server.password), true);
  const dec = decryptConfigSecrets(out, ss);
  assert.equal(dec.svn_credentials.password, 'p1');
  assert.equal(dec.server.password, 'p2');
});
