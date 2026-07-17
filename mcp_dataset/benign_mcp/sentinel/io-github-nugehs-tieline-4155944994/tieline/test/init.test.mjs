import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

import { detect, runInit } from '../src/init.mjs';
import { withTempRepo } from './helpers.mjs';

test('detect — separate web + api repos under cwd', () => {
  withTempRepo(
    {
      'web/package.json': JSON.stringify({ dependencies: { '@reduxjs/toolkit': '^2' } }),
      'web/src/redux/apis/.keep': '',
      'api/package.json': JSON.stringify({ dependencies: { '@nestjs/core': '^10' } }),
      'api/src/.keep': '',
    },
    (dir) => {
      const { client, server } = detect(dir);
      assert.equal(client.adapter, 'rtk-query');
      assert.equal(path.basename(client.dir), 'web');
      assert.equal(server.adapter, 'nestjs');
      assert.equal(path.basename(server.dir), 'api');
    },
  );
});

test('detect — express + axios + angular + fastify + next', () => {
  const cases = [
    [{ express: '^4' }, 'server', 'express'],
    [{ fastify: '^4' }, 'server', 'fastify'],
    [{ next: '^14' }, 'server', 'next'],
    [{ axios: '^1' }, 'client', 'axios-fetch'],
    [{ '@tanstack/react-query': '^5' }, 'client', 'axios-fetch'],
    [{ '@angular/core': '^17' }, 'client', 'angular-http'],
  ];
  for (const [deps, side, adapter] of cases) {
    withTempRepo({ 'repo/package.json': JSON.stringify({ dependencies: deps }) }, (dir) => {
      const got = detect(dir)[side];
      assert.ok(got, `expected a ${side} match for ${Object.keys(deps)[0]}`);
      assert.equal(got.adapter, adapter);
    });
  }
});

test('detect — python (fastapi/flask) and spring', () => {
  withTempRepo({ 'requirements.txt': 'fastapi==0.110\nuvicorn' }, (dir) => {
    assert.equal(detect(dir).server.adapter, 'fastapi');
  });
  withTempRepo({ 'requirements.txt': 'Flask==3.0' }, (dir) => {
    assert.equal(detect(dir).server.adapter, 'flask');
  });
  withTempRepo({ 'pom.xml': '<project><groupId>org.springframework.boot</groupId></project>' }, (dir) => {
    assert.equal(detect(dir).server.adapter, 'spring');
  });
});

test('detect — openapi doc is a fallback server when no native framework', () => {
  withTempRepo({ 'openapi.json': '{}' }, (dir) => {
    const { server } = detect(dir);
    assert.equal(server.adapter, 'openapi');
    assert.equal(server.spec, 'openapi.json');
  });
  // A native framework wins over a stray spec file.
  withTempRepo(
    { 'package.json': JSON.stringify({ dependencies: { express: '^4' } }), 'openapi.json': '{}' },
    (dir) => assert.equal(detect(dir).server.adapter, 'express'),
  );
});

test('detect — dir-name bias picks the right side when deps are ambiguous', () => {
  // Both repos ship express; the one named "api" should be the server.
  withTempRepo(
    {
      'api/package.json': JSON.stringify({ dependencies: { express: '^4' } }),
      'web/package.json': JSON.stringify({ dependencies: { express: '^4', '@reduxjs/toolkit': '^2' } }),
    },
    (dir) => {
      const { client, server } = detect(dir);
      assert.equal(path.basename(server.dir), 'api');
      assert.equal(path.basename(client.dir), 'web');
    },
  );
});

test('runInit — writes a valid, ready-to-run config and overwrites', () => {
  withTempRepo(
    {
      'web/package.json': JSON.stringify({ dependencies: { '@reduxjs/toolkit': '^2' } }),
      'web/src/redux/apis/.keep': '',
      'api/package.json': JSON.stringify({ dependencies: { '@nestjs/core': '^10' } }),
      'api/src/.keep': '',
      'tieline.config.json': '{"stale":true}',
    },
    (dir) => {
      const { config } = runInit({ cwd: dir });
      assert.equal(config.client.adapter, 'rtk-query');
      assert.deepEqual(config.client.roots, ['src/redux/apis']);
      assert.equal(config.server.adapter, 'nestjs');
      assert.deepEqual(config.failOn, ['drift']);

      // File on disk is valid JSON the loader can parse, and overwrote the stale one.
      const onDisk = JSON.parse(fs.readFileSync(path.join(dir, 'tieline.config.json'), 'utf8'));
      assert.equal(onDisk.stale, undefined);
      assert.equal(onDisk.server.repo, 'api');
    },
  );
});

test('runInit — placeholder config when nothing is detected', () => {
  // Run from a nested dir so its only sibling is the (empty) temp root — keeps
  // unrelated repos in the system tmpdir out of the sibling scan.
  withTempRepo({ 'solo/.keep': '' }, (dir) => {
    const { client, server, config } = runInit({ cwd: path.join(dir, 'solo') });
    assert.equal(client, null);
    assert.equal(server, null);
    // Still emits a usable template the user can edit.
    assert.equal(config.client.adapter, 'rtk-query');
    assert.equal(config.server.adapter, 'nestjs');
  });
});
