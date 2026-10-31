---
title: "웹 취약점 진단 프로젝트: OWASP Juice Shop"
description: 격리 환경에 구축한 OWASP Juice Shop을 수동 진단하며 인증 우회, SQLi, XXE, 스마트컨트랙트 재진입까지 찾아낸 기록입니다.
date: 2026-09-30 21:00:00 +0900
category: bug-bounty
tags: [bug-bounty, owasp, juice-shop, pentest, project]
---

버그바운티 팀 프로젝트로 진행한 웹 취약점 진단입니다. 팀장을 맡아서 진단부터 보고서 작성까지 끌고 갔습니다.

## 진단 개요

교육용 취약 웹 애플리케이션인 OWASP Juice Shop(v20.1.1)을 Docker 컨테이너로 올린 격리 환경에서만 진단했습니다. 실제 서비스가 아니라 직접 구축한 학습 환경입니다.

| 항목 | 내용 |
| --- | --- |
| 대상 | OWASP Juice Shop v20.1.1 (Docker, 내부망) |
| 기간 | 2026.09.22 ~ 09.26 |
| 방식 | 인가된 블랙박스/그레이박스 수동 진단 |
| 기준 | OWASP Top 10:2021, OWASP WSTG |
| 도구 | Burp Suite, jwt.io, Dedaub Decompiler, 브라우저 |

발견에서 멈추지 않고, 라우트 소스코드에서 원인을 찾고 대응 방안까지 보고서로 정리하는 걸 목표로 했습니다.

## 찾은 취약점

여덟 건을 확인했습니다. 인증과 세션 관리 쪽 결함이 특히 치명적이었습니다.

| 취약점 | 분류 | 위험도 |
| --- | --- | --- |
| 로그인 SQL Injection 인증 우회 | A03 Injection, CWE-89 | 치명적 |
| 상품 검색 UNION SQLi | A03 Injection, CWE-89 | 치명적 |
| JWT 서명 검증 우회 (alg:none) | A07 Auth Failures, CWE-347 | 높음 |
| XXE 내부 파일 노출 | A05 Misconfiguration, CWE-611 | 높음 |
| 주문 조회 XSS | A03 Injection, CWE-79 | 높음 |
| NoSQL Injection ($where) | CWE-943 | 치명적 |
| 스마트컨트랙트 재진입 (withdraw) | SWC-107, CWE-841 | 치명적 |
| MetaMask 통화 심볼 불일치 | 설정 결함 | 낮음 |

## 인상 깊었던 세 가지

### UNION 기반 SQL Injection

상품 검색 `GET /rest/products/search`의 `q` 파라미터가 파라미터 바인딩 없이 쿼리 문자열에 그대로 들어갔습니다. 인증도 필요 없었습니다. 먼저 컬럼 수를 맞춘 뒤 UNION으로 Users 테이블을 통째로 끌어왔습니다.

```text
q=')) UNION SELECT id,email,password,4,5,6,7,8,9 FROM Users--
```

admin 계정 이메일과 MD5 패스워드 해시가 검색 응답에 그대로 섞여 나왔습니다. 대응은 ORM과 파라미터 분리입니다.

### XXE 내부 파일 노출

레거시 파일 업로드 `POST /file-upload`가 인증 없이 XML을 받아 서버 파서로 처리했습니다. 이 파서는 외부 엔티티 로딩이 켜져 있었고, 파싱 결과를 에러 응답에 그대로 실었습니다.

```xml
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/hostname">]>
<foo>&xxe;</foo>
```

외부 엔티티가 치환되면서 내부 파일 내용이 응답에 노출됐습니다. 대응은 DTD와 외부 엔티티 로딩 비활성화, 그리고 파서의 파일시스템 provider 등록 제거입니다.

### 스마트컨트랙트 재진입

Web3 챌린지 컨트랙트의 `withdraw()`가 Checks-Effects-Interactions 원칙을 어기고 있었습니다. 잔고를 차감하기 전에 외부 이더 전송을 먼저 했습니다. 바이트코드를 Dedaub으로 디컴파일해 그 구간을 확인했습니다.

전송 시점에 공격자 컨트랙트의 fallback이 실행되고, 잔고가 아직 안 깎인 상태에서 `withdraw()`를 다시 부르면 잔액이 소진될 때까지 반복 인출됩니다. 대응은 CEI 원칙 준수와 ReentrancyGuard 적용입니다.

## 느낀 점

취약점을 찾는 것보다, 라우트 소스에서 원인을 짚고 올바른 대응까지 적는 과정이 훨씬 공부가 됐습니다. 특히 같은 SQLi라도 인증 우회와 데이터 유출은 들어가는 지점과 영향이 전혀 달랐습니다. 웹부터 스마트컨트랙트까지 한 대상 안에서 넓게 볼 수 있었던 프로젝트였습니다 :)

> 모든 진단은 직접 구축한 격리 환경에서 인가된 범위로만 진행했습니다.
