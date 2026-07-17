#!/usr/bin/env bash
# Sync the canonical packages/mcp/ tree from the AR monorepo into this mirror.
#
# Usage (run from monorepo root):
#   bash public-mirrors/agentresources-mcp/scripts/sync-from-source.sh
#
# Idempotent. Safe to re-run. Drops anything in the mirror that no longer
# exists in the canonical source so deletes propagate.
#
# We mirror src/, bin/, package.json, tsconfig.json, tsup.config.ts,
# vitest.config.ts, and CHANGELOG.md. We do NOT mirror dist/ — consumers
# should fetch the npm tarball, not the build artefact.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIRROR_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${MIRROR_DIR}/../.." && pwd)"

CANONICAL="${REPO_ROOT}/packages/mcp"

if [[ ! -d "${CANONICAL}" ]]; then
  echo "FATAL: canonical source ${CANONICAL} not found." >&2
  exit 1
fi

echo "[sync] canonical: ${CANONICAL}"
echo "[sync] mirror:    ${MIRROR_DIR}"

# Mirror the source tree.
rsync -av --delete \
  --exclude="node_modules/" \
  --exclude="dist/" \
  --exclude=".turbo/" \
  --exclude="coverage/" \
  --exclude=".DS_Store" \
  "${CANONICAL}/src/" "${MIRROR_DIR}/src/"

if [[ -d "${CANONICAL}/bin" ]]; then
  rsync -av --delete \
    --exclude=".DS_Store" \
    "${CANONICAL}/bin/" "${MIRROR_DIR}/bin/"
fi

# Copy individual files when present.
for f in package.json tsconfig.json tsup.config.ts vitest.config.ts CHANGELOG.md; do
  if [[ -f "${CANONICAL}/${f}" ]]; then
    cp "${CANONICAL}/${f}" "${MIRROR_DIR}/${f}"
  fi
done

# Strip workspace:* references from the mirrored package.json so installs work
# outside the monorepo. Replace with the published versions of the AR packages.
node "${SCRIPT_DIR}/normalise-package-json.mjs" "${MIRROR_DIR}/package.json"

echo "[sync] done. Review with: git -C \"${MIRROR_DIR}\" status"
