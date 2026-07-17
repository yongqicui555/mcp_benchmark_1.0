import OpenAI from 'openai';
const client = new OpenAI();
export async function autoBook(req) {
  const completion = await client.chat.completions.create({ model: 'gpt-4', messages: req.messages });
  const choice = JSON.parse(completion.choices[0].message.content);
  // directly creates a booking + charges from model output, no confirmation
  await prisma.booking.create({ data: choice.booking });
  await stripe.charges.create({ amount: choice.amount, source: req.token });
  return choice;
}
