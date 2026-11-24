---
title: "EIP-1967, 프록시가 구현 주소를 저장하는 표준 슬롯"
description: 업그레이드 가능한 컨트랙트의 프록시가 구현 주소를 저장하는 표준 위치 EIP-1967을 정리하고, Compound와 Aave의 슬롯을 읽어 USDC가 옛 방식을 쓴다는 점을 확인했습니다.
date: 2026-11-16 14:00:00 +0900
category: tech-docs
tags: [ethereum, erc, eip-1967, proxy, upgradeable]
---

배포된 스마트 컨트랙트의 코드는 고칠 수 없습니다. 그런데 Aave나 Compound 같은 프로토콜은 배포 뒤에도 로직을 바꿉니다. 이를 가능하게 하는 것이 프록시입니다. 사용자는 늘 같은 주소(프록시)와 대화하고, 프록시는 실제 일을 하는 다른 컨트랙트(구현)에 `delegatecall`로 일을 넘깁니다. 이때 프록시는 지금 어떤 구현에 일을 넘기는지, 곧 구현 주소를 저장소 어딘가에 적어 두어야 합니다. EIP-1967은 그 위치를 모두가 같은 곳으로 정하자는 표준입니다.

## 필요했던 이유

`delegatecall`로 부르면 구현의 코드가 프록시의 저장소를 읽고 씁니다. 이때 충돌이 생깁니다. 프록시가 구현 주소를 저장소 0번 슬롯에 두면, 구현 컨트랙트의 첫 번째 변수도 0번 슬롯을 써서 둘이 서로를 덮어씁니다.

그래서 업계에서는 컴파일러가 쓸 일이 없을 만큼 멀리 떨어진 슬롯에 구현 주소를 두기 시작했습니다. OpenZeppelin이 `keccak256("org.zeppelinos.proxy.implementation")`의 해시 값을 슬롯 번호로 쓴 것이 한 예입니다. 그런데 프로젝트마다 이름이 달랐습니다. 블록 익스플로러는 어떤 컨트랙트가 프록시인지, 진짜 로직이 어디인지 알아낼 일반적인 방법이 없었습니다. 익스플로러가 구현의 ABI를 보여 주려면 구현 주소를 알아야 합니다.

EIP-1967은 슬롯 위치를 표준으로 정해서 이 문제를 풉니다. 익스플로러가 정해진 슬롯만 읽으면 프록시인지, 구현이 어디인지 알 수 있고, 구현 컨트랙트도 자신이 프록시 뒤에 있다는 것을 알고 업그레이드 기능을 넣을 수 있습니다.

## 표준 슬롯

| 용도 | 슬롯 | 만드는 방법 |
|---|---|---|
| 구현 주소 | `0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc` | `keccak256('eip1967.proxy.implementation') - 1` |
| 관리자 주소 | `0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103` | `keccak256('eip1967.proxy.admin') - 1` |
| 비콘 주소 | `0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50` | `keccak256('eip1967.proxy.beacon') - 1` |

세 값은 keccak256을 직접 계산해 1을 뺀 결과와 일치했습니다. 1을 빼는 이유는 이렇습니다. 해시 값을 그대로 쓰면 그 값을 만든 입력이 알려지고, 공격자가 매핑이나 배열의 키를 골라 같은 슬롯을 가리키게 만들 여지가 생깁니다. 1을 빼면 이 슬롯의 번호를 만들어 내는 입력을 아무도 모르게 되어 충돌을 일부러 만들 수 없습니다.

비콘은 구현 주소를 한곳에 모아 두는 컨트랙트입니다. 프록시가 여러 개일 때 비콘 하나만 바꾸면 전부 업그레이드됩니다. 슬롯이 바뀔 때는 `Upgraded`, `AdminChanged`, `BeaconUpgraded` 이벤트를 내도록 권고하고, 덕분에 모니터링 도구가 업그레이드를 바로 알아챌 수 있습니다.

## 메인넷 슬롯 확인

`eth_getStorageAt`으로 메인넷 컨트랙트의 표준 슬롯을 읽었습니다. 값은 모두 조회 당시의 최신 상태입니다.

| 컨트랙트 | 구현 슬롯 | 관리자 슬롯 |
|---|---|---|
| Compound III USDC (`0xc3d688B66703497DAA19211EEdff47f25384cdc3`) | `0x0b07565a8ef48170e15918b251ebd95109b23255` | `0x1ec63b5883c3481134fd50d5daebc83ecd2e8779` |
| Aave V3 Pool (`0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2`) | `0x4295fe69b3e978eb511e4558b4407ad871612fcb` | 비어 있음 |

Compound의 컨트랙트는 `name()`을 부르면 `Compound USDC`, `symbol()`은 `cUSDCv3`라고 답했습니다. Aave는 풀 주소 공급자(`ADDRESSES_PROVIDER`)를 부르니 `0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e`가 나와서 Aave V3의 Pool 프록시로 판단했습니다. 두 구현 주소 모두 코드가 있었습니다.

관리자 슬롯이 어떻게 된 건지도 따라가 봤습니다.

- Aave의 관리자 슬롯이 비어 있는 이유는 검증된 소스에서 찾았습니다. 프록시 이름이 `InitializableImmutableAdminUpgradeabilityProxy`이고, 부모 컨트랙트에 `address internal immutable _admin;`이 선언되어 있습니다. 관리자 주소를 저장소가 아니라 배포할 때 코드에 박아 넣는 방식이라서 슬롯을 읽어도 0이 나옵니다. 표준이 모든 슬롯을 채우라고 강제하지는 않습니다.
- Compound의 관리자 슬롯 주소는 `CometProxyAdmin`이고, 이 컨트랙트의 `owner()`는 `Timelock`(`0x6d903f6003cca6255d85cca4d3b5e5146dc33925`)이었습니다. `Timelock`의 `delay()`는 172,800초, 곧 2일이고 `admin()`은 `CompoundGovernor` 구현을 쓰는 프록시였습니다. 업그레이드 권한이 지갑 하나가 아니라 거버넌스 컨트랙트와 2일의 대기를 거치는 구조입니다.

USDC(`0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48`)는 표준 슬롯을 쓰지 않았습니다. EIP-1967 문서는 Etherscan에서 프록시로 표시되는 예시로 USDC 주소를 듭니다. 그런데 표준 슬롯을 읽으니 구현과 관리자 슬롯이 모두 0이었습니다. 대신 ZeppelinOS 시절의 슬롯인 `keccak256("org.zeppelinos.proxy.implementation")` 값(`0x7050c9e0f4ca769c69bd3a8ef740bc37934f8e2c036e5a723fd8ee048ed3f8c3`)을 읽으니 `0x43506849d7c04f9138d1a2050bbf3a0c054402dd`가 나왔고 이 주소에는 코드가 있었습니다. 탐색기 기록으로 USDC 프록시는 2018년 8월 3일에 만들어졌고, EIP-1967은 2019년 4월 24일에 작성됐습니다(문서 머리말 기준). 표준보다 먼저 배포된 프록시라서 옛 슬롯을 씁니다. 이미 배포된 컨트랙트는 저장 위치를 바꿀 수 없어서, 도구가 오래된 프록시까지 다루려면 옛 슬롯도 함께 확인해야 합니다.

직접 읽어 보려면 Foundry의 `cast`가 간편합니다.

```bash
cast storage 0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2 \
  0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc \
  --rpc-url https://ethereum-rpc.publicnode.com
```

## 구현 예시

OpenZeppelin v5는 이 슬롯을 다루는 코드를 `ERC1967Utils`로 묶어 두었습니다. UUPS 방식의 구현 컨트랙트는 이렇게 씁니다. solc 0.8.26과 OpenZeppelin Contracts(upgradeable 포함) 5.6.1로 컴파일되는 것까지 확인했습니다.

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Initializable} from "@openzeppelin/contracts-upgradeable/proxy/utils/Initializable.sol";
import {UUPSUpgradeable} from "@openzeppelin/contracts-upgradeable/proxy/utils/UUPSUpgradeable.sol";
import {OwnableUpgradeable} from "@openzeppelin/contracts-upgradeable/access/OwnableUpgradeable.sol";

contract CounterV1 is Initializable, OwnableUpgradeable, UUPSUpgradeable {
    uint256 public count;

    /// @custom:oz-upgrades-unsafe-allow constructor
    constructor() { _disableInitializers(); }

    function initialize(address owner_) external initializer {
        __Ownable_init(owner_);
    }

    function inc() external { count++; }

    function _authorizeUpgrade(address) internal override onlyOwner {}
}
```

배포는 이 컨트랙트를 먼저 올리고, `ERC1967Proxy`를 `(구현 주소, initialize 호출 데이터)`로 올리는 순서입니다. 그러면 구현 주소가 위 표준 슬롯에 기록되고 `Upgraded` 이벤트가 나옵니다.

## 조심할 점

1. 표준 슬롯은 프록시 자신의 변수만 지켜 줍니다. V1에서 V2로 올릴 때 구현의 상태 변수 순서나 타입을 바꾸면 저장된 데이터가 엉뚱하게 읽힙니다. 변수는 뒤에 추가하는 식으로만 늘려야 합니다.
2. 구현 컨트랙트가 초기화되지 않은 채로 배포되면 누군가 먼저 `initialize`를 불러 주인이 될 수 있습니다. 위 코드의 `_disableInitializers()`가 이를 막습니다.
3. 업그레이드 권한은 신뢰의 문제입니다. 관리자가 EOA 하나라면 그 키 하나가 프로토콜을 바꿀 수 있습니다. Compound에서 한 것처럼 관리자 슬롯의 주소가 타임락이나 멀티시그인지 따라가 보는 것이 좋은 점검입니다. Aave처럼 관리자를 `immutable`로 두는 프록시는 슬롯만으로는 알 수 없어서 소스도 같이 봐야 합니다.

## 확인하지 못한 것

- 위 컨트랙트를 배포하거나 V2로 업그레이드해 보지는 못했습니다. 테스트 네트워크에서 프록시를 올려야 하는데 준비하지 않았습니다.
- Aave 프록시의 관리자 주소가 누구인지는 코드 안의 값을 디코딩해야 알 수 있는데 하지 않았습니다.
- Compound 거버넌스의 투표 규칙과 제안 이력은 확인하지 않았습니다.

---

참고: [EIP-1967 원문](https://eips.ethereum.org/EIPS/eip-1967)
