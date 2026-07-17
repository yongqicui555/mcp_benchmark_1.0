import OpenAI from 'openai';
import { z } from 'zod';

const client = new OpenAI();

// Schema validates the shape and bounds of model output before it touches any side-effect
const bookingSchema = z.object({
  booking: z.object({
    eventId: z.string().uuid(),
    seats: z.number().int().min(1).max(10),
  }),
  amount: z.number().positive().max(100_000),
  confidence: z.number().min(0).max(1),
});

export async function autoBook(req) {
  try {
    const completion = await client.chat.completions.create({
      model: 'gpt-4',
      messages: req.messages,
      logprobs: true,
    });

    // Confidence: use log-probability to gate low-certainty outputs
    const topLogprob = completion.choices[0].logprobs?.content?.[0]?.logprob ?? -Infinity;
    const confidence = Math.exp(topLogprob);
    if (confidence < 0.85) {
      return { status: 'low_confidence', message: 'Could not determine booking details with sufficient certainty. Please complete manually.' };
    }

    // Validation: parse and validate output against schema before use
    const parsed = bookingSchema.safeParse(JSON.parse(completion.choices[0].message.content));
    if (!parsed.success) {
      return { status: 'invalid_output', errors: parsed.error.issues };
    }

    const { booking, amount } = parsed.data;

    // Human-in-the-loop: require explicit confirmation before any payment or db write
    const pending = await prisma.bookingDraft.create({ data: { ...booking, amount, status: 'PENDING', requireApproval: true } });
    await notifyUserForConfirmation(pending.id);

    return { status: 'awaiting_confirmation', draftId: pending.id };
  } catch (error) {
    // Error isolation: AI failures never propagate to the caller unhandled
    logger.error('autoBook failed', error);
    return { status: 'error', message: 'Booking could not be processed. Please try again.' };
  }
}
