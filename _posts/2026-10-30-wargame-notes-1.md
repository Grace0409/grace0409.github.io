---
title: "워게임 풀이 노트 #1 — free_hook, Mole, Error-Based SQLi"
description: 포너블, 안드로이드, 웹 세 분야에서 풀어 본 문제의 접근 방식을 요약했습니다.
date: 2026-10-30 22:20:00 +0900
category: ctf-wargame
tags: [writeup, pwnable, android, sqli, dreamhack]
---

"풀었다"보다 **어떻게 접근했는지**를 남기려고 합니다. 세 문제의 핵심 흐름만 먼저 정리하고, 자세한 풀이는 하나씩 따로 올릴 예정입니다.

## [Pwnable · DreamHack] __free_hook Overwrite

힙 기반 문제입니다.

1. libc 주소를 누출(leak)합니다.
2. 누출한 주소로 `__free_hook`의 위치를 계산합니다.
3. 제약 조건을 만족하는 `one_gadget` 주소로 `__free_hook`을 덮어씁니다.
4. 이후 `free()`가 호출되는 순간 셸을 얻습니다.

> 포인트: `free()` 한 번이 곧 원하는 함수 호출로 바뀐다는 점. one_gadget은 레지스터·스택 제약 조건을 꼭 확인해야 합니다.

## [Mobile · Android CTF] Whitehat 2018 'Mole'

플래그가 **BroadcastReceiver 100개의 우선순위 체인** 뒤에 숨어 있는 문제였습니다. 체인을 하나씩 따라가는 대신 이렇게 접근했습니다.

1. `jadx`로 디컴파일해 AES 복호화 루틴과 키(`"Kings Never Die!"`)를 찾습니다.
2. `Frida`로 앱의 복호화 함수를 **직접 호출**합니다.
3. 체인을 전혀 거치지 않고 플래그를 복원합니다.

> 포인트: 앱이 정해 둔 경로를 꼭 따라갈 필요는 없습니다. 결국 필요한 건 복호화 함수 하나였어요.

## [Web · DreamHack] Error-Based SQL Injection

1. 에러 메시지에 쿼리 실행 결과가 그대로 노출되는 지점을 찾습니다.
2. `updatexml()`로 **의도적인 XPath 에러**를 일으켜, 에러 메시지 안에 원하는 값이 찍히게 합니다.
3. DB 정보를 한 조각씩 추출합니다.

> 포인트: 결과가 화면에 안 나와도 에러 메시지가 출력 채널이 될 수 있습니다.

## 사용한 도구

`pwntools` · `gdb` · `jadx` · `Frida` · `apktool` · `Ghidra` · `Burp Suite`
