// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";
import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

contract AccessControlERC20Mint is ERC20, AccessControl, Ownable {
    bytes32 public constant DAPP_ROLE = keccak256("DAPP_ROLE");

    constructor(uint256 initialSupply) ERC20("MyToken", "TKN") Ownable(msg.sender) {
      _mint(msg.sender, initialSupply);
    }
    
    function setDapp(address dapp) external onlyOwner{
        _grantRole(DAPP_ROLE, dapp);
        renounceOwnership();
    }

    function mintAfterTimestamp(address to, uint256 amount, uint256 ts) public onlyRole(DAPP_ROLE) {
        require(block.timestamp >= ts);
        _mint(to, amount);
    }

    function burnAfterTimestamp(address from, uint256 amount, uint256 ts) public onlyRole(DAPP_ROLE) {
        require(block.timestamp >= ts);
        _burn(from, amount);
    }
}
