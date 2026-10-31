---
title: "[개념] XSS: 반사형, DOM, 필터 우회"
description: 입력값이 페이지에 그대로 반영될 때 생기는 XSS와, 필터 우회 및 DOM 기반 유형을 정리했습니다.
date: 2026-09-16 21:00:00 +0900
category: tech-docs
tags: [web, concept, xss]
---

사용자 입력이 검증 없이 페이지에 반영될 때 스크립트가 실행되는 취약점입니다. 유형이 여러 가지라 하나씩 정리했습니다.

## 반사형과 필터 우회

입력이 응답에 그대로 박히면 `<script>`로 스크립트를 실행할 수 있습니다. 보통 관리자 봇이 제출된 URL을 대신 방문하는 구조라, 봇의 쿠키를 탈취하는 게 목표가 됩니다.

필터가 `script`, `on`, `javascript` 같은 키워드를 치우는 경우가 많은데, 단순 치환 로직은 문자열을 쪼개서 우회할 수 있습니다.

```text
<sscriptcript>location.href="/memo?memo="+document.cookie;</sscriptcript>
```

안쪽 `script`가 한 번 지워지면 바깥이 합쳐져서 `<script>`가 됩니다.

## DOM 기반

서버를 거치지 않고, 브라우저 안 자바스크립트가 입력을 위험한 자리(sink)에 넣을 때 생깁니다. `location.hash`나 쿼리 값이 `innerHTML`에 검증 없이 들어가는 구조가 전형입니다.

`innerHTML`에 `<script>`를 넣으면 실행이 안 되는 경우가 많아서, `onerror` 같은 이벤트 핸들러로 먼저 실행 여부를 확인합니다.

```text
?query=<img src=x onerror=alert(1)>
```

## 막는 법

출력하는 맥락에 맞게 이스케이프하는 게 기본입니다. HTML, 속성, 자바스크립트 자리마다 처리 방법이 다릅니다. `innerHTML` 대신 `textContent`를 쓰고, CSP로 인라인 스크립트 실행을 제한하면 더 단단해집니다.

실제 적용은 [XSS 필터 우회](/posts/xss-filtering-bypass/)와 [DOM XSS](/posts/dom-xss/) 라이트업에 있습니다.
