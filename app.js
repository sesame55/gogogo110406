(function () {
  var root = document.documentElement,
    btn = document.getElementById("themeBtn");
  function isDark() {
    var t = root.getAttribute("data-theme");
    if (t) return t === "dark";
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  }
  function label() {
    var t = isDark() ? "淺色" : "深色";
    btn.querySelector("span").textContent = t;
    btn.setAttribute("aria-label", "切換" + t + "模式");
  }
  label();
  btn.addEventListener("click", function () {
    var n = isDark() ? "light" : "dark";
    root.setAttribute("data-theme", n);
    label();
    try {
      localStorage.setItem("trip-theme", n);
    } catch (e) {}
  });

  /* font size picker (in the drawer) */
  var fsOpts = [].slice.call(document.querySelectorAll("#fsPanel button"));
  function showFs() {
    var cur = root.getAttribute("data-fs") || "m";
    fsOpts.forEach(function (b) {
      b.setAttribute("aria-pressed", b.dataset.fs === cur ? "true" : "false");
    });
  }
  showFs();
  fsOpts.forEach(function (b) {
    b.addEventListener("click", function () {
      var v = b.dataset.fs;
      if (v === "m") root.removeAttribute("data-fs");
      else root.setAttribute("data-fs", v);
      showFs();
      try {
        localStorage.setItem("trip-fs", v);
      } catch (e) {}
    });
  });

  var KEY = "yilan-trip-checks",
    saved = {};
  try {
    saved = JSON.parse(localStorage.getItem(KEY) || "{}") || {};
  } catch (e) {
    saved = {};
  }
  document.querySelectorAll(".checks").forEach(function (list) {
    var g = list.getAttribute("data-group");
    list.querySelectorAll("input").forEach(function (box, i) {
      var id = g + "-" + i;
      box.checked = !!saved[id];
      box.addEventListener("change", function () {
        saved[id] = box.checked;
        try {
          localStorage.setItem(KEY, JSON.stringify(saved));
        } catch (e) {}
      });
    });
  });

  /* ---------- maps ---------- */
  var LM = {
    ruifang: {
      marks: [{ name: "瑞芳車站", lat: 25.1087356, lng: 121.8059692, type: "rail" }],
      rings: true,
      route: false,
    },
    jiaoxi: {
      marks: [
        { name: "礁溪車站", lat: 24.827034, lng: 121.775353, type: "rail" },
        { name: "美嘉美飯店", lat: 24.8288597, lng: 121.7672528, type: "hotel" },
      ],
      rings: true,
      route: false,
    },
    taiping: { marks: [], rings: false, route: true },
    tpslodge: {
      marks: [{ name: "太平山莊", lat: 24.49237, lng: 121.53652, type: "hotel" }],
      rings: true,
      route: false,
    },
    tpscuifeng: {
      marks: [{ name: "翠峰山屋", lat: 24.50966, lng: 121.61058, type: "hotel" }],
      rings: true,
      route: false,
    },
    jiuzhize: { marks: [], rings: false, route: false },
    yinyang: { marks: [], rings: false, route: false },
    caoling: {
      marks: [{ name: "福隆車站", lat: 25.0159203, lng: 121.9446682, type: "rail" }],
      rings: false,
      route: false,
    },
    jxnight: {
      marks: [{ name: "美嘉美飯店", lat: 24.8288597, lng: 121.7672528, type: "hotel" }],
      rings: false,
      route: false,
    },
    fulong: {
      marks: [{ name: "福隆車站", lat: 25.0159203, lng: 121.9446682, type: "rail" }],
      rings: true,
      route: false,
    },
  };
  /* optional map look overrides: window.MAP_STYLE = { dots, vignette, casing, rail, rings, route } */
  var MS = window.MAP_STYLE || {};
  function ms(k, d) {
    return k in MS ? MS[k] : d;
  }
  var NS = "http://www.w3.org/2000/svg";
  function E(t, a, p) {
    var e = document.createElementNS(NS, t);
    for (var k in a) e.setAttribute(k, a[k]);
    if (p) p.appendChild(e);
    return e;
  }
  var uid = 0;
  document.querySelectorAll(".food[data-map]").forEach(function (block) {
    var key = block.getAttribute("data-map"),
      cfg = LM[key] || { marks: [] },
      mapEl = block.querySelector(".map");
    var shops = [].slice.call(block.querySelectorAll(".shop"));
    var pts = shops.map(function (s) {
      var a = s.querySelector("h5 a");
      return {
        lat: +s.dataset.lat,
        lng: +s.dataset.lng,
        num: s.querySelector(".num").textContent,
        closed: s.classList.contains("closed"),
        href: a.href,
        name: a.textContent,
        short: s.dataset.short,
        hrs: s.querySelector(".hrs").textContent.replace(/\s+/g, " ").trim(),
        el: s,
      };
    });
    var all = pts.concat(cfg.marks);
    var la = all.map(function (p) {
        return p.lat;
      }),
      ln = all.map(function (p) {
        return p.lng;
      });
    var minLat = Math.min.apply(null, la),
      maxLat = Math.max.apply(null, la),
      minLng = Math.min.apply(null, ln),
      maxLng = Math.max.apply(null, ln);
    var lat0 = (minLat + maxLat) / 2,
      k = Math.cos((lat0 * Math.PI) / 180);
    var sx = (maxLng - minLng) * k,
      sy = maxLat - minLat,
      min = 0.0026;
    if (sx < min) {
      var c = (minLng + maxLng) / 2;
      minLng = c - min / k / 2;
      maxLng = c + min / k / 2;
      sx = min;
    }
    if (sy < min * 0.75) {
      var c2 = (minLat + maxLat) / 2;
      minLat = c2 - min * 0.375;
      maxLat = c2 + min * 0.375;
      sy = min * 0.75;
    }
    var W = 360,
      H = 270,
      pad = 44,
      s = Math.min((W - 2 * pad) / sx, (H - 2 * pad) / sy),
      ox = (W - sx * s) / 2,
      oy = (H - sy * s) / 2 + 6;
    function P(p) {
      return { x: ox + (p.lng - minLng) * k * s, y: oy + (maxLat - p.lat) * s };
    }
    var id = "m" + uid++;
    var svg = E("svg", {
      viewBox: "0 0 " + W + " " + H,
      role: "img",
      "aria-label": "店家位置地圖",
    });
    var defs = E("defs", {}, svg);
    var pat = E(
      "pattern",
      { id: id + "d", width: 12, height: 12, patternUnits: "userSpaceOnUse" },
      defs,
    );
    E("circle", { cx: 2, cy: 2, r: 1, fill: "hsl(var(--map-dot))" }, pat);
    var rg = E("radialGradient", { id: id + "g", cx: "50%", cy: "45%", r: "75%" }, defs);
    E(
      "stop",
      { offset: "0%", "stop-color": "hsl(var(--map-land))", "stop-opacity": "0" },
      rg,
    );
    E(
      "stop",
      { offset: "100%", "stop-color": "hsl(var(--foreground))", "stop-opacity": ".05" },
      rg,
    );
    var sh = E(
      "filter",
      { id: id + "s", x: "-50%", y: "-50%", width: "200%", height: "200%" },
      defs,
    );
    E(
      "feDropShadow",
      { dx: 0, dy: 1.5, stdDeviation: 1.5, "flood-color": "#000", "flood-opacity": ".3" },
      sh,
    );
    E("rect", { width: W, height: H, fill: "hsl(var(--map-land))" }, svg);
    if (ms("dots", true)) E("rect", { width: W, height: H, fill: "url(#" + id + "d)" }, svg);
    if (ms("vignette", true)) E("rect", { width: W, height: H, fill: "url(#" + id + "g)" }, svg);

    /* streets (OpenStreetMap, simplified) */
    var roads = (STREETS[key] || []).map(function (w) {
      return {
        c: w.c,
        n: w.n,
        q: w.p.split(" ").map(function (s) {
          var a = s.split(",");
          return P({ lat: +a[0], lng: +a[1] });
        }),
      };
    });
    function dpath(q) {
      return (
        "M" +
        q
          .map(function (o) {
            return o.x.toFixed(1) + " " + o.y.toFixed(1);
          })
          .join("L")
      );
    }
    function layer(cls, color, width, extra) {
      var d = roads
        .filter(function (r) {
          return r.c === cls;
        })
        .map(function (r) {
          return dpath(r.q);
        })
        .join("");
      if (!d) return;
      var a = {
        d: d,
        fill: "none",
        stroke: "hsl(var(--" + color + "))",
        "stroke-width": width,
        "stroke-linecap": "round",
        "stroke-linejoin": "round",
      };
      for (var x in extra) a[x] = extra[x];
      E("path", a, svg);
    }
    var water = roads
      .filter(function (r) {
        return r.c === "water";
      })
      .map(function (r) {
        return dpath(r.q) + "Z";
      })
      .join("");
    if (water) E("path", { d: water, fill: "hsl(var(--map-water))" }, svg);
    var wide = s < 3000; /* mountain-scale map: thinner roads */
    var casing = ms("casing", true);
    if (casing) layer("minor", "map-road-edge", wide ? 2.2 : 4.5);
    layer("minor", "map-road", wide ? 1.2 : 3);
    layer("path", "map-path", 1.6, { "stroke-dasharray": "3 3" });
    if (casing) layer("major", "map-major-edge", wide ? 3.6 : 7);
    layer("major", "map-major", wide ? 2.4 : 5);
    if (ms("rail", "dashed") === "thin") {
      layer("rail", "map-rail", 1.5);
    } else {
      layer("rail", "map-rail", 3, { "stroke-linecap": "butt" });
      layer("rail", "map-land", 1.4, { "stroke-linecap": "butt", "stroke-dasharray": "5 5" });
    }
    layer("walk", "primary", 3.5, { "stroke-dasharray": "0.1 6", "stroke-opacity": ".85" });
    /* name the longest visible streets */
    var named = {};
    roads.forEach(function (r) {
      if (!r.n || r.c === "rail" || r.c === "water") return;
      var run = [],
        cur = [];
      r.q.forEach(function (o) {
        if (o.x > 6 && o.x < W - 6 && o.y > 6 && o.y < H - 6) cur.push(o);
        else cur = [];
        if (cur.length > run.length) run = cur.slice();
      });
      var len = 0;
      for (var i = 1; i < run.length; i++)
        len += Math.hypot(run[i].x - run[i - 1].x, run[i].y - run[i - 1].y);
      if (!named[r.n] || named[r.n].len < len) named[r.n] = { n: r.n, c: r.c, q: run, len: len };
    });
    Object.keys(named)
      .map(function (n) {
        return named[n];
      })
      .filter(function (r) {
        return r.len > r.n.length * 10 + 24;
      })
      .sort(function (a, b) {
        return (b.c === "major") - (a.c === "major") || b.len - a.len;
      })
      .slice(0, 3)
      .forEach(function (r, j) {
        var q = r.q[0].x > r.q[r.q.length - 1].x ? r.q.slice().reverse() : r.q,
          pid = id + "r" + j;
        E("path", { id: pid, d: dpath(q), fill: "none" }, defs);
        var tx = E(
          "text",
          {
            dy: 3.2,
            "font-size": 9.5,
            "font-weight": 500,
            fill: "hsl(var(--muted-foreground))",
            stroke: "hsl(var(--map-land))",
            "stroke-width": 2.5,
            "paint-order": "stroke",
          },
          svg,
        );
        var tp = E("textPath", { href: "#" + pid, startOffset: "50%", "text-anchor": "middle" }, tx);
        tp.textContent = r.n;
      });

    /* walking rings around first landmark */
    if (cfg.rings && cfg.marks.length) {
      var softRings = ms("rings", "dashed") === "soft";
      var c0 = P(cfg.marks[0]),
        mPer = 111320;
      [100, 200, 400, 800, 1600, 3200].forEach(function (m) {
        var r = (m / mPer) * s;
        if (r < 26 || r > Math.max(W, H) * 0.95) return;
        E(
          "circle",
          {
            cx: c0.x,
            cy: c0.y,
            r: r,
            fill: "hsl(var(--map-ring))",
            "fill-opacity": softRings ? ".03" : ".05",
            stroke: "hsl(var(--map-ring))",
            "stroke-opacity": softRings ? ".35" : ".45",
            "stroke-width": softRings ? 1 : 1.2,
            "stroke-dasharray": softRings ? "none" : "4 4",
          },
          svg,
        );
        var mins = Math.round(m / 80),
          ty = c0.y - r - 3;
        if (ty > 12) {
          var lb = E(
            "text",
            {
              x: c0.x,
              y: ty,
              "text-anchor": "middle",
              "font-size": 10,
              "font-weight": 600,
              fill: "hsl(var(--map-ring))",
              stroke: "hsl(var(--map-land))",
              "stroke-width": 3,
              "paint-order": "stroke",
            },
            svg,
          );
          lb.textContent = "步行約 " + mins + " 分";
        }
      });
    }
    /* route line (Taipingshan) */
    if (cfg.route && ms("route", true)) {
      var order = [0, 1, 2].map(function (i) {
        return P(pts[i]);
      });
      var d =
        "M" +
        order
          .map(function (q) {
            return q.x.toFixed(1) + " " + q.y.toFixed(1);
          })
          .join(" L");
      E(
        "path",
        {
          d: d,
          fill: "none",
          stroke: "hsl(var(--map-ring))",
          "stroke-width": 2.5,
          "stroke-dasharray": "6 5",
          "stroke-linecap": "round",
          "stroke-opacity": ".7",
        },
        svg,
      );
      var mid = { x: (order[1].x + order[2].x) / 2, y: (order[1].y + order[2].y) / 2 };
      var rt = E(
        "text",
        {
          x: mid.x + 8,
          y: mid.y,
          "font-size": 10.5,
          "font-weight": 600,
          fill: "hsl(var(--muted-foreground))",
          stroke: "hsl(var(--map-land))",
          "stroke-width": 3,
          "paint-order": "stroke",
        },
        svg,
      );
      rt.textContent = "下山車程";
    }
    /* landmarks */
    cfg.marks.forEach(function (l) {
      var q = P(l),
        g = E("g", { filter: "url(#" + id + "s)" }, svg);
      E(
        "rect",
        {
          x: q.x - 11,
          y: q.y - 11,
          width: 22,
          height: 22,
          rx: 6,
          fill:
            l.type === "hotel"
              ? "hsl(var(--map-hotel, 271 37% 47%))"
              : "hsl(var(--map-station, 211 60% 30%))",
          stroke: "#fff",
          "stroke-width": 2,
        },
        g,
      );
      if (l.type === "rail") {
        E("rect", { x: q.x - 5, y: q.y - 6, width: 10, height: 9, rx: 2, fill: "#fff" }, g);
        E(
          "rect",
          { x: q.x - 3.5, y: q.y - 4.5, width: 7, height: 3, fill: "hsl(211 60% 30%)" },
          g,
        );
        E(
          "path",
          {
            d:
              "M" +
              (q.x - 4) +
              " " +
              (q.y + 6) +
              "l2-3M" +
              (q.x + 4) +
              " " +
              (q.y + 6) +
              "l-2-3",
            stroke: "#fff",
            "stroke-width": 1.4,
          },
          g,
        );
      } else {
        E(
          "path",
          {
            d:
              "M" +
              (q.x - 6) +
              " " +
              (q.y + 5) +
              "V" +
              (q.y - 1) +
              "h12V" +
              (q.y + 5) +
              "M" +
              (q.x - 6) +
              " " +
              (q.y + 1) +
              "h12M" +
              (q.x - 6) +
              " " +
              (q.y - 1) +
              "V" +
              (q.y - 5),
            stroke: "#fff",
            "stroke-width": 1.6,
            fill: "none",
          },
          g,
        );
      }
      var t = E(
        "text",
        {
          x: q.x,
          y: q.y + 24,
          "text-anchor": "middle",
          "font-size": 11,
          "font-weight": 700,
          fill: "hsl(var(--map-ink))",
          stroke: "hsl(var(--map-land))",
          "stroke-width": 3.5,
          "paint-order": "stroke",
        },
        svg,
      );
      t.textContent = l.name;
    });
    /* pins with collision spread */
    var placed = cfg.marks.map(function (l) {
        return P(l);
      }),
      groups = [];
    pts.forEach(function (p) {
      var q = P(p),
        bx = q.x,
        by = q.y,
        ang = -Math.PI / 2,
        tries = 0;
      while (
        placed.some(function (o) {
          return Math.hypot(o.x - q.x, o.y - q.y) < 24;
        }) &&
        tries < 80
      ) {
        ang += 0.85;
        var r = 14 + tries * 1.4;
        q = { x: bx + Math.cos(ang) * r, y: by + Math.sin(ang) * r };
        tries++;
      }
      q.x = Math.max(16, Math.min(W - 16, q.x));
      q.y = Math.max(30, Math.min(H - 8, q.y));
      if (tries) {
        E(
          "line",
          {
            x1: bx,
            y1: by,
            x2: q.x,
            y2: q.y,
            stroke: "hsl(var(--muted-foreground))",
            "stroke-width": 1,
            "stroke-opacity": ".7",
          },
          svg,
        );
        E("circle", { cx: bx, cy: by, r: 2.2, fill: "hsl(var(--muted-foreground))" }, svg);
      }
      placed.push(q);
      p.q = q;
      var g = E(
        "g",
        { class: "pin-g", tabindex: 0, role: "button", "aria-label": p.num + " " + p.name },
        svg,
      );
      var body = E(
        "g",
        {
          class: "body",
          filter: "url(#" + id + "s)",
          style: "transform-origin:" + q.x + "px " + q.y + "px",
        },
        g,
      );
      var col = p.closed ? "hsl(240 4% 60%)" : "hsl(var(--pin, var(--primary)))";
      E(
        "path",
        {
          d:
            "M" +
            q.x +
            " " +
            q.y +
            " c-3-6 -11-10 -11-18 a11 11 0 1 1 22 0 c0 8 -8 12 -11 18z",
          fill: col,
          stroke: "#fff",
          "stroke-width": 2,
        },
        body,
      );
      var n = E(
        "text",
        {
          x: q.x,
          y: q.y - 14.5,
          "text-anchor": "middle",
          "font-size": 11.5,
          "font-weight": 700,
          fill: "#fff",
        },
        body,
      );
      n.textContent = p.num;
      p.g = g;
      groups.push(g);
    });
    /* compass + scale */
    var cp = E("g", { transform: "translate(" + (W - 24) + " 24)" }, svg);
    E("circle", { r: 13, fill: "hsl(var(--background))", stroke: "hsl(var(--border))" }, cp);
    E("path", { d: "M0 -9 L4 3 L0 1 L-4 3Z", fill: "hsl(var(--primary))" }, cp);
    var nn = E(
      "text",
      {
        y: 10,
        "text-anchor": "middle",
        "font-size": 7,
        "font-weight": 700,
        fill: "hsl(var(--muted-foreground))",
      },
      cp,
    );
    nn.textContent = "N";
    if (roads.length) {
      var osm = E(
        "text",
        {
          x: 6,
          y: 12,
          "font-size": 8,
          fill: "hsl(var(--muted-foreground))",
          stroke: "hsl(var(--map-land))",
          "stroke-width": 2,
          "paint-order": "stroke",
        },
        svg,
      );
      osm.textContent = "© OpenStreetMap";
    }
    var tg = [50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000],
      len = 0,
      mm = 0;
    for (var i = 0; i < tg.length; i++) {
      var px = (tg[i] / 111320) * s;
      if (px >= 44 && px <= 120) {
        len = px;
        mm = tg[i];
        break;
      }
    }
    if (len) {
      var sg = E(
        "g",
        { transform: "translate(" + (W - len - 14) + " " + (H - 16) + ")" },
        svg,
      );
      E(
        "rect",
        {
          x: -6,
          y: -16,
          width: len + 12,
          height: 24,
          rx: 6,
          fill: "hsl(var(--background))",
          "fill-opacity": ".85",
          stroke: "hsl(var(--border))",
        },
        sg,
      );
      E(
        "path",
        {
          d: "M0 0V4H" + len + "V0",
          fill: "none",
          stroke: "hsl(var(--foreground))",
          "stroke-width": 1.5,
        },
        sg,
      );
      var stt = E(
        "text",
        {
          x: len / 2,
          y: -4,
          "text-anchor": "middle",
          "font-size": 10,
          fill: "hsl(var(--foreground))",
        },
        sg,
      );
      stt.textContent = mm >= 1000 ? mm / 1000 + " 公里" : mm + " 公尺";
    }
    mapEl.appendChild(svg);

    var lg = document.createElement("div");
    lg.className = "legend";
    lg.innerHTML =
      '<span><i style="background:hsl(var(--pin, var(--primary)))"></i>店家</span>' +
      (pts.some(function (p) {
        return p.closed;
      })
        ? '<span><i style="background:hsl(240 4% 60%)"></i>當天公休</span>'
        : "") +
      (cfg.marks.length
        ? '<span><i style="background:hsl(var(--map-station, 211 60% 30%));border-radius:2px"></i>車站／飯店</span>'
        : "");
    mapEl.appendChild(lg);
    var pop = document.createElement("div");
    pop.className = "pop";
    pop.hidden = true;
    mapEl.appendChild(pop);

    var cur = null;
    function select(p, scrollList) {
      if (cur === p) {
        cur = null;
        pop.hidden = true;
        p.g.classList.remove("sel");
        p.el.classList.remove("sel");
        return;
      }
      if (cur) {
        cur.g.classList.remove("sel");
        cur.el.classList.remove("sel");
      }
      cur = p;
      p.g.classList.add("sel");
      p.el.classList.add("sel");
      p.g.parentNode.appendChild(p.g);
      pop.innerHTML = "";
      var b = document.createElement("b");
      b.textContent = p.num + ". " + p.name;
      pop.appendChild(b);
      var h = document.createElement("div");
      h.className = "muted";
      h.textContent = p.hrs;
      pop.appendChild(h);
      var a = document.createElement("a");
      a.href = p.href;
      a.target = "_blank";
      a.rel = "noopener";
      a.textContent = "在 Google 地圖開啟 ↗";
      pop.appendChild(a);
      var xp = (p.q.x / W) * 100,
        yp = ((p.q.y - 24) / H) * 100;
      pop.style.left = Math.max(24, Math.min(76, xp)) + "%";
      pop.style.top = Math.max(34, yp) + "%";
      pop.hidden = false;
      if (scrollList && window.matchMedia("(min-width:821px)").matches)
        p.el.scrollIntoView({ block: "nearest", behavior: "smooth" });
    }
    pts.forEach(function (p) {
      p.g.addEventListener("click", function (e) {
        e.stopPropagation();
        select(p, true);
      });
      p.g.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          select(p, true);
        }
      });
      p.el.addEventListener("click", function (e) {
        if (e.target.closest("a")) return;
        select(p, false);
        if (!window.matchMedia("(min-width:821px)").matches)
          mapEl.scrollIntoView({ block: "nearest", behavior: "smooth" });
      });
    });
    svg.addEventListener("click", function () {
      if (cur) {
        cur.g.classList.remove("sel");
        cur.el.classList.remove("sel");
        cur = null;
        pop.hidden = true;
      }
    });
  });

  /* ---------- paging: one time slot per page ---------- */
  var main = document.querySelector("main"),
    footer = document.getElementById("siteFooter"),
    prevBtn = document.getElementById("prevBtn"),
    nextBtn = document.getElementById("nextBtn"),
    pgInfo = document.getElementById("pgInfo");
  var tops = [].slice.call(main.children).filter(function (el) {
    return el.tagName === "SECTION";
  });
  var pages = [].slice.call(main.querySelectorAll(".page, .slot"));
  var idx = 0;

  /* time-slot switcher under each day header */
  document.querySelectorAll(".day").forEach(function (day) {
    var nav = document.createElement("nav");
    nav.className = "slots";
    nav.setAttribute("aria-label", day.dataset.label + "時段");
    day.querySelectorAll(".slot").forEach(function (s) {
      var a = document.createElement("a");
      a.href = "#" + s.id;
      a.textContent = s.dataset.slot;
      nav.appendChild(a);
    });
    var h = day.querySelector(".day-h");
    h.parentNode.insertBefore(nav, h.nextSibling);
  });

  function pageLabel(p) {
    var day = p.closest(".day");
    return day ? day.dataset.label + "・" + p.dataset.slot : p.dataset.label;
  }
  function resolve(id) {
    var el = id && document.getElementById(id);
    if (!el || !main.contains(el)) return pages[0];
    if (el.classList.contains("day")) return el.querySelector(".slot");
    return el.closest(".page, .slot") || pages[0];
  }
  function render() {
    var hash = location.hash.slice(1);
    try {
      hash = decodeURIComponent(hash);
    } catch (e) {}
    var pg = resolve(hash),
      day = pg.closest(".day");
    idx = pages.indexOf(pg);
    tops.forEach(function (s) {
      s.hidden = s !== pg && s !== day;
    });
    if (day)
      day.querySelectorAll(".slot").forEach(function (s) {
        s.hidden = s !== pg;
      });
    var groupHref = "#" + (day ? day.id : pg.id);
    document.querySelectorAll(".tabs-list a").forEach(function (a) {
      a.classList.toggle("on", a.getAttribute("href") === groupHref);
    });
    document.querySelectorAll(".slots a, .menu a").forEach(function (a) {
      a.classList.toggle("on", a.getAttribute("href") === "#" + pg.id);
    });
    footer.hidden = idx !== pages.length - 1;
    prevBtn.disabled = idx === 0;
    nextBtn.disabled = idx === pages.length - 1;
    pgInfo.innerHTML = "";
    var b = document.createElement("b");
    b.textContent = pageLabel(pg);
    pgInfo.appendChild(b);
    pgInfo.appendChild(document.createTextNode(idx + 1 + " / " + pages.length));
    scrollToHash(pg, hash);
  }
  /* anchors inside a page (e.g. #d1-opts) scroll to that spot */
  function scrollToHash(pg, hash) {
    var target = hash && document.getElementById(hash);
    if (target && target !== pg && pg.contains(target)) target.scrollIntoView();
    else window.scrollTo(0, 0);
  }
  function go(i) {
    if (i < 0 || i >= pages.length || i === idx) return;
    location.hash = pages[i].id;
  }
  if ("scrollRestoration" in history) history.scrollRestoration = "manual";
  window.addEventListener("hashchange", render);
  window.addEventListener("load", function () {
    scrollToHash(pages[idx], location.hash.slice(1));
  });
  prevBtn.addEventListener("click", function () {
    go(idx - 1);
  });
  nextBtn.addEventListener("click", function () {
    go(idx + 1);
  });
  render();

  /* swipe left / right to turn pages (not on tables or maps) */
  var tx = null,
    ty = 0;
  main.addEventListener(
    "touchstart",
    function (e) {
      tx =
        e.touches.length === 1 && !e.target.closest(".table-wrap, .map, .line")
          ? e.touches[0].clientX
          : null;
      if (tx !== null) ty = e.touches[0].clientY;
    },
    { passive: true },
  );
  main.addEventListener(
    "touchend",
    function (e) {
      if (tx === null) return;
      var t = e.changedTouches[0],
        dx = t.clientX - tx,
        dy = t.clientY - ty;
      tx = null;
      if (Math.abs(dx) > 70 && Math.abs(dx) > Math.abs(dy) * 1.8) go(idx + (dx < 0 ? 1 : -1));
    },
    { passive: true },
  );

  /* hamburger drawer */
  var drawer = document.getElementById("drawer"),
    menuBtn = document.getElementById("menuBtn"),
    closeBtn = document.getElementById("closeBtn");
  function setDrawer(open) {
    if (drawer.classList.contains("open") === open) return;
    drawer.classList.toggle("open", open);
    drawer.inert = !open;
    menuBtn.setAttribute("aria-expanded", open ? "true" : "false");
    root.style.overflow = open ? "hidden" : "";
    (open ? closeBtn : menuBtn).focus({ preventScroll: true });
  }
  menuBtn.addEventListener("click", function () {
    setDrawer(true);
  });
  drawer.addEventListener("click", function (e) {
    if (e.target.closest("[data-close], .menu a")) setDrawer(false);
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") return setDrawer(false);
    if (drawer.classList.contains("open") || e.altKey || e.ctrlKey || e.metaKey) return;
    if (e.target.closest("input, textarea, select, [role=button]")) return;
    if (e.key === "ArrowLeft") go(idx - 1);
    else if (e.key === "ArrowRight") go(idx + 1);
  });
})();
