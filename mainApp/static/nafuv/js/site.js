/* NAFUV — small interactions, no library. Developed by Nami Industries. */
(function () {
  "use strict";

  // Mobile menu ----------------------------------------------------------------
  var bouton = document.querySelector(".menu-bouton");
  var nav = document.getElementById("navigation");
  if (bouton && nav) {
    bouton.addEventListener("click", function () {
      var ouvert = nav.classList.toggle("ouvert");
      bouton.setAttribute("aria-expanded", ouvert ? "true" : "false");
    });
  }

  // Hero slideshow ----------------------------------------------------------------
  var diapos = Array.prototype.slice.call(document.querySelectorAll(".hero-diapo"));
  var points = Array.prototype.slice.call(document.querySelectorAll(".hero-points button"));
  if (diapos.length > 1) {
    var courant = 0, minuteur;
    var montrer = function (i) {
      diapos[courant].classList.remove("actif");
      if (points[courant]) points[courant].removeAttribute("aria-current");
      courant = (i + diapos.length) % diapos.length;
      diapos[courant].classList.add("actif");
      if (points[courant]) points[courant].setAttribute("aria-current", "true");
    };
    var lancer = function () {
      clearInterval(minuteur);
      if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        minuteur = setInterval(function () { montrer(courant + 1); }, 6500);
      }
    };
    points.forEach(function (p, i) { p.addEventListener("click", function () { montrer(i); lancer(); }); });
    lancer();
  }

  // Gallery viewer ----------------------------------------------------------------
  var objets = Array.prototype.slice.call(document.querySelectorAll("[data-visionneuse]"));
  var boite = document.getElementById("visionneuse");
  if (objets.length && boite) {
    var img = boite.querySelector("img"), titre = boite.querySelector("h3"), texte = boite.querySelector("p");
    var index = 0, origine = null;
    var afficher = function (i) {
      index = (i + objets.length) % objets.length;
      var o = objets[index];
      img.src = o.getAttribute("data-image");
      img.alt = o.getAttribute("data-titre") || "";
      titre.textContent = o.getAttribute("data-titre") || "";
      texte.textContent = o.getAttribute("data-texte") || "";
    };
    var ouvrir = function (i) {
      origine = document.activeElement;
      afficher(i);
      boite.classList.add("ouverte");
      boite.setAttribute("aria-hidden", "false");
      document.body.style.overflow = "hidden";
      boite.querySelector(".fermer").focus();
    };
    var fermer = function () {
      boite.classList.remove("ouverte");
      boite.setAttribute("aria-hidden", "true");
      document.body.style.overflow = "";
      if (origine) origine.focus();
    };
    objets.forEach(function (o, i) { o.addEventListener("click", function () { ouvrir(i); }); });
    boite.querySelector(".fermer").addEventListener("click", fermer);
    boite.querySelector(".precedent").addEventListener("click", function () { afficher(index - 1); });
    boite.querySelector(".suivant").addEventListener("click", function () { afficher(index + 1); });
    boite.addEventListener("click", function (e) { if (e.target === boite) fermer(); });
    document.addEventListener("keydown", function (e) {
      if (!boite.classList.contains("ouverte")) return;
      if (e.key === "Escape") fermer();
      if (e.key === "ArrowLeft") afficher(index - 1);
      if (e.key === "ArrowRight") afficher(index + 1);
    });
  }

  // Donation amounts: preset buttons fill the free amount ---------------------------
  var libre = document.getElementById("id_montant");
  Array.prototype.slice.call(document.querySelectorAll("input[name='montant_choisi']")).forEach(function (r) {
    r.addEventListener("change", function () { if (libre && r.checked) libre.value = r.value; });
  });
  if (libre) {
    libre.addEventListener("input", function () {
      Array.prototype.slice.call(document.querySelectorAll("input[name='montant_choisi']")).forEach(function (r) {
        r.checked = r.value === libre.value.trim();
      });
    });
  }

  // Missing or broken images: calm placeholder instead of a broken icon -------------
  var marquer = function (img) { img.classList.add("image-cassee"); img.removeAttribute("srcset"); };
  Array.prototype.forEach.call(document.images, function (img) {
    if (!img.getAttribute("src")) { marquer(img); return; }
    if (img.complete && img.naturalWidth === 0) { marquer(img); return; }
    img.addEventListener("error", function () { marquer(img); }, { once: true });
  });

  // Gentle reveal on scroll ----------------------------------------------------------
  var elements = document.querySelectorAll(".apparait");
  if ("IntersectionObserver" in window) {
    var obs = new IntersectionObserver(function (entrees) {
      entrees.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("vu"); obs.unobserve(e.target); } });
    }, { threshold: 0.12 });
    Array.prototype.forEach.call(elements, function (el) { obs.observe(el); });
  } else {
    Array.prototype.forEach.call(elements, function (el) { el.classList.add("vu"); });
  }
})();
