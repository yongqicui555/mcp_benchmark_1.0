import { apitierPost, type ApitierConfig } from "../client.js";

const BARCODE_FORMATS = [
  "code128", "code128a", "code128b", "code128c",
  "ean13", "ean8", "ean5", "ean2",
  "upc", "code39", "itf14",
  "msi", "msi10", "msi11",
  "pharmacode", "codabar",
] as const;

type BarcodeFormat = typeof BARCODE_FORMATS[number];

export const generateBarcodeTool = {
  name: "generate_barcode",
  geography: ["GLOBAL"] as const,
  domain: "utilities" as const,
  description:
    "Generate a barcode image from text or numeric data. Returns a base64-encoded PNG image. " +
    "Supports all major barcode formats: Code128, EAN-13, EAN-8, UPC, Code39, ITF-14, and more. " +
    "Use for inventory management, product labelling, logistics, and retail automation agents.",
  inputSchema: {
    type: "object",
    properties: {
      text: {
        type: "string",
        description: "The data to encode in the barcode (e.g. '123456789012' for EAN-13)",
      },
      format: {
        type: "string",
        enum: BARCODE_FORMATS,
        description: "Barcode format. Defaults to 'code128' if not specified.",
      },
      width: {
        type: "number",
        description: "Bar width in pixels (default: 2)",
      },
      height: {
        type: "number",
        description: "Barcode height in pixels (default: 100)",
      },
      displayValue: {
        type: "boolean",
        description: "Whether to display the encoded text below the barcode (default: true)",
      },
      background: {
        type: "string",
        description: "Background colour as hex (default: '#ffffff')",
      },
      lineColor: {
        type: "string",
        description: "Bar colour as hex (default: '#000000')",
      },
    },
    required: ["text"],
  },
} as const;

export const generateQrCodeTool = {
  name: "generate_qrcode",
  geography: ["GLOBAL"] as const,
  domain: "utilities" as const,
  description:
    "Generate a QR code image from any text or URL. Returns a base64-encoded PNG image. " +
    "Supports custom colours, embedded logo, and title. " +
    "Use for marketing campaigns, payment links, product traceability, and contactless sharing agents.",
  inputSchema: {
    type: "object",
    properties: {
      text: {
        type: "string",
        description: "The content to encode — URL, plain text, vCard, WiFi config, etc.",
      },
      width: {
        type: "number",
        description: "Image width in pixels (default: 256)",
      },
      height: {
        type: "number",
        description: "Image height in pixels (default: 256)",
      },
      colorDark: {
        type: "string",
        description: "Dark module colour as hex (default: '#000000')",
      },
      colorLight: {
        type: "string",
        description: "Light module colour as hex (default: '#ffffff')",
      },
      logo: {
        type: "string",
        description: "URL of a logo image to embed in the centre of the QR code",
      },
      title: {
        type: "string",
        description: "Optional title text to display below the QR code",
      },
      correctLevel: {
        type: "number",
        enum: [1, 0, 3, 2],
        description: "Error correction level: 1=L(7%), 0=M(15%), 3=Q(25%), 2=H(30%). Use 3 or 2 when embedding a logo.",
      },
    },
    required: ["text"],
  },
} as const;

export async function runGenerateBarcode(
  args: {
    text: string;
    format?: BarcodeFormat;
    width?: number;
    height?: number;
    displayValue?: boolean;
    background?: string;
    lineColor?: string;
  },
  config: ApitierConfig
): Promise<string> {
  const format = args.format ?? "code128";

  const body = {
    text: args.text,
    file: "png",
    options: {
      displayValue: args.displayValue ?? true,
      width: args.width ?? 2,
      height: args.height ?? 100,
      background: args.background ?? "#ffffff",
      lineColor: args.lineColor ?? "#000000",
    },
  };

  const base64 = await apitierPost(
    `${config.baseUrls.barcode}/generate/${format}`,
    body,
    config.keys.barcode!,
    true
  );

  return JSON.stringify({
    format: "png",
    encoding: "base64",
    data: base64,
    note: "Decode this base64 string to get the PNG image bytes",
  });
}

export async function runGenerateQrCode(
  args: {
    text: string;
    width?: number;
    height?: number;
    colorDark?: string;
    colorLight?: string;
    logo?: string;
    title?: string;
    correctLevel?: number;
  },
  config: ApitierConfig
): Promise<string> {
  const body = {
    text: args.text,
    file: "png",
    options: {
      width: args.width ?? 256,
      height: args.height ?? 256,
      colorDark: args.colorDark ?? "#000000",
      colorLight: args.colorLight ?? "#ffffff",
      correctLevel: args.correctLevel ?? 3,
      ...(args.logo && { logo: args.logo, logoWidth: 80, logoHeight: 80 }),
      ...(args.title && { title: args.title }),
    },
  };

  const base64 = await apitierPost(
    `${config.baseUrls.barcode}/generate/qrcode`,
    body,
    config.keys.barcode!,
    true
  );

  return JSON.stringify({
    format: "png",
    encoding: "base64",
    data: base64,
    note: "Decode this base64 string to get the PNG image bytes",
  });
}
