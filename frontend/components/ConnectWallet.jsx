"use client";
import { useState } from "react";
import { ethers } from "ethers";

export default function ConnectWallet({ setWallet }) {
  const connectWallet = async () => {
    const provider = new ethers.BrowserProvider(window.ethereum);
    const signer = await provider.getSigner();
    const address = await signer.getAddress();
    setWallet(address);
  };

  return (
    <button
      onClick={connectWallet}
      className="bg-purple-600 text-white px-4 py-2 rounded-xl"
    >
      Connect MetaMask
    </button>
  );
}
