/* API adapter for the original single-page prototype. No UI action is called
   successful unless the backend returns a successful HTTP response. */
(() => {
  const html = value => String(value ?? "").replace(/[&<>"']/g, character => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character]);
  const api = async (path, options = {}) => {
    const response = await fetch(`/api/${path}`, {
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      ...options,
    });
    const body = response.status === 204 ? null : await response.json().catch(() => null);
    if (!response.ok) throw new Error(body?.detail?.[0]?.msg || body?.detail || body?.error || `Request failed (${response.status})`);
    return body;
  };

  const materialName = (label, types) => {
    const text = label.toLowerCase();
    const aliases = text.includes("flower") ? ["flowers and leaves"]
      : text.includes("coconut") && text.includes("shell") ? ["coconut shells"]
      : text.includes("coconut") ? ["coconut husks"]
      : text.includes("plastic") ? ["plastic packaging"]
      : ["jute and textile materials"];
    return types.find(t => aliases.includes(t.name.toLowerCase()));
  };

  function show(formResult, heading, message) {
    formResult.innerHTML = `<div class="ok"><h3>${heading}</h3><p>${message}</p></div>`;
  }

  function clarifyDemoLabels() {
    const route = window.location.hash.replace(/^#\/?/, "").split("?")[0];
    const notice = document.querySelector("#app .demo");
    if (!notice) return;
    const messages = {
      collect: "DEMO ONLY seed rows are fictional. New collection reports are saved to the local database when the API is connected.",
      artisans: "Seed profiles are fictional. New artisan profiles are saved to the local database; no email or notification is sent.",
      store: "Catalog entries are loaded from the database. Seed products are fictional DEMO ONLY examples; checkout saves a simulated order without payment.",
      dashboard: "Dashboard values are read from saved database records. Fictional DEMO ONLY seed rows are identified below; no environmental savings are inferred.",
    };
    if (messages[route]) notice.textContent = messages[route];
    if (route === "collect") {
      const heading = [...document.querySelectorAll("#app h3")].find(item => item.textContent.includes("Request status"));
      if (heading) heading.textContent = "Recorded waste reports";
    }
  }

  async function submitCollection(form) {
    const result = document.querySelector("#cr");
    const name = document.querySelector("#tn").value.trim();
    const types = (await api("waste-types?limit=100")).items;
    const type = materialName(document.querySelector("#tm").value, types);
    if (!type) throw new Error("This material type is not configured in the database. Ask the project admin to seed reference data.");
    const users = (await api("users?limit=100")).items;
    const organizer = users.find(user => user.role === "organizer");
    if (!organizer) throw new Error("No organizer account is available. Load the clearly labelled demo seed or create an organizer through the API.");
    const existing = (await api("waste-sources?limit=100")).items.find(source => source.source_name.toLowerCase() === name.toLowerCase());
    const sourceFields = {
      source_name: name,
      source_type: "temple",
      address: document.querySelector("#tl").value.trim(),
      contact_phone: document.querySelector("#tc").value.trim(),
    };
    const source = existing
      ? await api(`waste-sources/${existing.id}`, { method: "PATCH", body: JSON.stringify(sourceFields) })
      : await api("waste-sources", { method: "POST", body: JSON.stringify(sourceFields) });
    const day = document.querySelector("#td").value;
    const availability = new Date(`${day}T00:00:00+05:30`).toISOString();
    const pickup = document.querySelector("#tt").value.toLowerCase();
    const report = await api("waste-reports", { method: "POST", body: JSON.stringify({
      source_id: source.id,
      waste_type_id: type.id,
      quantity: Number(document.querySelector("#tq").value),
      unit: "kg",
      availability_at: availability,
      preferred_pickup_window: pickup.startsWith("morning") ? "morning" : pickup.startsWith("midday") ? "midday" : "evening",
      festival_collection: document.querySelector("#fs").checked,
      collection_status: "pending",
      reported_by_user_id: organizer.id,
    }) });
    show(result, "Saved to the database", `Collection report #${report.id} is recorded as Pending. A collector has not yet been assigned.`);
    form.reset();
    refreshCollectionCount();
    const table = document.querySelector("#app table");
    if (table) { delete table.dataset.apiLoaded; delete table.dataset.apiLoading; }
    refreshCollectionTable();
  }

  async function submitArtisan(form) {
    const result = document.querySelector("#rr");
    const skills = document.querySelector("#rs").value.trim();
    const preference = document.querySelector("#rm").value;
    const artisan = await api("artisans", { method: "POST", body: JSON.stringify({
      display_name: document.querySelector("#rn").value.trim(),
      location: document.querySelector("#rl").value.trim(),
      skills,
      preferred_materials: preference,
      monthly_capacity_kg: Number(document.querySelector("#rc").value),
      contact_email: document.querySelector("#re").value.trim().toLowerCase(),
      availability_status: "available",
      contact_visibility: "private",
    }) });
    show(result, "Registration saved", `Artisan profile #${artisan.id} is saved. Your contact email is stored privately and is not shown on public profiles.`);
    form.reset();
    const grid = document.querySelector("#ag");
    if (grid) { delete grid.dataset.apiLoaded; delete grid.dataset.apiLoading; }
    refreshArtisans();
  }

  function bindForms() {
    const collectionForm = document.querySelector("#cf");
    if (collectionForm && !collectionForm.dataset.apiBound) {
      collectionForm.dataset.apiBound = "true";
      collectionForm.addEventListener("submit", event => {
        event.preventDefault(); event.stopImmediatePropagation();
        const result = document.querySelector("#cr");
        submitCollection(collectionForm).catch(error => show(result, "Could not save the request", error.message));
      }, true);
    }
    const artisanForm = document.querySelector("#rf");
    if (artisanForm && !artisanForm.dataset.apiBound) {
      artisanForm.dataset.apiBound = "true";
      artisanForm.addEventListener("submit", event => {
        event.preventDefault(); event.stopImmediatePropagation();
        const result = document.querySelector("#rr");
        submitArtisan(artisanForm).catch(error => show(result, "Could not save registration", error.message));
      }, true);
    }
  }

  async function refreshCollectionCount() {
    const target = document.querySelector("#cr");
    if (!target) return;
    try {
      const reports = await api("waste-reports?limit=1");
      const line = document.createElement("p");
      line.textContent = `Database currently contains ${reports.total} waste report(s), including any DEMO ONLY seed data.`;
      target.append(line);
    } catch (_) { /* the form submission already reports API errors */ }
  }

  async function refreshCollectionTable() {
    const table = document.querySelector("#app table");
    if (!table || !window.location.hash.includes("/collect") || table.dataset.apiLoaded || table.dataset.apiLoading) return;
    table.dataset.apiLoading = "true";
    try {
      const [reports, sources, types] = await Promise.all([
        api("waste-reports?limit=100"), api("waste-sources?limit=100"), api("waste-types?limit=100"),
      ]);
      const sourceById = new Map(sources.items.map(item => [item.id, item]));
      const typeById = new Map(types.items.map(item => [item.id, item.name]));
      table.innerHTML = `<tr><th>Source</th><th>Location</th><th>Material</th><th>Quantity</th><th>Available</th><th>Pickup window</th><th>Festival</th><th>Status</th></tr>` +
        (reports.items.length ? reports.items.map(report => {
          const status = report.collection_status[0].toUpperCase() + report.collection_status.slice(1);
          const source = sourceById.get(report.source_id);
          const available = report.availability_at ? new Date(report.availability_at).toLocaleString() : "—";
          const pickup = report.preferred_pickup_window ? report.preferred_pickup_window[0].toUpperCase() + report.preferred_pickup_window.slice(1) : "—";
          return `<tr><td>${html(source?.source_name || `Source #${report.source_id}`)}</td><td>${html(source?.address || "—")}</td><td>${html(typeById.get(report.waste_type_id) || "Unknown type")}</td><td>${Number(report.quantity).toFixed(2)} ${html(report.unit)}</td><td>${html(available)}</td><td>${html(pickup)}</td><td>${report.festival_collection ? "Yes" : "No"}</td><td><span class="st ${html(status)}">${html(status)}</span></td></tr>`;
        }).join("") : `<tr><td colspan="8">No waste reports have been saved yet.</td></tr>`);
      table.dataset.apiLoaded = "true";
    } catch (error) {
      const notice = document.createElement("p");
      notice.className = "demo";
      notice.textContent = `Database report list unavailable: ${error.message}. Any remaining sample rows are demonstration only.`;
      table.before(notice);
      table.dataset.apiLoaded = "true";
    } finally { delete table.dataset.apiLoading; }
  }

  async function refreshArtisans() {
    const grid = document.querySelector("#ag");
    if (!grid || !window.location.hash.includes("/artisans") || grid.dataset.apiLoaded || grid.dataset.apiLoading) return;
    grid.dataset.apiLoading = "true";
    try {
      const { items } = await api("artisans?limit=100");
      const cats = { "flowers and leaves": "flower", "coconut husks": "coconut", "coconut shells": "coconut", "plastic packaging": "plastic", "jute and textile materials": "jute" };
      grid.innerHTML = items.length ? items.map((a, i) => {
        const material = a.preferred_materials.split(/[;,]/)[0].trim().toLowerCase();
        const cat = cats[material] || "jute";
        return `<article class="card">${art(cat, i % 2, html(a.display_name))}<div class="b"><h3>${html(a.display_name)}</h3><small>${html(a.location)}</small><div><span class="tag">${html(a.skills)}</span></div><small>Materials: ${html(a.preferred_materials)}<br>Capacity: ${a.monthly_capacity_kg == null ? "Not provided" : `${Number(a.monthly_capacity_kg).toLocaleString()} kg/month`}<br>Availability: ${html(a.availability_status)}</small><small>Seeded profiles are fictional; contact details are private.</small></div></article>`;
      }).join("") : "<p>No artisan profiles have been recorded yet.</p>";
      grid.dataset.apiLoaded = "true";
    } catch (error) { grid.innerHTML = `<p>Could not load profiles from the API: ${error.message}</p>`; grid.dataset.apiLoaded = "true"; }
    finally { delete grid.dataset.apiLoading; }
  }

  async function refreshProducts() {
    const grid = document.querySelector("#sg");
    if (!grid || !window.location.hash.includes("/store") || grid.dataset.apiLoaded || grid.dataset.apiLoading) return;
    grid.dataset.apiLoading = "true";
    try {
      const { items } = await api("products?limit=100");
      const categoryKey = { flower: "flower", coconut: "coconut", jute: "jute", plastic: "plastic" };
      const display = items.filter(p => p.status === "active").map(p => ({
        id: p.id, n: html(p.product_name), k: categoryKey[p.category] || "flower", p: Number(p.price), m: html(p.description),
        a: "Producer profile recorded in the database",
      }));
      grid.innerHTML = display.length ? display.map(pcard).join("") : "<p>No active products are recorded in the database.</p>";
      wire(document.querySelector("#app"));
      let notice = document.querySelector("#catalog-live-note");
      if (!notice) { notice = document.createElement("p"); notice.id = "catalog-live-note"; notice.className = "demo"; grid.before(notice); }
      notice.textContent = "Catalog loaded from the database. Seed products are marked DEMO ONLY. Cart checkout creates a simulated order; no payment is taken.";
      grid.dataset.apiLoaded = "true";
    } catch (error) { grid.innerHTML = `<p>Could not load products from the API: ${error.message}</p>`; grid.dataset.apiLoaded = "true"; }
    finally { delete grid.dataset.apiLoading; }
  }

  async function refreshDashboard() {
    const target = document.querySelector("#dd");
    if (!target || !window.location.hash.includes("/dashboard") || target.dataset.apiLoaded || target.dataset.apiLoading) return;
    target.dataset.apiLoading = "true";
    try {
      const d = await api("dashboard");
      document.querySelector("#df")?.closest("label")?.remove();
      target.innerHTML = `<div class="stats">
        <div class="stat"><b>${d.collected_report_count}</b><small>Reports marked collected</small></div>
        <div class="stat"><b>${Number(d.recorded_collected_quantity).toFixed(2)} kg</b><small>Reported amount on collected reports</small></div>
        <div class="stat"><b>${Number(d.recorded_processed_quantity).toFixed(2)} kg</b><small>Recorded processing output</small></div>
        <div class="stat"><b>${d.demo_records_present ? "Demo rows included" : "No seeded demo rows"}</b><small>Data status</small></div></div>
        <div class="ok"><p>${d.note}</p><p>Processing records do not imply independent verification. No carbon or water savings are estimated.</p></div>`;
      target.dataset.apiLoaded = "true";
    } catch (error) { target.innerHTML = `<div class="demo">Dashboard unavailable: ${error.message}. The previous prototype figures are demonstration values.</div>`; target.dataset.apiLoaded = "true"; }
    finally { delete target.dataset.apiLoading; }
  }

  async function placeOrder(button) {
    if (!Array.isArray(cart) || !cart.length) throw new Error("Your cart is empty.");
    const users = (await api("users?limit=100")).items;
    const customer = users.find(user => user.role === "customer");
    if (!customer) throw new Error("No customer profile is configured. Load the DEMO ONLY seed before checkout.");
    const result = await api("checkout", { method: "POST", body: JSON.stringify({
      customer_user_id: customer.id,
      items: cart.map(item => ({ product_id: item.id, quantity: item.q })),
    }) });
    cart = [];
    updCart();
    const panel = document.querySelector("#cart");
    panel.innerHTML = `<div class="ok"><h3>Order saved</h3><p>Order #${result.order.id} was saved to the database for ₹${Number(result.order.total_amount).toFixed(2)}. Payment is simulated; no payment details were collected.</p><button class="btn g" id="api-close-cart">Close</button></div>`;
    document.querySelector("#api-close-cart").onclick = () => { panel.classList.remove("on"); document.querySelector("#ov").classList.remove("on"); };
    const grid = document.querySelector("#sg");
    if (grid) { delete grid.dataset.apiLoaded; delete grid.dataset.apiLoading; }
    refreshProducts();
  }

  document.addEventListener("click", event => {
    if (!event.target.closest("#co")) return;
    event.preventDefault(); event.stopImmediatePropagation();
    const button = event.target.closest("#co");
    button.disabled = true; button.textContent = "Saving order…";
    placeOrder(button).catch(error => { button.disabled = false; button.textContent = "Place demo order"; alert(`Order was not saved: ${error.message}`); });
  }, true);

  async function setApiStatus() {
    const pill = document.createElement("div");
    pill.id = "api-status";
    pill.style.cssText = "position:fixed;right:12px;bottom:12px;z-index:80;padding:6px 12px;border-radius:99px;background:#fff;border:1px solid #cfc8b2;font-size:12px";
    pill.textContent = "Checking API…";
    document.body.append(pill);
    try { await api("health"); pill.textContent = "API connected"; pill.style.color = "#174D35"; }
    catch (_) { pill.textContent = "API unavailable"; pill.style.color = "#a3321f"; }
  }

  // The page is a hash-routed SPA. The MutationObserver previously watched
  // changes made by these refresh functions and could recursively trigger
  // itself, freezing the browser during navigation. Route changes are the
  // single source of lifecycle updates instead.
  window.addEventListener("hashchange", () => { clarifyDemoLabels(); bindForms(); refreshCollectionTable(); refreshDashboard(); refreshArtisans(); refreshProducts(); });
  setApiStatus();
  bindForms();
  clarifyDemoLabels();
  refreshDashboard();
  refreshCollectionTable();
  refreshArtisans();
  refreshProducts();
})();
