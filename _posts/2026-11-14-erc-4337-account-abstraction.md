---
title: "ERC-4337, 프로토콜을 바꾸지 않고 만든 계정 추상화"
description: 합의 계층을 건드리지 않는 계정 추상화 ERC-4337의 구성을 정리하고, 메인넷 EntryPoint의 UserOperation 로그를 세어 누가 어떻게 쓰는지 확인했습니다.
date: 2026-11-14 13:00:00 +0900
category: tech-docs
tags: [ethereum, erc, erc-4337, account-abstraction, eip-7702]
---

이더리움 계정은 두 종류입니다. 개인키 하나로 움직이는 EOA와, 코드로 움직이는 컨트랙트 계정입니다. 그런데 거래를 시작할 수 있는 쪽은 EOA뿐입니다. 키를 잃으면 되살릴 방법이 없고, 수수료는 반드시 ETH로 내야 하고, 서명 방식도 정해져 있습니다. 계정 추상화는 서명 검증이나 수수료 지불 같은 규칙을 계정이 코드로 직접 정하게 하자는 아이디어이고, ERC-4337은 이를 프로토콜을 바꾸지 않고 구현한 표준입니다.

## 프로토콜을 바꾸지 않은 이유

계정 추상화는 오래된 목표였고, 프로토콜을 직접 고치는 제안이 여러 번 논의됐지만 구현까지 가지 못했습니다. ERC-4337 문서는 합의 계층 개발이 확장성 쪽에 우선순위가 가 있어서 당분간 프로토콜을 바꿀 기회가 없을 수 있다고 봅니다. 합의 계층을 건드리지 않으니 새 트랜잭션 타입도 만들 수 없습니다. 대신 `UserOperation`이라는 거래 비슷한 객체를 정의하고, 이를 따로 모으는 별도의 멤풀을 둡니다.

## 구성 요소

| 이름 | 하는 일 |
|---|---|
| UserOperation | 사용자가 하려는 일을 담은 묶음. 거래와 비슷하지만 서명 방식은 계정이 정합니다 |
| 스마트 계정 | 사용자의 계정 컨트랙트. 서명을 검증하는 규칙을 스스로 가집니다 |
| EntryPoint | 모든 UserOperation을 실행하는 하나뿐인 컨트랙트 |
| 번들러 | UserOperation을 모아 `handleOps` 거래 하나로 묶어 블록에 넣는 노드 |
| Paymaster | 사용자 대신 가스를 내 주는 컨트랙트 |
| Factory | 아직 배포되지 않은 계정을 대신 배포해 주는 컨트랙트 |

흐름은 이렇습니다. 사용자가 UserOperation에 서명해 번들러에게 보내고, 번들러가 여러 개를 모아 `handleOps` 거래로 올립니다. EntryPoint는 각 UserOperation마다 먼저 검증(계정의 `validateUserOp`, 필요하면 Paymaster 검증)을 하고, 통과하면 계정의 `callData`를 실행합니다. 가스는 계정이나 Paymaster가 EntryPoint에 미리 맡겨 둔 예치금에서 빠집니다.

계정이 꼭 구현해야 하는 함수는 하나입니다.

```solidity
interface IAccount {
  function validateUserOp(
      PackedUserOperation calldata userOp,
      bytes32 userOpHash,
      uint256 missingAccountFunds
  ) external returns (uint256 validationData);
}
```

문서가 계정에 요구하는 것은 이렇습니다. 호출한 쪽이 믿을 수 있는 EntryPoint인지 확인하고, `userOpHash`에 대한 서명이 맞는지 검증하고, 부족한 예치금(`missingAccountFunds`)을 EntryPoint에 채워 넣어야 합니다. 서명이 틀렸을 때는 되돌리지 말고 실패 값(1)을 반환하도록 권장하는데, 가스 추정이 가능하도록 하기 위해서입니다. nonce는 192비트 key와 64비트 sequence로 나뉩니다. key가 다르면 서로 순서가 독립이라서, EOA는 앞 거래가 막히면 뒤가 전부 막히지만 4337 계정은 key를 나눠 쓰면 병렬로 보낼 수 있습니다.

## 메인넷 사용 현황

EntryPoint는 버전마다 주소가 따로 있고 구버전도 계속 쓰입니다. 공식 저장소(eth-infinitism/account-abstraction)의 [릴리스](https://github.com/eth-infinitism/account-abstraction/releases)에 적힌 주소를 기준으로 네 버전 모두 코드가 올라가 있음을 확인했습니다.

| 버전 | 주소 | 코드 크기 |
|---|---|---|
| v0.6 | `0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789` | 23,689 바이트 |
| v0.7 | `0x0000000071727De22E5E9d8BAf0edAc6f37da032` | 16,035 바이트 |
| v0.8 | `0x4337084D9E255Ff0702461CF8895CE9E3b5Ff108` | 21,738 바이트 |
| v0.9 | `0x433709009B8330FDa32311DF1C2AFA402eD8D009` | 22,425 바이트 |

EntryPoint는 UserOperation 하나를 처리할 때마다 `UserOperationEvent`를 남깁니다. 이 로그를 블록 26,421,009번부터 26,422,009번까지 1,001개 블록(3시간 남짓) 동안 세었습니다.

| 버전 | UserOperation 수 | Paymaster가 가스를 낸 비율 |
|---|---|---|
| v0.6 | 405 | 58.0% |
| v0.7 | 3,769 | 74.6% |
| v0.8 | 929 | 79.0% |
| v0.9 | 8 | 건수가 적어 생략 |

네 버전을 합치면 5,111건이고 v0.7이 73.7%, v0.8이 18.2%, v0.6이 7.9%, v0.9가 0.2%입니다. 다른 구간(블록 26,423,000번부터 26,424,000번)도 세어 보니 건수는 v0.6이 510, v0.7이 2,425, v0.8이 771, v0.9가 14로 꽤 달랐지만, v0.7에서 Paymaster 비율은 74.6%와 74.7%로 거의 같았습니다. 짧은 구간 두 곳이라 추세로 읽지는 못합니다.

Paymaster는 소수에게 몰려 있습니다. v0.7의 Paymaster는 서로 다른 주소 11개뿐이었고 1위(`0x777777777777aec03fd955926dbf81597e66834c`)가 2,262건(60.0%)을 맡았습니다. 이 컨트랙트의 검증된 소스에는 이름이 `SingletonPaymasterV7`, 작성자가 Pimlico로 적혀 있습니다. 2위는 503건(13.3%)인데 프록시 뒤의 구현 소스가 검증되지 않아서 운영 주체를 알아내지 못했습니다. v0.8의 1위도 같은 계열인 `SingletonPaymasterV8`(Pimlico 표기)로 284건(30.6%)이었습니다.

묶음의 효과는 작습니다. 번들 거래 하나에 담긴 UserOperation은 평균 v0.6이 1.01건, v0.7이 1.08건, v0.8이 1.10건이었습니다. 번들러가 여러 건을 모아 고정 비용을 나누는 모습은 이 구간에서는 거의 보이지 않았습니다.

구간 안의 서로 다른 sender(UserOperation을 보낸 계정)를 전부 조회해 코드 형태를 분류했습니다.

| 분류 | v0.6 | v0.7 | v0.8 |
|---|---|---|---|
| EIP-7702로 위임된 EOA | 61.8% | 91.9% | 99.7% |
| 컨트랙트로 배포한 계정 | 38.2% | 8.1% | 0.3% |

EIP-7702는 EOA가 자기 주소에 다른 컨트랙트의 코드를 위임해 쓰게 해 주는 방식입니다. 이렇게 위임된 계정은 코드가 `0xef0100` 뒤에 위임 대상 주소가 붙은 모양이라 구분됩니다. 위임 대상 구현체는 검증된 소스의 이름과 작성자 표기로 확인했습니다.

- v0.6은 Coinbase 표기의 `EIP7702Proxy`가 UserOperation의 62.0%를 차지했습니다.
- v0.7은 `Biz`가 58.3%, Alchemy 표기의 `SemiModularAccount7702`가 19.7%, `Kernel`이 10.9%였습니다. 이 셋이 88.9%입니다.
- v0.8은 `Simple7702Account`를 쓰는 sender가 577개 중 451개(78.2%)였습니다.

이 분류는 조회 당시의 코드를 본 것이라 위임이 바뀐 계정이 있으면 달라질 수 있습니다. 그래서 v0.7 sender 150개를 무작위로 뽑아 UserOperation이 실행된 블록 시점의 코드와 비교했고, 150개 모두 분류가 같았습니다. 4337은 EOA 없이도 쓸 수 있는 계정을 목표로 출발했는데, 이 구간에서는 새 컨트랙트 계정보다 기존 EOA에 7702로 코드를 얹어 쓰는 경우가 훨씬 많았습니다.

로그에서 거래도 두 건 열어 봤습니다. 블록 26,421,015번의 `0x62890316ef50fc2562ca8ba0ac0b21086d16a5df369cdc08d6ab0b60413b6d8d`는 v0.6 EntryPoint로, 블록 26,421,010번의 `0x2e1cb35672fad280651ed4835186f62dfab8085684ef2f5cbaab93507d6555e4`는 v0.7 EntryPoint로 가는 거래였고 둘 다 EIP-1559 타입(0x2)이었습니다. 번들러는 묶음을 [EIP-1559 거래](/posts/eip-1559-fee-market/)로 올립니다.

## 계정 컨트랙트 예시

소유자 EOA 하나가 서명하는 가장 단순한 계정은 이런 모양입니다. 학습용으로 줄인 코드이고 감사받은 코드가 아닙니다. 실제로 쓸 때는 eth-infinitism 구현이나 Safe처럼 검증된 계정을 가져오는 편이 안전합니다. solc 0.8.26, OpenZeppelin Contracts 5.6.1, `@account-abstraction/contracts` 0.7.0 조합에서 컴파일되는 것까지 확인했습니다.

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {IAccount} from "@account-abstraction/contracts/interfaces/IAccount.sol";
import {PackedUserOperation} from "@account-abstraction/contracts/interfaces/PackedUserOperation.sol";
import {ECDSA} from "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import {MessageHashUtils} from "@openzeppelin/contracts/utils/cryptography/MessageHashUtils.sol";

contract SimpleOwnerAccount is IAccount {
    address public immutable entryPoint;
    address public immutable owner;

    constructor(address _entryPoint, address _owner) {
        entryPoint = _entryPoint;
        owner = _owner;
    }

    function validateUserOp(
        PackedUserOperation calldata userOp,
        bytes32 userOpHash,
        uint256 missingAccountFunds
    ) external returns (uint256 validationData) {
        require(msg.sender == entryPoint, "only entrypoint");

        bytes32 digest = MessageHashUtils.toEthSignedMessageHash(userOpHash);
        (address signer, ECDSA.RecoverError err, ) = ECDSA.tryRecover(digest, userOp.signature);
        // 서명이 틀리면 되돌리지 않고 1을 반환(가스 추정이 가능하도록)
        validationData = (err == ECDSA.RecoverError.NoError && signer == owner) ? 0 : 1;

        if (missingAccountFunds != 0) {
            (bool ok, ) = payable(msg.sender).call{value: missingAccountFunds}("");
            require(ok, "prefund failed");
        }
    }

    function execute(address to, uint256 value, bytes calldata data) external {
        require(msg.sender == entryPoint, "only entrypoint");
        (bool ok, bytes memory ret) = to.call{value: value}(data);
        if (!ok) assembly { revert(add(ret, 32), mload(ret)) }
    }

    receive() external payable {}
}
```

## 알아 둘 점

- 가스가 더 듭니다. UserOperation은 EOA 거래 하나로 끝날 일에 검증과 실행, 예치금 정산 단계를 더하기 때문에 같은 동작이라도 더 들 수밖에 없습니다.
- 번들러가 새로운 믿음의 대상이 됩니다. 검증 결과가 환경에 따라 달라지는 UserOperation을 받아 주면 번들러가 가스비를 잃을 수 있어서, 검증 단계가 접근할 수 있는 저장소와 opcode를 제한하는 규칙이 EntryPoint 코드 바깥에 따로 정해져 있습니다.
- EIP-7702와는 함께 쓰입니다. 4337 문서도 7702 계정을 UserOperation으로 다루는 방법을 정해 두었습니다. 7702 타입 거래(0x4)는 [EIP-1559 글](/posts/eip-1559-fee-market/)의 표본에서 최근 10개 블록의 1.2%였습니다.

## 확인하지 못한 것

- 위 계정을 배포하거나 EntryPoint로 UserOperation을 실제로 실행해 보지는 못했습니다. 번들러와 EntryPoint가 있는 테스트 환경(로컬 노드나 테스트넷)과 가스를 낼 계정이 필요한데 만들지 않았습니다.
- 가스 차이를 수치로 재지 못했습니다. 같은 동작(예: USDC 전송)을 EOA와 4337 계정에서 같은 조건으로 실행해야 하는데 계정 배포와 실제 전송이 필요하고, 로그에서 뽑으면 호출 내용과 Paymaster 유무, 계정 구현이 달라서 조건이 맞지 않습니다.
- Paymaster 2위 등 일부 주소의 운영 주체는 구현 소스가 검증되지 않아 알아내지 못했습니다. 위 구현체 이름은 탐색기에 올라온 소스의 값이고 제품 이름과 같다고 단정하지 않습니다.
- 7702 분류의 실행 시점 비교는 v0.7만 했고 v0.6과 v0.8은 하지 않았습니다.

---

다음 글에서는 컨트랙트를 업그레이드할 수 있게 하는 프록시의 저장 위치 표준 [EIP-1967](/posts/eip-1967-proxy-slots/)을 다룹니다.

참고: [ERC-4337 원문](https://eips.ethereum.org/EIPS/eip-4337), [EIP-7702 원문](https://eips.ethereum.org/EIPS/eip-7702)
