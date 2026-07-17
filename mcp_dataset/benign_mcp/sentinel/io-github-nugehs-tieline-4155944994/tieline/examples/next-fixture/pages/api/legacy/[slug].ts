import type { NextApiRequest, NextApiResponse } from 'next';

// Pages-router API route: one handler serves any method.
export default function handler(req: NextApiRequest, res: NextApiResponse) {
  res.status(200).json({ slug: req.query.slug });
}
