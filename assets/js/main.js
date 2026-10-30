(function () {
  var root = document.documentElement;

  // 라이트/다크 테마 전환
  var toggle = document.querySelector(".theme-toggle");
  if (toggle) {
    toggle.addEventListener("click", function () {
      var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("theme", next); } catch (e) {}
    });
  }

  // 모바일 사이드바
  var sidebar = document.getElementById("sidebar");
  var menuBtn = document.querySelector(".menu-toggle");
  var scrim = document.querySelector(".scrim");
  function setMenu(open) {
    sidebar.classList.toggle("open", open);
    scrim.hidden = !open;
    menuBtn.setAttribute("aria-expanded", String(open));
  }
  if (sidebar && menuBtn && scrim) {
    menuBtn.addEventListener("click", function () { setMenu(!sidebar.classList.contains("open")); });
    scrim.addEventListener("click", function () { setMenu(false); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") setMenu(false); });
  }

  // 코드 블록 복사 버튼
  document.querySelectorAll(".prose div.highlighter-rouge").forEach(function (block) {
    var code = block.querySelector("pre");
    if (!code || !navigator.clipboard) return;
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "copy-btn";
    btn.textContent = "copy";
    btn.addEventListener("click", function () {
      navigator.clipboard.writeText(code.innerText.replace(/\n$/, "")).then(function () {
        btn.textContent = "copied!";
        btn.classList.add("done");
        setTimeout(function () { btn.textContent = "copy"; btn.classList.remove("done"); }, 1500);
      });
    });
    block.appendChild(btn);
  });
})();
