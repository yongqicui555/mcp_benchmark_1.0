import client from "../muapi/sdkClient.js";

export async function editImage(
    image,
    prompt
) {
    const generation =
        await client.images.edit({
            image,
            prompt,
            model: "flux-kontext-dev",
        });

    const result =
        await client.predictions.wait(
            generation.request_id
        );

    return {
        success: true,
        message: "Image edited successfully",
        result,
    };
}