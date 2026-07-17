import OpenAI from 'openai';

const client = new OpenAI();

// Reads profile fields named like side-effects (isStripeConnected,
// bookingsAsVendor, email) but performs no payment/booking/email action.
export async function summarizeProfile(profile) {
  const ctx = {
    isStripeConnected: profile.isStripeConnected,
    bookingsAsVendor: profile.bookingsAsVendor?.length ?? 0,
    email: profile.email,
  };
  const r = await client.chat.completions.create({
    model: 'gpt-4',
    messages: [{ role: 'user', content: JSON.stringify(ctx) }],
  });
  return r.choices[0].message.content;
}
