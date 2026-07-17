// CommonJS Bedrock connector (anything-llm shape). The package name contains
// the "bedrock-runtime" host fragment, so this fixture guards that the match
// comes from the PACKAGE registry, not from host-substring matching the
// require string.
const {
  BedrockRuntimeClient,
  ConverseStreamCommand,
} = require('@aws-sdk/client-bedrock-runtime');

const client = new BedrockRuntimeClient({ region: process.env.AWS_REGION });

async function getChatCompletion(messages) {
  const response = await client.send(new ConverseStreamCommand({ messages }));
  return stream(response);
}

function stream(response) {
  return response;
}

module.exports = { getChatCompletion };
