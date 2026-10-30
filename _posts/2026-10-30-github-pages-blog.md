---
title: "GitHub Pages와 Jekyll로 나만의 블로그 만들기"
description: GitHub Pages가 뭔지부터 username.github.io 블로그를 만들고 배포하기까지 정리했습니다.
date: 2026-10-30 20:00:00 +0900
category: dev
tags: [github-pages, jekyll]
---

이 블로그를 만들면서 알게 된 GitHub Pages 이야기예요.

## GitHub Pages란?

GitHub 저장소에 올린 HTML, CSS, JS 파일을 그대로 웹사이트로 띄워 주는 정적 사이트 호스팅이에요. 서버를 따로 안 차려도 `git push` 한 번이면 배포됩니다. 공개 저장소면 무료고요.

대신 PHP나 DB 같은 서버 코드는 못 돌려요. 정적 파일만 내보냅니다. Jekyll이라는 정적 사이트 생성기가 기본으로 들어 있어서, 마크다운으로 글을 쓰면 HTML로 바꿔 줘요.

사이트는 두 종류가 있어요.

| 종류 | 저장소 이름 | 주소 |
| --- | --- | --- |
| 사용자 사이트 | `<username>.github.io` | `https://<username>.github.io` |
| 프로젝트 사이트 | 아무 이름 (예: `my-project`) | `https://<username>.github.io/my-project` |

개인 블로그는 보통 사용자 사이트로 만들어요. 저장소 이름은 꼭 `아이디.github.io`여야 합니다.

## Jekyll은 어떻게 돌아갈까

정해진 폴더 구조를 읽어서 완성된 HTML 사이트(`_site/`)를 뽑아내요.

```text
.
├── _config.yml        # 사이트 설정 (제목, URL, 플러그인)
├── _data/             # YAML 데이터 (여기선 카테고리 목록)
├── _includes/         # 여러 페이지에서 같이 쓰는 HTML 조각
├── _layouts/          # 페이지 뼈대 (default, post, category ...)
├── _posts/            # 글 (YYYY-MM-DD-제목.md)
├── assets/            # CSS, JS, 이미지
└── index.html         # 메인 페이지
```

글 파일 맨 위에는 front matter라는 YAML 블록을 넣어요. 제목, 날짜, 카테고리 같은 걸 적는 곳이에요.

```yaml
---
title: "글 제목"
date: 2026-10-30 20:00:00 +0900
category: ctf-wargame
tags: [pwnable, bof]
---
```

## 이 블로그를 만든 순서

먼저 GitHub에 `아이디.github.io` 이름으로 Public 저장소를 만들었어요.

기본 테마는 안 썼어요. 레이아웃과 CSS를 직접 짰고, 좋아하는 게임 UI 느낌을 살려서 핑크랑 블랙으로 꾸몄습니다. 카테고리 6개는 `_data/categories.yml`에 정의하고 카테고리마다 페이지를 만들었어요.

그다음 push 했어요.

```bash
git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/<username>/<username>.github.io.git
git push -u origin main
```

마지막으로 저장소 Settings의 Pages 메뉴에서 배포 소스가 `main` 브랜치 `/ (root)`인지 봤어요. 1~2분 기다렸다가 `https://<username>.github.io`에 들어가면 끝이에요.

## 새 글 쓰는 법

`_posts/` 폴더에 `2026-11-01-my-first-writeup.md` 같은 이름으로 파일을 만들어요. front matter의 `category`에 아래 값 중 하나를 넣으면 알아서 그 카테고리로 들어갑니다.

| category 값 | 카테고리 |
| --- | --- |
| `dev` | 개발 |
| `ctf-wargame` | CTF/Wargame |
| `bug-bounty` | Bug Bounty |
| `tech-docs` | 블로그/기술문서 |
| `paper-conference` | 논문/컨퍼런스 |
| `contest-cert` | 공모전/자격증 |

## 알아 두면 좋은 것

사이트 용량은 1GB 아래를 권장해요. 빌드도 시간당 횟수 제한이 느슨하게 걸려 있고요. 플러그인은 GitHub Pages가 지원하는 것만 쓸 수 있어요. 여기선 `jekyll-feed`, `jekyll-seo-tag`, `jekyll-sitemap`을 씁니다.

그리고 공개 저장소니까 API 키나 개인정보는 절대 커밋하면 안 돼요. 보안 공부하는 사람이 제일 먼저 지켜야 할 거죠.
