---
title: "[Dreamhack] command-injection-1 라이트업"
description: 클라이언트 측 형식 검증만 있는 ping 기능을 Burp로 우회해, 서버에서 명령을 실행한 과정입니다.
date: 2026-09-23 22:00:00 +0900
category: ctf-wargame
tags: [web, dreamhack, command-injection, writeup]
---

클라이언트 검증만 믿으면 안 된다는 걸 보여 주는 문제입니다. 개념은 [Command Injection 정리](/posts/concept-command-injection/)에 적어 뒀습니다.

## 막힌 지점

호스트를 입력받아 ping을 실행해 주는 기능이었습니다. `8.8.8.8 && cat flag.py`처럼 명령을 이어 붙이니 "요청한 형식과 일치시키세요"라는 메시지에 걸려 요청 자체가 전송되지 않았습니다. 형식 검증이 브라우저 자바스크립트에 있었던 겁니다.

## 서버 측에는 필터가 없다

서버 소스를 보니 `host` 값을 큰따옴표로 감싸 그대로 쉘 명령에 넣고 있었습니다.

```text
ping -c 3 "{host}"
```

클라이언트 검증만 있을 뿐 서버에는 필터가 없었습니다. 클라이언트 검증은 요청을 가로채면 우회됩니다.

## Burp로 우회

Burp Repeater로 정상 요청을 잡아 `host` 파라미터를 직접 고쳤습니다.

```text
host=8.8.8.8"; cat "flag.py
```

큰따옴표를 닫고 이어 붙인 `cat`이 그대로 실행되어, ping 결과 뒤에 `flag.py` 내용이 함께 나왔습니다.

```text
DH{pingpingppppppppping!!}
```
