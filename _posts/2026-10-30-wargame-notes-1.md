---
title: "워게임 풀이 노트 #1: free_hook, Mole, Error-Based SQLi"
description: 포너블, 안드로이드, 웹에서 하나씩 풀어 본 문제를 어떻게 접근했는지 적었습니다.
date: 2026-10-30 22:20:00 +0900
category: ctf-wargame
tags: [writeup, pwnable, android, sqli, dreamhack]
---

풀었다는 것보다 어떻게 접근했는지를 남기고 싶었어요. 일단 세 문제의 흐름만 적고, 자세한 풀이는 하나씩 따로 올릴게요.

## [Pwnable, DreamHack] __free_hook Overwrite

힙 문제예요.

1. libc 주소를 leak 합니다.
2. 그 주소로 `__free_hook` 위치를 계산해요.
3. 제약 조건이 맞는 `one_gadget` 주소로 `__free_hook`을 덮어요.
4. 다음에 `free()`가 불리는 순간 셸이 떨어집니다.

`free()` 한 번이 내가 원하는 함수 호출로 바뀌는 거예요. one_gadget은 레지스터랑 스택 조건을 꼭 확인해야 해요.

## [Mobile, Android CTF] Whitehat 2018 'Mole'

플래그가 BroadcastReceiver 100개짜리 우선순위 체인 뒤에 숨어 있었어요. 하나씩 따라가면 끝이 없어서 방향을 바꿨습니다.

jadx로 디컴파일해서 AES 복호화 루틴과 키(`Kings Never Die!`)를 찾았어요. 그다음 Frida로 앱의 복호화 함수를 바로 불렀고요. 체인은 하나도 안 거치고 플래그가 나왔어요.

앱이 깔아 둔 길을 꼭 따라갈 필요는 없더라고요. 결국 필요한 건 복호화 함수 하나였어요.

## [Web, DreamHack] Error-Based SQL Injection

에러 메시지에 쿼리 결과가 그대로 찍히는 곳을 먼저 찾았어요. 거기에 `updatexml()`로 XPath 에러를 일부러 내서, 에러 안에 원하는 값이 보이게 했습니다. DB 정보를 한 조각씩 빼냈어요.

결과가 화면에 안 나와도 에러 메시지가 출력 통로가 될 수 있다는 게 포인트예요.

## 사용한 도구

pwntools, gdb, jadx, Frida, apktool, Ghidra, Burp Suite
