import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
    ListToolsRequestSchema,
    CallToolRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

import { accountBalance } from "./tools/accountBalance.js";
import { generateImage } from "./tools/generateImage.js";
import { generateVideo } from "./tools/generateVideo.js";
import { getPrediction } from "./tools/getPrediction.js";
import { listModels } from "./tools/listModels.js";
import { editImage } from "./tools/editImage.js";
import { imageToVideo } from "./tools/imageToVideo.js";
import { uploadFile } from "./tools/uploadFile.js";
import { modelDetails } from "./tools/modelDetails.js";

console.error(
    "MCP KEY EXISTS:",
    !!process.env.MUAPI_API_KEY
);

const server = new Server(
    {
        name: "muapi-mcp",
        version: "1.0.0",
    },
    {
        capabilities: {
            tools: {},
        },
    }
);

server.setRequestHandler(
    ListToolsRequestSchema,
    async () => ({
        tools: [
            {
                name: "account_balance",
                description: "Get MuAPI account balance",
                inputSchema: {
                    type: "object",
                    properties: {},
                },
            },
            {
                name: "generate_image",
                description: "Generate an image using MuAPI",
                inputSchema: {
                    type: "object",
                    properties: {
                        prompt: {
                            type: "string",
                            description: "Image generation prompt",
                        },
                    },
                    required: ["prompt"],
                },
            },
            {
                name: "generate_video",
                description: "Generate a video using MuAPI",
                inputSchema: {
                    type: "object",
                    properties: {
                        prompt: {
                            type: "string",
                            description: "Video generation prompt",
                        },
                    },
                    required: ["prompt"],
                },
            },
            {
                name: "get_prediction",
                description: "Get prediction result by request ID",
                inputSchema: {
                    type: "object",
                    properties: {
                        request_id: {
                            type: "string",
                        },
                    },
                    required: ["request_id"],
                },
            },
            {
                name: "list_models",
                description: "List available MuAPI model categories",
                inputSchema: {
                    type: "object",
                    properties: {},
                },
            },
            {
                name: "model_details",
                description: "Get details about a specific model",
                inputSchema: {
                    type: "object",
                    properties: {
                        model: {
                            type: "string",
                        },
                    },
                    required: ["model"],
                },
            },
            {
                name: "edit_image",
                description: "Edit an image using MuAPI",
                inputSchema: {
                    type: "object",
                    properties: {
                        image: {
                            type: "string",
                            description: "Image URL",
                        },
                        prompt: {
                            type: "string",
                            description: "Edit instruction",
                        },
                    },
                    required: ["image", "prompt"],
                },
            },
            {
                name: "image_to_video",
                description: "Convert an image into a video",
                inputSchema: {
                    type: "object",
                    properties: {
                        image: {
                            type: "string",
                        },
                        prompt: {
                            type: "string",
                        },
                    },
                    required: ["image", "prompt"],
                },
            },
            {
                name: "upload_file",
                description: "Upload a file to MuAPI",
                inputSchema: {
                    type: "object",
                    properties: {
                        filepath: {
                            type: "string",
                        },
                    },
                    required: ["filepath"],
                },
            },
        ],
    })
);

server.setRequestHandler(
    CallToolRequestSchema,
    async (request) => {
        const { name, arguments: args } = request.params;

        switch (name) {
            case "account_balance": {
                const result = await accountBalance();

                return {
                    content: [
                        {
                            type: "text",
                            text: JSON.stringify(result, null, 2),
                        },
                    ],
                };
            }

            case "generate_image": {
                const result = await generateImage(
                    args?.prompt
                );

                return {
                    content: [
                        {
                            type: "text",
                            text: JSON.stringify(result, null, 2),
                        },
                    ],
                };
            }

            case "generate_video": {
                const result = await generateVideo(
                    args?.prompt
                );

                return {
                    content: [
                        {
                            type: "text",
                            text: JSON.stringify(result, null, 2),
                        },
                    ],
                };
            }

            case "get_prediction": {
                const result = await getPrediction(
                    args?.request_id
                );

                return {
                    content: [
                        {
                            type: "text",
                            text: JSON.stringify(result, null, 2),
                        },
                    ],
                };
            }

            case "list_models": {
                const result = await listModels();

                return {
                    content: [
                        {
                            type: "text",
                            text: JSON.stringify(result, null, 2),
                        },
                    ],
                };
            }

            case "model_details": {
                const result = await modelDetails(
                    args?.model
                );

                return {
                    content: [
                        {
                            type: "text",
                            text: JSON.stringify(result, null, 2),
                        },
                    ],
                };
            }

            case "edit_image": {
                const result = await editImage(
                    args?.image,
                    args?.prompt
                );

                return {
                    content: [
                        {
                            type: "text",
                            text: JSON.stringify(result, null, 2),
                        },
                    ],
                };
            }

            case "image_to_video": {
                const result = await imageToVideo(
                    args?.image,
                    args?.prompt
                );

                return {
                    content: [
                        {
                            type: "text",
                            text: JSON.stringify(result, null, 2),
                        },
                    ],
                };
            }

            case "upload_file": {
                const result = await uploadFile(
                    args?.filepath
                );

                return {
                    content: [
                        {
                            type: "text",
                            text: JSON.stringify(result, null, 2),
                        },
                    ],
                };
            }

            default:
                throw new Error(
                    `Unknown tool: ${name}`
                );
        }
    }
);

const transport =
    new StdioServerTransport();

await server.connect(transport);

console.error(
    "MuAPI MCP Server running..."
);