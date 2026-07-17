// CommonJS service: plain `require` of a provider SDK (LibreChat api/ shape).
const OpenAI = require('openai');

const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

async function replyToCustomer(message) {
  try {
    const out = await client.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [{ role: 'user', content: message }],
    });
    return out.choices[0].message.content;
  } catch (err) {
    return null;
  }
}

module.exports = { replyToCustomer };
