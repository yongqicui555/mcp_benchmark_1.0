// Dynamic import() of a provider in an otherwise CommonJS file.
async function loadClient() {
  const { OpenAI } = await import('openai');
  return new OpenAI();
}

async function answer(question) {
  const client = await loadClient();
  const out = await client.chat.completions.create({
    model: 'gpt-4o-mini',
    messages: [{ role: 'user', content: question }],
  });
  return out.choices[0].message.content;
}

module.exports = { answer };
