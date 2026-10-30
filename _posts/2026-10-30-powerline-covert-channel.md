---
title: "에어갭을 넘는 전원선 은닉 채널, 탐지하고 차단하기"
description: CISC-S'25 발표와 제8회 부채널 정보분석 경진대회 회장상으로 이어진 전원선 변조 공격 방어 연구입니다.
date: 2026-10-30 22:50:00 +0900
category: paper-conference
tags: [side-channel, air-gap, covert-channel, award]
---

<div class="paper-card">
  <span class="paper-venue">CISC-S'25 · Gyeongju · 2025.06</span>
  <b>에어갭 환경에서 전원선 변조 기반 암묵적 채널 공격에 대한 적응형 방어 시스템</b>
  <span class="paper-authors"><u>김가영</u>, 박나은, 이일구</span>
</div>

<div class="paper-card">
  <span class="paper-venue">제8회 부채널 정보분석 경진대회 · 2025.07</span>
  <b>전원선 변조 공격의 실시간 주기 패턴 탐지 및 적응형 노이즈 차단 시스템</b>
  <span class="paper-authors"><u>김가영</u>, 박나은, 이일구</span>
  <span class="paper-badges"><i class="gold">🏆 한국정보보호학회 회장상</i></span>
</div>

## 어떤 공격인가

에어갭(air-gap) 환경은 외부 네트워크와 물리적으로 분리되어 있지만, 악성코드가 **전원선의 전력 소비 패턴을 변조**하면 그 신호를 통해 정보를 몰래 밖으로 내보낼 수 있습니다. 네트워크가 끊겨 있어도 전기는 연결되어 있으니까요.

## 어떻게 막았나

- **탐지** — 변조 신호에는 반복되는 주기 패턴이 생깁니다. 이를 **자기상관** 기반으로 실시간 탐지했습니다.
- **차단** — 탐지되면 **위상 반전 노이즈**를 주입해 은닉 신호를 상쇄합니다.

## 결과

- 수신 SNR **+19.3dB**
- 정보 유출량 **−13.8%**

같은 연구를 확장해 부채널 정보분석 경진대회에 나갔고, 대학생 부문 **한국정보보호학회 회장상**을 받았습니다. 첫 수상이라 특히 기억에 남는 연구예요.
