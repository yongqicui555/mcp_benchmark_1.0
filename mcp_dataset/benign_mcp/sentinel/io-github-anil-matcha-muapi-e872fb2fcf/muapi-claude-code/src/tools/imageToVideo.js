import client from "../muapi/sdkClient.js";

export async function imageToVideo(
    image,
    prompt
) {
    const generation =
        await client.videos.fromImage({
            image,
            prompt,
            model: "kling-master",
        });

    const result =
        await client.predictions.wait(
            generation.request_id
        );

    return {
        success: true,
        message: "Image converted to video successfully",
        result,
    };
}