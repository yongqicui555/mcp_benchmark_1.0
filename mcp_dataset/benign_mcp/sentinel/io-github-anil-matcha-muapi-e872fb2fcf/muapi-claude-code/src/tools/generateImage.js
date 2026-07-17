import client from "../muapi/sdkClient.js";

export async function generateImage(prompt) {
    const generation =
        await client.images.generate({
            prompt,
            model: "flux-dev",
        });

    const result =
        await client.predictions.wait(
            generation.request_id
        );

    return {
        success: true,
        message: "Image generated successfully",
        result,
    };
}