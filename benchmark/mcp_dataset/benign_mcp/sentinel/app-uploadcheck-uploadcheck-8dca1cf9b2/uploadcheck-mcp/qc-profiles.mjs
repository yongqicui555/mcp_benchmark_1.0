export const NTO_LONG_FORM_CHECKS = [
  "canvas_fill",
  "loop_freeze",
  "repeat_fatigue",
  "speaker_visual_binding",
  "static_head_dominance",
  "literal_subject_match",
  "visual_narration_match",
  "first_three_seconds",
  "end_screen_tease",
  "rehook_cadence",
  "contact_sheet_evidence",
  "text_crop_jitter",
  "text_overlap",
  "thumbnail_text_readability",
  "hallucinated_plate_text",
  "clean_segment_source_scrub",
  "voiceover_music_balance",
  "dead_air",
  "text_contrast",
  "text_safe_area"
];

export const PROFILE_CHECKS = {
  nto_long_form: NTO_LONG_FORM_CHECKS,
  generic_creator_video: [
    "canvas_fill",
    "loop_freeze",
    "repeat_fatigue",
    "dead_air",
    "text_contrast",
    "text_overlap",
    "text_safe_area"
  ],
  shorts: [
    "canvas_fill",
    "shorts_format",
    "opening_footer_text_presence",
    "first_three_seconds",
    "end_screen_tease",
    "text_contrast",
    "text_safe_area",
    "text_crop_jitter",
    "text_overlap",
    "repeat_fatigue",
    "sentence_boundary",
    "dialogue_in_music_short",
    "voiceover_music_balance",
    "dead_air"
  ],
  audio: [
    "dead_air",
    "voiceover_music_balance",
    "spoken_leaks",
    "pronunciation_watchlist",
    "script_faithfulness",
    "sentence_boundary",
    "chunk_sidecar_failures"
  ],
  npo_podcast_or_audio: [
    "dead_air",
    "voiceover_music_balance",
    "spoken_leaks",
    "pronunciation_watchlist",
    "script_faithfulness",
    "sentence_boundary",
    "chunk_sidecar_failures"
  ],
  thumbnail: [
    "text_overlap",
    "thumbnail_text_readability"
  ]
};

export const PROFILE_IDS = [...Object.keys(PROFILE_CHECKS), "auto"];

export function normalizeProfileId(value) {
  const normalized = String(value || "").trim().toLowerCase().replaceAll("-", "_");
  if (!normalized) return null;
  if (normalized === "long_form" || normalized === "nto") return "nto_long_form";
  if (normalized === "short" || normalized === "youtube_short" || normalized === "reels" || normalized === "tiktok") return "shorts";
  if (normalized === "podcast" || normalized === "npo_audio") return "npo_podcast_or_audio";
  if (normalized === "generic_video" || normalized === "creator_video") return "generic_creator_video";
  if (PROFILE_IDS.includes(normalized)) return normalized;
  return null;
}

export function checksForProfile(profile, context = {}) {
  const normalized = normalizeProfileId(profile);
  if (!normalized) return null;
  const resolved = normalized === "auto" ? inferProfile(context) : normalized;
  const checks = PROFILE_CHECKS[resolved];
  return checks ? { profile: resolved, requestedProfile: normalized, checks: checks.join(",") } : null;
}

export function inferProfile(context = {}) {
  const mediaKind = String(context.mediaKind || context.media_kind || "").toLowerCase();
  if (mediaKind === "audio") return "audio";
  if (mediaKind === "image") return "thumbnail";
  const durationSeconds = Number(context.durationSeconds ?? context.duration_seconds ?? 0) || 0;
  const filename = String(context.filename || context.mediaFilename || context.media_filename || "").toLowerCase();
  if ((durationSeconds >= 45 && durationSeconds <= 75) || filename.includes("short") || filename.includes("reel") || filename.includes("tiktok")) {
    return "shorts";
  }
  return "generic_creator_video";
}

export function applyProfileToInput(input = {}) {
  const profile = input.profile || input.qc_profile || input.qcProfile;
  if (input.checks || !profile) return { ...input };
  const resolved = checksForProfile(profile, {
    mediaKind: input.media_kind || input.mediaKind,
    durationSeconds: input.duration_seconds || input.durationSeconds,
    filename: input.filename || input.media_filename || input.mediaFilename
  });
  if (!resolved) return { ...input };
  return {
    ...input,
    profile: resolved.profile,
    requested_profile: resolved.requestedProfile,
    checks: resolved.checks
  };
}
