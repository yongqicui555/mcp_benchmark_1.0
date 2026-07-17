import client from "../muapi/sdkClient.js";

export async function listModels() {
    return client.models.categories();
}