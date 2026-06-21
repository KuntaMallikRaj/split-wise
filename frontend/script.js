// Same origin: works in local dev and on Render without changes.
const API = "";

let users = [];
let currentGroup = null;

// ---------- helpers ----------
async function api(path, method = "GET", body = null) {
  const res = await fetch(API + path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : null,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
  return data;
}

function toast(msg, type = "") {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.className = `toast show ${type}`;
  setTimeout(() => (t.className = "toast"), 3000);
}

const money = (n) => `$${Number(n).toFixed(2)}`;
const userName = (id) => (users.find((u) => u.id === id) || {}).name || `#${id}`;

function fillSelect(sel, items, { value = "id", label = "name", placeholder } = {}) {
  sel.innerHTML =
    (placeholder ? `<option value="">${placeholder}</option>` : "") +
    items.map((it) => `<option value="${it[value]}">${it[label]}</option>`).join("");
}

// ---------- users ----------
async function loadUsers() {
  users = await api("/api/users");
  document.getElementById("userList").innerHTML =
    users.map((u) => `<li>${u.name}</li>`).join("") || "<li>No people yet</li>";
}

document.getElementById("userForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await api("/api/users", "POST", {
      name: document.getElementById("userName").value,
      email: document.getElementById("userEmail").value,
    });
    e.target.reset();
    await loadUsers();
    toast("Person added", "success");
  } catch (err) {
    toast(err.message, "error");
  }
});

// ---------- groups ----------
async function loadGroups() {
  const groups = await api("/api/groups");
  document.getElementById("groupList").innerHTML =
    groups
      .map(
        (g) => `<li data-id="${g.id}">
          <span><strong>${g.name}</strong></span>
          <span class="meta">${g.members.length} member(s)</span>
        </li>`
      )
      .join("") || "<li>No groups yet</li>";

  document.querySelectorAll("#groupList li[data-id]").forEach((li) =>
    li.addEventListener("click", () => openGroup(Number(li.dataset.id)))
  );
}

document.getElementById("groupForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    const g = await api("/api/groups", "POST", {
      name: document.getElementById("groupName").value,
    });
    e.target.reset();
    await loadGroups();
    openGroup(g.id);
    toast("Group created", "success");
  } catch (err) {
    toast(err.message, "error");
  }
});

// ---------- group detail ----------
async function openGroup(id) {
  currentGroup = await api(`/api/groups/${id}`);
  document.getElementById("groupDetail").classList.remove("hidden");
  document.getElementById("detailName").textContent = currentGroup.name;
  renderMembers();
  renderBalances();
  renderExpenses();
  renderExpenseForm();
  renderSettleForm();
  document.getElementById("groupDetail").scrollIntoView({ behavior: "smooth" });
}

document.getElementById("closeDetail").addEventListener("click", () => {
  document.getElementById("groupDetail").classList.add("hidden");
  currentGroup = null;
});

function renderMembers() {
  const members = currentGroup.members;
  document.getElementById("memberList").innerHTML =
    members.map((m) => `<li>${m.name}</li>`).join("") || "<li>No members</li>";

  // people not yet in the group
  const memberIds = new Set(members.map((m) => m.id));
  const candidates = users.filter((u) => !memberIds.has(u.id));
  fillSelect(document.getElementById("memberSelect"), candidates, {
    placeholder: candidates.length ? "Select a person" : "Everyone is already in",
  });
}

document.getElementById("memberForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const userId = Number(document.getElementById("memberSelect").value);
  if (!userId) return;
  try {
    await api(`/api/groups/${currentGroup.id}/members`, "POST", { user_id: userId });
    await openGroup(currentGroup.id);
    toast("Member added", "success");
  } catch (err) {
    toast(err.message, "error");
  }
});

function renderBalances() {
  const bl = document.getElementById("balanceList");
  bl.innerHTML =
    currentGroup.balances
      .filter((b) => Math.abs(b.net) > 0.005)
      .map((b) => {
        const cls = b.net > 0 ? "pos" : "neg";
        const txt = b.net > 0 ? `gets back ${money(b.net)}` : `owes ${money(-b.net)}`;
        return `<li><span>${b.user_name}</span><span class="${cls}">${txt}</span></li>`;
      })
      .join("") || "<li><span>All settled up 🎉</span></li>";

  const sl = document.getElementById("settleList");
  sl.innerHTML =
    currentGroup.settle_up
      .map(
        (s) => `<li>${s.from_name} → ${s.to_name}: <strong>${money(s.amount)}</strong></li>`
      )
      .join("") || `<li class="empty">Nothing to settle 🎉</li>`;
}

function renderExpenses() {
  document.getElementById("expenseList").innerHTML =
    currentGroup.expenses
      .map(
        (ex) => `<li>
          <div class="exp-main">
            <span><strong>${ex.description}</strong></span>
            <span class="exp-sub">${ex.payer_name} paid · split ${ex.split_type}</span>
          </div>
          <div class="row">
            <span class="amt">${money(ex.amount)}</span>
            <button class="mini" data-del="${ex.id}">Delete</button>
          </div>
        </li>`
      )
      .join("") || "<li>No expenses yet</li>";

  document.querySelectorAll("[data-del]").forEach((btn) =>
    btn.addEventListener("click", async () => {
      try {
        await api(`/api/expenses/${btn.dataset.del}`, "DELETE");
        await openGroup(currentGroup.id);
        toast("Expense deleted", "success");
      } catch (err) {
        toast(err.message, "error");
      }
    })
  );
}

function renderExpenseForm() {
  const members = currentGroup.members;
  fillSelect(document.getElementById("expPaidBy"), members, { placeholder: "Paid by" });
  buildParticipants();
  document.getElementById("expSplitType").onchange = buildParticipants;
}

function buildParticipants() {
  const type = document.getElementById("expSplitType").value;
  const box = document.getElementById("participantsBox");
  box.innerHTML = currentGroup.members
    .map((m) =>
      type === "exact"
        ? `<label>${m.name}<input type="number" step="0.01" min="0" data-uid="${m.id}" placeholder="0.00" /></label>`
        : `<label><input type="checkbox" data-uid="${m.id}" checked /> ${m.name}</label>`
    )
    .join("");
}

document.getElementById("expenseForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const type = document.getElementById("expSplitType").value;
  const payload = {
    group_id: currentGroup.id,
    description: document.getElementById("expDesc").value,
    amount: parseFloat(document.getElementById("expAmount").value),
    paid_by: Number(document.getElementById("expPaidBy").value),
    split_type: type,
  };

  if (type === "exact") {
    payload.shares = [...document.querySelectorAll("#participantsBox input[data-uid]")]
      .filter((i) => i.value !== "")
      .map((i) => ({ user_id: Number(i.dataset.uid), share: parseFloat(i.value) }));
  } else {
    payload.participants = [...document.querySelectorAll("#participantsBox input:checked")].map(
      (i) => Number(i.dataset.uid)
    );
  }

  try {
    await api("/api/expenses", "POST", payload);
    e.target.reset();
    await openGroup(currentGroup.id);
    toast("Expense added", "success");
  } catch (err) {
    toast(err.message, "error");
  }
});

function renderSettleForm() {
  fillSelect(document.getElementById("settlePayer"), currentGroup.members, { placeholder: "Payer" });
  fillSelect(document.getElementById("settlePayee"), currentGroup.members, { placeholder: "Payee" });
}

document.getElementById("settleForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await api("/api/settlements", "POST", {
      group_id: currentGroup.id,
      payer_id: Number(document.getElementById("settlePayer").value),
      payee_id: Number(document.getElementById("settlePayee").value),
      amount: parseFloat(document.getElementById("settleAmount").value),
    });
    e.target.reset();
    await openGroup(currentGroup.id);
    toast("Payment recorded", "success");
  } catch (err) {
    toast(err.message, "error");
  }
});

// ---------- init ----------
(async function init() {
  try {
    await loadUsers();
    await loadGroups();
  } catch (err) {
    toast("Failed to load: " + err.message, "error");
  }
})();
