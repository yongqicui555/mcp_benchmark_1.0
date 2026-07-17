import client from "../muapi/sdkClient.js";

export async function modelDetails(
    model
) {
    return client.models.get(model);
}