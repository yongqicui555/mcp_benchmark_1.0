import { apitierPost, type ApitierConfig } from "../client.js";

const DATA_FORMATS = ["csv", "json", "xml", "yaml"] as const;
type DataFormat = typeof DATA_FORMATS[number];

export const convertDataTool = {
  name: "convert_data",
  geography: ["GLOBAL"] as const,
  domain: "utilities" as const,
  description:
    "Convert data between formats: CSV, JSON, XML, and YAML. " +
    "Pass the source data as a string and specify input and output formats. " +
    "Use in ETL pipelines, data processing agents, API integration workflows, and document automation.",
  inputSchema: {
    type: "object",
    properties: {
      data: {
        type: "string",
        description: "The source data string to convert",
      },
      from: {
        type: "string",
        enum: DATA_FORMATS,
        description: "Source data format",
      },
      to: {
        type: "string",
        enum: DATA_FORMATS,
        description: "Target data format",
      },
    },
    required: ["data", "from", "to"],
  },
} as const;

export async function runConvertData(
  args: { data: string; from: DataFormat; to: DataFormat },
  config: ApitierConfig
): Promise<string> {
  if (args.from === args.to) {
    return args.data;
  }

  const result = await apitierPost(
    `${config.baseUrls.convertData}/convert/${args.from}/to/${args.to}`,
    args.data,
    config.keys.convertData!,
    false,
    true   // send raw string body, not JSON-encoded
  );

  if (typeof result === "string") return result;
  return JSON.stringify(result, null, 2);
}
