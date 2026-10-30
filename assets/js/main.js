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

  // 클릭하면 별 조각이 튀는 효과
  if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    document.addEventListener("pointerdown", function (e) {
      for (var i = 0; i < 7; i++) {
        var s = document.createElement("span");
        var a = (Math.PI * 2 * i) / 7 + Math.random() * 0.5;
        var d = 26 + Math.random() * 22;
        s.className = "spark";
        s.style.left = e.clientX + "px";
        s.style.top = e.clientY + "px";
        s.style.setProperty("--dx", Math.cos(a) * d + "px");
        s.style.setProperty("--dy", Math.sin(a) * d + "px");
        document.body.appendChild(s);
        setTimeout(s.remove.bind(s), 600);
      }
    });
  }
})();
