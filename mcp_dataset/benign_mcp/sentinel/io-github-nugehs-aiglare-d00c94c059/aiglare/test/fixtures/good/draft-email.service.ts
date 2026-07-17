import Anthropic from '@anthropic-ai/sdk';
export async function draftEmail(input) {
  try {
    const a = new Anthropic();
    const msg = await a.messages.create({ model: 'claude-3', max_tokens: 800, messages: input.messages });
    // does NOT send — stores a draft pending human review/approval
    return { status: 'pending_review', draft: msg.content[0].text, requiresApproval: true };
  } catch {
    return { status: 'failed', draft: null };
  }
}
