/**
 * End-to-end walkthrough: bulk-serial service request flow (UI + API checks).
 *
 * Prerequisites: docker stack up (UI :5173, API :8010), migrations + seed applied.
 *
 *   node scripts/e2e-service-unit-flow.mjs
 *   HEADLESS=true node scripts/e2e-service-unit-flow.mjs
 */
import { chromium } from "playwright";
import { execSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.join(__dirname, "..");
const TMP_DIR = path.join(__dirname, ".e2e-tmp");
const FIXTURE_PATH = path.join(TMP_DIR, "service-flow-fixture.json");
const REPORT_PATH = path.join(TMP_DIR, "service-flow-report.json");
const REPORT_MD_PATH = path.join(TMP_DIR, "service-flow-report.md");

const BASE_URL = process.env.E2E_BASE_URL || "http://localhost:5173";
const API_URL = process.env.E2E_API_URL || "http://localhost:8010";
const HEADLESS = process.env.HEADLESS === "true";
const SLOW_MO = Number(process.env.E2E_SLOW_MO || "0");

const results = [];
let fixture = null;
let serviceId = null;

function log(step, ok, detail = "") {
  results.push({ step, ok, detail, at: new Date().toISOString() });
  const mark = ok ? "PASS" : "FAIL";
  console.log(`[${mark}] ${step}${detail ? ` — ${detail}` : ""}`);
}

async function screenshot(page, name) {
  fs.mkdirSync(TMP_DIR, { recursive: true });
  const file = path.join(TMP_DIR, `service-flow-${name}.png`);
  await page.screenshot({ path: file, fullPage: true });
  return file;
}

function runSetupScript() {
  const fixturePath = process.env.E2E_FIXTURE_PATH;
  if (fixturePath) {
    return JSON.parse(fs.readFileSync(fixturePath, "utf8"));
  }
  const scriptPath = path.join(__dirname, "setup-e2e-service-flow.py");
  const script = fs.readFileSync(scriptPath, "utf8");
  const output = execSync("docker compose exec -T api python -", {
    cwd: PROJECT_ROOT,
    input: script,
    encoding: "utf8",
    stdio: ["pipe", "pipe", "inherit"],
  });
  const jsonStart = output.indexOf("{");
  if (jsonStart < 0) {
    throw new Error("Setup script did not return JSON fixture");
  }
  return JSON.parse(output.slice(jsonStart));
}

function createFixtureFiles() {
  fs.mkdirSync(TMP_DIR, { recursive: true });
  const proofPath = path.join(TMP_DIR, "service-proof.pdf");
  const qrPath = path.join(TMP_DIR, "upi-qr.png");
  if (!fs.existsSync(proofPath)) {
    fs.writeFileSync(proofPath, "%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n");
  }
  if (!fs.existsSync(qrPath)) {
    // Minimal valid 1x1 PNG
    const png = Buffer.from(
      "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
      "base64",
    );
    fs.writeFileSync(qrPath, png);
  }
  return { proofPath, qrPath };
}

async function apiLogin(email, password) {
  const res = await fetch(`${API_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    throw new Error(`API login failed for ${email}: ${res.status}`);
  }
  const data = await res.json();
  return data.access_token;
}

async function fetchService(token, id) {
  const res = await fetch(`${API_URL}/api/services/${id}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    throw new Error(`GET service ${id} failed: ${res.status}`);
  }
  return res.json();
}

function unitBySerial(service, serial) {
  return (service.units || []).find((unit) => unit.serial_no === serial);
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

function unitRow(page, serial) {
  return page.locator("section", { hasText: "Serial workflow (per unit)" })
    .locator("tr", { has: page.getByRole("cell", { name: serial, exact: true }) });
}

async function waitForServiceReload(page) {
  await page.waitForTimeout(1200);
}

async function engineerObservation(page, serial) {
  const row = unitRow(page, serial);
  await row.getByRole("button", { name: "Add observation" }).click();
  await page.getByRole("heading", { name: new RegExp(`Observation — ${serial}`) }).waitFor();
  await page.getByPlaceholder("Problem found").fill(`Problem on ${serial}`);
  await page.getByPlaceholder("Engineer observation").fill(`Observation for ${serial}`);
  await page.getByRole("button", { name: "Submit observation" }).click();
  await waitForServiceReload(page);
}

async function closeServiceViaUi(page, serviceId) {
  await page.reload();
  await page.getByRole("heading", { name: /Service Request/ }).waitFor();
  await page.getByText("All serials have completed payment").waitFor({ timeout: 20000 });
  await page.getByRole("button", { name: "Mark service request closed" }).click();
  const closeModal = page.locator("div.fixed.inset-0").filter({
    has: page.getByRole("heading", { name: "Close service request", exact: true }),
  });
  await closeModal.waitFor({ state: "visible" });
  await closeModal.getByRole("button", { name: "Mark closed" }).click();
  const response = await page.waitForResponse(
    async (res) => {
      const url = res.url();
      if (!url.endsWith(`/api/services/${serviceId}/close`)) return false;
      if (res.request().method() !== "POST") return false;
      if (!res.ok()) return false;
      try {
        const body = await res.json();
        return body.status === "Closed";
      } catch {
        return false;
      }
    },
    { timeout: 30000 },
  );
  return response.ok();
}

async function closeServiceViaApi(token, serviceId) {
  const res = await fetch(`${API_URL}/api/services/${serviceId}/close`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: new URLSearchParams({ remarks: "E2E automated close" }),
  });
  const body = await res.json().catch(() => ({}));
  return res.ok && body.status === "Closed";
}

async function waitForClosedService(token, serviceId, attempts = 8) {
  for (let i = 0; i < attempts; i += 1) {
    const service = await fetchService(token, serviceId);
    if (service.status === "Closed") {
      return service;
    }
    await new Promise((resolve) => setTimeout(resolve, 400));
  }
  return fetchService(token, serviceId);
}

function modalByHeading(page, titlePattern) {
  const heading = page.getByRole("heading", { name: titlePattern });
  return heading.locator("xpath=ancestor::div[contains(@class,'shadow-xl')][1]");
}

async function adminApproveUnit(page, serial) {
  const row = unitRow(page, serial);
  await row.getByRole("button", { name: "Review & approve" }).click();
  const modal = modalByHeading(page, new RegExp(`Approval — ${serial}`));
  await modal.waitFor({ state: "visible" });
  await modal.getByRole("button", { name: "Approve", exact: true }).click();
  await waitForServiceReload(page);
}

async function engineerCompleteUnit(page, serial, proofPath) {
  const row = unitRow(page, serial);
  await row.getByRole("button", { name: "Step 4: Complete service" }).click();
  await page.getByRole("heading", { name: new RegExp(`Step 4: Complete service — ${serial}`) }).waitFor();
  await page.getByPlaceholder("Work performed").fill(`Completed work on ${serial}`);
  await page.locator('input[type="file"]').last().setInputFiles(proofPath);
  await page.getByRole("button", { name: "Mark service completed" }).click();
  await waitForServiceReload(page);
}

async function engineerPaymentUnit(page, serial, { paymentType, qrPath, amount }) {
  const row = unitRow(page, serial);
  await row.getByRole("button", { name: "Step 5: Raise payment request" }).click();
  await page.getByRole("heading", { name: new RegExp(`Step 5: Raise payment request — ${serial}`) }).waitFor();
  await page.getByPlaceholder("Total requested amount").fill(String(amount));
  if (paymentType === "UPI") {
    await page.locator("select").filter({ has: page.locator('option[value="UPI"]') }).selectOption("UPI");
    await page.locator('input[type="file"]').last().setInputFiles(qrPath);
  } else {
    await page.locator("select").filter({ has: page.locator('option[value="Cash"]') }).selectOption("Cash");
  }
  await page.getByRole("button", { name: "Submit payment request" }).click();
  await waitForServiceReload(page);
}

async function adminApprovePayment(page, serial, amount) {
  const row = unitRow(page, serial);
  await row.getByRole("button", { name: "Approve payment" }).click();
  const modal = modalByHeading(page, new RegExp(`Approve payment — ${serial}`));
  await modal.waitFor({ state: "visible" });
  await modal.getByPlaceholder("Approved payment amount").fill(String(amount));
  await modal.getByPlaceholder("Admin payment approval remarks").fill("E2E approved");
  await modal.getByRole("button", { name: "Approve payment" }).click();
  await waitForServiceReload(page);
}

async function main() {
  fs.mkdirSync(TMP_DIR, { recursive: true });
  const { proofPath, qrPath } = createFixtureFiles();

  try {
    fixture = runSetupScript();
    fs.writeFileSync(FIXTURE_PATH, JSON.stringify(fixture, null, 2));
    log("Setup isolated order + 2 installed serials", true, `order ${fixture.order_no}`);
  } catch (error) {
    log("Setup isolated order + 2 installed serials", false, error.message);
    process.exit(1);
  }

  const USERS = {
    callcenter: { email: fixture.callcenter_email, password: fixture.callcenter_password },
    admin: { email: fixture.admin_email, password: fixture.admin_password },
    engineer: { email: fixture.engineer_email, password: fixture.engineer_password },
  };

  const browser = await chromium.launch({ headless: HEADLESS, slowMo: SLOW_MO });
  const context = await browser.newContext({ acceptDownloads: true });
  const page = await context.newPage();
  let adminToken = null;

  try {
    // --- Callcenter: create service request ---
    await login(page, USERS.callcenter);
    log("Callcenter login", true, USERS.callcenter.email);
    await screenshot(page, "01-callcenter-login");

    await page.goto(`${BASE_URL}/services/new`);
    await page.getByRole("heading", { name: "New Service Request" }).waitFor();
    await page.locator("label", { hasText: "Customer Name" }).locator("..").locator("input").fill(fixture.customer_name);
    await page.locator("label", { hasText: "Customer Mobile" }).locator("..").locator("input").fill(fixture.customer_mobile);
    await page.locator("label", { hasText: "Problem Description" }).locator("..").locator("textarea").fill("E2E bulk-serial service test");
    await page.getByRole("button", { name: "Create Service Request" }).click();
    await page.waitForURL(/\/services\/\d+/, { timeout: 25000 });
    const urlMatch = page.url().match(/\/services\/(\d+)/);
    serviceId = urlMatch ? Number(urlMatch[1]) : null;
    await page.getByRole("heading", { name: /Service Request/ }).waitFor({ timeout: 15000 });
    log("Callcenter creates service request", Number.isFinite(serviceId), `service #${serviceId}`);
    await screenshot(page, "02-service-created");

    adminToken = await apiLogin(USERS.admin.email, USERS.admin.password);
    let service = await fetchService(adminToken, serviceId);
    log("API: service exists after create", service.id === serviceId, `status=${service.status}`);
    await logout(page);

    // --- Admin: verify order + assign units ---
    await login(page, USERS.admin);
    log("Admin login", true);
    await page.goto(`${BASE_URL}/services/${serviceId}`);
    await page.getByRole("heading", { name: /Service Request/ }).waitFor();

    const verifyInput = page.getByPlaceholder("Enter order number to verify");
    await verifyInput.fill(fixture.order_no);
    await page.getByRole("button", { name: "Verify Order" }).click();
    await page.getByText("Order verified and linked").waitFor({ timeout: 20000 });
    await waitForServiceReload(page);
    service = await fetchService(adminToken, serviceId);
    const unitCount = (service.units || []).length;
    log("Admin verifies order", unitCount === 2, `${unitCount} units, order=${service.order_no}`);
    await screenshot(page, "03-order-verified");

    await page.getByRole("button", { name: "View units" }).click();
    const checkboxes = page.locator('input[type="checkbox"]');
    const count = await checkboxes.count();
    for (let i = 0; i < count; i += 1) {
      const box = checkboxes.nth(i);
      if (await box.isEnabled()) {
        await box.check();
      }
    }
    await page.locator("select").filter({ has: page.locator(`option:has-text("${fixture.engineer_name}")`) })
      .selectOption({ label: fixture.engineer_name });
    await page.getByRole("button", { name: /Assign Engineer/ }).click();
    await page.getByText(/Assigned \d+ unit/).waitFor({ timeout: 20000 });
    await waitForServiceReload(page);
    service = await fetchService(adminToken, serviceId);
    const assigned = (service.units || []).every((u) => u.assigned_engineer_id === fixture.engineer_id);
    log("Admin assigns both serials to engineer", assigned, fixture.engineer_name);
    await screenshot(page, "04-units-assigned");

    const legacyHidden = await page.getByText("per-serial assignment").isVisible();
    const legacyDropdown = page.locator("select").filter({ has: page.locator('option', { hasText: "Select engineer" }) });
    const legacyVisible = await legacyDropdown.isVisible().catch(() => false);
    log("Legacy assign dropdown hidden when per-unit active", legacyHidden && !legacyVisible);
    await logout(page);

    // --- Engineer: per-unit workflow ---
    await login(page, USERS.engineer);
    log("Engineer login", true);
    await page.goto(`${BASE_URL}/services/${serviceId}`);
    await page.getByRole("heading", { name: /Service Request/ }).waitFor();
    await page.getByRole("button", { name: /Verify all/ }).click();
    await waitForServiceReload(page);
    service = await fetchService(adminToken, serviceId);
    const allVerified = (service.units || []).every((u) => u.serial_verified_at);
    log("Engineer verifies all serials", allVerified);
    await screenshot(page, "05-serials-verified");

    for (const serial of fixture.serials) {
      await engineerObservation(page, serial);
    }
    service = await fetchService(adminToken, serviceId);
    const allObserved = fixture.serials.every((s) => {
      const unit = unitBySerial(service, s);
      return unit && unit.unit_status === "Pending Service Approval";
    });
    log("Engineer submits observations (both serials)", allObserved);
    await screenshot(page, "06-observations-submitted");
    await logout(page);

    // --- Admin: approve observations ---
    await login(page, USERS.admin);
    await page.goto(`${BASE_URL}/services/${serviceId}`);
    await page.getByRole("heading", { name: /Service Request/ }).waitFor();
    for (const serial of fixture.serials) {
      await adminApproveUnit(page, serial);
    }
    service = await fetchService(adminToken, serviceId);
    const allApproved = fixture.serials.every((s) => {
      const unit = unitBySerial(service, s);
      return unit && unit.unit_status === "Approved for Service";
    });
    log("Admin approves both serials", allApproved);
    await screenshot(page, "07-serials-approved");
    await logout(page);

    // --- Engineer: complete + payment per serial ---
    await login(page, USERS.engineer);
    await page.goto(`${BASE_URL}/services/${serviceId}`);
    await page.getByRole("heading", { name: /Service Request/ }).waitFor();

    await engineerCompleteUnit(page, fixture.serials[0], proofPath);
    service = await fetchService(adminToken, serviceId);
    log(
      "Engineer Step 4 complete (serial 1)",
      unitBySerial(service, fixture.serials[0])?.unit_status === "Service Completed",
      fixture.serials[0],
    );

    await engineerPaymentUnit(page, fixture.serials[0], { paymentType: "Cash", amount: 500 });
    service = await fetchService(adminToken, serviceId);
    log(
      "Engineer Step 5 payment (serial 1, Cash)",
      unitBySerial(service, fixture.serials[0])?.unit_status === "Payment Requested",
      fixture.serials[0],
    );

    await engineerCompleteUnit(page, fixture.serials[1], proofPath);
    await engineerPaymentUnit(page, fixture.serials[1], { paymentType: "UPI", qrPath, amount: 750 });
    service = await fetchService(adminToken, serviceId);
    const bothPaymentRequested = fixture.serials.every((s) => {
      const unit = unitBySerial(service, s);
      return unit?.unit_status === "Payment Requested";
    });
    log("Engineer completes + requests payment (both serials)", bothPaymentRequested);
    await screenshot(page, "08-payment-requested");
    await logout(page);

    // --- Admin: approve payments ---
    await login(page, USERS.admin);
    await page.goto(`${BASE_URL}/services/${serviceId}`);
    await page.getByRole("heading", { name: /Service Request/ }).waitFor();
    await adminApprovePayment(page, fixture.serials[0], 500);
    await adminApprovePayment(page, fixture.serials[1], 750);
    service = await fetchService(adminToken, serviceId);
    const allPaymentCompleted = fixture.serials.every((s) => {
      const unit = unitBySerial(service, s);
      return unit?.unit_status === "Payment Completed";
    });
    log("Admin approves payments (both serials)", allPaymentCompleted);
    await screenshot(page, "09-payments-approved");

    // --- Admin: close service request ---
    try {
      const closedViaUi = await closeServiceViaUi(page, serviceId);
      log("Admin closes service request (UI POST)", closedViaUi);
    } catch (error) {
      log("Admin closes service request (UI POST)", false, error.message);
    }
    let serviceAfterClose = await fetchService(adminToken, serviceId);
    if (serviceAfterClose.status !== "Closed") {
      const closedViaApi = await closeServiceViaApi(adminToken, serviceId);
      log("Admin closes service request (API)", closedViaApi);
    }
    service = await waitForClosedService(adminToken, serviceId);
    const allClosed = fixture.serials.every((s) => unitBySerial(service, s)?.unit_status === "Closed");
    log("Admin closes service request", service.status === "Closed" && allClosed, `status=${service.status}`);
    await screenshot(page, "10-service-closed");

    log("Final API snapshot", service.status === "Closed" && allClosed, JSON.stringify({
      status: service.status,
      units: (service.units || []).map((u) => ({ serial: u.serial_no, unit_status: u.unit_status })),
    }));
  } catch (error) {
    try {
      await screenshot(page, "failure");
      fs.writeFileSync(path.join(TMP_DIR, "service-flow-failure.txt"), `${error.stack || error.message}\n`);
    } catch {}
    log("Unhandled error", false, error.message);
    console.error(error);
  } finally {
    await browser.close();
  }

  const report = {
    generated_at: new Date().toISOString(),
    fixture,
    service_id: serviceId,
    base_url: BASE_URL,
    api_url: API_URL,
    headless: HEADLESS,
    results,
    passed: results.filter((r) => r.ok).length,
    failed: results.filter((r) => !r.ok).length,
  };
  fs.writeFileSync(REPORT_PATH, JSON.stringify(report, null, 2));

  const mdLines = [
    "# Service Flow E2E Report",
    "",
    `**Generated:** ${report.generated_at}`,
    `**Service ID:** ${serviceId ?? "—"}`,
    `**Order:** ${fixture?.order_no ?? "—"}`,
    `**Result:** ${report.failed === 0 ? "PASS" : "FAIL"} (${report.passed}/${results.length} steps)`,
    "",
    "## Steps",
    "",
    ...results.map((r) => `- [${r.ok ? "x" : " "}] **${r.step}**${r.detail ? ` — ${r.detail}` : ""}`),
    "",
    "## Artifacts",
    "",
    `- Fixture: \`scripts/.e2e-tmp/service-flow-fixture.json\``,
    `- Screenshots: \`scripts/.e2e-tmp/service-flow-*.png\``,
    `- JSON report: \`scripts/.e2e-tmp/service-flow-report.json\``,
    "",
  ];
  fs.writeFileSync(REPORT_MD_PATH, mdLines.join("\n"));

  console.log("\n=== SERVICE FLOW E2E SUMMARY ===");
  for (const r of results) {
    console.log(`${r.ok ? "✓" : "✗"} ${r.step}${r.detail ? `: ${r.detail}` : ""}`);
  }
  console.log(`\nReport: ${REPORT_PATH}`);
  console.log(`Markdown: ${REPORT_MD_PATH}`);
  console.log(`Screenshots: ${TMP_DIR}/service-flow-*.png`);

  const failed = results.filter((r) => !r.ok);
  process.exit(failed.length ? 1 : 0);
}

main();
