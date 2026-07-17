"use strict";

const { generateChangelog, suggestVersionBump } = require("./lib/generator");
const { getGitLog, getLatestTag, getTags, getRemoteUrl, parseConventionalCommit } = require("./lib/git");

module.exports = {
  generateChangelog,
  suggestVersionBump,
  getGitLog,
  getLatestTag,
  getTags,
  getRemoteUrl,
  parseConventionalCommit,
};
