---
title: "[Dreamhack] tcache poisoning 라이트업"
description: UAF로 tcache key를 깨 double free를 만들고, stdout 포인터로 libc를 흘려 __free_hook에 one_gadget을 적은 과정입니다.
date: 2026-10-30 10:00:00 +0900
category: ctf-wargame
tags: [pwnable, dreamhack, heap, tcache, uaf, writeup]
---

힙 공부의 첫 관문이었던 문제입니다. 개념은 [tcache poisoning 정리](/posts/concept-tcache/)에 적어 뒀습니다.

## 보호기법과 구조

```text
RELRO: Full RELRO        ← GOT 불가, __free_hook 타겟
NX:    enabled           ← 쉘코드 불가, one_gadget
PIE:   No PIE            ← stdout 포인터 위치 고정
libc:  glibc 2.27 (tcache key 검사 백포트)
```

메뉴는 Allocate, Free, Print, Edit입니다. `free(chunk)`가 포인터를 NULL로 밀지 않아서 UAF가 생깁니다. 해제된 청크를 Print로 읽고(leak) Edit로 fd와 key를 덮을 수 있습니다.

## double free를 막는 key부터 깬다

이 libc에는 tcache key 검사가 들어 있습니다. UAF Edit로 해제된 청크의 key를 0으로 덮으면 검사를 통과해서, 같은 청크를 두 번 해제할 수 있습니다.

```text
alloc → free → edit("\x00"*16) → free   ⇒  리스트가 A → A 로 꼬임
```

## stdout 포인터로 libc leak

No PIE라 바이너리의 `stdout`(FILE*) 전역이 `0x601010`에 고정입니다. 그 안에는 libc 내부 주소가 들어 있어요. tcache fd에 `0x601010`을 심어 malloc이 그 주소를 반환하게 한 뒤 `%s`로 읽으면 libc 주소가 샙니다.

여기서 핵심은 size=1 트릭입니다. Allocate는 매번 `read(0, chunk, size-1)`을 합니다. 타겟 주소를 반환하는 malloc에서 1바이트라도 쓰면 stdout 포인터가 깨져서 이후 printf가 죽습니다. `size=1`이면 `size-1=0`이라 아무것도 안 써서 포인터가 보존됩니다.

```text
leak _IO_2_1_stdout_ = 0x7f3c3c11e760
libc base            = 0x7f3c3bd32000   (페이지 정렬 확인)
```

## __free_hook에 one_gadget 쓰기

같은 패턴을 0x30 빈에서 반복해서 malloc이 `__free_hook`을 반환하게 만들고, Allocate의 강제 read로 그 자리에 one_gadget을 적습니다. 그다음 `free()` 한 번이면 `(*__free_hook)()`이 실행됩니다.

one_gadget 후보 네 개를 로컬에서 전수로 돌려서 제약을 만족하는 `0x4f432`만 채택했습니다. 로컬에서 고른 값이 리모트에서도 그대로 맞았습니다.

```text
DH{f9e02bd556d6643f11d9a83570ef5192795cf91c6b443cd603e9f83787ab02fc}
```

## 두 줄 정리

size=1로 read 쓰기를 0바이트로 만들어 leak 타겟을 보존하고, one_gadget `0x4f432`를 로컬 전수 테스트로 선별해 리모트에 적중시켰습니다. 로컬 재현은 제공된 libc-2.27과 같은 계열 로더로 patchelf해서 맞췄습니다.
