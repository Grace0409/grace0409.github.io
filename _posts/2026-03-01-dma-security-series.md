---
title: "동적 메모리 할당 보안 연구: 제안부터 KCI 저널까지"
description: 직접 제안한 메커니즘의 취약점을 스스로 찾고 방어까지 설계한, 2025년 한 해의 연구 흐름을 정리했습니다.
date: 2026-03-01 10:00:00 +0900
category: paper-conference
tags: [system-security, dma, kci, award]
---

학부연구생으로 처음 시작한 연구 주제입니다. "내가 만든 시스템을 내가 공격해 보고, 다시 막는다"는 흐름으로 다섯 편의 논문이 이어졌습니다.

## 1. 제안 — CPP-DMA

<div class="paper-card">
  <span class="paper-venue">ASK 2025 (KIPS) · 경북대학교 · 2025.05.29–31</span>
  <b>콘텐츠 인기도 예측 기반의 동적 메모리 할당 메커니즘</b>
  <span class="paper-authors"><u>김가영</u>, 문정민, 박나은, 이일구</span>
</div>

콘텐츠 인기도를 예측해 메모리를 동적으로 할당하는 메커니즘을 제안해 **처리 시간을 30.3% 줄였습니다.**

## 2. 공격 — 취약점 분석

<div class="paper-card">
  <span class="paper-venue">WISA 2025 · Jeju · 2025.08.20–22</span>
  <b>Security Vulnerability Analysis of Real-time Content Popularity Prediction-based Dynamic Memory Allocation System</b>
  <span class="paper-authors"><u>Ga-Yeong Kim</u>, Na-Eun Park, Il-Gu Lee</span>
  <span class="paper-badges"><i>POSTER</i></span>
</div>

인기도 예측에 의존한다는 점이 곧 약점이었습니다. 악의적인 트래픽으로 예측을 흔들면 할당이 왜곡될 수 있다는 구조적 취약점을 스스로 찾아 분석했습니다.

## 3. 방어 — ADE-DMA

<div class="paper-card">
  <span class="paper-venue">한국융합보안학회 2025 추계 · 2025.11.07</span>
  <b>ADE-DMA: 이상 감지 및 입력 데이터 정제 기반의 향상된 동적 메모리 할당 기법</b>
  <span class="paper-authors"><u>김가영</u>, 박나은, 이일구</span>
  <span class="paper-badges"><i class="gold">🏆 우수논문상</i></span>
</div>

악성 트래픽을 **입력 단계에서 정제**하는 방어 계층을 설계해 공격 차단율 87%를 확인했고, 우수논문상을 받았습니다.

<div class="paper-card">
  <span class="paper-venue">MobiSec 2025 · Sapporo, Japan · 2025.12.16–18</span>
  <b>Real-time Anomaly Detection-enhanced Defense for Dynamic Memory Allocation</b>
  <span class="paper-authors"><u>Ga-Yeong Kim</u>, Na-Eun Park, Il-Gu Lee</span>
  <span class="paper-badges"><i>POSTER</i></span>
</div>

같은 방어 구조를 실시간 이상 탐지 관점에서 정리해 일본 삿포로에서 포스터로 발표했습니다.

## 4. 저널 — DMA-Shield

<div class="paper-card">
  <span class="paper-venue">융합보안논문지 Vol.26 No.2 · 2026.03</span>
  <b>Anomalous Traffic Input Sanitization for Enhancing the Security of Popularity Prediction–Based Dynamic Memory Allocation</b>
  <span class="paper-authors"><u>Ga-Yeong Kim</u>, Na-Eun Park, Il-Gu Lee</span>
  <span class="paper-badges"><i class="gold">KCI 등재</i></span>
</div>

1년 동안의 연구를 모아 KCI 등재 저널에 게재했습니다.

## 배운 것

제안한 사람이 가장 잘 아는 약점도 있다는 걸 배웠습니다. 성능을 올리는 설계가 곧 공격 표면이 될 수 있다는 감각이 이후 AVF·SVF 연구에서 "공격자가 규칙을 학습하면?"이라는 질문으로 이어졌습니다.
