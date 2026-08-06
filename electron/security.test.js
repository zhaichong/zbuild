const test = require('node:test');
const assert = require('node:assert/strict');
const {
  isPrivateOrLocalHost,
  assertSafeMockUrl,
  assertDbHostAllowed,
  assertSafeInsertSql,
} = require('./security');

test('isPrivateOrLocalHost detects common private ranges', () => {
  assert.equal(isPrivateOrLocalHost('127.0.0.1'), true);
  assert.equal(isPrivateOrLocalHost('192.168.1.1'), true);
  assert.equal(isPrivateOrLocalHost('10.0.0.5'), true);
  assert.equal(isPrivateOrLocalHost('172.16.0.1'), true);
  assert.equal(isPrivateOrLocalHost('169.254.169.254'), true);
  assert.equal(isPrivateOrLocalHost('8.8.8.8'), false);
  assert.equal(isPrivateOrLocalHost('example.com'), false);
});

test('assertSafeMockUrl allows hospital intranet http URLs', () => {
  const u = assertSafeMockUrl('http://192.168.78.63/api/orgs');
  assert.equal(u.hostname, '192.168.78.63');
});

test('assertSafeMockUrl blocks non-http schemes and metadata', () => {
  assert.throws(() => assertSafeMockUrl('file:///c:/windows/system32'), /不允许的协议/);
  assert.throws(() => assertSafeMockUrl('http://169.254.169.254/latest'), /云元数据/);
  assert.throws(() => assertSafeMockUrl('http://user:pass@192.168.1.1/'), /用户名\/密码/);
});

test('assertSafeMockUrl private-only mode blocks public hosts', () => {
  assert.throws(
    () => assertSafeMockUrl('https://example.com/api', { ZBUILD_HTTP_PRIVATE_ONLY: '1' }),
    /严格模式/,
  );
});

test('assertDbHostAllowed defaults to private hosts', () => {
  assert.equal(assertDbHostAllowed('192.168.1.10'), '192.168.1.10');
  assert.throws(() => assertDbHostAllowed('8.8.8.8'), /仅允许内网/);
  assert.equal(assertDbHostAllowed('db.example.com', { ZBUILD_DB_HOST_ALLOWLIST: 'db.example.com' }), 'db.example.com');
});

test('assertSafeInsertSql only allows INSERT', () => {
  assert.equal(
    assertSafeInsertSql("INSERT INTO t (a) VALUES ('1')"),
    "INSERT INTO t (a) VALUES ('1')",
  );
  assert.equal(
    assertSafeInsertSql("INSERT IGNORE INTO t (a) VALUES ('1');"),
    "INSERT IGNORE INTO t (a) VALUES ('1')",
  );
  assert.equal(assertSafeInsertSql('-- comment'), null);
  assert.throws(() => assertSafeInsertSql('DROP TABLE users'), /仅允许 INSERT/);
  assert.throws(() => assertSafeInsertSql('DELETE FROM users'), /仅允许 INSERT/);
  assert.throws(
    () => assertSafeInsertSql("INSERT INTO t (a) VALUES ('1'); DROP TABLE t"),
    /多个 SQL/,
  );
});
