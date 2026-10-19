import {baseMul, secret, HMultiply, pointAdd, hashToScalarMulti, pointMul, compressedBytes, compressedHex, HexToPoint, bigIntToBytesLE, concat, lenPrefix} from "./Math";
import {EdwardsPoint} from "@noble/curves/abstract/edwards.js";
import { sha256 } from '@noble/hashes/sha2.js';

const enc = new TextEncoder();
const idx = (i: number) => bigIntToBytesLE(BigInt(i), 4);
const Byte_toHex = (b:Uint8Array<ArrayBuffer>) => Array.from(b, (x) => x.toString(16).padStart(2, '0')).join('');
// @ts-ignore
const Hex_toByte = (h:string) => Uint8Array.from(h.match(/.{2}/g).map((x) => parseInt(x, 16)));

function createStealthAddress(SharedPoint:EdwardsPoint, i:number, spendKeyPublic:EdwardsPoint){
    const outPutTransaction = idx(i);
    const pointA = hashToScalarMulti(compressedBytes(SharedPoint), outPutTransaction)
    return compressedHex(pointAdd(baseMul(pointA), spendKeyPublic));
}
function createCommitment(SharedPoint:EdwardsPoint, i:number, amount:number){
    const mask = deriveMask(SharedPoint, i);
    const v = BigInt(amount);
    checkAmount(v);
    return compressedHex(pointAdd(baseMul(mask), HMultiply(v)));
}
function encryptAmount(amount:number, SharedPoint:EdwardsPoint, i:number){
    const v = BigInt(amount);
    return xor8(bigIntToBytesLE(v, 8), deriveAmountPad(SharedPoint, i)).toString();
}
function deriveAmountPad(SharedPoint:EdwardsPoint, index: number): Uint8Array {
  const data = concat(...[enc.encode('amount'), compressedBytes(SharedPoint), idx(index)].map(lenPrefix));
  return sha256(data).slice(0, 8);
}

function xor8(amount8: Uint8Array, pad: Uint8Array): Uint8Array {
  return amount8.map((b, i) => b ^ pad[i]);
}
function deriveMask(SharedPoint:EdwardsPoint, i:number){
    return hashToScalarMulti(enc.encode('mask'), compressedBytes(SharedPoint), idx(i));
}
function checkAmount(v: bigint) {
  if (v < 0n || v >= 2n ** 64n) throw new Error('amount out of range');
}
function main(){

}
