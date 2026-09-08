# Service Flow E2E Report

**Generated:** 2026-08-29T13:07:18.277Z
**Service ID:** 3
**Order:** E2E-SRV-20260829130611
**Result:** PASS (19/19 steps)

## Steps

- [x] **Setup isolated order + 2 installed serials** — order E2E-SRV-20260829130611
- [x] **Callcenter login** — callcenter@indcool.com
- [x] **Callcenter creates service request** — service #3
- [x] **API: service exists after create** — status=New
- [x] **Admin login**
- [x] **Admin verifies order** — 2 units, order=E2E-SRV-20260829130611
- [x] **Admin assigns both serials to engineer** — Ravi Kumar
- [x] **Legacy assign dropdown hidden when per-unit active**
- [x] **Engineer login**
- [x] **Engineer verifies all serials**
- [x] **Engineer submits observations (both serials)**
- [x] **Admin approves both serials**
- [x] **Engineer Step 4 complete (serial 1)** — E2E-SN-1-20260829130611
- [x] **Engineer Step 5 payment (serial 1, Cash)** — E2E-SN-1-20260829130611
- [x] **Engineer completes + requests payment (both serials)**
- [x] **Admin approves payments (both serials)**
- [x] **Admin closes service request (UI POST)**
- [x] **Admin closes service request** — status=Closed
- [x] **Final API snapshot** — {"status":"Closed","units":[{"serial":"E2E-SN-1-20260829130611","unit_status":"Closed"},{"serial":"E2E-SN-2-20260829130611","unit_status":"Closed"}]}

## Artifacts

- Fixture: `scripts/.e2e-tmp/service-flow-fixture.json`
- Screenshots: `scripts/.e2e-tmp/service-flow-*.png`
- JSON report: `scripts/.e2e-tmp/service-flow-report.json`
