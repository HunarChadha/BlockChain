import {unlockWallet} from "./Wallet";
import {baseMul, secret, HMultiply, pointAdd, hashToScalarMulti, pointMul, compressedBytes, compressedHex, HexToPoint} from "./Math";
import {EdwardsPoint} from "@noble/curves/abstract/edwards.js";

const privview = secret()
const privspend = secret()
const pubvew = baseMul(privview)
const pubspend = baseMul(privspend)

export async function fetchBalance(){
    const API_URL = "http://127.0.0.1:8000";
    const res = await fetch(`${API_URL}/Balance`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({hey:'Hello'}),
    });
    const receive = await res.json();
    for(const [key, value] of Object.entries(receive)){
        const scanner = scan(privview, value.TransKey, pubspend);
        console.log(scanner);
    }
}

function createCommitment(amount:number){
    const y = secret()
    return compressedHex(pointAdd(baseMul(y), HMultiply(BigInt(amount))))
}
function createSpoint(secretviewKey:bigint, TransKeyPub:string){
    const TransKey = HexToPoint(TransKeyPub);
    return compressedHex(pointMul(TransKey, secretviewKey));
}
function createOneTimeAddress(r:bigint, viewKeyPublic:EdwardsPoint, spendKeyPublic:EdwardsPoint, i:number){
    const byte = new Uint8Array([i])
    const pointA = hashToScalarMulti(compressedBytes(pointMul(viewKeyPublic, r)), byte)
    return compressedHex(pointAdd(baseMul(pointA), spendKeyPublic));
}
export async function createTestAmount(){
    const r = secret()
    const data = {
        oneTimeAddress:createOneTimeAddress(r, pubvew, pubspend, 0),
        commit: createCommitment(10),
        TransKey: compressedHex(baseMul(r))
    }
    console.log(data)
    const API_URL = "http://127.0.0.1:8000";
    const res = await fetch(`${API_URL}/Test`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    const receive = await res.json();
    console.log(receive)
}
function scan(privateKey:bigint, TransKey:string, publicspendKey:EdwardsPoint){
    const transKey:EdwardsPoint = HexToPoint(TransKey)
    const byte = new Uint8Array([0])
    const pointA = hashToScalarMulti(compressedBytes(pointMul(transKey, privateKey)), byte)
    return compressedHex(pointAdd(baseMul(pointA), publicspendKey))
}