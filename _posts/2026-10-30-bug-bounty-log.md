---
title: "버그바운티 활동 기록: 버그헌팅마스터 3기 & Juice Shop 팀 프로젝트"
description: 버그헌팅마스터 3기 B트랙 수료와, 팀장으로 진행한 OWASP Juice Shop 버그바운티 프로젝트를 정리했습니다.
date: 2026-10-30 22:30:00 +0900
category: bug-bounty
tags: [bug-bounty, web, owasp]
---

## 버그헌팅마스터 3기 · B트랙

<div class="paper-card">
  <span class="paper-venue">2026 여름</span>
  <b>버그헌팅마스터 3기 B트랙 수료</b>
  <span class="paper-authors">포트폴리오 심사 → 기술시험 → 면접을 거쳐 선발</span>
  <span class="paper-badges"><i>수료</i></span>
</div>

선발 과정을 거쳐 참여했고, 실제 웹 서비스를 대상으로 버그헌팅을 수행했습니다. 실습 환경이 아닌 진짜 서비스에서 범위(scope)를 지키며 취약점을 찾는 경험을 할 수 있었습니다.

## 해킹 동아리 HASH · 버그바운티 팀 프로젝트

2026년 2학기부터 해킹 동아리 HASH에서 **OWASP Juice Shop**을 대상으로 한 버그바운티 팀 프로젝트의 팀장을 맡고 있습니다.

### 진행 방식

1. 팀원마다 각자 환경에 Juice Shop을 띄우고, 엔드포인트별로 정찰합니다.
2. 찾은 취약점은 **PoC 수준까지 재현**합니다.
3. 발견에서 멈추지 않고 실제 라우트 소스코드에서 **원인 지점**을 찾습니다.
4. 시큐어 코딩으로 직접 고쳐 봅니다.

### 다룬 취약점

| 유형 | 원인 예시 |
| --- | --- |
| SQL Injection | 입력값 검증 부재 |
| NoSQL Injection | `$where`에 문자열을 그대로 연결 |
| IDOR | 객체 접근 시 권한 확인 누락 |
| XXE | 외부 엔티티를 허용하는 XML 파싱 |
| Reflected XSS | 출력 시 이스케이프 누락 |

### 사용한 도구

`Burp Suite` · `sqlmap` · `nuclei` · `ffuf` · `feroxbuster` · `dalfox`

## 함께 공부한 것

PortSwigger Web Security Academy로 Blind SQLi, Padding Oracle, 메서드 기반 접근제어 우회, OAuth 공격 등을 익혔습니다. 앞으로 실제 제보한 사례가 생기면 공개 가능한 범위에서 이 카테고리에 정리할 예정입니다.
