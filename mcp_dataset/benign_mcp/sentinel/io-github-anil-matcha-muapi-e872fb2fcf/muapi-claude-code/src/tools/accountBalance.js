import client from "../muapi/sdkClient.js";

export async function accountBalance() {
  return await client.account.balance();
}