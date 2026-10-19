import {ed25519} from "@noble/curves/ed25519.js";
import {get, set} from "idb-keyval";
import {bytesToHex} from "@noble/curves/utils.js";
import {baseMul, secret, compressedHex, bigIntToBytesLE, pointMul, hashToScalarMulti, compressedBytes, pointAdd} from "./Math";
import {EdwardsPoint} from "@noble/curves/abstract/edwards.js";

const Byte_toHex = (b:Uint8Array<ArrayBuffer>) => Array.from(b, (x) => x.toString(16).padStart(2, '0')).join('');
// @ts-ignore
const Hex_toByte = (h:string) => Uint8Array.from(h.match(/.{2}/g).map((x) => parseInt(x, 16)));
const enc = new TextEncoder();

async function deriveKey(password:string, salt:Uint8Array<ArrayBuffer>){
    const base = await crypto.subtle.importKey('raw', enc.encode(password), 'PBKDF2', false, ['deriveKey']);
    return crypto.subtle.deriveKey(
    { name: 'PBKDF2', salt, iterations: 600000, hash: 'SHA-256' },
    base,
    { name: 'AES-GCM', length: 256 },
    false,
    ['encrypt', 'decrypt']
  );
}

async function createWallet(password:string){
    const viewKeyPriv = secret()
    const spendKeyPriv = secret()
    const viewKeyPub = compressedHex(baseMul(viewKeyPriv))
    const spendKeyPub = compressedHex(baseMul(spendKeyPriv))

    const salt = crypto.getRandomValues(new Uint8Array(16));
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const key =  await deriveKey(password, salt)
    const ct = new Uint8Array(await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, key, bigIntToBytesLE(spendKeyPriv)));
    await set('wallet', { viewKeyPub:viewKeyPub, viewKeyPriv:viewKeyPriv, spendKeyPriv:spendKeyPriv, spendKeyPub:spendKeyPub, salt: Byte_toHex(salt), iv: Byte_toHex(iv), ct: Byte_toHex(ct) });
}
async function sendInfo(publicKey: Uint8Array<ArrayBufferLike> & Uint8Array<ArrayBuffer>, nonce: number){
    const API_URL = "http://127.0.0.1:8000";
    const res = await fetch(`${API_URL}/storeData`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({publicKey: publicKey, nonce: nonce}),
    });
    const data = await res.json();
    console.log(data)
}
async function unlockWallet(password:string) {
  const w = await get('wallet');
  if (!w) throw new Error('No wallet found');
  const key = await deriveKey(password, Hex_toByte(w.salt));
  const spendKeyPriv = new Uint8Array(
    await crypto.subtle.decrypt({ name: 'AES-GCM', iv: Hex_toByte(w.iv) }, key, Hex_toByte(w.ct))
  );
  return {spendKeyPriv:spendKeyPriv, viewKeyPriv:w.viewKeyPriv, spendKeyPub: w.spendKeyPub, viewKeyPub:w.viewKeyPub};

}
function one_time_address(publicviewKey:EdwardsPoint, i:number, spendKeyPublic){
    const addressOneTime = secret()
    const E:EdwardsPoint = pointMul(publicviewKey, addressOneTime)
    const byte = new Uint8Array([i])
    const hash = hashToScalarMulti(compressedBytes(E), byte)
    const P = baseMul(hash);
    return pointAdd(P, spendKeyPublic)
}
function deleteWallet(){
    const DB_NAME = "wallet"
    const deleteRequest = indexedDB.deleteDatabase(DB_NAME);
    deleteRequest.onsuccess = function() {
        console.log(`Database "${DB_NAME}" deleted successfully.`);
    };

    deleteRequest.onerror = function(event) {
        // @ts-ignore
        console.error("Error deleting database:", event.target.errorCode);
    };

    deleteRequest.onblocked = function() {
        console.warn("Deletion blocked! Please close all other tabs open to this site.");
    };
}
async function sendTrans(signData: { pub: any; sign: string; details: { pub: any; address: string; amount: number; nonce: any; }; }){
    const API_URL = "http://127.0.0.1:8000";
    const res = await fetch(`${API_URL}/money`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(signData),
    });
    const data = await res.json();
    console.log(data)
}
export {unlockWallet, createWallet, deleteWallet, sendTrans}
