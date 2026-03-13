// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract ContractProof {

    struct ContractData {
        bytes32 contractHash;
        bytes signatureA;
        bytes signatureB;
        address walletA;
        address walletB;
        uint256 timestamp;
    }

    mapping(uint256 => ContractData) public contracts;
    uint256 public contractCount;

    event ContractStored(uint256 indexed id, bytes32 hash);

    function storeContractProof(
        bytes32 contractHash,
        bytes memory sigA,
        bytes memory sigB,
        address walletA,
        address walletB
    ) public {
        contractCount++;

        contracts[contractCount] = ContractData(
            contractHash,
            sigA,
            sigB,
            walletA,
            walletB,
            block.timestamp
        );

        emit ContractStored(contractCount, contractHash);
    }
}
