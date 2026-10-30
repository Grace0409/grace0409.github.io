---
title: "버그바운티 활동 기록: 버그헌팅마스터 3기와 Juice Shop 팀 프로젝트"
description: 버그헌팅마스터 3기 B트랙 수료, 그리고 팀장으로 맡은 OWASP Juice Shop 버그바운티 프로젝트 이야기입니다.
date: 2026-10-30 22:30:00 +0900
category: bug-bounty
tags: [bug-bounty, web, owasp]
---

## 버그헌팅마스터 3기, B트랙

<div class="paper-card">
  <span class="paper-venue">2026 여름</span>
  <b>버그헌팅마스터 3기 B트랙 수료</b>
  <span class="paper-authors">포트폴리오 심사, 기술시험, 면접을 거쳐 선발</span>
  <span class="paper-badges"><i>수료</i></span>
</div>

선발 과정을 거쳐 들어갔고, 실제 웹 서비스를 대상으로 버그헌팅을 했습니다. 실습용 환경이 아니라 진짜 서비스라서 범위(scope)를 지키는 데 가장 신경을 썼습니다.

## HASH 버그바운티 팀 프로젝트

2026년 2학기부터 해킹 동아리 HASH에서 OWASP Juice Shop 버그바운티 프로젝트 팀장을 맡고 있습니다!

진행은 이렇게 합니다. 팀원마다 자기 환경에 Juice Shop을 띄우고 엔드포인트별로 정찰합니다. 찾은 취약점은 PoC까지 재현합니다. 거기서 끝내지 않고 라우트 소스코드에서 원인을 찾고, 시큐어 코딩으로 직접 고쳐 봅니다.

지금까지 다룬 취약점은 아래와 같습니다.

| 유형 | 원인 |
| --- | --- |
| SQL Injection | 입력값 검증이 없음 |
| NoSQL Injection | `$where`에 문자열을 그대로 붙임 |
| IDOR | 객체에 접근할 때 권한 확인을 빠뜨림 |
| XXE | XML 파싱에서 외부 엔티티를 허용 |
| Reflected XSS | 출력할 때 이스케이프를 안 함 |

도구는 Burp Suite, sqlmap, nuclei, ffuf, feroxbuster, dalfox를 썼습니다 :)

## 같이 공부한 것

PortSwigger Web Security Academy로 Blind SQLi, Padding Oracle, 메서드 기반 접근제어 우회, OAuth 공격을 익혔습니다.
