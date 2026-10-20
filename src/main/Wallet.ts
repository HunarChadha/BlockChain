import { get, set, del } from "idb-keyval";
import { baseMul, secret, compressedHex, bigIntToBytesLE, bytesToBigIntLE, bytesToHex, hexToBytes, hexToPoint } from "./Math";

const enc = new TextEncoder();

async function deriveKey(password: string, salt: Uint8Array<ArrayBuffer>) {
  const base = await crypto.subtle.importKey("raw", enc.encode(password), "PBKDF2", false, ["deriveKey"]);
  return crypto.subtle.deriveKey(
    { name: "PBKDF2", salt, iterations: 600000, hash: "SHA-256" },
    base,
    { name: "AES-GCM", length: 256 },
    false,
    ["encrypt", "decrypt"]
  );
}

async function createWallet(password: string) {
  if (await get("wallet")) throw new Error("Wallet already exists");

  const viewKeyPriv = secret();
  const spendKeyPriv = secret();
  const viewKeyPub = compressedHex(baseMul(viewKeyPriv));
  const spendKeyPub = compressedHex(baseMul(spendKeyPriv));

  // pack both private keys (32 bytes each) into one blob
  const plain = new Uint8Array(64);
  plain.set(bigIntToBytesLE(spendKeyPriv), 0);
  plain.set(bigIntToBytesLE(viewKeyPriv), 32);

  const salt = crypto.getRandomValues(new Uint8Array(16));
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const key = await deriveKey(password, salt);
  const ct = new Uint8Array(await crypto.subtle.encrypt({ name: "AES-GCM", iv }, key, plain));
  plain.fill(0);

  await set("wallet", {
    spendKeyPub,
    viewKeyPub,
    salt: bytesToHex(salt),
    iv: bytesToHex(iv),
    ct: bytesToHex(ct),
  });
  return { spendKeyPub, viewKeyPub };
}
async function unlockWallet(password: string) {
  const w = await get("wallet");
  if (!w) throw new Error("No wallet found");

  const key = await deriveKey(password, hexToBytes(w.salt));
  let plain: Uint8Array;
  try {
    plain = new Uint8Array(
      await crypto.subtle.decrypt({ name: "AES-GCM", iv: hexToBytes(w.iv) }, key, hexToBytes(w.ct))
    );
  } catch {
    throw new Error("Wrong password");
  }

  const result = {
    spendKeyPriv: bytesToBigIntLE(plain.slice(0, 32)),   // bigint
    viewKeyPriv: bytesToBigIntLE(plain.slice(32, 64)),   // bigint
    spendKeyPub: hexToPoint(w.spendKeyPub),              // Edwards point
    viewKeyPub: hexToPoint(w.viewKeyPub),                // Edwards point
  };
  console.log(bytesToHex(bigIntToBytesLE(result.spendKeyPriv)))
  console.log(bytesToHex(bigIntToBytesLE(result.viewKeyPriv)))
  console.log(compressedHex(result.spendKeyPub))
  console.log(compressedHex(result.viewKeyPub))
  plain.fill(0);
  return result;
}


async function deleteWallet() {
  await del("wallet");
}

export { unlockWallet, createWallet, deleteWallet };