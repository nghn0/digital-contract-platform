async function main() {
  const ContractProof = await ethers.getContractFactory("ContractProof");
  const contract = await ContractProof.deploy();

  await contract.waitForDeployment();

  console.log("Contract deployed to:", await contract.getAddress());
}

main().catch(console.error);
