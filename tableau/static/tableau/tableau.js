/* NAFUV dashboard interactions, no library. Developed by Nami Industries. */
(function () {
  "use strict";
  var $$ = function (sel, racine) { return Array.prototype.slice.call((racine || document).querySelectorAll(sel)); };

  // Mobile menu --------------------------------------------------------------
  var menu = document.getElementById("menu");
  var voile = document.querySelector(".voile");
  var basculer = function (ouvrir) {
    if (!menu) return;
    menu.classList.toggle("ouvert", ouvrir);
    if (voile) voile.classList.toggle("visible", ouvrir);
  };
  $$(".menu-ouvrir").forEach(function (b) { b.addEventListener("click", function () { basculer(!menu.classList.contains("ouvert")); }); });
  $$("[data-fermer-menu]").forEach(function (v) { v.addEventListener("click", function () { basculer(false); }); });

  // Notifications --------------------------------------------------------------
  $$("[data-fermer]").forEach(function (b) { b.addEventListener("click", function () { b.parentElement.remove(); }); });
  $$(".notifications .notification:not(.error)").forEach(function (n) {
    setTimeout(function () { n.style.transition = "opacity .4s"; n.style.opacity = "0"; setTimeout(function () { n.remove(); }, 400); }, 5000);
  });

  // Language tabs --------------------------------------------------------------
  $$(".onglets").forEach(function (groupe) {
    var boutons = $$(".onglet", groupe);
    boutons.forEach(function (b) {
      b.addEventListener("click", function () {
        boutons.forEach(function (x) {
          var actif = x === b;
          x.classList.toggle("actif", actif);
          x.setAttribute("aria-selected", actif ? "true" : "false");
          var panneau = document.getElementById(x.getAttribute("data-onglet"));
          if (panneau) panneau.classList.toggle("actif", actif);
        });
      });
    });
    // A tab with an error opens first
    var enErreur = boutons.filter(function (b) { return b.querySelector(".point-erreur"); })[0];
    if (enErreur) enErreur.click();
  });

  // Live preview of the main picture --------------------------------------------
  var apercu = function (input, cible) {
    if (!input.files || !input.files[0] || !cible) return;
    var lecteur = new FileReader();
    lecteur.onload = function (e) {
      cible.classList.remove("vide");
      cible.innerHTML = "";
      var img = document.createElement("img");
      img.src = e.target.result;
      img.alt = "";
      cible.appendChild(img);
    };
    lecteur.readAsDataURL(input.files[0]);
  };
  document.addEventListener("change", function (e) {
    var input = e.target;
    if (!input.matches || !input.matches("input[type='file']")) return;
    if (input.hasAttribute("data-depot")) {
      var etat = input.parentElement.querySelector("[data-depot-etat]");
      var n = input.files.length;
      if (etat) etat.textContent = n ? n + " ✓" : "";
      return;
    }
    var principal = document.querySelector("[data-apercu-cible='" + input.name + "']");
    if (principal) { apercu(input, principal); return; }
    var carte = input.closest(".sous-carte");
    if (carte) apercu(input, carte.querySelector(".apercu-petit"));
  });

  // Drop zone highlight -----------------------------------------------------------
  $$(".depot").forEach(function (zone) {
    ["dragenter", "dragover"].forEach(function (t) { zone.addEventListener(t, function () { zone.classList.add("survol"); }); });
    ["dragleave", "drop"].forEach(function (t) { zone.addEventListener(t, function () { zone.classList.remove("survol"); }); });
  });

  // "Add a row" for the sub-items (royal lineage) ------------------------------------
  var bouton = document.querySelector("[data-ajouter-sous]");
  var modele = document.querySelector("template[data-modele-sous]");
  var liste = document.querySelector("[data-sous-liste]");
  var total = document.querySelector("input[name='sous-TOTAL_FORMS']");
  if (bouton && modele && liste && total) {
    bouton.addEventListener("click", function () {
      var index = parseInt(total.value, 10);
      var html = modele.innerHTML.replace(/__prefix__/g, index);
      var conteneur = document.createElement("div");
      conteneur.innerHTML = html.trim();
      var carte = conteneur.firstElementChild;
      liste.appendChild(carte);
      total.value = index + 1;
      var premier = carte.querySelector("input[type='text'], input[type='date']");
      if (premier) premier.focus();
    });
  }

  // Warn before leaving a form with unsaved changes ------------------------------------
  var formulaire = document.querySelector(".formulaire-edition");
  if (formulaire) {
    var modifie = false;
    formulaire.addEventListener("input", function () { modifie = true; });
    formulaire.addEventListener("change", function () { modifie = true; });
    formulaire.addEventListener("submit", function () { modifie = false; });
    window.addEventListener("beforeunload", function (e) { if (modifie) { e.preventDefault(); e.returnValue = ""; } });
  }
})();
