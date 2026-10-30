---
title: "동적 메모리 할당 보안 연구: 제안부터 KCI 저널까지"
description: 직접 제안한 메커니즘의 약점을 스스로 찾고, 막는 방법까지 만든 2025년 한 해의 연구 기록입니다.
date: 2026-03-01 10:00:00 +0900
category: paper-conference
tags: [system-security, dma, kci, award]
---

학부연구생이 되고 처음 잡은 주제예요. 내가 만든 시스템을 내가 공격해 보고, 다시 막았습니다. 그렇게 다섯 편이 이어졌어요.

## 1. 제안, CPP-DMA

<div class="paper-card">
  <span class="paper-venue">ASK 2025 (KIPS), 경북대학교, 2025.05.29~31</span>
  <b>콘텐츠 인기도 예측 기반의 동적 메모리 할당 메커니즘</b>
  <span class="paper-authors"><u>김가영</u>, 문정민, 박나은, 이일구</span>
</div>

콘텐츠 인기도를 예측해서 메모리를 미리 나눠 주는 방식이에요. 처리 시간이 30.3% 줄었습니다.

## 2. 공격, 취약점 분석

<div class="paper-card">
  <span class="paper-venue">WISA 2025, Jeju, 2025.08.20~22</span>
  <b>Security Vulnerability Analysis of Real-time Content Popularity Prediction-based Dynamic Memory Allocation System</b>
  <span class="paper-authors"><u>Ga-Yeong Kim</u>, Na-Eun Park, Il-Gu Lee</span>
  <span class="paper-badges"><i>POSTER</i></span>
</div>

예측에 기대는 구조라는 게 곧 약점이었어요. 악의적인 트래픽으로 예측을 흔들면 할당이 틀어집니다. 이 구조적인 취약점을 직접 찾아서 분석했어요.

## 3. 방어, ADE-DMA

<div class="paper-card">
  <span class="paper-venue">한국융합보안학회 2025 추계, 2025.11.07</span>
  <b>ADE-DMA: 이상 감지 및 입력 데이터 정제 기반의 향상된 동적 메모리 할당 기법</b>
  <span class="paper-authors"><u>김가영</u>, 박나은, 이일구</span>
  <span class="paper-badges"><i class="gold">🏆 우수논문상</i></span>
</div>

악성 트래픽을 입력 단계에서 걸러 내는 방어 계층을 만들었어요. 공격 차단율은 87%였고, 이 논문으로 우수논문상을 받았습니다.

<div class="paper-card">
  <span class="paper-venue">MobiSec 2025, Sapporo, Japan, 2025.12.16~18</span>
  <b>Real-time Anomaly Detection-enhanced Defense for Dynamic Memory Allocation</b>
  <span class="paper-authors"><u>Ga-Yeong Kim</u>, Na-Eun Park, Il-Gu Lee</span>
  <span class="paper-badges"><i>POSTER</i></span>
</div>

같은 방어 구조를 실시간 이상 탐지 쪽에서 다시 정리했어요. 삿포로에서 포스터로 발표했습니다.

## 4. 저널

<div class="paper-card">
  <span class="paper-venue">융합보안논문지 Vol.26 No.2, 2026.03</span>
  <b>Anomalous Traffic Input Sanitization for Enhancing the Security of Popularity Prediction-Based Dynamic Memory Allocation</b>
  <span class="paper-authors"><u>Ga-Yeong Kim</u>, Na-Eun Park, Il-Gu Lee</span>
  <span class="paper-badges"><i class="gold">KCI 등재</i></span>
</div>

1년 동안 한 걸 모아서 KCI 등재 저널에 실었어요.

## 배운 것

만든 사람이라서 제일 잘 보이는 약점도 있더라고요. 성능을 올리려고 넣은 설계가 그대로 공격 표면이 되기도 해요. 이 감각이 나중에 AVF와 SVF 연구로 이어졌습니다. 공격자가 규칙을 배우면 어떻게 될까, 그 질문이요.
