import CryptoJS from "crypto-js";
import { ethers } from "ethers";

export const signWithMetaMask = async (fileUrl) => {
  // fetch file
  const res = await fetch(fileUrl);
  const buffer = await res.arrayBuffer();

  // SHA-256 hash
  const hash = CryptoJS.SHA256(
    CryptoJS.lib.WordArray.create(buffer)
  ).toString();

  // MetaMask
  const provider = new ethers.BrowserProvider(window.ethereum);
  const signer = await provider.getSigner();
  const wallet = await signer.getAddress();

  const signature = await signer.signMessage(hash);

  return { hash, signature, wallet };
};
