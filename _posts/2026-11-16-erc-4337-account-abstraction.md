---
title: "ERC-4337, 합의 계층을 건드리지 않는 계정 추상화"
description: 합의 계층을 바꾸지 않는 계정 추상화 ERC-4337의 구성요소를 정리하고, 메인넷 EntryPoint의 UserOperation 로그와 sender 계정 형태를 집계했습니다.
date: 2026-11-16 13:00:00 +0900
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

EntryPoint는 버전별로 주소가 따로 있습니다. 두 곳에 코드가 있음을 확인했습니다.

| 버전 | 주소 | 배포된 코드 크기 |
|---|---|---|
| v0.6 | `0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789` | 23,689 바이트 |
| v0.7 | `0x0000000071727De22E5E9d8BAf0edAc6f37da032` | 16,035 바이트 |

`UserOperationEvent` 로그를 세어 실제 사용량도 봤습니다. 이 이벤트는 UserOperation 하나가 처리될 때마다 EntryPoint가 냅니다. 블록 26,421,009번부터 26,422,009번까지 1,001개 블록, 시간으로는 3시간 남짓입니다.

| 지표 | v0.6 | v0.7 |
|---|---|---|
| UserOperation 수 | 405 | 3,769 |
| Paymaster가 가스를 낸 수 | 235 (58.0%) | 2,810 (74.6%) |
| 실행에 성공한 수 | 400 (98.8%) | 3,746 (99.4%) |

두 버전을 합치면 4,174건이고, 그중 90.3%가 v0.7로 들어왔습니다. 짧은 구간이라 추세로 읽을 수는 없습니다. 같은 방식으로 블록 26,423,000번부터 26,424,000번까지 다시 세었더니 v0.6이 510건(Paymaster 247건), v0.7이 2,425건(Paymaster 1,811건)이었습니다. 건수는 구간마다 꽤 달라도 v0.7에서 Paymaster가 가스를 낸 비율은 74.6%와 74.7%로 거의 같았습니다.

구간 안을 조금 더 들여다보면 세 가지가 보입니다.

첫째는 Paymaster가 소수에게 몰려 있다는 점입니다. 첫 구간에서 v0.7의 Paymaster는 서로 다른 주소 11개뿐이었고, 그중 주소 `0x777777777777aec03fd955926dbf81597e66834c` 하나가 2,262건(60.0%), 두 번째 주소가 503건(13.3%)을 맡았습니다. 상위 둘이 73.3%입니다. v0.6도 주소 6개 중 1위가 151건(37.3%)이었습니다. 이 주소들이 어떤 서비스인지는 확인하지 않았습니다.

둘째는 묶음의 효과가 작다는 점입니다. v0.7은 번들 트랜잭션 3,498개에 UserOperation 3,769건이 담겨 트랜잭션당 평균 1.08건이었고, v0.6은 402개에 405건이었습니다. 번들러가 여러 건을 모아 가스를 나누는 모습은 이 구간에서는 거의 보이지 않았습니다.

셋째는 sender의 정체입니다. 구간 안의 서로 다른 sender 중 v0.6의 251개는 전부, v0.7의 2,571개는 무작위로 200개를 골라 지금 시점의 코드를 조회했습니다.

| 분류 | v0.6 (251개 전수) | v0.7 (200개 표본) |
|---|---|---|
| 일반 컨트랙트 계정 | 96 (38.2%) | 21 (10.5%) |
| EIP-7702로 위임된 EOA | 155 (61.8%) | 178 (89.0%) |
| 코드 없음 | 0 | 1 (0.5%) |

7702로 위임된 계정은 코드가 `0xef0100` 뒤에 20바이트 주소로 되어 있어서 구분됩니다. 이 분류는 UserOperation이 실행된 시점이 아니라 조회한 지금 시점의 코드를 본 것이고, 위임을 취소한 계정은 코드 없음으로 잡힙니다. 그래도 방향은 분명합니다. 이 구간의 4337 물량은 새 컨트랙트 계정을 배포해 쓰는 사용자보다 기존 EOA에 7702로 코드를 위임해 4337 EntryPoint를 쓰는 사용자 쪽이 훨씬 많았습니다. 4337이 "EOA 없이도 쓸 수 있는 계정 추상화"로 출발했지만, 지금의 메인넷에서는 7702와 결합한 형태가 주류가 된 것으로 보입니다.

로그에서 샘플 트랜잭션도 열어 봤습니다. 블록 26,421,015번의 트랜잭션 `0x62890316ef50fc2562ca8ba0ac0b21086d16a5df369cdc08d6ab0b60413b6d8d`는 v0.6 EntryPoint로, 블록 26,421,010번의 `0x2e1cb35672fad280651ed4835186f62dfab8085684ef2f5cbaab93507d6555e4`는 v0.7 EntryPoint로 가는 트랜잭션이었습니다. 둘 다 타입이 0x2, 곧 EIP-1559 트랜잭션입니다. [EIP-1559 글](/posts/eip-1559-fee-market/)에서 본 구조 위에 4337이 얹혀 있다는 사실이 여기서 확인됩니다.

어떤 지갑 제품이 이 물량의 얼마를 차지하는지는 확인하지 못했습니다. sender가 쓰는 구현 컨트랙트나 Paymaster 주소의 운영 주체를 하나씩 대조해야 하는 일이라 이번 범위를 넘겼습니다.

## 계정 컨트랙트 맛보기

EOA 한 개를 소유자로 두는 가장 단순한 계정은 이런 모양입니다. 학습용 축약이라 감사받은 코드가 아닙니다. 실제로 쓸 때는 eth-infinitism 구현이나 Safe 같은 검증된 계정을 가져오는 편이 안전합니다.

```solidity
import {IAccount} from "account-abstraction/contracts/interfaces/IAccount.sol";
import {PackedUserOperation} from "account-abstraction/contracts/interfaces/PackedUserOperation.sol";
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

가스 부담이 있습니다. UserOperation은 EOA 트랜잭션 하나로 끝나는 일에 검증과 실행, 예치금 정산 단계를 더하므로 같은 동작이라도 더 들 수밖에 없습니다. 이번 글에서는 그 차이를 수치로 재 보지 않았습니다.

번들러가 새로운 신뢰 지점입니다. 검증이 환경에 따라 결과가 달라지는 UserOperation을 받아 주면 번들러가 가스비를 잃을 수 있어서, 검증 단계에서 접근할 수 있는 저장소와 opcode를 제한하는 규칙이 별도로 정해져 있습니다. 규칙을 지키는 번들러끼리만 공용 멤풀을 공유할 수 있고, 이 규칙은 EntryPoint 코드 바깥에 있습니다.

EIP-7702와의 관계도 짚어 둘 부분입니다. EOA에 컨트랙트 코드를 위임할 수 있게 한 EIP-7702가 들어온 뒤, 이 EIP의 문서도 7702 계정을 `UserOperation`으로 다루는 방법을 명시하고 있습니다. [EIP-1559 글](/posts/eip-1559-fee-market/)의 표본에서 타입 0x4 트랜잭션이 최근 10개 블록의 1.2%였던 것과 위의 sender 분류를 함께 보면, 두 흐름은 경쟁하기보다 섞여 쓰이고 있습니다.

## 정리

ERC-4337은 합의 계층을 바꾸지 않고, `UserOperation`, 번들러, EntryPoint라는 상위 인프라로 계정 추상화를 구현했습니다. 메인넷에서 두 EntryPoint 버전을 모두 확인했고, 3시간 남짓의 구간에서 4,174건의 UserOperation이 처리되었습니다. v0.7에서는 4건 중 3건 가까이를 Paymaster가 대신 부담했고 그 대부분은 주소 두 개가 맡았으며, sender는 대부분 7702로 위임된 EOA였습니다. 다음 글에서는 컨트랙트를 업그레이드 가능하게 만드는 프록시의 저장 위치 표준, [EIP-1967](/posts/eip-1967-proxy-slots/)을 다룹니다.

참고: [ERC-4337 원문](https://eips.ethereum.org/EIPS/eip-4337), [EIP-7702 원문](https://eips.ethereum.org/EIPS/eip-7702)
