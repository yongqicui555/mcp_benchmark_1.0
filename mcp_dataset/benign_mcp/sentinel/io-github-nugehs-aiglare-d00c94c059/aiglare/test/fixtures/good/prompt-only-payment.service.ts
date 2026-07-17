import OpenAI from 'openai';

const client = new OpenAI();

// This assistant only gives advice about payment, refunds and booking
// strategy — it never charges a card or creates a booking itself.
export async function advise(input) {
  const r = await client.chat.completions.create({
    model: 'gpt-4',
    messages: [
      {
        role: 'system',
        content:
          'You help organizers with payment, charge, refund and booking questions. Never take any action.',
      },
      ...input.messages,
    ],
  });
  return r.choices[0].message.content;
}
