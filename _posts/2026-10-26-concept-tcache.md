---
title: "[개념] tcache와 poisoning"
description: glibc의 tcache 구조, double free를 막는 key 검사, 그리고 그걸 우회하는 흐름을 정리했습니다.
date: 2026-10-26 21:00:00 +0900
category: tech-docs
tags: [pwnable, concept, heap, tcache]
---

힙 공부를 시작하면서 가장 먼저 정리한 구조입니다. tcache는 glibc 2.26부터 들어온 작은 청크 캐시입니다.

## tcache 기본 구조

같은 크기의 청크를 해제하면 tcache라는 단일 연결 리스트에 쌓입니다. 다음 할당 때 리스트 맨 앞 청크를 바로 꺼내 주기 때문에 빠릅니다. 해제된 청크의 맨 앞 8바이트(fd)에 다음 청크 주소가 들어갑니다.

poisoning은 이 fd를 조작하는 공격입니다. fd를 내가 원하는 주소로 덮으면, 몇 번의 할당 뒤에 malloc이 그 주소를 반환합니다. 즉 임의 주소에 읽고 쓸 수 있게 됩니다.

## double free와 key 검사

poisoning을 하려면 보통 같은 청크를 두 번 해제해서 리스트를 꼬아 놓습니다. 그런데 glibc에는 이걸 막는 장치가 있습니다. 청크를 tcache에 넣을 때 fd 다음 8바이트(key)에 tcache 구조체 주소를 적어 둡니다. 두 번째 해제에서 key가 그 값이면 중복으로 보고 바로 죽습니다.

```text
e->key = tcache;                       // 넣을 때 표시
if (e->key == tcache)  abort();        // 두 번째 free에서 걸림
```

## key를 깨면 우회된다

중복 탐지는 오직 key 필드만 봅니다. UAF로 해제된 청크의 key를 0으로 덮으면, "tcache에서 나온 청크가 아니다"라고 착각하고 그대로 다시 넣습니다. double free가 성립합니다.

| 단계 | 상태 |
| --- | --- |
| free | 리스트에 A, `A.key = &tcache` |
| key를 0으로 덮기 | `A.key = 0` |
| 다시 free | 검사 통과, 리스트가 A → A 로 꼬임 |

그다음은 fd를 원하는 주소로 덮고, 할당을 반복해 그 주소를 손에 넣습니다. Full RELRO라 GOT를 못 쓰면 `__free_hook`을 노리는 게 전형적입니다. 거기에 one_gadget을 적고 `free()`를 한 번 부르면 셸이 뜹니다. 실제 풀이는 [tcache poisoning 라이트업](/posts/tcache-poisoning/)에 있습니다.
