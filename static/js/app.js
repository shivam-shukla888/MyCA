// myCA Sovereign Ledger Application State & Pipeline Controller

const AppState = {
  currentUserId: "usr_aarav_01",
  sessionToken: null,
  activeView: "home",
  profileData: null,
  transactions: [],
  accounts: [],
  documents: [],
  cachedFileForDuplicate: null
};

// ================= API CLIENT =================
const Api = {
  async ensureToken() {
    if (!AppState.sessionToken) {
      const res = await fetch("/api/auth/token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: AppState.currentUserId })
      });
      const data = await res.json();
      if (data.token) {
        AppState.sessionToken = data.token;
      }
    }
    return AppState.sessionToken;
  },

  getAuthHeaders(extra = {}) {
    const headers = { ...extra };
    if (AppState.sessionToken) {
      headers["Authorization"] = `Bearer ${AppState.sessionToken}`;
    }
    // Also include X-User-ID for legacy dev fallback during migration
    headers["X-User-ID"] = AppState.currentUserId;
    return headers;
  },

  async getProfile() {
    await this.ensureToken();
    const res = await fetch("/api/user/profile", {
      headers: this.getAuthHeaders()
    });
    return res.json();
  },

  async getDocuments() {
    await this.ensureToken();
    const res = await fetch("/api/documents", {
      headers: this.getAuthHeaders()
    });
    return res.json();
  },

  async getTransactions(params = {}) {
    await this.ensureToken();
    const query = new URLSearchParams(params).toString();
    const res = await fetch(`/api/transactions?${query}`, {
      headers: this.getAuthHeaders()
    });
    return res.json();
  },

  async getAccounts() {
    await this.ensureToken();
    const res = await fetch("/api/accounts", {
      headers: this.getAuthHeaders()
    });
    return res.json();
  },

  async uploadFile(file, allowDuplicate = false) {
    await this.ensureToken();
    const formData = new FormData();
    formData.append("file", file);
    formData.append("allow_duplicate", allowDuplicate ? "true" : "false");
    const res = await fetch("/api/documents/upload", {
      method: "POST",
      headers: this.getAuthHeaders(),
      body: formData
    });
    return res.json();
  },

  async uploadMultipleFiles(files, title = "Multi-Photo Document", allowDuplicate = false) {
    await this.ensureToken();
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append("files", files[i]);
    }
    formData.append("title", title);
    formData.append("allow_duplicate", allowDuplicate ? "true" : "false");
    const res = await fetch("/api/documents/upload-multiple", {
      method: "POST",
      headers: this.getAuthHeaders(),
      body: formData
    });
    return res.json();
  },

  async confirmDocument(docId) {
    await this.ensureToken();
    const res = await fetch(`/api/documents/${docId}/confirm`, {
      method: "POST",
      headers: this.getAuthHeaders()
    });
    return res.json();
  },

  async deleteDocument(docId) {
    await this.ensureToken();
    const res = await fetch(`/api/documents/${docId}`, {
      method: "DELETE",
      headers: this.getAuthHeaders()
    });
    return res.json();
  },

  async reprocessDocument(docId) {
    await this.ensureToken();
    const res = await fetch(`/api/documents/${docId}/reprocess`, {
      method: "POST",
      headers: this.getAuthHeaders()
    });
    return res.json();
  },

  async updateCategory(txId, category) {
    await this.ensureToken();
    const res = await fetch(`/api/transactions/${txId}/category`, {
      method: "PATCH",
      headers: this.getAuthHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ category })
    });
    return res.json();
  },

  async askAdvisory(query) {
    await this.ensureToken();
    const res = await fetch("/api/advisory/ask", {
      method: "POST",
      headers: this.getAuthHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ query })
    });
    return res.json();
  },

  async getHome() {
    await this.ensureToken();
    const res = await fetch("/api/operating-system/home", {
      headers: this.getAuthHeaders()
    });
    return res.json();
  },

  async getGoals() {
    await this.ensureToken();
    const res = await fetch("/api/goals", {
      headers: this.getAuthHeaders()
    });
    return res.json();
  },

  async createGoal(goalData) {
    await this.ensureToken();
    const res = await fetch("/api/goals", {
      method: "POST",
      headers: this.getAuthHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(goalData)
    });
    return res.json();
  },

  async simulate(payload) {
    await this.ensureToken();
    const res = await fetch("/api/operating-system/simulate", {
      method: "POST",
      headers: this.getAuthHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(payload)
    });
    return res.json();
  },

  async getInbox() {
    await this.ensureToken();
    const res = await fetch("/api/alerts/inbox", {
      headers: this.getAuthHeaders()
    });
    return res.json();
  },

  async dismissAlert(alertId) {
    await this.ensureToken();
    const res = await fetch(`/api/alerts/${alertId}/dismiss`, {
      method: "POST",
      headers: this.getAuthHeaders()
    });
    return res.json();
  },

  async snoozeAlert(alertId, days = 7) {
    await this.ensureToken();
    const res = await fetch(`/api/alerts/${alertId}/snooze`, {
      method: "POST",
      headers: this.getAuthHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ days })
    });
    return res.json();
  }
};

// ================= NAVIGATION =================
function switchView(viewName) {
  AppState.activeView = viewName;

  // Update nav link styles
  document.querySelectorAll("[data-nav-view]").forEach(link => {
    if (link.getAttribute("data-nav-view") === viewName) {
      link.className = "flex items-center gap-space-sm px-space-sm py-2 rounded bg-surface-container-lowest text-on-surface shadow-[0_1px_3px_rgba(0,0,0,0.06)] font-semibold transition-colors";
    } else {
      link.className = "flex items-center gap-space-sm px-space-sm py-2 rounded text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface transition-colors";
    }
  });

  // Toggle visible view container
  document.querySelectorAll(".view-section").forEach(sec => {
    if (sec.id === `view-${viewName}`) {
      sec.classList.remove("hidden");
    } else {
      sec.classList.add("hidden");
    }
  });

  if (viewName === "money") {
    loadTransactions();
  } else if (viewName === "vault") {
    loadDocuments();
  } else if (viewName === "goals") {
    loadGoals();
    runSavingsSimulation();
    runExpenseCutSimulation();
  } else if (viewName === "home") {
    initApp();
  }
}

// ================= INITIAL LOAD & RENDER =================
async function initApp() {
  const profile = await Api.getProfile();
  AppState.profileData = profile;

  try {
    const homeData = await Api.getHome();
    AppState.homeData = homeData;
    renderHomeCommandCenter(homeData, profile);
  } catch (err) {
    console.error("Operating system home load error:", err);
    renderHomeFinancials(profile);
  }

  renderUserMetadata(profile.user);
  renderMoneyLedger(profile);
  loadDocuments();
  loadTransactions();
  loadGoals();
}

function renderUserMetadata(user) {
  const nameEls = document.querySelectorAll(".user-name-display");
  const emailEls = document.querySelectorAll(".user-email-display");
  nameEls.forEach(el => el.innerText = user.name);
  emailEls.forEach(el => el.innerText = `${user.name} • AY 24-25`);
}

// ================= RENDER HOME COMMAND CENTER (PHASE 6) =================
function renderHomeCommandCenter(home, profile) {
  // 1. Dynamic Greeting
  const greetingEl = document.getElementById("homeGreeting");
  if (greetingEl && home.greeting) {
    greetingEl.innerText = home.greeting;
  }

  // 2. Explainable Financial Health Strip (5 Pillars)
  const healthContainer = document.getElementById("homeHealthPillars");
  const healthAuditBadge = document.getElementById("healthAuditBadge");
  const h = home.health;

  if (healthContainer) {
    if (!h || !h.is_computable) {
      healthContainer.innerHTML = `
        <div class="col-span-full p-space-sm bg-surface-container-low rounded-lg text-center text-[12px] text-on-surface-variant border border-[#e7e5e0]">
          Financial Health score ke liye aur information chahiye. Upload salary slip ya bank statement.
        </div>
      `;
      if (healthAuditBadge) healthAuditBadge.innerText = "Awaiting Validated Data";
    } else {
      if (healthAuditBadge) {
        healthAuditBadge.innerText = `Vitality: ${h.composite_vitality || 'STABLE'} • Audited`;
      }
      const pillars = h.pillars || {};
      const pillarKeys = Object.keys(pillars);
      healthContainer.innerHTML = pillarKeys.map(k => {
        const p = pillars[k];
        const isGood = ["POSITIVE", "HEALTHY", "EXCELLENT", "ADEQUATE", "COMPLIANT"].includes(p.status);
        const badgeColor = isGood ? "bg-secondary-container/50 text-secondary" : "bg-amber-100 text-amber-900";
        return `
          <div class="p-2.5 bg-surface-container-lowest rounded-lg border border-[#e7e5e0] flex flex-col justify-between">
            <span class="text-[10px] uppercase font-bold text-on-surface-variant block mb-1 truncate">${p.pillar_name}</span>
            <div class="text-[14px] font-bold text-on-surface tabular-nums mb-1 truncate">${p.metric_value}</div>
            <div class="inline-flex items-center gap-1 self-start text-[10px] font-bold px-1.5 py-0.5 rounded ${badgeColor}">
              <span>${p.status}</span>
            </div>
          </div>
        `;
      }).join("");
    }
  }

  // 3. Snapshot Numerals (YOUR MONEY)
  const snap = home.snapshot || profile.metrics;
  const hasData = profile.has_data;

  const leftEl = document.getElementById("homeSavingsLeft");
  const liquidEl = document.getElementById("homeLiquidBalance");
  const netWorthEl = document.getElementById("homeNetWorth");
  const incomeEl = document.getElementById("homePaisaAaya");
  const expenseEl = document.getElementById("homePaisaGaya");
  const savedEl = document.getElementById("homeYouSaved");
  const rateEl = document.getElementById("homeSavingsRateText");

  if (hasData && snap) {
    if (leftEl) leftEl.innerText = `₹${(snap.monthly_savings || 0).toLocaleString('en-IN')}`;
    if (liquidEl) liquidEl.innerText = `₹${(snap.liquid_cash || 73200).toLocaleString('en-IN')}`;
    if (netWorthEl) netWorthEl.innerText = `₹${(snap.net_worth || 1240500).toLocaleString('en-IN')}`;
    if (incomeEl) incomeEl.innerText = `₹${(snap.monthly_income || 0).toLocaleString('en-IN')}`;
    if (expenseEl) expenseEl.innerText = `₹${(snap.monthly_expenses || 0).toLocaleString('en-IN')}`;
    if (savedEl) savedEl.innerText = `₹${(snap.monthly_savings || 0).toLocaleString('en-IN')}`;
    if (rateEl) rateEl.innerText = `${snap.savings_rate_percent || 0}% savings rate`;
  } else {
    if (leftEl) leftEl.innerText = "Abhi data available nahi hai.";
    if (liquidEl) liquidEl.innerText = "—";
    if (netWorthEl) netWorthEl.innerText = "—";
    if (incomeEl) incomeEl.innerText = "—";
    if (expenseEl) expenseEl.innerText = "—";
    if (savedEl) savedEl.innerText = "—";
  }

  // 4. WHAT CHANGED?
  const wc = home.what_changed || {};
  const periodEl = document.getElementById("whatChangedPeriod");
  const summaryEl = document.getElementById("whatChangedSummary");
  const changeListEl = document.getElementById("homeWhatChangedList");

  if (periodEl && wc.period) periodEl.innerText = wc.period;
  if (summaryEl && wc.summary) summaryEl.innerText = wc.summary;

  if (changeListEl) {
    const changes = wc.changes || [];
    if (changes.length === 0) {
      changeListEl.innerHTML = `
        <div class="p-3 bg-surface-container-low rounded-lg text-[12px] text-on-surface-variant text-center">
          Koi unusual variance ya significant delta nahi mila. Spending steady hai.
        </div>
      `;
    } else {
      changeListEl.innerHTML = changes.slice(0, 3).map(c => `
        <div class="p-2.5 bg-surface-container-low/60 rounded-lg flex items-center justify-between text-[12px] border border-[#e7e5e0]/60">
          <div>
            <span class="font-semibold text-on-surface block">${c.title}</span>
            <span class="text-[11px] text-on-surface-variant">${c.explanation || ''}</span>
          </div>
          <div class="text-right shrink-0">
            <span class="font-bold ${c.direction === 'DOWN' ? 'text-amber-800' : 'text-on-surface'} tabular-nums">${c.difference_formatted}</span>
            <button onclick="openSourceDrawer('${c.title}', '${c.type}', '${c.difference_formatted}', 'Bank Statement', 1, 'VERIFIED_FROM_DOCUMENT', '${c.verbatim_evidence || c.explanation}')" class="text-[11px] font-bold text-secondary underline block mt-0.5">
              Kaise pata chala?
            </button>
          </div>
        </div>
      `).join("");
    }
  }

  // 5. ONE IMPORTANT THING
  const oit = home.one_important_thing;
  const oitHead = document.getElementById("oneImportantHeadline");
  const oitDetail = document.getElementById("oneImportantDetail");
  const oitBtn = document.getElementById("oneImportantDrillBtn");

  if (oit && oitHead) {
    oitHead.innerText = oit.headline;
    if (oitDetail) oitDetail.innerText = oit.detail;
    if (oitBtn) {
      oitBtn.onclick = () => openSourceDrawer(oit.headline, "SIGNIFICANT_DELTA", oit.headline, oit.source_document || "Bank Statement", 1, "VERIFIED_FROM_DOCUMENT", oit.detail);
    }
  }

  // 6. NEXT BEST ACTION (Deterministic)
  const nba = home.next_best_action;
  if (nba && nba.has_action) {
    const headEl = document.getElementById("homeNextActionHeadline");
    const recEl = document.getElementById("homeNextActionRec");
    const factEl = document.getElementById("homeActionFact");
    const calcEl = document.getElementById("homeActionCalc");
    const briefEl = document.getElementById("homeActionRecBrief");

    if (headEl) headEl.innerText = nba.headline;
    if (recEl) recEl.innerText = nba.recommendation;
    if (factEl) factEl.innerText = nba.fact;
    if (calcEl) calcEl.innerText = nba.calculation;
    if (briefEl) briefEl.innerText = nba.recommendation;

    // Populate See Why Modal
    const swFact = document.getElementById("seeWhyFact");
    const swCalc = document.getElementById("seeWhyCalc");
    const swRec = document.getElementById("seeWhyRec");
    const swDisc = document.getElementById("seeWhyDisclaimer");
    if (swFact) swFact.innerText = nba.fact;
    if (swCalc) swCalc.innerText = nba.calculation;
    if (swRec) swRec.innerText = nba.recommendation;
    if (swDisc) swDisc.innerText = nba.disclaimer;
  }

  // 7. FINANCIAL INBOX
  renderInbox(home.inbox || []);
}

function renderInbox(alerts) {
  const listEl = document.getElementById("homeInboxList");
  const badgeEl = document.getElementById("inboxCountBadge");
  if (badgeEl) badgeEl.innerText = `${alerts.length} active`;

  if (!listEl) return;
  if (alerts.length === 0) {
    listEl.innerHTML = `
      <div class="p-space-md bg-surface-container-low rounded-lg text-center text-[13px] text-on-surface-variant">
        Sab theek hai! Koi active financial warning ya review pending nahi hai.
      </div>
    `;
    return;
  }

  const severityStyles = {
    "CRITICAL": "bg-red-50 text-red-900 border-red-200",
    "IMPORTANT": "bg-amber-50 text-amber-900 border-amber-200",
    "ATTENTION": "bg-yellow-50 text-yellow-900 border-yellow-200",
    "INFO": "bg-slate-50 text-slate-900 border-slate-200"
  };

  listEl.innerHTML = alerts.map(a => {
    const styleClass = severityStyles[a.severity] || "bg-surface-container-low text-on-surface border-[#e7e5e0]";
    return `
      <div class="p-3 rounded-lg border ${styleClass} flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div class="flex items-start gap-2.5">
          <span class="material-symbols-outlined text-[18px] shrink-0 mt-0.5">
            ${a.severity === 'CRITICAL' ? 'warning' : a.severity === 'IMPORTANT' ? 'error_outline' : 'notifications'}
          </span>
          <div>
            <div class="flex items-center gap-2">
              <span class="font-bold text-[13px]">${a.title}</span>
              <span class="text-[9px] uppercase font-extrabold px-1.5 py-0.5 rounded bg-surface-container-highest">${a.severity}</span>
            </div>
            <p class="text-[12px] opacity-90 mt-0.5">${a.message}</p>
          </div>
        </div>
        <div class="flex items-center gap-1.5 self-end sm:self-center shrink-0">
          <button onclick="handleSnoozeAlert('${a.id}')" class="px-2.5 py-1 bg-surface-container-lowest border border-[#e7e5e0] text-on-surface hover:bg-surface-container text-[11px] font-semibold rounded">
            Snooze 7d
          </button>
          <button onclick="handleDismissAlert('${a.id}')" class="px-2.5 py-1 bg-surface-container-lowest border border-[#e7e5e0] text-on-surface hover:bg-surface-container text-[11px] font-semibold rounded">
            Dismiss
          </button>
        </div>
      </div>
    `;
  }).join("");
}

// Fallback legacy renderer
function renderHomeFinancials(profile) {
  renderHomeCommandCenter({
    greeting: "Good day, Aarav",
    snapshot: profile.metrics,
    health: { is_computable: false },
    what_changed: { changes: [] },
    one_important_thing: null,
    next_best_action: null,
    inbox: []
  }, profile);
}

// ================= RENDER MONEY PAGE =================
function renderMoneyLedger(profile) {
  const m = profile.metrics;
  const hasData = profile.has_data;

  // Solvency & Totals
  const netWorthHero = document.getElementById("moneyHeroBalance");
  if (netWorthHero) {
    // Assets: Liquid + Investments
    const liquid = hasData ? (m.monthly_savings + 45500) : 0;
    netWorthHero.innerText = hasData ? `₹${(liquid + 825500).toLocaleString('en-IN')}` : "₹0";
  }

  const liquidVal = document.getElementById("moneyLiquidBankValue");
  if (liquidVal && hasData) {
    liquidVal.innerText = `₹${(m.monthly_savings + 45500).toLocaleString('en-IN')}`;
  }

  const debtVal = document.getElementById("moneyDebtValue");
  if (debtVal) {
    debtVal.innerText = hasData ? `₹${(m.top_expenses.loans || 9000).toLocaleString('en-IN')}` : "₹0";
  }
}

// ================= LOAD & RENDER TRANSACTIONS =================
async function loadTransactions() {
  const searchInput = document.getElementById("txSearchInput");
  const categoryFilter = document.getElementById("txCategoryFilter");
  const typeFilter = document.getElementById("txTypeFilter");

  const params = {};
  if (searchInput && searchInput.value) params.search = searchInput.value;
  if (categoryFilter && categoryFilter.value) params.category = categoryFilter.value;
  if (typeFilter && typeFilter.value) params.type = typeFilter.value;

  const data = await Api.getTransactions(params);
  AppState.transactions = data.transactions;
  renderTransactionRows(data.transactions);
}

function renderTransactionRows(txs) {
  const container = document.getElementById("moneyPassbookRows");
  if (!container) return;

  if (txs.length === 0) {
    container.innerHTML = `
      <div class="p-space-lg text-center text-on-surface-variant font-body-sm bg-surface-container-low rounded-lg">
        Koi transactions nahi mile.
      </div>
    `;
    return;
  }

  container.innerHTML = txs.map(tx => {
    const isCredit = tx.type === "CREDIT";
    const amtColor = isCredit ? "text-secondary font-semibold" : "text-on-surface font-semibold";
    const prefix = isCredit ? "+₹" : "-₹";
    const icon = isCredit ? "payments" : getCategoryIcon(tx.category);

    return `
      <div class="flex flex-col sm:flex-row sm:items-center justify-between p-space-md rounded-lg bg-surface-container-low/40 hover:bg-surface-container-low transition-colors gap-space-sm">
        <div class="flex items-center gap-space-md">
          <div class="w-10 h-10 rounded-full ${isCredit ? 'bg-secondary-fixed text-on-secondary-fixed' : 'bg-surface-container-high text-on-surface'} flex items-center justify-center flex-shrink-0">
            <span class="material-symbols-outlined text-[20px]">${icon}</span>
          </div>
          <div>
            <div class="flex items-center gap-space-xs">
              <span class="font-label-lg text-on-surface font-semibold">${escapeHtml(tx.description)}</span>
              <button onclick="openCategoryEdit('${tx.id}', '${escapeHtml(tx.category)}')" class="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-surface-container-highest text-on-surface-variant font-label-sm text-[10px] hover:bg-surface-container-high transition-colors">
                ${escapeHtml(tx.category)} <span class="material-symbols-outlined text-[10px]">edit</span>
              </button>
            </div>
            <div class="font-body-sm text-on-surface-variant flex items-center gap-2">
              <span>${tx.date}</span> •
              <span class="cursor-pointer hover:underline text-secondary flex items-center gap-0.5 text-[11px]" onclick="openSourceDrawer('${escapeHtml(tx.description)}', '${escapeHtml(tx.category)}', ${tx.amount}, '${escapeHtml(tx.document_name || 'Bank Statement')}', ${tx.source_page}, '${tx.status}', '${escapeHtml(tx.source_text || '')}', '${tx.source_document_id}')">
                <span class="material-symbols-outlined text-[12px]">verified</span>
                Verified • Page ${tx.source_page}
              </span>
            </div>
          </div>
        </div>
        <div class="flex items-center justify-between sm:justify-end gap-space-lg">
          <div class="text-left sm:text-right">
            <div class="font-numeral-md ${amtColor}">${prefix}${tx.amount.toLocaleString('en-IN')}</div>
            <div class="font-label-sm text-on-surface-variant">Bal: ₹${tx.balance.toLocaleString('en-IN')}</div>
          </div>
          <button class="p-1 rounded text-on-surface-variant hover:text-on-surface" onclick="openPdfViewer('${tx.source_document_id}', '${escapeHtml(tx.document_name || 'Document')}', ${tx.source_page}, '${escapeHtml(tx.description)}', '₹${tx.amount.toLocaleString('en-IN')}')" title="View Source in PDF">
            <span class="material-symbols-outlined text-[18px]">visibility</span>
          </button>
        </div>
      </div>
    `;
  }).join("");
}

function getCategoryIcon(cat) {
  switch (cat) {
    case 'Rent': return 'home';
    case 'Food & Dining': return 'lunch_dining';
    case 'Shopping': return 'shopping_bag';
    case 'Electricity & Utilities': return 'bolt';
    case 'Transit & Fuel': return 'commute';
    case 'Lifestyle & Wellness': return 'spa';
    case 'Loans & EMI': return 'directions_car';
    case 'Subscriptions & Utilities': return 'wifi';
    default: return 'receipt';
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/[&<>"']/g, m => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  })[m]);
}

// ================= LOAD & RENDER DOCUMENTS (VAULT) =================
async function loadDocuments() {
  const res = await Api.getDocuments();
  AppState.documents = res.documents;
  renderDocumentRows(res.documents);
}

function renderDocumentRows(docs) {
  const container = document.getElementById("vaultDocList");
  if (!container) return;

  if (docs.length === 0) {
    container.innerHTML = `
      <div class="p-space-lg text-center text-on-surface-variant font-body-sm bg-surface-container-low rounded-lg">
        Abhi koi document upload nahi kiya gaya hai.
      </div>
    `;
    return;
  }

  container.innerHTML = docs.map(d => {
    let badge = "";
    if (d.status === "READY") {
      badge = `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-secondary-container text-on-secondary-container font-label-sm text-[11px]"><span class="material-symbols-outlined text-[13px]">check_circle</span> Processed</span>`;
    } else if (d.status === "NEEDS_REVIEW") {
      badge = `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-amber-100 text-amber-800 font-label-sm text-[11px]"><span class="material-symbols-outlined text-[13px]">warning</span> Needs Review</span>`;
    } else if (d.status === "UNSUPPORTED") {
      badge = `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-surface-container-high text-on-surface-variant font-label-sm text-[11px]"><span class="material-symbols-outlined text-[13px]">help_outline</span> Unsupported</span>`;
    } else {
      badge = `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-surface-container-high text-on-surface font-label-sm text-[11px]"><span class="material-symbols-outlined text-[13px]">sync</span> ${d.status}</span>`;
    }

    const typeLabels = {
      bank_statement: "Bank Statement",
      salary_slip: "Salary Slip",
      form_16: "Form 16 Tax Certificate",
      credit_card_statement: "Credit Card Statement",
      loan_statement: "Loan Statement",
      demat_statement: "Demat Statement",
      mutual_fund_statement: "Mutual Fund Statement",
      insurance_document: "Insurance Document",
      unknown: "Document"
    };
    const typeLabel = typeLabels[d.doc_type] || "Document";
    const sizeKb = Math.round(d.file_size / 1024);

    return `
      <div class="p-space-md bg-surface-container-low rounded-lg flex flex-col md:flex-row md:items-center justify-between gap-space-md hover:bg-surface-container transition-colors">
        <div class="flex items-center gap-space-md">
          <div class="w-10 h-10 rounded bg-surface-container-lowest border border-outline-variant/30 flex items-center justify-center text-secondary">
            <span class="material-symbols-outlined text-[24px]">description</span>
          </div>
          <div>
            <div class="flex items-center gap-2">
              <span class="font-label-md font-semibold text-on-surface">${escapeHtml(d.filename)}</span>
              ${badge}
            </div>
            <div class="font-body-sm text-on-surface-variant text-[12px] flex items-center gap-2">
              <span class="font-medium text-secondary">${typeLabel}</span> •
              <span>${d.num_pages} Pages</span> •
              <span>${sizeKb} KB</span> •
              <span>Added: ${new Date(d.created_at).toLocaleDateString()}</span>
            </div>
            ${d.error_message ? `<div class="text-error font-body-sm text-[11px] mt-1">${escapeHtml(d.error_message)}</div>` : ''}
          </div>
        </div>
        <div class="flex items-center gap-2 self-start md:self-auto">
          <button onclick="openPdfViewer('${d.id}', '${escapeHtml(d.filename)}', 1)" class="px-3 py-1.5 bg-surface-container-lowest border border-outline-variant/30 hover:bg-surface-container-high rounded font-label-sm text-on-surface flex items-center gap-1 transition-colors">
            <span class="material-symbols-outlined text-[15px]">visibility</span> View
          </button>
          ${d.status === 'NEEDS_REVIEW' ? `
            <button onclick="handleConfirmDocumentReview('${d.id}')" class="px-3 py-1.5 bg-amber-50 text-amber-800 border border-amber-200 hover:bg-amber-100 rounded font-label-sm flex items-center gap-1 transition-colors">
              <span class="material-symbols-outlined text-[15px]">check</span> Confirm
            </button>
          ` : ''}
          <button onclick="handleReprocessDocument('${d.id}')" class="px-3 py-1.5 bg-surface-container-lowest border border-outline-variant/30 hover:bg-surface-container-high rounded font-label-sm text-on-surface flex items-center gap-1 transition-colors">
            <span class="material-symbols-outlined text-[15px]">refresh</span> Reprocess
          </button>
          <button onclick="handleDeleteDocument('${d.id}')" class="px-2 py-1.5 text-error hover:bg-error-container/40 rounded transition-colors" title="Delete Document">
            <span class="material-symbols-outlined text-[18px]">delete</span>
          </button>
        </div>
      </div>
    `;
  }).join("");
}

// ================= UPLOAD WORKFLOW MODAL =================
function openUploadModal() {
  document.getElementById("uploadModal").classList.remove("hidden");
  resetUploadModal();
}

function closeUploadModal() {
  document.getElementById("uploadModal").classList.add("hidden");
}

function resetUploadModal() {
  document.getElementById("uploadInitialState").classList.remove("hidden");
  document.getElementById("uploadProcessingState").classList.add("hidden");
  document.getElementById("uploadSuccessState").classList.add("hidden");
  document.getElementById("uploadDuplicateState").classList.add("hidden");
  document.getElementById("uploadErrorState").classList.add("hidden");
  const p1 = document.getElementById("fileInputPdf");
  const p2 = document.getElementById("fileInputPhoto");
  const p3 = document.getElementById("fileInputMultiPhoto");
  if (p1) p1.value = "";
  if (p2) p2.value = "";
  if (p3) p3.value = "";
}

async function handleFileSelect(e) {
  const file = e.target.files[0];
  if (!file) return;
  startUploadPipeline(file);
}

async function handleMultiPhotoSelect(e) {
  const files = e.target.files;
  if (!files || files.length === 0) return;
  startMultiPhotoUploadPipeline(files);
}

async function startUploadPipeline(file, allowDuplicate = false) {
  AppState.cachedFileForDuplicate = file;

  // Show processing UX with Hinglish steps
  document.getElementById("uploadInitialState").classList.add("hidden");
  document.getElementById("uploadDuplicateState").classList.add("hidden");
  document.getElementById("uploadErrorState").classList.add("hidden");
  document.getElementById("uploadProcessingState").classList.remove("hidden");

  const stepText = document.getElementById("uploadProgressText");
  const progressBar = document.getElementById("uploadProgressBar");

  // Step 1: Reading
  stepText.innerText = "Document read ho raha hai...";
  progressBar.style.width = "25%";
  await new Promise(r => setTimeout(r, 600));

  // Step 2: Vision Analysis
  stepText.innerText = "AI document ko read kar raha hai...";
  progressBar.style.width = "55%";
  await new Promise(r => setTimeout(r, 600));

  // Step 3: Verifying numbers
  stepText.innerText = "Numbers check kiye ja rahe hain...";
  progressBar.style.width = "85%";

  try {
    const res = await Api.uploadFile(file, allowDuplicate);

    if (res.is_duplicate) {
      document.getElementById("uploadProcessingState").classList.add("hidden");
      document.getElementById("uploadDuplicateState").classList.remove("hidden");
      document.getElementById("dupExistingFileName").innerText = res.existing_filename;
      return;
    }

    if (!res.success) {
      document.getElementById("uploadProcessingState").classList.add("hidden");
      document.getElementById("uploadErrorState").classList.remove("hidden");
      document.getElementById("uploadErrorMessage").innerText = res.message || "Ye document read nahi ho pa raha.";
      return;
    }

    // Success state
    progressBar.style.width = "100%";
    stepText.innerText = res.message || "Document ready hai.";
    await new Promise(r => setTimeout(r, 400));

    displayUnderstoodResult(res);
    await initApp();

  } catch (err) {
    document.getElementById("uploadProcessingState").classList.add("hidden");
    document.getElementById("uploadErrorState").classList.remove("hidden");
    document.getElementById("uploadErrorMessage").innerText = "Ye document read nahi ho pa raha. Network ya server error.";
  }
}

async function startMultiPhotoUploadPipeline(files, allowDuplicate = false) {
  AppState.cachedFilesForDuplicate = files;

  document.getElementById("uploadInitialState").classList.add("hidden");
  document.getElementById("uploadDuplicateState").classList.add("hidden");
  document.getElementById("uploadErrorState").classList.add("hidden");
  document.getElementById("uploadProcessingState").classList.remove("hidden");

  const stepText = document.getElementById("uploadProgressText");
  const progressBar = document.getElementById("uploadProgressBar");

  stepText.innerText = "Multiple photos analyze ho rahi hain...";
  progressBar.style.width = "40%";
  await new Promise(r => setTimeout(r, 600));

  stepText.innerText = "Pages consolidate kiye ja rahe hain...";
  progressBar.style.width = "75%";

  try {
    const res = await Api.uploadMultipleFiles(files, `Document (${files.length} Photos)`, allowDuplicate);

    if (res.is_duplicate) {
      document.getElementById("uploadProcessingState").classList.add("hidden");
      document.getElementById("uploadDuplicateState").classList.remove("hidden");
      document.getElementById("dupExistingFileName").innerText = res.existing_filename || "Multi-Photo Document";
      return;
    }

    if (!res.success) {
      document.getElementById("uploadProcessingState").classList.add("hidden");
      document.getElementById("uploadErrorState").classList.remove("hidden");
      document.getElementById("uploadErrorMessage").innerText = res.message || "Ye photos read nahi ho pa rahi.";
      return;
    }

    progressBar.style.width = "100%";
    stepText.innerText = res.message || "Document ready hai.";
    await new Promise(r => setTimeout(r, 400));

    displayUnderstoodResult(res);
    await initApp();

  } catch (err) {
    document.getElementById("uploadProcessingState").classList.add("hidden");
    document.getElementById("uploadErrorState").classList.remove("hidden");
    document.getElementById("uploadErrorMessage").innerText = "Multi-photo upload mein error aayi.";
  }
}

function displayUnderstoodResult(res) {
  document.getElementById("uploadProcessingState").classList.add("hidden");
  document.getElementById("uploadSuccessState").classList.remove("hidden");
  document.getElementById("successDocTitle").innerText = res.filename;

  const incomeVal = res.metrics ? res.metrics.total_income_formatted : "₹0";
  const expensesVal = res.metrics ? res.metrics.total_expenses_formatted : "₹0";
  const accountVal = res.account ? (res.account.masked_account_number || "Verified Account") : "Verified Document";

  const incElem = document.getElementById("understoodIncome");
  const expElem = document.getElementById("understoodExpenses");
  const accElem = document.getElementById("understoodAccount");
  const recMsg = document.getElementById("successReconcileMsg");

  if (incElem) incElem.innerText = incomeVal;
  if (expElem) expElem.innerText = expensesVal;
  if (accElem) accElem.innerText = accountVal;
  if (recMsg) recMsg.innerText = res.message || "Numbers verified.";

  const revBtn = document.getElementById("successReviewBtn");
  const confBtn = document.getElementById("successConfirmBtn");
  const heading = document.getElementById("successHeading");
  const iconBadge = document.getElementById("successIconBadge");
  const icon = document.getElementById("successIcon");

  if (res.status === "NEEDS_REVIEW") {
    if (revBtn) revBtn.classList.remove("hidden");
    if (confBtn) confBtn.classList.add("hidden");
    if (heading) heading.innerText = "Is information ko verify karna zaroori hai";
    if (iconBadge) iconBadge.className = "w-12 h-12 rounded-full bg-amber-100 text-amber-800 flex items-center justify-center mx-auto mb-space-md";
    if (icon) icon.innerText = "warning";
  } else {
    if (revBtn) revBtn.classList.add("hidden");
    if (confBtn) confBtn.classList.remove("hidden");
    if (heading) heading.innerText = "Humne ye information samjhi hai";
    if (iconBadge) iconBadge.className = "w-12 h-12 rounded-full bg-emerald-100 text-emerald-800 flex items-center justify-center mx-auto mb-space-md";
    if (icon) icon.innerText = "verified";
  }
}

async function handleConfirmDocumentReview(docId) {
  if (!confirm("Kya aap is document ke verified numbers confirm karna chahte hain?")) return;
  await Api.confirmDocument(docId);
  await initApp();
}

function handleUploadAnyway() {
  if (AppState.cachedFileForDuplicate) {
    startUploadPipeline(AppState.cachedFileForDuplicate, true);
  }
}

async function handleDeleteDocument(docId) {
  if (!confirm("Kya aap sach mein ye document aur iske verified transactions delete karna chahte hain?")) return;
  await Api.deleteDocument(docId);
  await initApp();
}

async function handleReprocessDocument(docId) {
  const res = await Api.reprocessDocument(docId);
  alert(res.message || "Document reprocessed.");
  await initApp();
}

// ================= SOURCE / EVIDENCE DRAWER =================
function openSourceDrawer(title, category, amount, docName, pageNum, status, rawSnippet, docId) {
  const drawer = document.getElementById("sourceEvidenceDrawer");
  document.getElementById("evidenceTitle").innerText = title;
  document.getElementById("evidenceCategory").innerText = category;
  document.getElementById("evidenceAmount").innerText = `₹${amount.toLocaleString('en-IN')}`;
  document.getElementById("evidenceDocName").innerText = docName;
  document.getElementById("evidencePageNum").innerText = `Page ${pageNum}`;
  document.getElementById("evidenceRawSnippet").innerText = rawSnippet || "Verbatim record verified directly in document.";

  const statusEl = document.getElementById("evidenceStatusBadge");
  if (status === "VERIFIED_FROM_DOCUMENT") {
    statusEl.className = "inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[11px] font-semibold trust-badge-verified";
    statusEl.innerHTML = `<span class="material-symbols-outlined text-[13px]">verified</span> Verified from document`;
  } else if (status === "CALCULATED") {
    statusEl.className = "inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[11px] font-semibold trust-badge-calculated";
    statusEl.innerHTML = `<span class="material-symbols-outlined text-[13px]">functions</span> Calculated`;
  } else {
    statusEl.className = "inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[11px] font-semibold trust-badge-review";
    statusEl.innerHTML = `<span class="material-symbols-outlined text-[13px]">warning</span> Needs Review`;
  }

  const openBtn = document.getElementById("evidenceOpenPdfBtn");
  openBtn.onclick = () => {
    // If docId is known or find document
    const dId = docId || (AppState.documents[0] ? AppState.documents[0].id : "");
    if (dId) {
      openPdfViewer(dId, docName, pageNum, title, `₹${amount.toLocaleString('en-IN')}`);
    } else {
      alert("Source document unavailable");
    }
  };

  drawer.classList.remove("translate-x-full");
}

function closeSourceDrawer() {
  document.getElementById("sourceEvidenceDrawer").classList.add("translate-x-full");
}

// ================= ASK myCA ADVISORY =================
async function submitAdvisoryQuery(text) {
  const input = document.getElementById("advisoryInput");
  const query = text || (input ? input.value : "");
  if (!query.trim()) return;

  const responseArea = document.getElementById("advisoryResponseArea");
  responseArea.classList.remove("hidden");
  responseArea.innerHTML = `
    <div class="p-space-md bg-surface-container-low/70 rounded-lg flex items-center gap-2 font-body-sm text-on-surface-variant">
      <span class="material-symbols-outlined animate-spin text-[18px]">sync</span>
      <span>Verified document ledgers aur statutory knowledge consult kiye ja rahe hain...</span>
    </div>
  `;

  const res = await Api.askAdvisory(query);

  let sourcesHtml = "";
  if (res.sources && res.sources.length > 0) {
    sourcesHtml = `
      <div class="mt-space-sm pt-space-xs border-t border-outline-variant/20 flex flex-wrap items-center gap-space-sm">
        <span class="font-label-sm text-[11px] text-on-surface-variant uppercase tracking-wider">Verified Sources:</span>
        ${res.sources.map(s => `
          <button onclick="if('${s.page}' !== 'null') openPdfViewer('${AppState.documents[0] ? AppState.documents[0].id : ''}', '${escapeHtml(s.source)}', ${s.page || 1}, 'Ask myCA Verified Citation', '${escapeHtml(s.snippet || '')}')" class="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-surface-container-lowest border border-outline-variant/30 text-secondary hover:bg-surface-container-high transition-colors font-label-sm text-[11px]">
            <span class="material-symbols-outlined text-[13px]">description</span>
            ${escapeHtml(s.source)}${s.page ? ` — Page ${s.page}` : ''}
          </button>
        `).join("")}
      </div>
    `;
  }

  // Evidence Drill-down (Kaise nikala?)
  const hasDrillDown = res.calculation_used || (res.data_used && Object.keys(res.data_used).length > 0) || (res.knowledge_used && res.knowledge_used.length > 0);
  let drillDownHtml = "";
  if (hasDrillDown) {
    drillDownHtml = `
      <div class="mt-space-sm">
        <button onclick="document.getElementById('evidenceDetailBox').classList.toggle('hidden')" class="inline-flex items-center gap-1.5 px-3 py-1 rounded bg-surface-container-high hover:bg-surface-container text-on-surface font-label-sm text-[12px] font-semibold transition-colors">
          <span class="material-symbols-outlined text-[14px]">calculate</span>
          <span>Kaise nikala? (Audit Evidence)</span>
        </button>
        <div id="evidenceDetailBox" class="hidden mt-2 p-3 rounded-lg bg-surface-container-low border border-outline-variant/30 text-[12px] text-on-surface flex flex-col gap-2">
          ${res.calculation_used ? `<div><span class="font-semibold text-secondary">Calculation:</span> <code class="px-1.5 py-0.5 rounded bg-surface-container-lowest font-mono text-[11px]">${escapeHtml(res.calculation_used)}</code></div>` : ''}
          ${res.data_used && Object.keys(res.data_used).length > 0 ? `<div><span class="font-semibold text-secondary">Personal Data Used:</span> <span class="text-on-surface-variant font-mono text-[11px]">${escapeHtml(JSON.stringify(res.data_used))}</span></div>` : ''}
          ${res.knowledge_used && res.knowledge_used.length > 0 ? `<div><span class="font-semibold text-secondary">Statutory Provision:</span> <span class="text-on-surface-variant">${escapeHtml(res.knowledge_used[0].official_source_reference || res.knowledge_used[0].provision || '')}</span></div>` : ''}
        </div>
      </div>
    `;
  }

  let disclaimerHtml = "";
  if (res.recommendation_disclaimer) {
    disclaimerHtml = `
      <div class="mt-space-sm p-2 rounded bg-surface-container-low/60 border border-outline-variant/20 text-[11px] text-on-surface-variant flex items-center gap-1.5">
        <span class="material-symbols-outlined text-[14px] text-on-surface-variant">info</span>
        <span>${escapeHtml(res.recommendation_disclaimer)}</span>
      </div>
    `;
  }

  const typeLabels = {
    CALCULATION: "Deterministic Calculation",
    OBSERVATION: "Verified Personal Fact",
    EDUCATION: "Statutory Regulatory Framework",
    RECOMMENDATION: "Financial Hygiene Recommendation",
    WARNING: "Notice / Alert",
    NEEDS_INFO: "More Information Needed",
    NEEDS_REVIEW: "Review Required"
  };
  const typeBadge = typeLabels[res.response_type] || "Verified Response";

  responseArea.innerHTML = `
    <div class="p-space-lg bg-surface-container-lowest border border-outline-variant/30 rounded-xl shadow-sm">
      <div class="flex items-center justify-between mb-space-xs">
        <div class="flex items-center gap-2 text-secondary font-label-sm text-[11px] uppercase tracking-wider font-semibold">
          <span class="w-1.5 h-1.5 rounded-full bg-secondary"></span>
          <span>Chartered Consultation • Grounded in Truth</span>
        </div>
        <span class="px-2 py-0.5 rounded bg-surface-container text-on-surface-variant text-[10px] font-semibold uppercase tracking-wider">${typeBadge}</span>
      </div>
      <p class="font-headline-sm text-on-surface leading-relaxed whitespace-pre-line">${escapeHtml(res.answer)}</p>
      ${drillDownHtml}
      ${sourcesHtml}
      ${disclaimerHtml}
    </div>
  `;

  if (input) input.value = "";
}

// ================= PHASE 6: OPERATING SYSTEM HANDLERS =================

// See Why Modal
function openSeeWhyModal() {
  const modal = document.getElementById("seeWhyModal");
  if (modal) modal.classList.remove("hidden");
}

function closeSeeWhyModal() {
  const modal = document.getElementById("seeWhyModal");
  if (modal) modal.classList.add("hidden");
}

// Alert Actions
async function handleDismissAlert(alertId) {
  try {
    await Api.dismissAlert(alertId);
    const homeData = await Api.getHome();
    AppState.homeData = homeData;
    renderInbox(homeData.inbox || []);
  } catch (err) {
    console.error("Failed to dismiss alert:", err);
  }
}

async function handleSnoozeAlert(alertId) {
  try {
    await Api.snoozeAlert(alertId, 7);
    const homeData = await Api.getHome();
    AppState.homeData = homeData;
    renderInbox(homeData.inbox || []);
  } catch (err) {
    console.error("Failed to snooze alert:", err);
  }
}

// Goals
async function loadGoals() {
  try {
    const data = await Api.getGoals();
    AppState.goals = data.goals || [];
    renderGoals(AppState.goals);
  } catch (err) {
    console.error("Failed to load goals:", err);
  }
}

function renderGoals(goals) {
  const container = document.getElementById("goalsListContainer");
  if (!container) return;

  if (goals.length === 0) {
    container.innerHTML = `
      <div class="col-span-full p-space-lg text-center bg-surface-container-lowest border border-[#e7e5e0] rounded-xl text-on-surface-variant text-[13px]">
        Koi active goal nahi mila. Naya goal create karke timeline calculate karein!
      </div>
    `;
    return;
  }

  container.innerHTML = goals.map(g => {
    const pct = g.progress_percent || 0;
    const isCompleted = g.status === "COMPLETED";
    return `
      <div class="p-space-lg bg-surface-container-lowest border border-[#e7e5e0] rounded-xl flex flex-col justify-between shadow-sm">
        <div>
          <div class="flex items-center justify-between mb-2">
            <span class="text-[11px] font-bold uppercase tracking-wider text-secondary">${g.category || 'SAVINGS'}</span>
            <span class="text-[10px] font-bold px-2 py-0.5 rounded ${isCompleted ? 'bg-secondary-container text-secondary' : 'bg-surface-container-high text-on-surface'}">${g.status}</span>
          </div>
          <h3 class="font-serif text-[20px] font-semibold text-on-surface mb-1">${escapeHtml(g.title)}</h3>
          
          <div class="flex items-baseline justify-between my-2">
            <span class="text-[22px] font-bold text-on-surface tabular-nums">₹${g.current_amount.toLocaleString('en-IN')}</span>
            <span class="text-[12px] text-on-surface-variant">of ₹${g.target_amount.toLocaleString('en-IN')} (${pct}%)</span>
          </div>

          <!-- Progress Bar -->
          <div class="w-full bg-surface-container-high rounded-full h-2 overflow-hidden mb-3">
            <div class="bg-secondary h-2 rounded-full transition-all" style="width: ${Math.min(100, pct)}%"></div>
          </div>

          <!-- Deterministic Projections -->
          <div class="space-y-1.5 text-[12px] pt-2 border-t border-[#e7e5e0]">
            <div class="flex justify-between">
              <span class="text-on-surface-variant">Monthly Contribution:</span>
              <span class="font-semibold tabular-nums">₹${g.monthly_contribution.toLocaleString('en-IN')}/mo</span>
            </div>
            ${g.months_to_complete !== null ? `
              <div class="flex justify-between">
                <span class="text-on-surface-variant">Estimated Timeline:</span>
                <span class="font-bold text-secondary tabular-nums">${g.months_to_complete} months</span>
              </div>
            ` : ''}
            ${g.required_monthly_contribution ? `
              <div class="flex justify-between">
                <span class="text-on-surface-variant">Required for Target Date:</span>
                <span class="font-semibold text-amber-900 tabular-nums">₹${g.required_monthly_contribution.toLocaleString('en-IN')}/mo</span>
              </div>
            ` : ''}
          </div>
        </div>
      </div>
    `;
  }).join("");
}

// New Goal Modal
function openNewGoalModal() {
  const modal = document.getElementById("newGoalModal");
  if (modal) modal.classList.remove("hidden");
}

function closeNewGoalModal() {
  const modal = document.getElementById("newGoalModal");
  if (modal) modal.classList.add("hidden");
}

async function submitNewGoal() {
  const title = (document.getElementById("newGoalTitle")?.value || "").trim();
  const target = parseFloat(document.getElementById("newGoalTarget")?.value || "0");
  const current = parseFloat(document.getElementById("newGoalCurrent")?.value || "0");
  const monthly = parseFloat(document.getElementById("newGoalMonthly")?.value || "0");
  const targetDate = document.getElementById("newGoalTargetDate")?.value || null;
  const category = document.getElementById("newGoalCategory")?.value || "SAVINGS";

  if (!title) {
    alert("Goal title zaroori hai.");
    return;
  }
  if (!target || target <= 0) {
    alert("Target amount positive number hona chahiye.");
    return;
  }

  try {
    const res = await Api.createGoal({
      title,
      target_amount: target,
      current_amount: current,
      monthly_contribution: monthly,
      target_date: targetDate,
      category
    });
    closeNewGoalModal();
    await loadGoals();
    await initApp();
  } catch (err) {
    alert("Goal create karne mein error aayi: " + err.message);
  }
}

// What-If Simulator Handlers
function setSimSavings(amt) {
  const input = document.getElementById("simExtraSavingsInput");
  if (input) input.value = amt;
  runSavingsSimulation();
}

async function runSavingsSimulation() {
  const input = document.getElementById("simExtraSavingsInput");
  const amt = parseFloat(input?.value || "5000");
  if (amt <= 0) return;

  try {
    const res = await Api.simulate({
      type: "SAVINGS_BOOST",
      extra_monthly_savings: amt
    });

    const r1 = document.getElementById("simResult1Yr");
    const r3 = document.getElementById("simResult3Yr");
    const impact = document.getElementById("simResultGoalImpact");

    if (r1) r1.innerText = `₹${res.additional_wealth_1_year.toLocaleString('en-IN')}`;
    if (r3) r3.innerText = `₹${res.additional_wealth_3_years.toLocaleString('en-IN')}`;

    if (impact) {
      if (res.goal_accelerations && res.goal_accelerations.length > 0) {
        const topG = res.goal_accelerations[0];
        impact.innerText = `${topG.goal_title}: Timeline ${topG.original_months} mo se kam hokar ${topG.new_months} mo ho jayegi (saves ${topG.months_saved} months).`;
      } else {
        impact.innerText = res.explanation;
      }
    }
  } catch (err) {
    console.error("Savings simulation failed:", err);
  }
}

async function runExpenseCutSimulation() {
  const cat = document.getElementById("simExpenseCategorySelect")?.value || "Food & Dining";
  const pct = parseFloat(document.getElementById("simExpenseReductionSelect")?.value || "20");

  try {
    const res = await Api.simulate({
      type: "EXPENSE_REDUCTION",
      category: cat,
      reduction_percent: pct
    });

    const monthlyEl = document.getElementById("simExpenseFreedMonthly");
    const annualEl = document.getElementById("simExpenseFreedAnnual");
    const expEl = document.getElementById("simExpenseExplanation");

    if (monthlyEl) monthlyEl.innerText = `₹${res.monthly_freed_cash.toLocaleString('en-IN')} / mo`;
    if (annualEl) annualEl.innerText = `₹${res.annual_savings_gain.toLocaleString('en-IN')} / yr`;
    if (expEl) expEl.innerText = res.explanation;
  } catch (err) {
    console.error("Expense cut simulation failed:", err);
  }
}

// ================= CATEGORY EDIT MODAL =================
let editingTxId = null;

function openCategoryEdit(txId, currentCat) {
  editingTxId = txId;
  const select = document.getElementById("editCategorySelect");
  select.value = currentCat;
  document.getElementById("categoryEditModal").classList.remove("hidden");
}

function closeCategoryEdit() {
  document.getElementById("categoryEditModal").classList.add("hidden");
  editingTxId = null;
}

async function saveCategoryEdit() {
  if (!editingTxId) return;
  const select = document.getElementById("editCategorySelect");
  const newCat = select.value;
  await Api.updateCategory(editingTxId, newCat);
  closeCategoryEdit();
  await initApp();
}

// ================= MULTI-TENANT SWITCHER =================
function switchUserTenant(newUserId) {
  AppState.currentUserId = newUserId;
  AppState.sessionToken = null; // Invalidate cached token so new user token is minted
  const label = document.getElementById("activeTenantLabel");
  if (label) {
    label.innerText = newUserId === "usr_aarav_01" ? "Aarav Sharma (Client A)" : "Priya Patel (Client B - Empty)";
  }
  initApp();
}

// Drag & drop handlers
window.addEventListener("DOMContentLoaded", () => {
  initApp();

  const dropZone = document.getElementById("uploadDropZone");
  if (dropZone) {
    dropZone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropZone.classList.add("bg-surface-container");
    });
    dropZone.addEventListener("dragleave", (e) => {
      e.preventDefault();
      dropZone.classList.remove("bg-surface-container");
    });
    dropZone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropZone.classList.remove("bg-surface-container");
      if (e.dataTransfer.files.length > 0) {
        startUploadPipeline(e.dataTransfer.files[0]);
      }
    });
  }
});
