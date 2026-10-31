---
title: "[개념] SQL Injection과 Error-Based 추출"
description: 입력값이 쿼리에 그대로 붙을 때 생기는 SQLi와, 에러 메시지를 출력 통로로 쓰는 기법을 정리했습니다.
date: 2026-09-15 21:00:00 +0900
category: tech-docs
tags: [web, concept, sql-injection]
---

웹 보안의 기본이자 가장 많이 만나는 취약점입니다. 공부한 내용을 하나씩 정리합니다.

## 왜 생기나

사용자 입력을 검증 없이 쿼리 문자열에 그대로 이어 붙이면, 입력이 데이터가 아니라 쿼리 구문으로 해석됩니다. 작은따옴표 하나로 문법이 깨지면서 에러가 나면 SQLi가 가능하다는 신호입니다.

```sql
SELECT * FROM user WHERE uid = '입력값'
-- 입력값에 '  를 넣으면 문법 오류 → DB 에러 노출
```

뒤에 남는 구문 때문에 오류가 나지 않게 `--`나 `#`로 주석 처리해서, 넣은 구문이 정상 실행되게 만듭니다.

## Error-Based 추출

결과가 화면에 직접 나오지 않아도, 에러 메시지가 출력 통로가 될 수 있습니다. MySQL의 `extractvalue()`나 `updatexml()`은 XPath 표현식이 잘못되면 그 내용을 에러 메시지에 그대로 찍습니다. 이 특성을 이용해 원하는 SELECT 결과를 에러에 실어서 빼냅니다.

```sql
1' and extractvalue(0x3a, concat(0x3a, (SELECT upw FROM user LIMIT 0,1)));--
```

에러 메시지는 길이 제한(보통 30자 안팎)이 있어서, `substr()`로 구간을 잘라 여러 번 요청해 이어 붙입니다.

## 막는 법

가장 확실한 건 파라미터 바인딩(prepared statement)입니다. 입력을 쿼리 구문이 아니라 값으로만 다루게 만듭니다. ORM을 쓰면서 문자열 조립을 피하는 것도 같은 맥락입니다.

실제로 적용한 문제는 [Error-Based SQLi 라이트업](/posts/error-based-sqli/)에, UNION 기반은 [진단 프로젝트](/posts/juice-shop-assessment/)에 있습니다.
