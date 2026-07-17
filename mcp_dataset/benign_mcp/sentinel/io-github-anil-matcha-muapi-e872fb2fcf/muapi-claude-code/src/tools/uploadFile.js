import client from "../muapi/sdkClient.js";

export async function uploadFile(
    filepath
) {
    return await client.uploads.upload(
        filepath
    );
}