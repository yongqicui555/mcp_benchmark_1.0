import client from "../muapi/sdkClient.js";

export async function getPrediction(requestId) {
    return await client.predictions.wait(
        requestId
    );
}