---
title: "[개념] FILE 구조체와 FSOP"
description: glibc의 FILE 구조체가 가진 vtable을 덮으면 왜 임의 함수 호출로 이어지는지 정리했습니다.
date: 2026-10-27 21:00:00 +0900
category: tech-docs
tags: [pwnable, concept, file-structure, fsop]
---

`stdout`, `stderr` 같은 스트림이 실제로는 `FILE` 구조체 포인터라는 걸 알고 나서 정리한 개념입니다. FSOP(File Stream Oriented Programming)의 출발점입니다.

## FILE은 함수 포인터 표를 들고 있다

glibc의 `FILE`(정확히는 `_IO_FILE_plus`)은 구조체 본문 바로 뒤에 vtable 포인터를 둡니다. vtable은 `__xsputn`, `__overflow` 같은 입출력 함수들의 주소 표입니다.

`fprintf`, `fwrite`, `fclose`, `puts` 같은 함수는 전부 `fp->vtable->어떤함수` 형태로 간접 호출합니다. 그래서 vtable 포인터를 가짜 주소로 바꾸면, 다음 출력 때 내가 심은 함수가 불립니다. 문자열 쓰기는 vtable의 `+0x38` 자리(`__xsputn`)를 탑니다.

## 가짜 vtable 만들기

바꿔야 할 건 vtable 포인터 하나입니다. 이걸 내가 값을 통제할 수 있는 영역(bss 전역 등)으로 돌리고, 그 영역의 `+0x38` 위치에 원하는 함수 주소를 심어 둡니다.

```text
vtable 포인터 ← (타겟 전역 - 0x38)
그 전역 위치   ← get_shell 주소
fprintf 호출 → (*(vtable + 0x38))() = get_shell()
```

## 버전이 중요하다

glibc 2.24부터는 `IO_validate_vtable` 검사가 들어갑니다. vtable이 정해진 섹션 범위 안에 있는지 확인하고, 아니면 죽습니다. 그래서 버전을 꼭 확인해야 합니다.

| glibc 버전 | vtable 검사 | 영향 |
| --- | --- | --- |
| 2.23 이하 | 없음 | bss 등 임의 주소를 vtable로 지정 가능 |
| 2.24 이상 | 있음 | `_IO_str_jumps` 오남용 같은 별도 우회 필요 |

버전이 낮으면 아주 단순하게 풀립니다. 실제 적용은 [iofile_vtable 라이트업](/posts/iofile-vtable/)에 정리했습니다 :)
