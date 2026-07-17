"use strict";

const { execSync } = require("node:child_process");

function git(repoPath, args) {
  return execSync(`git -C "${repoPath}" ${args}`, {
    encoding: "utf8",
    maxBuffer: 10 * 1024 * 1024,
  }).trim();
}

function getLatestTag(repoPath) {
  try {
    return git(repoPath, "describe --tags --abbrev=0 HEAD");
  } catch {
    // No tags — try first commit
    try {
      return git(repoPath, "rev-list --max-parents=0 HEAD").split("\n")[0];
    } catch {
      return null;
    }
  }
}

function getTags(repoPath) {
  try {
    const raw = git(
      repoPath,
      'tag --sort=-version:refname --format="%(refname:short)|%(creatordate:short)"'
    );
    return raw.split("\n").filter(Boolean).map((line) => {
      const [name, date] = line.replace(/"/g, "").split("|");
      return { name, date };
    });
  } catch {
    return [];
  }
}

function getGitLog(repoPath, fromRef, toRef, maxCommits) {
  const SEP = "---COMMIT_SEP---";
  const FIELD = "---FIELD---";

  const format = ["%H", "%h", "%an", "%ae", "%ad", "%s", "%b"].join(FIELD);

  const range = `${fromRef}..${toRef}`;

  let raw;
  try {
    raw = git(
      repoPath,
      `log ${range} --format="${SEP}${format}" --date=short -n ${maxCommits}`
    );
  } catch {
    return [];
  }

  if (!raw) return [];

  return raw
    .split(SEP)
    .filter(Boolean)
    .map((block) => {
      const fields = block.trim().split(FIELD);
      if (fields.length < 6) return null;

      const subject = fields[5].split("\n")[0].trim();
      const parsed = parseConventionalCommit(subject);

      return {
        hash: fields[0],
        hashShort: fields[1],
        author: fields[2],
        email: fields[3],
        date: fields[4],
        subject,
        body: fields[6] || "",
        type: parsed.type,
        scope: parsed.scope,
        breaking: parsed.breaking,
        description: parsed.description,
      };
    })
    .filter(Boolean);
}

function parseConventionalCommit(subject) {
  // Match: type(scope)!: description
  const match = subject.match(
    /^(\w+)(?:\(([^)]+)\))?(!)?\s*:\s*(.+)$/
  );

  if (match) {
    return {
      type: match[1].toLowerCase(),
      scope: match[2] || null,
      breaking: !!match[3] || /BREAKING[ -]CHANGE/i.test(subject),
      description: match[4],
    };
  }

  // Fallback: detect type from keywords (prefix first, then anywhere)
  const lower = subject.toLowerCase();
  let type = "other";

  // Prefix patterns (highest confidence)
  if (/^fix|^bug|^patch|^hotfix|^resolve/i.test(lower)) type = "fix";
  else if (/^feat|^add|^new|^implement|^introduce|^create|^support/i.test(lower)) type = "feat";
  else if (/^docs?|^readme|^update readme|^update docs/i.test(lower)) type = "docs";
  else if (/^refactor|^clean|^restructure|^simplify|^extract|^move|^rename|^reorganize/i.test(lower)) type = "refactor";
  else if (/^test|^spec|^add test|^update test/i.test(lower)) type = "test";
  else if (/^chore|^ci|^deps|^bump|^release|^merge|^initial commit|^update dep|^upgrade/i.test(lower)) type = "chore";
  else if (/^style|^format|^lint|^prettier|^eslint/i.test(lower)) type = "style";
  else if (/^perf|^optim|^speed|^cache|^faster/i.test(lower)) type = "perf";
  else if (/^remove|^delete|^drop|^deprecate/i.test(lower)) type = "refactor";
  else if (/^update|^change|^modify|^improve|^enhance|^adjust/i.test(lower)) type = "feat";
  // Keyword-anywhere patterns (lower confidence, for commits that don't match prefix)
  else if (/\bfix(es|ed)?\b|\bbug\b|\bregress|\bcrash|\berror\b|\bissue\b/.test(lower)) type = "fix";
  else if (/\bdocument|\breadme|\btypedoc|\bjsdoc|\bchangelog/.test(lower)) type = "docs";
  else if (/\btest(s|ing)?\b|\bspec\b|\bcoverage/.test(lower)) type = "test";
  else if (/\bci\b|\bpipeline|\bgithub.actions|\bworkflow|\bdocker/.test(lower)) type = "ci";
  else if (/\brefactor|\bclean.?up|\bdead.?code|\bunused/.test(lower)) type = "refactor";
  else if (/\bperformance|\blatency|\bthroughput|\bmemory.?leak/.test(lower)) type = "perf";

  return {
    type,
    scope: null,
    breaking: /BREAKING[ -]CHANGE/i.test(subject),
    description: subject,
  };
}

function getRemoteUrl(repoPath) {
  try {
    let url = git(repoPath, "config --get remote.origin.url").replace(/\.git$/, "");
    if (url.startsWith("git@")) {
      url = url.replace(/^git@([^:]+):/, "https://$1/");
    }
    return url;
  } catch {
    return null;
  }
}

module.exports = { getGitLog, getLatestTag, getTags, getRemoteUrl, parseConventionalCommit };
