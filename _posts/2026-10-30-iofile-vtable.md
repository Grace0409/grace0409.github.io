---
title: "[Dreamhack] iofile_vtable 라이트업"
description: stderr의 FILE vtable 포인터를 덮어, fprintf가 get_shell을 호출하게 만든 FSOP 문제입니다.
date: 2026-10-30 11:00:00 +0900
category: ctf-wargame
tags: [pwnable, dreamhack, file-structure, fsop, writeup]
---

FILE 구조체의 vtable을 덮는 FSOP 문제입니다. 개념은 [FILE 구조체와 FSOP 정리](/posts/concept-file-structure-fsop/)에 적어 뒀습니다.

## 보호기법과 취약점

```text
PIE:  No PIE (0x400000)   ← get_shell, name 주소 고정
libc: glibc 2.23          ← vtable 검사 없음
get_shell @ 0x40094a      name @ 0x6010d0
```

```c
char name[8];
void get_shell() { system("/bin/sh"); }
int main() {
    read(0, name, 8);
    while (1) {
        switch (sel) {
            case 2: fprintf(stderr, "ERROR\n"); break;   // vtable 통해 호출 (트리거)
            case 4: read(0, stderr + 1, 8); break;        // vtable 포인터 덮기
        }
    }
}
```

`stderr`는 `FILE*`입니다. `stderr + 1`은 구조체 본문(0xd8) 뒤의 vtable 포인터 자리예요. case 4가 그 8바이트를 임의 값으로 덮게 해 줍니다. case 2의 `fprintf`는 출력하면서 `vtable->__xsputn`(`+0x38`)을 간접 호출합니다. 이게 트리거입니다.

## libc leak은 필요 없다

출력 기반 leak 수단이 없고, No PIE라 `get_shell`과 `name` 주소가 고정입니다. 승리 함수 `get_shell`도 이미 있습니다. case 4는 바이너리가 런타임에 `stderr`를 역참조해서 쓰는 거라 libc 주소를 몰라도 됩니다. 그래서 leak 없이 풀립니다.

## 가짜 vtable 배치

전역 `name`에 `get_shell`을 심고, vtable 포인터를 `name - 0x38`로 둡니다. 그러면 `fprintf`가 타는 `vtable + 0x38` 자리가 정확히 `name`을 가리키고, 거기엔 `get_shell`이 있습니다.

```text
name           ← p64(get_shell)
stderr vtable  ← name - 0x38 (= 0x601098)
fprintf → (*(0x601098 + 0x38))() = (*(name))() = get_shell()
```

glibc 2.23이라 vtable 범위 검사가 없어서 bss 주소를 vtable로 써도 통합니다. 2.24 이상이었다면 별도 우회가 필요했을 거예요.

```text
DH{9f746608b2c9239b6b80eb5bbcae06ed}
```

로컬은 Docker 대신 같은 버전 glibc 2.23을 추출해 patchelf로 재현했습니다. 효과는 동일했습니다.

## 한 줄 정리

`stderr + 1`이 곧 FILE의 vtable 포인터라, 그 8바이트를 `name - 0x38`로 덮고 `name`엔 `get_shell`을 심으면 `fprintf`가 호출하는 `__xsputn`이 정확히 `get_shell`을 가리킵니다.
