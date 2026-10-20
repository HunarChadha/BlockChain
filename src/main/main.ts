import {checkAdd, calculateBalance, createNodeImage} from "./Recevier";
import {unlockWallet} from "./Wallet";
import {use} from "react";

function spitImageKeys(key:string){
    const list = key.split(":")
    return list[1];
}

async function fetchBalance(password:string){
    const API_URL = "http://127.0.0.1:8000";
    const userKeys: Promise<{
        spendKeyPriv: bigint;
        viewKeyPriv: bigint;
        spendKeyPub: EdwardsPoint;
        viewKeyPub: EdwardsPoint
    }>;
    userKeys = unlockWallet(password);
    let ImageKeysPub = []
    const res = await fetch(`${API_URL}/Balance`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({hey:'Hello'}),
    });
    const receive = await res.json();
    const pairs:Record<string, any> = {};
    for(const [key, value] of Object.entries(receive)){
        if(key.charAt(0) === "a"){
            if(checkAdd(key, value, userKeys)){
                pairs[`${(createNodeImage(value, key, userKeys))}`] = value;
            }
        }
        else{
            ImageKeysPub.push(spitImageKeys(key))
        }
    }
    console.log(calculateBalance(pairs, ImageKeysPub, userKeys));
}