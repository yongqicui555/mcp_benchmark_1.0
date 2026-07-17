import { readFile } from "node:fs/promises";

const samplePath = new URL("../examples/jobber-ops-sample.json", import.meta.url);
const sample = JSON.parse(await readFile(samplePath, "utf8"));

const staleEstimates = sample.estimates.filter(estimate => estimate.status === "sent" && estimate.sentDaysAgo >= 7);
const draftEstimates = sample.estimates.filter(estimate => estimate.status === "draft" && estimate.lastActivityDaysAgo >= 2);
const overdueInvoices = sample.invoices.filter(invoice => invoice.status === "overdue" && invoice.dueDaysAgo > 0);
const unscheduledJobs = sample.jobs.filter(job => job.status === "unscheduled");
const staleJobs = sample.jobs.filter(job => job.status === "active" && job.daysSinceLastVisit >= 14);

const openEstimateValue = staleEstimates.reduce((sum, estimate) => sum + estimate.value, 0);
const overdueInvoiceValue = overdueInvoices.reduce((sum, invoice) => sum + invoice.balance, 0);
const totalActionCount = staleEstimates.length + draftEstimates.length + overdueInvoices.length + unscheduledJobs.length + staleJobs.length;

const lines = [
  "# Sample Jobber Operations Pulse",
  "",
  "This is generated from fictional sample data. It shows the type of read-only summary OpsConduit can produce once a customer connects their own Jobber account.",
  "",
  "## Executive Summary",
  "",
  `- ${totalActionCount} operational items need attention.`,
  `- ${money(openEstimateValue)} in sent estimates are older than 7 days and likely worth follow-up.`,
  `- ${money(overdueInvoiceValue)} in invoices are overdue.`,
  `- ${unscheduledJobs.length + staleJobs.length} jobs are unscheduled or stale.`,
  "",
  "## Action Queue",
  ""
];

let actionNumber = 1;
for (const estimate of staleEstimates) {
  lines.push(`${actionNumber}. Follow up with ${estimate.client} on ${estimate.title}: ${money(estimate.value)} sent ${estimate.sentDaysAgo} days ago.`);
  actionNumber += 1;
}

for (const estimate of draftEstimates) {
  lines.push(`${actionNumber}. Finish or discard ${estimate.client} estimate draft for ${estimate.title}: last touched ${estimate.lastActivityDaysAgo} days ago.`);
  actionNumber += 1;
}

for (const invoice of overdueInvoices) {
  lines.push(`${actionNumber}. Collect from ${invoice.client} on ${invoice.title}: ${money(invoice.balance)} overdue by ${invoice.dueDaysAgo} days.`);
  actionNumber += 1;
}

for (const job of unscheduledJobs) {
  lines.push(`${actionNumber}. Schedule ${job.client} job for ${job.title}: job exists but has no upcoming visit.`);
  actionNumber += 1;
}

for (const job of staleJobs) {
  lines.push(`${actionNumber}. Check ${job.client} job for ${job.title}: active job has had no visit in ${job.daysSinceLastVisit} days.`);
  actionNumber += 1;
}

lines.push(
  "",
  "## Useful MCP Prompts After Install",
  "",
  "- Which sent estimates are older than 7 days and still open?",
  "- Which overdue invoices should I collect this week?",
  "- Which active jobs have no upcoming visit?",
  "- Which draft estimates have been sitting for more than 2 days?",
  "- Give me a short follow-up list ordered by likely revenue impact."
);

console.log(lines.join("\n"));

function money(value) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: sample.currency,
    maximumFractionDigits: 0
  }).format(value);
}
