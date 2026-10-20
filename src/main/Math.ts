import { ed25519 } from '@noble/curves/ed25519.js';
import { randomBytes } from '@noble/hashes/utils.js';
import {EdwardsPoint} from "@noble/curves/abstract/edwards.js";
import { sha256 } from '@noble/hashes/sha2.js';

const Point = ed25519.Point;
const G = Point.BASE;
const L = Point.Fn.ORDER; // use ed25519.CURVE.n on v1
const H = hashToPoint(G.toBytes())

const mod = (a: bigint) => ((a % L) + L) % L;
export const bytesToBigIntLE = (b: Uint8Array) =>
  b.reduceRight((n, byte) => (n << 8n) | BigInt(byte), 0n);


export function hashToPoint(data: Uint8Array) {
  for (let counter = 0; counter < 256; counter++) {
    const input = new Uint8Array(data.length + 1);
    input.set(data, 0);
    input[data.length] = counter;
    const h = sha256(input);
    try {
      const p = ed25519.Point.fromHex(bytesToHex(h)).multiply(8n);
      if (p.equals(ed25519.Point.ZERO)) continue;   // identity, skip
      return p;
    } catch {
      // not a valid point, try the next counter
    }
  }
  throw new Error('hashToPoint failed');
}

export function secret(): bigint {
  let s = 0n;
  while (s === 0n) s = mod(bytesToBigIntLE(randomBytes(64)));
  return s;
}
export function bigIntToBytesLE(n: bigint, length = 32): Uint8Array<ArrayBuffer> {
  if (n < 0n) throw new Error('negative bigint not supported');
  const out = new Uint8Array(new ArrayBuffer(length));
  for (let i = 0; i < length; i++) {
    out[i] = Number(n & 0xffn);
    n >>= 8n;
  }
  if (n !== 0n) throw new Error('bigint does not fit in length bytes');
  return out;
}
export  function lenPrefix(p: Uint8Array): Uint8Array<ArrayBuffer> {
  const out = new Uint8Array(new ArrayBuffer(4 + p.length));
  new DataView(out.buffer).setUint32(0, p.length, true);  // 4-byte length, little-endian
  out.set(p, 4);
  return out;
}
export function concat(...parts: Uint8Array[]): Uint8Array<ArrayBuffer> {
  const total = parts.reduce((n, p) => n + p.length, 0);
  const out = new Uint8Array(new ArrayBuffer(total));
  let offset = 0;
  for (const p of parts) {
    out.set(p, offset);
    offset += p.length;
  }
  return out;
}

export function hexToBytes(hex: string): Uint8Array<ArrayBuffer> {
  const out = new Uint8Array(new ArrayBuffer(hex.length / 2));
  for (let i = 0; i < out.length; i++) {
    out[i] = parseInt(hex.slice(i * 2, i * 2 + 2), 16);
  }
  return out;
}
export function bytesToHex(bytes: Uint8Array): string {
  return Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('');
}

export function hashToScalarMulti(...parts: Uint8Array[]): bigint {
  const data = concat(...parts.map(lenPrefix));            // concat() from the earlier code
  return bytesToBigIntLE(sha256(data)) % L;
}
export function hexToPoint(hex: string): EdwardsPoint {
  if (!/^[0-9a-fA-F]{64}$/.test(hex)) {
    throw new Error('expected 64 hex characters (32 bytes)');
  }
  return ed25519.Point.fromHex(hex);   // throws if not a valid curve point
}
export const scalarAdd = (a: bigint, b: bigint) => mod(a + b);
export const scalarMul = (a: bigint, b: bigint) => mod(a * b);
export const scalarNeg = (a: bigint) => mod(-a);
export const baseMul = (s: bigint) => G.multiply(s);
export const pointAdd = (A: typeof G, B: typeof G) => A.add(B);
export const pointMul = (A: typeof G, s: bigint) => A.multiply(s);
export const compressedHex = (s:EdwardsPoint) => s.toHex();
export const compressedBytes = (s:EdwardsPoint) => s.toBytes();
export const HMultiply = (s:bigint) => H.multiply(s)
export const idx = (i: number) => bigIntToBytesLE(BigInt(i), 4);