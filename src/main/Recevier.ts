import {
    baseMul,
    bytesToBigIntLE,
    compressedBytes, compressedHex, hashToPoint,
    hashToScalarMulti,
    hexToBytes,
    HexToPoint,
    hexToPoint, idx, pointAdd,
    pointMul, scalarAdd
} from "./Math";
import {deriveAmountPad, xor8, createCommitment} from "./Sender";
import {EdwardsPoint} from "@noble/curves/abstract/edwards.js";
import {keys} from "idb-keyval";


export function decryptAmount(data, keys){
    const SharedPoint = pointMul(hexToPoint(data.TransKey), keys.viewKeyPriv);
    const pad = deriveAmountPad(SharedPoint, data.i)
    return bytesToBigIntLE(xor8(hexToBytes(data.amt), pad));
}
function extractAdd(add:string){
    const list = add.split(":")
    return list[1];
}
function checkCommitment(data, keys){
    const amount = decryptAmount(data, keys);
    const commitment = createCommitment(pointMul(HexToPoint(data.TransKey), keys.viewKeyPriv), data.i, amount);
    if(commitment == data.commit){
        return Number(amount);
    }
    else {
        throw Error("commit has been altered");
    }
}
export function checkAdd(add:string, data, keys) {
    const transKey:EdwardsPoint = HexToPoint(data.TransKey)
    const A = hashToScalarMulti(compressedBytes(pointMul(transKey, keys.viewKeyPriv)), idx(data.i))
    const addX = compressedHex(pointAdd(baseMul(A), keys.spendKeyPub))
    return addX === extractAdd(add);
}
function SecretNodeCode(data, keys){
    const A = hashToScalarMulti(compressedBytes(pointMul(HexToPoint(data.TransKey), keys.viewKeyPriv)), idx(data.i))
    return scalarAdd(A, keys.spendKeyPriv);
}
export function createNodeImage(data, addX:string, keys){
    const add = extractAdd(addX);
    const SecretCode = SecretNodeCode(data, keys)
    return pointMul(hashToPoint(hexToBytes(add)), SecretCode);
}
export function calculateBalance(Pairs:Record<string, any>, ImageKeyList:string[], Keys){
    let balance = 0;
    for (const [item, value] of Object.entries(Pairs)) {
        let find = false
        for (const imageKey of ImageKeyList){
            if (imageKey === item){
                find = true;
            }
        }
        if (find){
            balance += checkCommitment(value, Keys);
        }
    }
    return balance;
}