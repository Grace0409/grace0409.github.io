---
title: "[Dreamhack] Apache htaccess 라이트업"
description: 확장자 블랙리스트를 대문자로 우회하고, .htaccess로 .txt를 PHP로 실행시켜 웹쉘로 명령을 실행한 과정입니다.
date: 2026-09-23 21:00:00 +0900
category: ctf-wargame
tags: [web, dreamhack, file-upload, webshell, writeup]
---

파일 업로드와 Apache 설정을 엮는 문제입니다. 개념은 [파일 업로드 취약점 정리](/posts/concept-file-upload/)에 적어 뒀습니다.

## 블랙리스트 우회

업로드는 차단 목록(deniedExts)에 없는 확장자만 그대로 저장하는 구조였습니다. `.php`는 막혔습니다. 소스를 보니 `php`, `php3`, `php4`, `php5`, `pht`, `phtml`만 나열한 단순 블랙리스트였고 대소문자 구분이 없었습니다.

`.PHP`(대문자)로 올리니 필터를 통과했습니다. 다만 서버가 대문자 확장자는 PHP로 실행해 주지 않아서, 이 상태로는 코드가 돌지 않았습니다.

## .htaccess로 실행 조건 만들기

문제 제목이 Apache htaccess라는 점에 착안했습니다. `.htaccess`로 디렉토리 설정을 바꿀 수 있으니, 특정 확장자를 PHP로 해석하게 만들었습니다.

```text
AddType application/x-httpd-php .txt
```

이 파일을 먼저 업로드 폴더에 올려 설정을 반영했습니다. 그다음 `cmd` 파라미터를 `system()`으로 실행하는 웹쉘을 `html.txt`로 올렸습니다. 설정 덕분에 `.txt`가 PHP로 실행됐습니다.

## 결과

`/upload/html.txt`에 접속하니 명령 실행 폼이 떴고, `cmd=/flag`로 flag를 확인했습니다.

```text
DH{9aeba1a6feed3769ae0915b62db2b4872bec98c2}
```
