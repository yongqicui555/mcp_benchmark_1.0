import { promises as fs } from "node:fs";
import path from "node:path";

export type SkillsOptions = {
  action: "get";
  slug: string;
  /** Where to land the skill. Default: <cwd>/.ar/skills/<slug>/SKILL.md */
  dir?: string;
  registryUrl: string;
};

/**
 * `ar skills get <slug>` (alias `ar skill add <slug>`) — fetches the live
 * SKILL.md from the AR registry's stable raw URL and writes it into the
 * caller's runtime skill directory.
 *
 * Per D34.a: AR skill stubs MUST point at this command rather than copying
 * the SKILL.md body. That keeps every load fresh.
 */
export async function runSkills(opts: SkillsOptions): Promise<number> {
  const slug = opts.slug.trim();
  if (!/^[a-z0-9][a-z0-9-]*$/u.test(slug)) {
    process.stderr.write(`Invalid skill slug: ${slug}\n`);
    return 2;
  }

  const url = `${opts.registryUrl.replace(/\/$/u, "")}/${slug}/SKILL.md`;
  let res: Response;
  try {
    res = await fetch(url, { headers: { accept: "text/markdown" } });
  } catch (err) {
    process.stderr.write(
      `Failed to fetch ${url}: ${err instanceof Error ? err.message : String(err)}\n`,
    );
    return 1;
  }

  if (res.status === 404) {
    process.stderr.write(`Skill not found: ${slug} (no SKILL.md at ${url})\n`);
    return 1;
  }
  if (!res.ok) {
    process.stderr.write(`Registry error ${res.status} fetching ${url}\n`);
    return 1;
  }

  const md = await res.text();
  const targetDir = opts.dir ?? path.join(process.cwd(), ".ar", "skills", slug);
  await fs.mkdir(targetDir, { recursive: true });
  const targetFile = path.join(targetDir, "SKILL.md");
  await fs.writeFile(targetFile, md, "utf8");

  process.stdout.write(`Installed ${slug}\n  ${targetFile}\n  source: ${url}\n`);
  return 0;
}
