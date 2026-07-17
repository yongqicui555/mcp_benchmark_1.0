// CommonJS DI wiring: requires the SDK and constructs the client but never
// calls the model — must NOT be reported as an AI surface.
const OpenAI = require('openai');

function buildClient(config) {
  return new OpenAI({ apiKey: config.apiKey });
}

module.exports = { buildClient };
