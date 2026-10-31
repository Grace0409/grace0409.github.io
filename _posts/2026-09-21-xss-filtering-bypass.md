---
title: "[Dreamhack] XSS Filtering Bypass 라이트업"
description: script, on, javascript를 치우는 필터를 문자열 쪼개기로 우회해 관리자 쿠키를 탈취한 과정입니다.
date: 2026-09-21 21:00:00 +0900
category: ctf-wargame
tags: [web, dreamhack, xss, writeup]
---

입력 필터를 우회해 관리자 봇의 쿠키를 가져오는 문제입니다. 개념은 [XSS 정리](/posts/concept-xss/)에 적어 뒀습니다.

## 필터 확인

입력값을 그대로 페이지에 반영하는 파라미터가 있었고, 관리자 봇이 제출한 URL을 대신 방문하는 구조였습니다. 기본 페이로드 `<script>alert(1)</script>`는 필터에 막혔습니다.

키워드를 하나씩 넣어 보니 `script`, `on`(이벤트 핸들러 접두사), `javascript`가 차단 키워드였습니다.

## 문자열 쪼개기로 우회

필터가 키워드를 한 번만 치환하는 단순 로직이라, 중간에 같은 키워드를 끼워 넣어 우회했습니다.

```text
<sscriptcript>location.href="/memo?memo="+document.cookie;</sscriptcript>
```

안쪽 `script`가 지워지면 바깥이 합쳐지면서 `<script>`가 됩니다.

## 결과

우회 페이로드가 필터를 통과했고, 관리자 봇이 이 URL을 방문하면서 자기 쿠키를 `/memo` 경로로 보냈습니다. memo 페이지에 남은 쿠키 값이 곧 flag였습니다.

```text
DH{81cd7cb24a49ad75b9ba37c2b0cda4ea}
```
