// Programmatic core: the adapter registries plus the check/doctor pipelines,
// returning structured results with no I/O. Both the CLI (src/cli.mjs) and the
// MCP server (src/mcp.mjs) build on this — keep it free of console/stdout writes.
import { extractRtkQuery } from './adapters/rtk-query.mjs';
import { extractNestjs } from './adapters/nestjs.mjs';
import { extractOpenapi } from './adapters/openapi.mjs';
import { extractExpress } from './adapters/express.mjs';
import { extractFastify } from './adapters/fastify.mjs';
import { extractNext } from './adapters/next.mjs';
import { extractFastapi } from './adapters/fastapi.mjs';
import { extractFlask } from './adapters/flask.mjs';
import { extractSpring } from './adapters/spring.mjs';
import { extractAxiosFetch } from './adapters/axios-fetch.mjs';
import { extractAngularHttp } from './adapters/angular-http.mjs';
import { match } from './match.mjs';
import { doctor } from './doctor.mjs';

export const CLIENT_ADAPTERS = {
  'rtk-query': extractRtkQuery,
  'axios-fetch': extractAxiosFetch,
  'angular-http': extractAngularHttp,
};

export const SERVER_ADAPTERS = {
  nestjs: extractNestjs,
  openapi: extractOpenapi,
  express: extractExpress,
  fastify: extractFastify,
  next: extractNext,
  fastapi: extractFastapi,
  flask: extractFlask,
  spring: extractSpring,
};

/** Run a FE↔BE contract check and return the raw match result. */
export async function runCheck(cfg) {
  const clientAdapter = CLIENT_ADAPTERS[cfg.client.adapter];
  const serverAdapter = SERVER_ADAPTERS[cfg.server.adapter];
  if (!clientAdapter) throw new Error(`Unknown client adapter: ${cfg.client.adapter}`);
  if (!serverAdapter) throw new Error(`Unknown server adapter: ${cfg.server.adapter}`);

  const endpoints = await clientAdapter(cfg.client);
  const routes = await serverAdapter(cfg.server);

  return match(endpoints, routes, {
    basePath: cfg.client.basePath,
    ignore: cfg.ignore,
  });
}

/** Diff native-parsed code routes against the OpenAPI spec; return the doctor result. */
export async function runDoctorCheck(cfg) {
  const codeAdapter = SERVER_ADAPTERS[cfg.server.adapter];
  if (!codeAdapter) throw new Error(`Unknown server adapter: ${cfg.server.adapter}`);
  if (cfg.server.adapter === 'openapi') {
    throw new Error("`doctor` needs a native server adapter (e.g. nestjs) as the code source, plus server.spec for the doc.");
  }
  if (!cfg.server.spec) {
    throw new Error('`doctor` needs `server.spec` (file path or url to the OpenAPI doc) in your config.');
  }

  const codeRoutes = await codeAdapter(cfg.server);
  const specRoutes = await extractOpenapi({
    spec: cfg.server.spec,
    stripPrefix: cfg.server.globalPrefix,
    repoRoot: cfg.server.repoRoot,
  });

  return doctor(codeRoutes, specRoutes, {
    basePath: cfg.server.globalPrefix,
    ignore: cfg.ignore,
  });
}
