// CommonJS: destructured require of a provider SDK.
const { Anthropic } = require('@anthropic-ai/sdk');

const anthropic = new Anthropic();

async function summarize(text) {
  const msg = await anthropic.messages.create({
    model: 'claude-sonnet-4-5',
    max_tokens: 512,
    messages: [{ role: 'user', content: text }],
  });
  return msg.content[0].text;
}

module.exports = { summarize };
