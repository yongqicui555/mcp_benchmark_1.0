// CommonJS: member access on the require() result.
const OpenAI = require('openai').OpenAI;

const client = new OpenAI();

async function classifyTicket(ticket) {
  const out = await client.chat.completions.create({
    model: 'gpt-4o-mini',
    messages: [{ role: 'user', content: ticket }],
  });
  return out.choices[0].message.content;
}

module.exports = { classifyTicket };
