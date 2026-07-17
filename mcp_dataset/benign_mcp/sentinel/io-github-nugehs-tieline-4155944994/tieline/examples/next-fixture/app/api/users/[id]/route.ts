export async function GET(req: Request, { params }: { params: { id: string } }) {
  return Response.json({ id: params.id });
}

export const DELETE = async () => new Response(null, { status: 204 });
