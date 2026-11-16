---
title: "ERC-4337, 합의 계층을 건드리지 않는 계정 추상화"
description: 합의 계층을 바꾸지 않는 계정 추상화 ERC-4337의 구성요소를 정리하고, 메인넷 EntryPoint의 UserOperation 로그와 sender 계정 형태를 집계했습니다.
date: 2026-11-14 13:00:00 +0900
category: tech-docs
tags: [ethereum, erc, erc-4337, account-abstraction, eip-7702]
---

이더리움 계정은 두 종류입니다. 개인키 하나로 움직이는 EOA와, 코드로 움직이는 컨트랙트 계정입니다. 문제는 트랜잭션을 시작할 수 있는 쪽이 EOA뿐이라는 점입니다. 키를 잃으면 복구할 방법이 없고, 수수료는 반드시 ETH로 내야 하며, 서명 방식도 secp256k1으로 고정됩니다. 컨트랙트 계정이 쓰는 로직을 지갑 수준에서 받아 주자는 아이디어가 계정 추상화이고, ERC-4337은 이를 프로토콜 변경 없이 구현한 표준입니다.

이 글은 ERC-4337의 구성요소와 흐름을 정리하고, 메인넷의 EntryPoint 컨트랙트에서 실제 UserOperation이 얼마나 처리되는지 로그로 세어 본 결과를 담았습니다.

## 등장 배경

계정 추상화는 오래된 목표입니다. 프로토콜을 직접 고치는 제안이 여러 번 논의되었지만 구현까지 이어지지 않았습니다. ERC-4337 문서는 이 점을 동기로 밝히고 방향을 바꿨습니다. 합의 계층은 확장성 쪽 개발에 우선순위가 가 있어서 당분간 프로토콜 변경 기회가 없을 수 있으니, 그 위의 인프라만으로 같은 일을 해 보자는 것입니다.

그렇다면 트랜잭션 타입을 새로 만들 수 없습니다. 대신 `UserOperation`이라는 의사 트랜잭션 객체를 정의하고, 이를 따로 모아 주는 별도의 멤풀을 둡니다.

## 구성요소

| 이름 | 역할 |
|---|---|
| UserOperation | 사용자가 하려는 일을 담은 구조체. 트랜잭션과 비슷하지만 서명 방식은 계정이 정한다 |
| Smart Contract Account | 사용자의 계정 컨트랙트. 서명 검증 로직을 스스로 가진다 |
| EntryPoint | 모든 UserOperation을 실행하는 싱글톤 컨트랙트 |
| Bundler | UserOperation을 모아 `handleOps` 트랜잭션 하나로 묶어 블록에 넣는 노드 |
| Paymaster | 사용자 대신 가스를 내주는 컨트랙트 |
| Factory | 계정이 아직 배포되지 않았을 때 배포해 주는 컨트랙트 |

`UserOperation`의 필드는 `sender`, `nonce`, `callData`, 가스 한도들, `maxFeePerGas`, `maxPriorityFeePerGas`, `signature` 등입니다. 이름이 EIP-1559 트랜잭션과 닮은 것은 우연이 아닙니다. 번들러가 결국 EIP-1559 트랜잭션으로 이 묶음을 올리기 때문입니다. 서명의 형식은 프로토콜이 아니라 계정 구현이 정합니다. 그래서 패스키, 멀티시그, 다른 곡선의 서명이 모두 같은 틀에서 동작합니다.

## 실행 흐름

1. 사용자가 `UserOperation`을 만들어 서명하고 번들러에게 보냅니다.
2. 번들러가 여러 개를 모아 `handleOps(ops, beneficiary)` 트랜잭션을 만들어 올립니다. `beneficiary`는 모인 가스비를 받을 주소입니다.
3. EntryPoint가 각 `UserOperation`마다 검증 단계를 먼저 돌립니다. 계정의 `validateUserOp`를 부르고, 필요하면 Paymaster 검증도 부릅니다.
4. 검증이 끝나면 실행 단계에서 계정의 `callData`를 실행합니다. 가스는 계정이나 Paymaster가 EntryPoint에 맡겨 둔 예치금에서 차감됩니다.

계정이 구현해야 할 최소 인터페이스는 하나입니다.

```solidity
interface IAccount {
  function validateUserOp(
      PackedUserOperation calldata userOp,
      bytes32 userOpHash,
      uint256 missingAccountFunds
  ) external returns (uint256 validationData);
}
```

문서가 계정에 요구하는 사항은 이렇습니다. 호출자가 신뢰하는 EntryPoint인지 확인해야 하고, `userOpHash`에 대한 서명이 맞는지 검증해야 하며, 서명이 틀렸다면 되돌리지 말고 `SIG_VALIDATION_FAILED`(1)를 반환하도록 권장합니다. 가스 추정을 위해서입니다. 부족한 예치금(`missingAccountFunds`)은 EntryPoint에 채워 넣어야 합니다. 반환값 `validationData`에는 유효 기간(`validUntil`, `validAfter`)도 함께 담깁니다.

nonce도 눈여겨볼 부분입니다. 192비트 key와 64비트 sequence로 나누어, key가 다르면 서로 독립된 순서를 가집니다. EOA는 nonce 하나가 줄지어 올라가는 구조라 앞의 트랜잭션이 막히면 뒤가 모두 막히지만, 4337 계정은 key를 나눠 쓰면 병렬로 보낼 수 있습니다.

`userOpHash`에는 `chainId`와 EntryPoint 주소가 들어갑니다. 다른 체인이나 EntryPoint 버전에서 서명이 재사용되지 않도록 하기 위해서입니다.

## 메인넷에서 확인하기

EntryPoint는 버전마다 주소가 따로 있고, 구버전도 계속 쓰입니다. 공식 저장소(eth-infinitism/account-abstraction)의 [릴리스](https://github.com/eth-infinitism/account-abstraction/releases)에 적힌 주소를 기준으로 네 버전 모두 코드가 올라가 있음을 확인했습니다.

| 버전 | 주소 | 배포된 코드 크기 |
|---|---|---|
| v0.6 | `0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789` | 23,689 바이트 |
| v0.7 | `0x0000000071727De22E5E9d8BAf0edAc6f37da032` | 16,035 바이트 |
| v0.8 | `0x4337084D9E255Ff0702461CF8895CE9E3b5Ff108` | 21,738 바이트 |
| v0.9 | `0x433709009B8330FDa32311DF1C2AFA402eD8D009` | 22,425 바이트 |

`UserOperationEvent` 로그를 세어 실제 사용량도 봤습니다. 이 이벤트는 UserOperation 하나가 처리될 때마다 EntryPoint가 냅니다. 블록 26,421,009번부터 26,422,009번까지 1,001개 블록, 시간으로는 3시간 남짓입니다.

| 지표 | v0.6 | v0.7 | v0.8 | v0.9 |
|---|---|---|---|---|
| UserOperation 수 | 405 | 3,769 | 929 | 8 |
| Paymaster가 가스를 낸 수 | 235 (58.0%) | 2,810 (74.6%) | 734 (79.0%) | 건수가 적어 생략 |
| 실행에 성공한 수 | 400 (98.8%) | 3,746 (99.4%) | 922 (99.2%) | 건수가 적어 생략 |

네 버전을 합치면 5,111건이고, v0.7이 73.7%, v0.8이 18.2%, v0.6이 7.9%, v0.9가 0.2%입니다. 짧은 구간이라 추세로 읽을 수는 없습니다. 같은 방식으로 블록 26,423,000번부터 26,424,000번까지 다시 세었더니 v0.6이 510건, v0.7이 2,425건, v0.8이 771건, v0.9가 14건이었습니다. 건수는 구간마다 꽤 달라도 v0.7에서 Paymaster가 가스를 낸 비율은 74.6%와 74.7%로 거의 같았습니다.

구간 안을 조금 더 들여다보면 세 가지가 보입니다.

첫째는 Paymaster가 소수에게 몰려 있다는 점입니다. 첫 구간에서 v0.7의 Paymaster는 서로 다른 주소 11개뿐이었고, 1위(`0x777777777777aec03fd955926dbf81597e66834c`)가 2,262건(60.0%), 2위가 503건(13.3%)을 맡았습니다. 상위 둘이 73.3%입니다. 1위는 검증된 소스에 컨트랙트 이름이 `SingletonPaymasterV7`, 작성자가 Pimlico로 적혀 있습니다. 2위는 `ERC1967Proxy`이고 뒤의 구현 컨트랙트 소스가 검증되어 있지 않아서 운영 주체를 알아내지 못했습니다. v0.8에서도 1위는 같은 계열인 `SingletonPaymasterV8`(Pimlico 표기)로 284건(30.6%)이었고, 2위 `MixinPaymaster`가 219건(23.6%)이었습니다. 이 컨트랙트의 소스에는 Solady 표기가 있는데 이는 가져다 쓴 라이브러리의 표기라서 운영 주체는 알 수 없습니다. v0.6은 주소 6개 중 1위가 151건(37.3%)이었으나 역시 구현이 검증되지 않았습니다.

둘째는 묶음의 효과가 작다는 점입니다. 번들 트랜잭션 하나에 담긴 UserOperation은 평균 v0.6이 1.01건(402개에 405건), v0.7이 1.08건(3,498개에 3,769건), v0.8이 1.10건(846개에 929건)이었습니다. 번들러가 여러 건을 모아 고정 비용을 나누는 모습은 이 구간에서는 거의 보이지 않았습니다.

셋째는 sender의 정체입니다. 구간 안의 서로 다른 sender 전부(v0.6 251개, v0.7 2,571개, v0.8 577개)의 코드를 조회해 분류했습니다.

| 분류 | v0.6 | v0.7 | v0.8 |
|---|---|---|---|
| EIP-7702로 위임된 EOA | 155 (61.8%) | 2,363 (91.9%) | 575 (99.7%) |
| 컨트랙트 계정(클론 포함) | 96 (38.2%) | 207 (8.1%) | 2 (0.3%) |
| 코드 없음 | 0 | 1 (0.04%) | 0 |

7702로 위임된 계정은 코드가 `0xef0100` 뒤에 20바이트 주소로 되어 있어서 구분됩니다. 이 주소가 위임 대상 구현체이고, 가장 많이 쓰인 구현체는 검증된 소스의 컨트랙트 이름과 작성자 표기로 확인했습니다.

| 버전 | 위임 대상 구현체 | 규모 |
|---|---|---|
| v0.6 | `EIP7702Proxy` (Coinbase 표기) | sender 155개, 405건 중 251건(62.0%) |
| v0.7 | `Biz` (회사 표기 없는 구현) | sender 1,649개, 3,769건 중 2,199건(58.3%) |
| v0.7 | `SemiModularAccount7702` (Alchemy 표기, 배포 주소 2개 합산) | sender 419개, 742건(19.7%) |
| v0.7 | `Kernel` | sender 287개, 410건(10.9%) |
| v0.8 | `Simple7702Account` | sender 577개 중 451개(78.2%) |
| v0.8 | `TokenPocketStatelessDelegator` | sender 75개 |

v0.7에서는 위 세 구현체가 3,351건(88.9%)을 차지합니다. v0.8의 나머지는 `CaliburEntry`(27개)와 `TokenPocketSimple7702Account`(20개) 등이었습니다. 컨트랙트 이름은 탐색기에 검증된 소스에 적힌 값이고, 제품 이름과 반드시 같지는 않습니다.

이 분류는 UserOperation이 실행된 시점이 아니라 조회 당시의 코드를 본 것이라, 위임을 바꾸거나 취소한 계정이 있으면 달라질 수 있습니다. 그래서 v0.7 구간의 sender 150개를 무작위로 뽑아 UserOperation이 실행된 블록 시점의 코드와 조회 당시의 코드를 비교했습니다. 시점 코드는 과거 상태를 제공하는 RPC에서 읽었고, 150개 모두 분류가 같았습니다(7702 위임 139개, 컨트랙트 11개). v0.6과 v0.8은 이 비교를 하지 않았습니다.

이 구간의 4337 물량은 새 컨트랙트 계정을 배포해 쓰는 사용자보다 기존 EOA에 7702로 코드를 위임해 EntryPoint를 쓰는 사용자가 훨씬 많았습니다. 4337이 "EOA 없이도 쓸 수 있는 계정 추상화"로 출발했지만, 조회 당시의 메인넷에서는 7702와 결합한 형태가 주류로 보입니다. 3시간 남짓의 구간 하나에서 본 모습이라 일반화는 조심해야 합니다.

로그에서 샘플 트랜잭션도 열어 봤습니다. 블록 26,421,015번의 트랜잭션 `0x62890316ef50fc2562ca8ba0ac0b21086d16a5df369cdc08d6ab0b60413b6d8d`는 v0.6 EntryPoint로, 블록 26,421,010번의 `0x2e1cb35672fad280651ed4835186f62dfab8085684ef2f5cbaab93507d6555e4`는 v0.7 EntryPoint로 가는 트랜잭션이었습니다. 둘 다 타입이 0x2, 곧 EIP-1559 트랜잭션입니다. [EIP-1559 글](/posts/eip-1559-fee-market/)에서 본 구조 위에 4337이 얹혀 있다는 사실이 여기서 확인됩니다.

## 계정 컨트랙트 맛보기

EOA 한 개를 소유자로 두는 가장 단순한 계정은 이런 모양입니다. 학습용 축약이라 감사받은 코드가 아닙니다. 실제로 쓸 때는 eth-infinitism 구현이나 Safe 같은 검증된 계정을 가져오는 편이 안전합니다. solc 0.8.26, OpenZeppelin Contracts 5.6.1, `@account-abstraction/contracts` 0.7.0 조합에서 컴파일되는 것까지는 확인했습니다. 배포하거나 EntryPoint로 UserOperation을 실제로 실행해 보지는 못했습니다. 그러려면 번들러와 EntryPoint가 갖춰진 테스트 환경(로컬 노드나 테스트넷)과 가스를 낼 계정이 필요한데, 이번 작업에서는 그 환경을 만들지 않았습니다.

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

## 한계와 주의할 점

가스 부담이 있습니다. UserOperation은 EOA 트랜잭션 하나로 끝나는 일에 검증과 실행, 예치금 정산 단계를 더하므로 같은 동작이라도 더 들 수밖에 없습니다. 다만 그 차이를 수치로 재 보지는 못했습니다. 같은 동작(예: USDC 전송)을 EOA와 4337 계정에서 같은 조건으로 실행해 가스를 비교해야 하는데, 이는 계정 배포와 실제 트랜잭션 전송이 필요합니다. 로그에서 가스 사용량을 뽑아 비교하는 방법은 호출 내용, Paymaster 유무, 계정 구현이 제각각이라 같은 조건이 되지 않습니다.

번들러가 새로운 신뢰 지점입니다. 검증이 환경에 따라 결과가 달라지는 UserOperation을 받아 주면 번들러가 가스비를 잃을 수 있어서, 검증 단계에서 접근할 수 있는 저장소와 opcode를 제한하는 규칙이 별도로 정해져 있습니다. 규칙을 지키는 번들러끼리만 공용 멤풀을 공유할 수 있고, 이 규칙은 EntryPoint 코드 바깥에 있습니다.

EIP-7702와의 관계도 짚어 둘 부분입니다. EOA에 컨트랙트 코드를 위임할 수 있게 한 EIP-7702가 들어온 뒤, 이 EIP의 문서도 7702 계정을 `UserOperation`으로 다루는 방법을 명시하고 있습니다. [EIP-1559 글](/posts/eip-1559-fee-market/)의 표본에서 타입 0x4 트랜잭션이 최근 10개 블록의 1.2%였던 것과 위의 sender 분류를 함께 보면, 두 흐름은 경쟁하기보다 섞여 쓰이고 있습니다.

## 정리

ERC-4337은 합의 계층을 바꾸지 않고, `UserOperation`, 번들러, EntryPoint라는 상위 인프라로 계정 추상화를 구현했습니다. 메인넷에서 EntryPoint v0.6부터 v0.9까지 네 버전을 확인했고, 3시간 남짓의 구간에서 5,111건의 UserOperation이 처리되었습니다. v0.7에서는 4건 중 3건 가까이를 Paymaster가 대신 부담했고 그 대부분은 주소 두 개가 맡았으며, sender는 세 버전 모두 대부분 7702로 위임된 EOA였습니다. 다음 글에서는 컨트랙트를 업그레이드 가능하게 만드는 프록시의 저장 위치 표준, [EIP-1967](/posts/eip-1967-proxy-slots/)을 다룹니다.

참고: [ERC-4337 원문](https://eips.ethereum.org/EIPS/eip-4337), [EIP-7702 원문](https://eips.ethereum.org/EIPS/eip-7702)
