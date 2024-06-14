// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";
import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

contract OYFToken is ERC20, AccessControl, Ownable {
    bytes32 public constant DAPP_ROLE = keccak256("DAPP_ROLE");

    constructor(uint256 initialSupply) ERC20("OYFToken", "OYF") Ownable(msg.sender) {
      _mint(msg.sender, initialSupply);
    }
    
    function setDapp(address dapp) external onlyOwner{
        _grantRole(DAPP_ROLE, dapp);
        renounceOwnership();
    }

    function mintAfterTimestamp(address _to, uint256 _amount, uint256 _ts) public onlyRole(DAPP_ROLE) {
        require(block.timestamp >= _ts);
        _mint(_to, _amount);
    }

    function burnAfterTimestamp(address _from, uint256 _amount, uint256 _ts) public onlyRole(DAPP_ROLE) {
        require(block.timestamp >= _ts);
        _burn(_from, _amount);
    }

    function transferAfterTimestamp(address _to, uint256 _amount, uint256 _ts) public {
        require(block.timestamp >= _ts);
        transfer(_to, _amount);
    }
}
