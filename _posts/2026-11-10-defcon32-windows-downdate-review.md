---
title: "[DEF CON 32 리뷰] Windows Downdate, 업데이트로 패치를 되돌리는 공격"
description: DEF CON 32 Windows Downdate 발표 리뷰입니다. Windows Update의 작업 목록을 바꿔치기해 최신 상태로 보이는 시스템에 이미 고쳐진 취약점을 되살리는 공격과 VBS 우회 과정을 정리했습니다.
date: 2026-11-10 10:00:00 +0900
category: paper-conference
tags: [defcon, windows, downgrade-attack, vbs, conference-review]
---

<div class="paper-card">
  <span class="paper-venue">DEF CON 32, Las Vegas, 2024.08 (Black Hat USA 2024 동시 발표)</span>
  <b>Windows Downdate: Downgrade Attacks Using Windows Updates</b>
  <span class="paper-authors">Alon Leviev (SafeBreach)</span>
  <span class="paper-badges"><i class="plain">TALK REVIEW</i></span>
</div>

[YouTube 영상(35:18)](https://www.youtube.com/watch?v=HHmxuxQ7bE8) / [발표 슬라이드(PDF)](https://i.blackhat.com/BH-US-24/Presentations/REVISED_US24-Leviev-Windows-Downdate-Downgrade-Attacks-Using-Windows-Updates-Wednesday.pdf) / [GitHub: WindowsDowndate](https://github.com/SafeBreach-Labs/WindowsDowndate)

해외 보안 컨퍼런스 영상을 하나 골라 보고 정리해 보기로 했습니다. DEF CON 유튜브 채널을 둘러보다가 제목 하나에서 손이 멈췄습니다.

> Windows Downdate: Downgrade Attacks Using Windows Updates

업데이트로 다운그레이드를 한다니, 제목부터 말이 안 되는 것 같아서 바로 재생 버튼을 눌렀습니다. 다 보고 나니 말이 되는 게 더 무서웠습니다.

발표자는 자기소개에서 22살이고 독학으로 공부했으며, 보안 일을 하기 전에는 주짓수 선수로 세계 대회 타이틀을 땄다고 밝힙니다. 첫 1분부터 이미 범상치 않습니다.

## 한 줄 요약

윈도우가 스스로 "최신 상태입니다"라고 말하게 둔 채, 이미 고쳐진 취약점 수십 개를 다시 살려 내는 공격입니다.

## 출발점이 된 BlackLotus

연구의 시작은 BlackLotus UEFI 부트킷입니다. BlackLotus는 최신 패치가 적용된 Windows 11에서 Secure Boot를 우회해 화제가 됐는데, 새 제로데이를 쓴 게 아니었습니다. 서명은 정상이지만 취약한 옛날 부트 매니저로 바꿔치기한 뒤, 이미 알려진 취약점을 다시 공격했습니다.

발표자는 여기서 질문을 하나 던집니다. Secure Boot 말고 다른 구성 요소도 이렇게 되돌릴 수 있지 않을까? 서드파티 드라이버를 들고 오는 BYOVD(Bring Your Own Vulnerable Driver)처럼, 윈도우 자체의 옛날 버전을 들고 오는 "Bring Your Own Vulnerable Windows"를 만들겠다는 목표였습니다.

## 완벽한 다운그레이드의 조건

본론에 들어가기 전에 발표자는 "완벽한 다운그레이드"의 조건을 네 가지로 먼저 정의합니다.

1. 탐지 불가: EDR이 막지 못하도록 최대한 정상적인 방법으로 되돌린다.
2. 보이지 않음: 되돌린 뒤에도 시스템은 최신 상태로 보인다.
3. 지속성: 이후 업데이트가 다운그레이드를 덮어쓰지 못한다.
4. 복구 불가: 검사/복구 도구가 손상을 찾거나 고치지 못한다.

이 기준을 먼저 세워 두니 뒤에 나오는 기법마다 "이건 몇 번 조건을 위한 장치구나" 하고 따라가기 쉬웠습니다. 발표 구성에서 가장 마음에 든 부분입니다.

## Windows Update를 그대로 이용하는 방법

가장 정상적으로 보이는 파일 교체 경로는 결국 Windows Update 자신입니다. 발표에서 설명한 업데이트 흐름을 간단히 옮기면 이렇습니다.

1. 클라이언트가 업데이트 폴더를 넘기며 서버에 업데이트를 요청한다.
2. 서버가 업데이트 폴더의 무결성을 검증한다.
3. 검증이 끝난 파일을 클라이언트가 접근할 수 없는 폴더에 저장한다.
4. 수행할 작업 목록(`pending.xml`)도 같은 보호 폴더에 저장한다.
5. 재부팅할 때 이 목록대로 파일을 바꾼다.

업데이트 파일 쪽은 꽤 단단했습니다. 매니페스트와 메타데이터는 서명된 카탈로그 파일로 보호되고, 서명이 없는 델타 파일도 최종 해시가 매니페스트에 박혀 있어서 손댈 수 없습니다.

구멍은 작업 목록 쪽에 있었습니다. 재부팅을 여러 번 거치는 과정이라 목록의 위치가 레지스트리(`PoqexecCmdline`)에 저장되는데, 이 키에는 TrustedInstaller 보호가 걸려 있지 않았습니다. 관리자 권한만 있으면 작업 목록 경로를 내가 만든 `pending.xml`로 바꿀 수 있다는 뜻입니다.

```
관리자 권한의 공격자
  └─ PoqexecCmdline 값을 직접 만든 pending.xml 경로로 변경
       └─ 재부팅 시 TrustedInstaller가 그 목록을 실행
            └─ 최신 시스템 파일 자리에 옛날 파일이 하드링크로 들어감
```

검증은 목록이 만들어지기 전 단계에서 끝나기 때문에, 이미 검증된 것으로 간주되는 목록을 바꿔치기하면 무결성 검사를 전부 건너뛸 수 있습니다. 관리자에서 TrustedInstaller로 올라가는 수상한 권한 상승도 필요 없습니다. 위험한 작업은 Windows Update가 대신 해 줍니다.

지속성과 복구 불가 조건은 더 대담하게 해결했습니다. 업데이트를 처리하는 구성 요소와 무결성 검사/복구 도구가 디지털 서명 검증을 받지 않는다는 점을 이용해 둘 다 패치해 버립니다. 이후 업데이트는 빈 업데이트로 "설치 완료" 처리되고, 복구 도구는 손상을 찾지 못합니다.

## 데모 세 개

데모는 세 번 나오는데, 매번 같은 장면으로 시작하고 끝납니다. 업데이트 확인 화면에서 "최신 상태"를 보여 주고, 공격하고, 재부팅하고, 다시 "최신 상태"를 보여 줍니다. 이 장면이 반복될수록 섬뜩함이 커집니다.

- 11:40 무렵, AFD.sys 다운그레이드: 커널 드라이버 `afd.sys`를 패치 전 버전으로 되돌린 뒤 권한 상승 익스플로잇을 실행해 SYSTEM 권한을 얻습니다. 공격 전에는 같은 익스플로잇이 실패하는 것도 함께 보여 줍니다.
- 19:00 무렵, Credential Guard, PPL, Defender 동시 무력화: PPLFault 패치를 되돌리고, VBS를 꺼서 Credential Guard를 무력화하고, Defender 실행 파일을 망가뜨립니다. 마지막에 mimikatz로 원래 보호받아야 할 자격 증명이 그대로 뽑혀 나옵니다.
- 28:00 무렵, 하이퍼바이저 다운그레이드: Hyper-V 하이퍼바이저를 2년 전 버전으로 되돌립니다. VBS와 Credential Guard는 아무 일 없었다는 듯 옛날 하이퍼바이저 위에서 계속 돌아갑니다.

## 가장 놀랐던 부분: 검증에 실패하면 VBS 없이 부팅

VBS(Virtualization-Based Security)는 커널이 이미 뚫렸다고 가정하고 만든 기능입니다. 하이퍼바이저가 VTL 0(일반 모드)과 VTL 1(보안 모드)을 나누고, Credential Guard 같은 핵심 기능은 VTL 1에 둡니다. 관리자가 레지스트리로 VBS를 꺼 버리지 못하게 "UEFI lock"으로 설정을 UEFI 변수에 잠가 두고, 이걸 풀려면 부팅 중에 사용자가 물리적으로 승인해야 합니다.

발표자는 Secure Kernel이나 하이퍼바이저 파일을 서명 없는 파일로 바꾸면 복구 환경으로 빠질 거라고 예상했습니다. 실제로는 OS 로더가 VBS 파일 검증에 실패하면 VBS 없이 평소처럼 부팅했습니다. 파일 하나 망가뜨리는 것만으로 UEFI lock이 우회되는 셈입니다.

복잡한 공격 체인 사이에 이런 단순한 설계 결함이 끼어 있다는 게 이 발표에서 가장 오래 기억에 남았습니다. 보안 기능이 실패했을 때 "닫힌 상태"가 아니라 "열린 상태"로 넘어가면, 공격자는 기능을 뚫을 필요 없이 실패시키기만 하면 됩니다.

## 보안 경계를 넘는 다운그레이드

마이크로소프트 기준으로 관리자에서 커널로 가는 것은 보안 경계가 아닙니다. 대신 VTL 0에서 VTL 1로, 혹은 커널에서 하이퍼바이저로 가는 것은 명확한 보안 경계입니다. 발표 후반부는 이 경계를 다운그레이드로 넘을 수 있는지 하나씩 확인합니다.

| 대상 | 되살린 취약점 | 넘은 경계 |
| --- | --- | --- |
| Credential Guard (LsaIso) | CVE-2022-34709 | Ring 3 VTL 0 → Ring 3 VTL 1 |
| Secure Kernel | CVE-2021-27090 | Ring 3 VTL 0 → Ring 0 VTL 1 |
| Hyper-V 하이퍼바이저 | 2년 전 버전으로 되돌림 | Ring 3 VTL 0 → Ring -1 |

Secure Kernel은 커널 파일 하나만 되돌려서는 동작하지 않았고, 의존하는 모듈까지 함께 되돌려야 했다고 합니다. 세 대상 모두 버전 검사나 폐기(revocation) 같은 다운그레이드 방지 장치가 없었습니다. 발표자는 당장 익스플로잇까지 이어지지 않더라도 방지 장치가 없다는 사실 자체를 취약점으로 봤는데, 앞으로 패치되는 취약점이 전부 다시 쓸 수 있는 무기가 되기 때문입니다.

## 마지막 한 수: Windows.old

마지막으로 관리자 권한도 필요 없는 경로가 하나 나옵니다. 품질 업데이트 후 복원용으로 남는 `Windows.old` 폴더에 일반 사용자가 전체 권한을 갖고 있었습니다. 원래 폴더 이름을 바꾸고 공격자가 만든 `Windows.old`를 넣어 두면, 관리자가 복원을 실행하는 순간 공격자의 운영체제가 쓰입니다.

## 공개 이후

발표자는 2024년 2월 마이크로소프트에 제보했고, CVE-2024-21302와 CVE-2024-38202가 발급됐습니다. 대응은 한 번에 끝나지 않았습니다. 2024년 8월 발표 시점에는 CVE-2024-38202에 대한 패치가 아직 없었고, 10월이 되어서야 패치가 배포됐습니다. CVE-2024-21302 쪽은 마이크로소프트가 서명한 폐기 정책을 적용하는 방식이라 별도로 설정해야 하는 완화책에 가깝습니다. 지금 운영 중인 시스템이 있다면 MSRC의 두 CVE 항목을 직접 확인해 보는 편이 좋겠습니다.

탐지 측면에서는 Splunk 등에서 `PoqexecCmdline`, `PendingXmlIdentifier` 레지스트리 변경이나 WinSxS 밖에서 만들어진 `pending.xml`을 잡는 룰이 공개돼 있습니다.

## 좋았던 점

- 조건을 먼저 정의하고 하나씩 채워 가는 구성이라, 35분 동안 길을 잃지 않습니다.
- 데모가 "최신 상태 확인 → 공격 → 다시 최신 상태 확인"으로 반복돼 메시지가 머리에 박힙니다.
- 무엇이 보안 경계이고 무엇이 아닌지를 마이크로소프트 기준으로 짚어 주기 때문에, 연구 결과의 무게를 스스로 가늠해 볼 수 있습니다.

## 아쉬운 점

대부분의 공격이 관리자 권한을 전제로 합니다. 발표자도 이 점을 인정하고 "기본 계정이 관리자인 경우가 많다"는 이유를 들지만, 위협 모델을 처음 보는 사람에게는 와닿기 어려울 수 있습니다.

하이퍼바이저 부분은 특정 취약점을 직접 익스플로잇하지 않습니다. 2년 전 버전이면 고쳐진 하이퍼바이저 권한 상승 취약점이 하나쯤은 있을 거라는 논리인데, 앞의 두 사례보다 증명의 강도가 약하게 느껴졌습니다.

VTL, Secure Kernel, LsaIso 같은 배경 지식이 빠르게 지나갑니다. 윈도우 내부 구조가 처음이라면 슬라이드를 옆에 띄워 두고 보는 걸 추천합니다.

## 보고 나서 든 생각

"패치를 다 했으니 안전하다"는 말이 무엇을 근거로 하는지 다시 생각하게 됐습니다. 업데이트 기록과 버전 번호는 결국 시스템이 스스로 보고하는 값이고, 그 보고를 만드는 경로가 오염되면 의미가 없어집니다.

발표자가 마지막에 강조한 교훈도 기억해 두고 싶습니다. BlackLotus라는 실제 공격 사례는 이미 1년 전부터 공개돼 있었고, 그걸 한 단계만 일반화했더니 가상화 스택 전체가 영향을 받았습니다. 실제 공격이 나왔을 때 "그 취약점이 고쳐졌나"에서 멈추지 않고 "같은 원리가 또 어디에 통할까"를 묻는 습관이 연구자에게 필요하다는 이야기로 받아들였습니다.

윈도우 내부 구조나 리버싱에 관심이 있다면 꼭 한 번 보시길 추천합니다 :)

## 참고 자료

- [DEF CON 32 - Windows Downdate: Downgrade Attacks Using Windows Updates - Alon Leviev (YouTube)](https://www.youtube.com/watch?v=HHmxuxQ7bE8)
- [Black Hat USA 2024 발표 슬라이드 (PDF)](https://i.blackhat.com/BH-US-24/Presentations/REVISED_US24-Leviev-Windows-Downdate-Downgrade-Attacks-Using-Windows-Updates-Wednesday.pdf)
- [SafeBreach-Labs/WindowsDowndate (GitHub)](https://github.com/SafeBreach-Labs/WindowsDowndate)
- [Help Net Security: "Perfect" Windows downgrade attack turns fixed vulnerabilities into zero-days](https://www.helpnetsecurity.com/2024/08/08/windows-downgrade-attack/)
- [SecurityWeek: More Details Shared on Windows Downgrade Attacks After Microsoft Rolls Out Mitigations](https://www.securityweek.com/more-details-shared-on-windows-downgrade-attacks-after-microsoft-rolls-out-mitigations/)
- [Splunk Research: Windows Downdate Registry Activity](https://research.splunk.com/endpoint/d984fca1-ba3a-4f89-aa58-800e235fdf53)
