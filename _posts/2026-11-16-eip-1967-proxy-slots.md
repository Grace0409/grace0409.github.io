---
title: "EIP-1967, 프록시가 구현 주소를 적어 두는 약속된 자리"
description: 업그레이드 가능한 프록시가 구현 주소를 저장하는 표준 슬롯 EIP-1967을 정리하고, Compound와 Aave의 슬롯을 읽어 USDC가 옛 슬롯을 쓰는 사실을 확인했습니다.
date: 2026-11-16 14:00:00 +0900
category: tech-docs
tags: [ethereum, erc, eip-1967, proxy, upgradeable]
---

배포된 스마트 컨트랙트의 코드는 고칠 수 없습니다. 그런데 Aave나 Compound 같은 프로토콜은 배포 후에도 로직을 바꿉니다. 비결은 사용자가 상호작용하는 주소에는 얇은 프록시를 두고, 실제 로직은 다른 컨트랙트에 둔 채 `delegatecall`로 빌려 쓰는 구조입니다. 이때 프록시는 "로직이 어디 있는지"를 저장소 어딘가에 적어 두어야 합니다. EIP-1967은 그 어딘가를 모두가 같은 곳으로 정하자는 약속입니다.

이 글에서는 이 약속이 왜 필요했는지, 슬롯 값이 어떻게 정해졌는지, 그리고 메인넷 컨트랙트 몇 개의 슬롯을 직접 읽어 본 결과를 정리합니다. 읽다 보면 USDC에서 의외의 사실이 하나 나옵니다 :)

## 등장 배경

프록시는 `delegatecall`을 쓰기 때문에, 로직 컨트랙트의 코드는 프록시의 저장소를 읽고 씁니다. 여기서 충돌 문제가 생깁니다. 프록시가 구현 주소를 슬롯 0에 두면, 로직 컨트랙트의 첫 번째 상태 변수도 슬롯 0을 씁니다. 둘이 서로를 덮어씁니다.

이미 업계에서는 이 문제를 피하려고 컴파일러가 절대 할당하지 않을 법한 슬롯에 구현 주소를 두는 방식을 쓰고 있었습니다. OpenZeppelin이 `keccak256("org.zeppelinos.proxy.implementation")` 같은 해시 값을 슬롯으로 쓴 것이 그 예입니다. 문제는 프로젝트마다 슬롯 이름이 달랐다는 점입니다. 블록 익스플로러는 어떤 컨트랙트가 프록시인지, 로직이 어디인지 알아낼 일반적인 방법이 없었습니다. 사용자가 보고 싶은 것은 프록시의 빈 ABI가 아니라 로직의 ABI인데도 말입니다.

EIP-1967은 슬롯을 표준화해서 이 문제를 풉니다. 문서의 동기도 정확히 이 부분입니다. 익스플로러가 정해진 슬롯만 보면 프록시 여부와 로직 주소를 알 수 있고, 로직 컨트랙트도 자신이 프록시 뒤에 있음을 알고 업그레이드 로직을 넣을 수 있습니다.

## 표준 슬롯

세 가지 슬롯이 정의되어 있습니다.

| 용도 | 슬롯 | 도출 방법 |
|---|---|---|
| 구현 주소 | `0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc` | `keccak256('eip1967.proxy.implementation') - 1` |
| 관리자 주소 | `0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103` | `keccak256('eip1967.proxy.admin') - 1` |
| 비콘 주소 | `0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50` | `keccak256('eip1967.proxy.beacon') - 1` |

세 값은 표의 도출 방법대로 keccak256을 직접 계산해 1을 뺀 결과와 일치했습니다. 해시에서 1을 빼는 데에는 이유가 있습니다. 해시값을 그대로 쓰면 그 값이 어떤 입력의 해시인지 알려지게 되고, 공격자가 매핑이나 배열의 키를 골라 같은 슬롯을 가리키게 만들 여지가 생깁니다. 1을 빼면 이 슬롯에 해당하는 원상(preimage)을 아무도 모르게 되어 충돌을 만들어 낼 수 없습니다.

비콘은 구현 주소를 한곳에 모아 두는 컨트랙트입니다. 프록시가 여러 개일 때 비콘 하나의 주소만 바꾸면 모두 업그레이드됩니다. 비콘은 `implementation()` 함수를 구현해야 합니다.

슬롯이 바뀔 때는 이벤트를 내도록 권고합니다. `Upgraded(address indexed implementation)`, `AdminChanged(address previousAdmin, address newAdmin)`, `BeaconUpgraded(address indexed beacon)`입니다. 초기화도 0에서 첫 값으로의 변경이므로 이벤트 대상입니다. 이벤트가 있어야 모니터링 도구가 업그레이드를 즉시 알아챌 수 있기 때문입니다.

## 메인넷에서 확인하기

`eth_getStorageAt`으로 메인넷 컨트랙트 몇 개의 표준 슬롯을 읽었습니다. 값은 모두 조회 당시의 최신 상태입니다.

| 컨트랙트 | 구현 슬롯 | 관리자 슬롯 |
|---|---|---|
| Compound III USDC (`0xc3d688B66703497DAA19211EEdff47f25384cdc3`) | `0x0b07565a8ef48170e15918b251ebd95109b23255` | `0x1ec63b5883c3481134fd50d5daebc83ecd2e8779` |
| Aave V3 Pool (`0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2`) | `0x4295fe69b3e978eb511e4558b4407ad871612fcb` | 비어 있음 |

Compound의 컨트랙트는 `name()`을 호출하면 `Compound USDC`, `symbol()`은 `cUSDCv3`라고 답했습니다. Aave 쪽은 풀 주소 공급자(`ADDRESSES_PROVIDER`) 호출 결과가 `0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e`로 나와 Aave V3의 Pool 프록시라고 판단했습니다. 두 구현 주소 모두 배포된 코드가 있음을 확인했습니다(각각 18,599, 21,814 바이트).

Aave의 관리자 슬롯이 비어 있는 이유는 검증된 소스에서 확인했습니다. 탐색기에 올라온 프록시 컨트랙트 이름은 `InitializableImmutableAdminUpgradeabilityProxy`이고, 부모 컨트랙트 `BaseImmutableAdminUpgradeabilityProxy.sol`에 `address internal immutable _admin;`이 선언되어 있습니다. 관리자 주소를 저장소 슬롯이 아니라 배포 때 코드에 박아 넣는 `immutable`로 보관하는 방식입니다. 그래서 슬롯을 읽어도 0이 나옵니다. 표준은 슬롯의 위치만 정할 뿐 모든 프록시가 모든 슬롯을 채우도록 강제하지 않는다는 점이 여기서도 보입니다. 이 관리자 주소가 누구인지는 코드에 들어 있는 값을 디코딩해야 알 수 있는데, 이번에는 하지 않았습니다.

Compound 쪽은 관리자 슬롯의 주소(`0x1ec63b5883c3481134fd50d5daebc83ecd2e8779`)를 따라가 봤습니다. 이 주소는 탐색기에 `CometProxyAdmin`으로 검증되어 있고, `owner()`를 호출하면 `Timelock` 컨트랙트(`0x6d903f6003cca6255d85cca4d3b5e5146dc33925`)를 돌려줍니다. 이 Timelock의 `delay()`는 172,800초, 곧 2일이었고, `admin()`은 구현이 `CompoundGovernor`로 표시되는 프록시(`0x309a862bbc1a00e45506cb8a802d1ff10004c8c0`)였습니다. 업그레이드 권한이 지갑 하나가 아니라 거버넌스 컨트랙트와 2일의 지연을 거치게 되어 있다는 뜻입니다. 거버넌스의 투표 규칙과 제안 이력까지는 확인하지 않았습니다. 구현 컨트랙트의 이름은 탐색기 기준으로 Compound가 `CometWithExtendedAssetList`, Aave가 `PoolInstance`였습니다.

반전이 하나 있습니다. EIP-1967 문서는 Etherscan에서 프록시로 표시되는 예시로 USDC(`0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48`)를 듭니다. 같은 방식으로 USDC의 표준 슬롯을 읽었더니 구현과 관리자 슬롯이 둘 다 0이었습니다. 대신 ZeppelinOS 시절의 슬롯인 `keccak256("org.zeppelinos.proxy.implementation")` 값(`0x7050c9e0f4ca769c69bd3a8ef740bc37934f8e2c036e5a723fd8ee048ed3f8c3`)을 읽으니 `0x43506849d7c04f9138d1a2050bbf3a0c054402dd`가 나왔고, 이 주소에는 23,464 바이트의 코드가 있었습니다. USDC 프록시는 표준이 나오기 전에 배포된 것이어서 옛 슬롯을 쓰고, 익스플로러는 이 옛 방식도 알아본다는 이야기가 됩니다.

표준은 앞으로 배포될 컨트랙트에 적용될 뿐, 이미 배포된 컨트랙트의 저장 위치는 바꿀 수 없다는 사실이 여기서 드러납니다. 도구가 표준 슬롯만 보면 되는 것도 아니어서, 오래된 프록시까지 다루려면 알려진 옛 슬롯을 함께 확인해야 합니다.

직접 읽어 보려면 Foundry의 `cast`가 간편합니다.

```bash
cast storage 0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2 \
  0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc \
  --rpc-url https://ethereum-rpc.publicnode.com
```

ethers v6라면 `await provider.getStorage(proxy, slot)`이고, 반환값 마지막 20바이트가 주소입니다.

## 구현해 보기

OpenZeppelin v5는 슬롯 처리를 `ERC1967Utils`로 묶어 두었습니다. UUPS 방식의 로직 컨트랙트 예입니다.

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

위 코드는 solc 0.8.26과 OpenZeppelin Contracts(upgradeable 포함) 5.6.1로 컴파일되는 것을 확인했습니다. 배포나 실제 업그레이드 시나리오는 실행해 보지 않았습니다. 테스트 네트워크에서 프록시를 올리고 V2로 바꿔 보는 과정이 필요한데 이번에 하지 않았습니다.

배포는 이 컨트랙트를 먼저 올리고, `ERC1967Proxy`를 `(구현 주소, initialize 호출 데이터)`로 올리는 순서입니다. 그러면 구현 주소가 위 표준 슬롯에 기록되고 `Upgraded` 이벤트가 발생합니다.

## 한계와 주의할 점

표준 슬롯은 프록시 자신의 변수만 지킬 뿐, 로직 컨트랙트끼리의 충돌은 막지 못합니다. V1에서 V2로 업그레이드할 때 상태 변수의 순서나 타입을 바꾸면 저장된 데이터가 엉뚱하게 해석됩니다. 변수는 뒤에 추가하는 식으로만 늘려야 합니다.

구현 컨트랙트 자체가 초기화되지 않은 채 배포되면 누군가 먼저 `initialize`를 호출해 소유자가 될 수 있습니다. 위 예시의 `_disableInitializers()`가 이를 막습니다.

업그레이드 권한은 신뢰의 문제입니다. 관리자 슬롯의 주소가 EOA 하나라면, 그 키 하나가 프로토콜 전체를 바꿀 수 있습니다. 위에서 Compound에서 한 것처럼 관리자 슬롯을 읽고 그 주소가 타임락이나 멀티시그 컨트랙트인지 따라가 보는 것이 프로토콜을 쓰기 전의 좋은 점검입니다. Aave처럼 관리자를 `immutable`로 두는 프록시는 슬롯만으로는 알 수 없어서 소스를 같이 봐야 합니다. `Upgraded` 이벤트를 구독해 두면 업그레이드가 일어난 순간을 알 수 있습니다.

## 정리

EIP-1967은 "구현 주소를 어디에 두는가"라는 사소해 보이는 선택을 표준으로 묶어, 충돌을 막고 익스플로러와 도구가 일관되게 프록시를 읽게 만들었습니다. Compound와 Aave의 프록시에서 구현 주소를 직접 읽었고, USDC가 표준 이전의 슬롯을 쓴다는 사실도 확인했습니다. 업그레이드 가능한 컨트랙트를 쓸 때는 구현 슬롯과 관리자 슬롯을 읽어 지금 어떤 코드가 돌고 있고 누가 그것을 바꿀 수 있는지 먼저 확인해 보세요.

참고: [EIP-1967 원문](https://eips.ethereum.org/EIPS/eip-1967)
