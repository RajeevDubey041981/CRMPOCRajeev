/**
 * End-to-end: vendor order → admin ship → vendor installation request →
 * admin assign → engineer complete + payment proof → admin approve.
 */
import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const BASE_URL = process.env.E2E_BASE_URL || "http://localhost:5173";
const API_URL = process.env.E2E_API_URL || "http://localhost:8010";
const HEADLESS = process.env.HEADLESS !== "false";
const RUN_ID = Date.now();
const ORDER_NO = `E2E-ORD-${RUN_ID}`;
const SERIAL1 = `E2ESN1-${RUN_ID}`;
const SERIAL2 = `E2ESN2-${RUN_ID}`;

const USERS = {
  vendor: { email: "vendor1@indcool.com", password: "vendor123", name: "Vendor One" },
  admin: { email: "admin@indcool.com", password: "admin123", name: "Administrator" },
  engineer: { email: "ravi@indcool.com", password: "engineer123", name: "Ravi Kumar" },
};

const results = [];

function log(step, ok, detail = "") {
  results.push({ step, ok, detail });
  const mark = ok ? "PASS" : "FAIL";
  console.log(`[${mark}] ${step}${detail ? ` — ${detail}` : ""}`);
}

async function pickFirstSearchableOption(page, placeholder, index = 0) {
  const input = page.getByPlaceholder(placeholder).nth(index);
  await input.click();
  const option = page.locator("div.absolute.z-10 .cursor-pointer").first();
  await option.waitFor({ state: "visible", timeout: 10000 });
  await option.click();
}

async function fetchInstallations(token, { orderId, search } = {}) {
  const params = new URLSearchParams({ page: "1", per_page: "20" });
  if (orderId) params.set("order_id", String(orderId));
  if (search) params.set("search", search);
  const res = await fetch(`${API_URL}/api/installations?${params}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.json();
}

async function findInstallationId(token, orderId, serialNo) {
  const data = await fetchInstallations(token, { orderId });
  const match = (data.items || []).find((row) => row.serial_no === serialNo);
  if (!match?.id) {
    throw new Error(`Installation not found for order #${orderId} / ${serialNo}`);
  }
  return match.id;
}

async function openInstallationEdit(page, installationId) {
  await page.goto(`${BASE_URL}/installations/${installationId}`);
  await page.getByRole("heading", { name: /Installation Request #/ }).waitFor({ timeout: 15000 });
  await page.getByRole("button", { name: "Edit status" }).click();
  await page.getByRole("heading", { name: /Edit installation/ }).waitFor();
}

function editModal(page) {
  return page.locator("div.shadow-xl").filter({ has: page.getByRole("heading", { name: /Edit installation/ }) });
}

async function saveInstallationStatus(page, { status, paymentAmount, paymentType, proofPath }) {
  const modal = editModal(page);
  if (status) {
    await modal.locator("select").first().selectOption(status);
    if (status === "Completed") {
      await modal.getByText("Payment Amount").waitFor({ state: "visible", timeout: 10000 });
    }
  }
  await modal.locator('input[type="date"]').fill(new Date().toISOString().slice(0, 10));
  if (paymentAmount) {
    await modal.locator('input[type="number"]').fill(String(paymentAmount));
  }
  if (paymentType) {
    await modal.locator("select").nth(1).selectOption(paymentType);
  }
  if (proofPath) {
    await modal.locator('input[type="file"]').setInputFiles(proofPath);
  }
  await modal.getByRole("button", { name: /Save changes|Update Payment Request/ }).click();
  await page.waitForTimeout(2000);
}

async function login(page, user) {
  await page.goto(`${BASE_URL}/login`);
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
  await page.locator('input[type="email"]').fill(user.email);
  await page.locator('input[type="password"]').fill(user.password);
  await page.getByRole("button", { name: "Sign in" }).click();
  const loginFailed = page.locator(".bg-rose-50");
  await Promise.race([
    page.getByRole("button", { name: "Logout" }).waitFor({ timeout: 45000 }),
    loginFailed.waitFor({ timeout: 45000 }).then(async () => {
      const msg = await loginFailed.textContent();
      throw new Error(msg || "Login failed");
    }),
  ]);
}

async function logout(page) {
  await page.getByRole("button", { name: "Logout" }).click();
  await page.locator('input[type="email"]').waitFor({ timeout: 15000 });
}

async function createFixtureFiles() {
  const dir = path.join(__dirname, ".e2e-tmp");
  fs.mkdirSync(dir, { recursive: true });
  const docPath = path.join(dir, "order-doc.pdf");
  const proofPath = path.join(dir, "installation-proof.pdf");
  const pdf = "%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n";
  if (!fs.existsSync(docPath)) fs.writeFileSync(docPath, pdf);
  if (!fs.existsSync(proofPath)) fs.writeFileSync(proofPath, pdf);
  return { dir, docPath, proofPath };
}

async function apiLogin(email, password) {
  const res = await fetch(`${API_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error(`API login failed: ${email}`);
  return (await res.json()).access_token;
}


async function main() {
  const { docPath, proofPath } = await createFixtureFiles();
  let orderId = null;

  const browser = await chromium.launch({ headless: HEADLESS });
  const context = await browser.newContext({ acceptDownloads: true });
  const page = await context.newPage();

  try {
    // --- Vendor: create order with serials ---
    await login(page, USERS.vendor);
    log("Vendor login", true, USERS.vendor.email);

    await page.goto(`${BASE_URL}/orders/new`);
    await page.getByRole("heading", { name: "Create Order" }).waitFor();
    await page.waitForTimeout(1200);

    await page.getByPlaceholder("e.g. GEMC-511687730897838").fill(ORDER_NO);
    await page.locator("label", { hasText: "Customer Name" }).locator("..").locator("input").fill("E2E Test Customer");
    await page.locator("label", { hasText: "Customer Contact" }).locator("..").locator("input").fill("9999888777");
    await page.locator("label", { hasText: "Customer City" }).locator("..").locator("input").fill("Delhi");
    await page.locator('input[type="file"]').first().setInputFiles(docPath);

    await page.getByRole("button", { name: "+ New" }).click();
    await page.waitForTimeout(500);
    await pickFirstSearchableOption(page, "Search item...");
    await page.getByPlaceholder("Serial Number 1").fill(SERIAL1);
    const serial2 = page.getByPlaceholder("Serial Number 2");
    if (await serial2.isVisible().catch(() => false)) {
      await serial2.fill(SERIAL2);
    }
    await pickFirstSearchableOption(page, "Years...", 0);
    await pickFirstSearchableOption(page, "Years...", 1);
    await pickFirstSearchableOption(page, "Years...", 2);
    await pickFirstSearchableOption(page, "Dry count...");
    await pickFirstSearchableOption(page, "Wet count...");

    await page.getByRole("button", { name: "Submit" }).click();
    await page.getByRole("heading", { name: "Order Created" }).waitFor({ timeout: 25000 });
    const orderIdText = await page.locator("text=Order ID:").locator("..").locator("span.font-semibold").textContent();
    orderId = Number(orderIdText);
    log("Vendor creates order with serials", Number.isFinite(orderId), `order #${orderId} (${ORDER_NO})`);
    await page.getByRole("button", { name: "View Order" }).click();
    await page.getByRole("heading", { name: ORDER_NO }).waitFor({ timeout: 15000 });
    await logout(page);

    // --- Admin: ship order (Delivered + OEM bill) ---
    await login(page, USERS.admin);
    log("Admin login", true);

    await page.goto(`${BASE_URL}/orders/${orderId}`);
    await page.getByRole("heading", { name: ORDER_NO }).waitFor({ timeout: 15000 });

    await page.getByRole("button", { name: "Edit Order" }).click();
    await page.locator("form").filter({ has: page.getByRole("button", { name: "Save Changes" }) }).locator("select").first().selectOption("Delivered");
    await page.locator("label", { hasText: "OEM Bill No" }).locator("..").locator("input").fill(`OEM-${RUN_ID}`);
    await page.locator("label", { hasText: "Courier" }).locator("..").locator("select").selectOption({ label: "Delivery" });
    await page.getByRole("button", { name: "Save Changes" }).click();
    await page.getByText("Delivered").first().waitFor({ timeout: 15000 });
    log("Admin ships order (Delivered + OEM bill)", true);
    await logout(page);

    // --- Vendor: submit installation request ---
    await login(page, USERS.vendor);
    await page.goto(`${BASE_URL}/orders/${orderId}`);
    await page.getByRole("heading", { name: ORDER_NO }).waitFor({ timeout: 15000 });

    const checkboxes = page.locator('input[type="checkbox"]');
    const count = await checkboxes.count();
    let checked = 0;
    for (let i = 0; i < count; i += 1) {
      const box = checkboxes.nth(i);
      if (!(await box.isVisible())) continue;
      if (!(await box.isEnabled())) continue;
      await box.check();
      checked += 1;
      if (checked >= 2) break;
    }
    await page.getByRole("button", { name: /Submit \(\d+\)/ }).click();
    await page.getByText(/submitted|row\(s\) submitted/i).first().waitFor({ timeout: 20000 });
    log("Vendor submits installation request", checked >= 1, `${checked} serial(s)`);
    await logout(page);

    // --- Admin: assign engineer ---
    await login(page, USERS.admin);
    await page.goto(`${BASE_URL}/orders/${orderId}`);
    await page.getByRole("heading", { name: ORDER_NO }).waitFor();
    await page.waitForTimeout(1500);

    const instCheckbox = page.locator("tbody input[type=\"checkbox\"]").first();
    await instCheckbox.waitFor({ timeout: 15000 });
    await instCheckbox.check();
    const engineerSelect = page.locator("select").filter({ has: page.locator("option", { hasText: "Ravi Kumar" }) });
    const engineerValue = await engineerSelect.locator("option", { hasText: "Ravi Kumar" }).getAttribute("value");
    await engineerSelect.selectOption(engineerValue);
    await page.getByRole("button", { name: "Assign" }).click();
    await page.getByText(/row\(s\) assigned/i).waitFor({ timeout: 15000 });
    log("Admin assigns engineer", true, "Ravi Kumar");
    await logout(page);

    const adminTokenAfterAssign = await apiLogin(USERS.admin.email, USERS.admin.password);
    const installationId = await findInstallationId(adminTokenAfterAssign, orderId, SERIAL1);

    // --- Engineer: complete + payment request with proof ---
    await login(page, USERS.engineer);
    log("Engineer login", true);

    await openInstallationEdit(page, installationId);
    await saveInstallationStatus(page, { status: "In Progress" });
    log("Engineer sets status In Progress", true);

    await openInstallationEdit(page, installationId);
    await saveInstallationStatus(page, {
      status: "Completed",
      paymentAmount: "500",
      paymentType: "Cash",
      proofPath,
    });

    const engToken = await apiLogin(USERS.engineer.email, USERS.engineer.password);
    const instData = await fetchInstallations(engToken, { orderId });
    const instRow = instData.items?.find((row) => row.id === installationId);
    const instStatus = instRow?.status;
    log("Engineer completes installation + payment request", instStatus === "Payment Pending", `status=${instStatus}`);
    await logout(page);

    // --- Admin: approve payment ---
    await login(page, USERS.admin);
    await openInstallationEdit(page, installationId);
    const approveModal = editModal(page);
    await approveModal.locator("select").first().selectOption("Completed");
    await approveModal.getByRole("button", { name: "Approve Payment" }).click();
    await page.waitForTimeout(2000);

    const adminToken = await apiLogin(USERS.admin.email, USERS.admin.password);
    const finalData = await fetchInstallations(adminToken, { orderId });
    const finalRow = finalData.items?.find((row) => row.id === installationId);
    const finalStatus = finalRow?.status;
    log("Admin approves payment / completes installation", finalStatus === "Completed", `status=${finalStatus}`);
  } catch (error) {
    try {
      await page.screenshot({ path: path.join(__dirname, ".e2e-tmp", "order-flow-failure.png"), fullPage: true });
      const bodyText = await page.locator("body").innerText();
      fs.writeFileSync(path.join(__dirname, ".e2e-tmp", "order-flow-failure.txt"), bodyText);
    } catch {}
    log("Unhandled error", false, error.message);
    console.error(error);
  } finally {
    await browser.close();
  }

  console.log("\n=== ORDER FLOW E2E SUMMARY ===");
  for (const r of results) {
    console.log(`${r.ok ? "✓" : "✗"} ${r.step}${r.detail ? `: ${r.detail}` : ""}`);
  }
  const failed = results.filter((r) => !r.ok);
  process.exit(failed.length ? 1 : 0);
}

main();
