---
title: "[Dreamhack] file-download-1 라이트업"
description: 저장과 읽기의 검증 차이를 이용해 경로 탐색으로 상위 디렉토리의 flag 파일을 읽은 과정입니다.
date: 2026-09-22 22:00:00 +0900
category: ctf-wargame
tags: [web, dreamhack, path-traversal, writeup]
---

경로 검증이 한쪽에만 있을 때 뚫리는 문제입니다. 개념은 [Path Traversal 정리](/posts/concept-path-traversal/)에 적어 뒀습니다.

## 검증 차이

메모를 저장하는 `/upload` 라우트는 `filename`에 `..`가 들어가면 걸러 냈습니다. 그런데 저장된 메모를 읽는 `/read` 라우트는 `name` 파라미터를 아무 검증 없이 파일 경로에 그대로 이어 붙이고 있었습니다. 저장할 때와 달리 읽을 때는 `..` 검사가 아예 없었습니다.

## 익스플로잇

먼저 평범한 이름으로 메모를 올려 정상 동작과 요청 형태를 확인했습니다. 요청은 `/read?name=<파일명>` 형태였습니다.

업로드에는 `..`가 막혀 있지만 읽기에는 필터가 없으니, `name`에 직접 상위 경로를 넣었습니다.

```text
/read?name=../flag.py
```

## 결과

상위 디렉토리의 `flag.py` 내용이 그대로 노출됐고, 거기서 flag를 확인했습니다.

```text
DH{uploading_webshell_in_python_program_is_my_dream}
```

같은 입력이라도 들어오는 모든 지점에서 똑같이 검증해야 한다는 걸 보여 주는 문제였습니다.
