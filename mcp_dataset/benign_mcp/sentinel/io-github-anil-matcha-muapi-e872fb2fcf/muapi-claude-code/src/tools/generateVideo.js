import client from "../muapi/sdkClient.js";

export async function generateVideo(prompt) {
    const generation =
        await client.videos.generate({
            prompt,
            model: "kling-master",
        });

    const result =
        await client.predictions.wait(
            generation.request_id
        );

    return {
        success: true,
        message: "Video generated successfully",
        result,
    };
}