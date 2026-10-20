import {
    baseMul,
    bigIntToBytesLE,
    compressedBytes,
    compressedHex,
    concat,
    hashToScalarMulti,
    HMultiply,
    lenPrefix,
    pointAdd,
    bytesToHex,
    idx
} from "./Math";

import {EdwardsPoint} from "@noble/curves/abstract/edwards.js";
import {sha256} from '@noble/hashes/sha2.js';

const enc = new TextEncoder();

function createStealthAddress(SharedPoint:EdwardsPoint, i:number, spendKeyPublic:EdwardsPoint){
    const outPutTransaction = idx(i);
    const pointA = hashToScalarMulti(compressedBytes(SharedPoint), outPutTransaction)
    return compressedHex(pointAdd(baseMul(pointA), spendKeyPublic));
}
export function createCommitment(SharedPoint:EdwardsPoint, i:number, amount:number|bigint){
    const mask = deriveMask(SharedPoint, i);
    const v = BigInt(amount);
    checkAmount(v);
    return compressedHex(pointAdd(baseMul(mask), HMultiply(v)));
}
export function encryptAmount(amount:number, SharedPoint:EdwardsPoint, i:number){
    const v = BigInt(amount);
    return bytesToHex(xor8(bigIntToBytesLE(v, 8), deriveAmountPad(SharedPoint, i)))
}
export function deriveAmountPad(SharedPoint:EdwardsPoint, index: number): Uint8Array {
  const data = concat(...[enc.encode('amount'), compressedBytes(SharedPoint), idx(index)].map(lenPrefix));
  return sha256(data).slice(0, 8);
}
export function xor8(amount8: Uint8Array, pad: Uint8Array): Uint8Array {
  return amount8.map((b, i) => b ^ pad[i]);
}
export function deriveMask(SharedPoint:EdwardsPoint, i:number){
    return hashToScalarMulti(enc.encode('mask'), compressedBytes(SharedPoint), idx(i));
}
function checkAmount(v: bigint) {
  if (v < 0n || v >= 2n ** 64n) throw new Error('amount out of range');
}
// export async function createTansTest(){
//     const r = secret();
//     const SharePoint = pointMul(viewKeyPub, r);
//     const i = 0;
//     const amt = 100;
//     const data = {
//         TransKey: compressedHex(baseMul(r)),
//         add: createStealthAddress(SharePoint, i, spendKeyPub),
//         commit: createCommitment(SharePoint, i, amt),
//         amt: encryptAmount(amt, SharePoint, i),
//         i: i
//     }
//     console.log(data)
//     const API_URL = "http://127.0.0.1:8000";
//     const res = await fetch(`${API_URL}/Test`, {
//       method: "POST",
//       headers: { "Content-Type": "application/json" },
//       body: JSON.stringify(data),
//     });
//     const receive = await res.json();
//     console.log(receive)
// }
