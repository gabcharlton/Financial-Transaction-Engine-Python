/* ============================================================
   Financial Transaction Engine — frontend JS
   All data lives in `state`. API calls go to Flask endpoints.
   ============================================================ */

"use strict";

// ─── State ───────────────────────────────────────────────────────────────────

const state = {
  structure:    "sole",
  acctType:     "asset",
  transactions: [],   // array of transaction objects
  accounts:     [],   // array of { name, type }
};

// Flat category list derived from the server-injected CATEGORIES object
const ALL_CATS = Object.values(CATEGORIES).flat();

// Map each category name → its group key
const CAT_TO_GROUP = {};
for (const [group, cats] of Object.entries(CATEGORIES)) {
  for (const cat of cats) CAT_TO_GROUP[cat] = group;
}

// ─── Navigation ──────────────────────────────────────────────────────────────

function goStep(n) {
  [1, 2, 3, 4].forEach(i => {
    document.getElementById("step" + i).classList.toggle("hidden", i !== n);
    const btn = document.getElementById("sn" + i);
    btn.classList.toggle("active", i === n);
    if (i < n) btn.classList.add("done");
    else        btn.classList.remove("done");
  });
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// ─── Step 1: Setup ───────────────────────────────────────────────────────────

function selectStructure(el, val) {
  document.querySelectorAll("#biz-structure .radio-card")
    .forEach(c => c.classList.remove("selected"));
  el.classList.add("selected");
  state.structure = val;
}

function selectAcctType(el, val) {
  document.querySelectorAll("[name=acct-type]")
    .forEach(c => c.closest(".radio-card").classList.remove("selected"));
  el.classList.add("selected");
  state.acctType = val;
}

// ─── Step 2: Import ───────────────────────────────────────────────────────────

function loadSample() {
  document.getElementById("acct-name").value = "TD Business Chequing";
  selectAcctType(document.getElementById("at-asset"), "asset");
  document.getElementById("csv-input").value = [
    "date,description,amount",
    "2024-01-05,Client payment - Acme Corp,3200.00",
    "2024-01-08,Office Depot - office supplies,-124.50",
    "2024-01-10,Google Ads,-450.00",
    "2024-01-15,Consulting income - freelance project,1800.00",
    "2024-01-18,Rent payment - Jan,-1200.00",
    "2024-01-20,Rogers Communications - internet,-89.99",
    "2024-01-22,Client payment - Beta Inc,2750.00",
    "2024-01-25,Payroll - staff wages,-2100.00",
    "2024-01-28,Bank service fee,-15.00",
    "2024-01-30,Interest earned,12.40",
    "2024-02-01,Client payment - Acme Corp,3200.00",
    "2024-02-05,Legal fees - contract review,-350.00",
    "2024-02-10,Insurance premium,-275.00",
    "2024-02-12,Travel - client lunch,-87.50",
    "2024-02-15,Rent payment - Feb,-1200.00",
    "2024-02-18,Consulting income - new client,2200.00",
    "2024-02-20,Office supplies - Amazon,-63.20",
    "2024-02-22,Payroll - staff wages,-2100.00",
    "2024-02-28,Interest earned,14.20",
  ].join("\n");
}

async function importTransactions() {
  const csvText  = document.getElementById("csv-input").value.trim();
  const acctName = document.getElementById("acct-name").value.trim() || "Account";
  const acctType = state.acctType;

  if (!csvText) {
    alert("Paste some CSV data first.");
    return;
  }

  // Show loading state
  document.getElementById("import-btn-text").textContent = "Importing…";
  document.getElementById("import-spinner").classList.remove("hidden");
  document.getElementById("import-btn").disabled = true;

  try {
    const res = await fetch("/api/parse-csv", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ csv_text: csvText, acct_name: acctName, acct_type: acctType }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || "Server error");
    }

    const data = await res.json();

    if (!data.transactions.length) {
      alert("No valid rows found. Check that your CSV has date, description, and amount columns.");
      return;
    }

    // Append to existing transactions (support multiple accounts)
    state.transactions = [...state.transactions, ...data.transactions];

    if (!state.accounts.find(a => a.name === acctName)) {
      state.accounts.push({ name: acctName, type: acctType });
    }

    renderAccountList();
    renderTxTable();

    // Clear inputs for next account
    document.getElementById("csv-input").value  = "";
    document.getElementById("acct-name").value = "";
    goStep(3);

  } catch (err) {
    alert("Import failed: " + err.message);
    console.error(err);
  } finally {
    document.getElementById("import-btn-text").textContent = "Import transactions →";
    document.getElementById("import-spinner").classList.add("hidden");
    document.getElementById("import-btn").disabled = false;
  }
}

function renderAccountList() {
  const container = document.getElementById("imported-accounts");
  if (!state.accounts.length) { container.innerHTML = ""; return; }

  const pills = state.accounts.map(a => `
    <span class="acct-pill">
      <i class="ti ti-${a.type === "asset" ? "building-bank" : "credit-card"}"></i>
      ${esc(a.name)}
      <span class="badge badge-${a.type === "asset" ? "asset" : "liability"}">${a.type}</span>
    </span>`).join("");

  container.innerHTML = `
    <div class="acct-list-label">Imported accounts</div>
    <div class="acct-pills">${pills}</div>`;
}

// ─── Step 3: Categorize ───────────────────────────────────────────────────────

function renderTxTable() {
  const tbody = document.getElementById("tx-body");
  if (!state.transactions.length) {
    tbody.innerHTML = '<tr><td colspan="7" class="empty-state">No transactions imported yet.</td></tr>';
    return;
  }

  // Build the <select> options once as a string template
  const optionsFor = (selected) =>
    ALL_CATS.map(c => `<option value="${esc(c)}"${c === selected ? " selected" : ""}>${esc(c)}</option>`).join("");

  tbody.innerHTML = state.transactions.map((tx, i) => {
    const amtStr  = (tx.amount >= 0 ? "+" : "") + "$" + Math.abs(tx.amount).toFixed(2);
    const amtCls  = tx.amount >= 0 ? "amount-pos" : "amount-neg";
    const typeCls = ["income","expense","asset","liability","equity","transfer"].includes(tx.tx_type)
      ? tx.tx_type : "transfer";
    const badge   = `<span class="badge badge-${typeCls}">${esc(tx.tx_type || "—")}</span>`;
    const aiIcon  = tx.ai_suggested
      ? `<i class="ti ti-sparkles" title="AI suggested" style="color:var(--text-pro);font-size:15px"></i>`
      : (tx.user_overridden
        ? `<i class="ti ti-pencil" title="Manually set" style="color:var(--text-muted);font-size:15px"></i>`
        : "");

    return `<tr>
      <td class="col-date" style="color:var(--text-muted);font-size:12px">${esc(tx.date)}</td>
      <td class="col-desc">${esc(tx.description)}</td>
      <td class="col-acct" style="font-size:12px;color:var(--text-muted)">${esc(tx.account_name)}</td>
      <td class="col-amount"><span class="${amtCls}">${amtStr}</span></td>
      <td class="col-cat">
        <select class="cat-select" onchange="updateCat(${i}, this.value)">${optionsFor(tx.category)}</select>
      </td>
      <td class="col-type">${badge}</td>
      <td class="col-ai" style="text-align:center">${aiIcon}</td>
    </tr>`;
  }).join("");

  const total   = state.transactions.length;
  const aiCount = state.transactions.filter(t => t.ai_suggested).length;
  document.getElementById("cat-summary-text").textContent =
    `${total} transaction${total !== 1 ? "s" : ""} imported across ${state.accounts.length} account${state.accounts.length !== 1 ? "s" : ""}. ` +
    `${aiCount} auto-categorized — review and adjust as needed.`;
}

function updateCat(i, cat) {
  state.transactions[i].category      = cat;
  state.transactions[i].user_overridden = true;
  state.transactions[i].ai_suggested   = false;
  state.transactions[i].tx_type        = CAT_TO_GROUP[cat] || "transfer";
  renderTxTable();
}

// ─── Step 4: Statements ───────────────────────────────────────────────────────

async function generateStatements() {
  if (!state.transactions.length) {
    alert("No transactions to generate statements from.");
    return;
  }

  const payload = {
    transactions:  state.transactions,
    biz_name:      document.getElementById("biz-name").value.trim() || "Your Business",
    structure:     state.structure,
    period_start:  document.getElementById("period-start").value.trim(),
    period_end:    document.getElementById("period-end").value.trim(),
  };

  try {
    const res = await fetch("/api/statements", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify(payload),
    });

    if (!res.ok) throw new Error("Failed to generate statements");
    const data = await res.json();
    renderStatements(data);
    goStep(4);

  } catch (err) {
    alert("Statement generation failed: " + err.message);
    console.error(err);
  }
}

function fmt(n) {
  const abs = Math.abs(n).toLocaleString("en-CA", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  return n < 0 ? `($${abs})` : `$${abs}`;
}

function fmtCls(n) { return n >= 0 ? "stmt-amount-pos" : "stmt-amount-neg"; }

function renderStatements(data) {
  const { biz_name, period_start, period_end, income_statement: is, balance_sheet: bs } = data;

  document.getElementById("stmt-company-name").textContent = biz_name;
  document.getElementById("stmt-period-label").textContent =
    (period_start && period_end) ? `For the period ${period_start} to ${period_end}` : "Financial statements";

  // ── Income statement ──────────────────────────────────────
  const revenueRows = Object.entries(is.revenue)
    .map(([cat, amt]) => `
      <div class="stmt-row indent">
        <span>${esc(cat)}</span>
        <span class="${fmtCls(amt)}">${fmt(amt)}</span>
      </div>`).join("");

  const opExpRows = Object.entries(is.operating_expenses)
    .map(([cat, amt]) => `
      <div class="stmt-row indent">
        <span>${esc(cat)}</span>
        <span class="stmt-amount-neg">${fmt(-amt)}</span>
      </div>`).join("");

  document.getElementById("stmt-income").innerHTML = `
    <div class="stmt-card">
      <div class="stmt-section">
        <div class="stmt-section-title">Revenue</div>
        ${revenueRows || '<div class="stmt-row indent" style="color:var(--text-muted)">No revenue transactions</div>'}
        <div class="stmt-row total">
          <span>Total revenue</span>
          <span class="${fmtCls(is.total_revenue)}">${fmt(is.total_revenue)}</span>
        </div>
      </div>

      <div class="stmt-section">
        <div class="stmt-section-title">Cost of goods sold</div>
        <div class="stmt-row indent">
          <span>Cost of goods sold</span>
          <span class="stmt-amount-neg">${fmt(-is.cogs)}</span>
        </div>
        <div class="stmt-row total">
          <span>Gross profit</span>
          <span class="${fmtCls(is.gross_profit)}">${fmt(is.gross_profit)}</span>
        </div>
      </div>

      <div class="stmt-section">
        <div class="stmt-section-title">Operating expenses</div>
        ${opExpRows || '<div class="stmt-row indent" style="color:var(--text-muted)">No operating expenses</div>'}
        <div class="stmt-row total">
          <span>Total operating expenses</span>
          <span class="stmt-amount-neg">${fmt(-is.total_op_expenses)}</span>
        </div>
      </div>

      <div class="stmt-row grand-total">
        <span>Operating income (EBIT)</span>
        <span class="${fmtCls(is.ebit)}">${fmt(is.ebit)}</span>
      </div>

      ${is.tax_expense ? `
        <div class="stmt-row indent">
          <span>Tax expense</span>
          <span class="stmt-amount-neg">${fmt(-is.tax_expense)}</span>
        </div>` : ""}

      <div class="stmt-row grand-total" style="font-size:15px">
        <span>Net income</span>
        <span class="${fmtCls(is.net_income)}">${fmt(is.net_income)}</span>
      </div>
    </div>`;

  // ── Balance sheet ─────────────────────────────────────────
  const assetRows = Object.entries(bs.assets)
    .map(([cat, amt]) => `
      <div class="stmt-row indent">
        <span>${esc(cat)}</span>
        <span class="stmt-amount-pos">${fmt(amt)}</span>
      </div>`).join("");

  const liabRows = Object.entries(bs.liabilities)
    .map(([cat, amt]) => `
      <div class="stmt-row indent">
        <span>${esc(cat)}</span>
        <span class="stmt-amount-neg">${fmt(-amt)}</span>
      </div>`).join("");

  document.getElementById("stmt-balance").innerHTML = `
    <div class="stmt-card">
      <div class="balance-grid">
        <div>
          <div class="stmt-section">
            <div class="stmt-section-title">Assets</div>
            ${assetRows}
            ${bs.asset_account_sum !== 0 ? `
              <div class="stmt-row indent">
                <span>Account balances (net)</span>
                <span class="${fmtCls(bs.asset_account_sum)}">${fmt(bs.asset_account_sum)}</span>
              </div>` : ""}
            <div class="stmt-row grand-total">
              <span>Total assets</span>
              <span class="${fmtCls(bs.total_assets)}">${fmt(bs.total_assets)}</span>
            </div>
          </div>
        </div>
        <div>
          <div class="stmt-section">
            <div class="stmt-section-title">Liabilities</div>
            ${liabRows}
            ${bs.liab_account_sum !== 0 ? `
              <div class="stmt-row indent">
                <span>Account balances (net)</span>
                <span class="stmt-amount-neg">${fmt(-bs.liab_account_sum)}</span>
              </div>` : ""}
            <div class="stmt-row total">
              <span>Total liabilities</span>
              <span class="stmt-amount-neg">${fmt(-bs.total_liabilities)}</span>
            </div>
          </div>

          <div class="stmt-section" style="margin-top:0.75rem">
            <div class="stmt-section-title">${esc(bs.equity_label)}</div>
            ${bs.capital_contributions ? `
              <div class="stmt-row indent">
                <span>Capital contributions</span>
                <span class="stmt-amount-pos">${fmt(bs.capital_contributions)}</span>
              </div>` : ""}
            <div class="stmt-row indent">
              <span>Retained earnings (net income)</span>
              <span class="${fmtCls(bs.retained_earnings)}">${fmt(bs.retained_earnings)}</span>
            </div>
            ${bs.distributions ? `
              <div class="stmt-row indent">
                <span>Distributions</span>
                <span class="stmt-amount-neg">${fmt(-bs.distributions)}</span>
              </div>` : ""}
            <div class="stmt-row total">
              <span>Total ${esc(bs.equity_label.toLowerCase())}</span>
              <span class="${fmtCls(bs.total_equity)}">${fmt(bs.total_equity)}</span>
            </div>
          </div>

          <div class="stmt-row grand-total">
            <span>Total liabilities + equity</span>
            <span class="${fmtCls(-bs.total_liabilities + bs.total_equity)}">${fmt(-bs.total_liabilities + bs.total_equity)}</span>
          </div>
        </div>
      </div>
    </div>`;

  // ── Transaction log ───────────────────────────────────────
  const txRows = state.transactions.map(tx => {
    const amtStr = (tx.amount >= 0 ? "+" : "") + "$" + Math.abs(tx.amount).toFixed(2);
    const amtCls = tx.amount >= 0 ? "amount-pos" : "amount-neg";
    return `<tr>
      <td style="font-size:12px;color:var(--text-muted)">${esc(tx.date)}</td>
      <td>${esc(tx.description)}</td>
      <td style="font-size:12px;color:var(--text-muted)">${esc(tx.account_name)}</td>
      <td><span class="badge badge-${tx.acct_type === "asset" ? "asset" : "liability"}">${esc(tx.acct_type)}</span></td>
      <td style="text-align:right"><span class="${amtCls}">${amtStr}</span></td>
      <td style="font-size:12px">${esc(tx.category)}</td>
    </tr>`;
  }).join("");

  document.getElementById("stmt-txlog").innerHTML = `
    <div class="stmt-card" style="overflow-x:auto">
      <table class="tx-table" style="table-layout:auto">
        <thead><tr>
          <th>Date</th><th>Description</th><th>Account</th>
          <th>Type</th><th style="text-align:right">Amount</th><th>Category</th>
        </tr></thead>
        <tbody>${txRows || '<tr><td colspan="6" class="empty-state">No transactions.</td></tr>'}</tbody>
      </table>
    </div>`;
}

function showStmt(which) {
  ["income", "balance", "txlog"].forEach((s, i) => {
    document.getElementById("stmt-" + s).classList.toggle("hidden", s !== which);
    document.querySelectorAll(".tab")[i].classList.toggle("active", s === which);
  });
}

// ─── Export ───────────────────────────────────────────────────────────────────

async function exportCSV() {
  try {
    const res = await fetch("/api/export-csv", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ transactions: state.transactions }),
    });
    if (!res.ok) throw new Error("Export failed");
    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href     = url;
    a.download = "transactions_categorized.csv";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (err) {
    alert("Export failed: " + err.message);
  }
}

// ─── Utility ─────────────────────────────────────────────────────────────────

function esc(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
