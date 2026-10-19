import {createWallet, unlockWallet ,sendTrans, deleteWallet} from "./main/Wallet";
import {use, useState} from "react";
import {send} from "vite";
import {createTestAmount, fetchBalance} from "./main/main";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [password, setPassword] = useState();
  const [unlockPass, setunlockPass] = useState();
  const [amount, setamount] = useState();
  const [passwordPaid, setpasswordPaid] = useState();
  const [address, setaddress] = useState();
  const [error, setError] = useState();
  const sendData = async () => {
    const signData = await signTrans(password, amount, address)
    console.log(signData);
    await sendTrans(signData)
  }
  return (
    <>
      <h1>Hello World</h1>
      <input placeholder={"Enter Create"} onChange={(event) => (setPassword(event.target.value))}/>
      <button onClick={() => (createWallet(password))}>create Wallet</button>
      <input placeholder={"Unlock"} onChange={(event) => (setunlockPass(event.target.value))}/>
      <button onClick={() => (unlockWallet(unlockPass))}> unlock</button>
      <input placeholder={"setAmount"} onChange={(event) => (setamount(event.target.value))}/>
      <input placeholder={"address"} onChange={(event) => (setaddress(event.target.value))}/>
      <button onClick={sendData}>Send Trans</button>
        <button onClick={() => deleteWallet()}>DeleteWallet</button>
        <button onClick={() => createTestAmount()}>Test1</button>
        <button onClick={() => fetchBalance()}>Balance</button>
    </>
  )
}

export default App;