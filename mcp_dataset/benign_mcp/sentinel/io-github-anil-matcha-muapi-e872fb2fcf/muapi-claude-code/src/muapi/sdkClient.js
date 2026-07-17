import "dotenv/config";
import { MuAPI } from "muapi-js";

console.error(
    "MUAPI key loaded:",
    !!process.env.MUAPI_API_KEY
);

const client = new MuAPI(
    process.env.MUAPI_API_KEY
);

export default client;