import json
import mimetypes
import sys
import traceback
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from uuid import uuid4


BASE_URL = "http://localhost:8010"
ADMIN_EMAIL = "admin@indcool.com"
ADMIN_PASSWORD = "admin123"
SAMPLE_PDF = Path(r"C:\crmpoc\CRMPOC1\sample-qa.pdf")


class ApiError(Exception):
    def __init__(self, status, body, headers=None):
        super().__init__(f"HTTP {status}: {body}")
        self.status = status
        self.body = body
        self.headers = headers or {}


class Client:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")
        self.token = None

    def _headers(self, extra=None):
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if extra:
            headers.update(extra)
        return headers

    def request(self, method, path, *, params=None, json_body=None, form=None, files=None, expected=(200,)):
        url = self.base_url + path
        if params:
            q = urllib.parse.urlencode(params, doseq=True)
            url = f"{url}?{q}"

        data = None
        headers = self._headers()

        if files is not None or form is not None:
            boundary = f"----CodexBoundary{uuid4().hex}"
            parts = []
            form = form or {}
            for key, value in form.items():
                if value is None:
                    continue
                parts.extend(
                    [
                        f"--{boundary}".encode(),
                        f'Content-Disposition: form-data; name="{key}"'.encode(),
                        b"",
                        str(value).encode(),
                    ]
                )
            for key, file_info in (files or {}).items():
                if file_info is None:
                    continue
                filename, content = file_info
                mime = mimetypes.guess_type(filename)[0] or "application/octet-stream"
                parts.extend(
                    [
                        f"--{boundary}".encode(),
                        f'Content-Disposition: form-data; name="{key}"; filename="{Path(filename).name}"'.encode(),
                        f"Content-Type: {mime}".encode(),
                        b"",
                        content,
                    ]
                )
            parts.append(f"--{boundary}--".encode())
            data = b"\r\n".join(parts)
            headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        elif json_body is not None:
            data = json.dumps(json_body).encode()
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = resp.read()
                if resp.status not in expected:
                    raise ApiError(resp.status, body.decode(errors="ignore"), dict(resp.headers))
                return self._parse_response(body, resp.headers)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode(errors="ignore")
            raise ApiError(exc.code, body, dict(exc.headers)) from None

    @staticmethod
    def _parse_response(body, headers):
        content_type = headers.get("Content-Type", "")
        if not body:
            return None
        if "application/json" in content_type:
            return json.loads(body.decode())
        return {
            "raw": body,
            "text": body.decode(errors="ignore"),
            "content_type": content_type,
            "length": len(body),
        }


class Regression:
    def __init__(self):
        self.client = Client(BASE_URL)
        self.results = []
        self.created = {}
        self.test_id = uuid4().hex[:8]
        self.prefix = f"API-QA-{self.test_id}"
        self.engineer = None
        self.sample_pdf_bytes = SAMPLE_PDF.read_bytes() if SAMPLE_PDF.exists() else None

    def check(self, name, fn):
        try:
            detail = fn()
            self.results.append({"name": name, "status": "PASS", "detail": detail})
        except Exception as exc:
            self.results.append({"name": name, "status": "FAIL", "detail": str(exc)})

    def run(self):
        self.check("auth.login", self.auth_login)
        self.check("auth.me", self.auth_me)
        self.check("users.list", self.users_list)
        self.check("roles.read", self.roles_read)
        self.check("dashboard", self.dashboard)
        self.check("serials", self.serials)
        self.check("item_masters.crud_export", self.item_masters)
        self.check("couriers.crud_export", self.couriers)
        self.check("roles.crud_permissions", self.roles_crud)
        self.check("users.crud_reset_change_password", self.users_crud)
        self.check("complaints.crud_status_action_export", self.complaints)
        self.check("calls.crud_transfer_followup", self.calls)
        self.check("claims.crud_status_export", self.claims)
        self.check("orders.lookups_crud_export_submit", self.orders)
        self.check("installations.crud_assign_cancel_status", self.installations)
        self.check("projects.crud_tasks_run", self.projects)
        self.check("market.crud_dashboard", self.market)
        self.check("auth.logout", self.auth_logout)
        self.print_report()
        return 1 if any(r["status"] == "FAIL" for r in self.results) else 0

    def auth_login(self):
        resp = self.client.request(
            "POST",
            "/api/auth/login",
            json_body={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )
        self.client.token = resp["access_token"]
        return f"user={resp['user']['email']}"

    def auth_me(self):
        me = self.client.request("GET", "/api/auth/me")
        return f"role={me['role']}"

    def auth_logout(self):
        self.client.request("POST", "/api/auth/logout")
        return "logout ok"

    def users_list(self):
        users = self.client.request("GET", "/api/users")
        self.engineer = next((u for u in users if u.get("role") == "engineer" and u.get("is_active", True)), None)
        if not self.engineer:
            raise RuntimeError("No active engineer user found")
        return f"users={len(users)} engineer={self.engineer['email']}"

    def roles_read(self):
        modules = self.client.request("GET", "/api/roles/modules")
        matrix = self.client.request("GET", "/api/roles/matrix")
        roles = self.client.request("GET", "/api/roles")
        self.created["role_modules"] = modules
        return f"modules={len(modules.get('modules', modules)) if isinstance(modules, dict) else len(modules)} matrix={len(matrix)} roles={len(roles)}"

    def dashboard(self):
        comp = self.client.request("GET", "/api/dashboard/complaints-summary")
        inst = self.client.request("GET", "/api/dashboard/installation-summary")
        orders = self.client.request("GET", "/api/dashboard/orders-summary")
        chart = self.client.request("GET", "/api/dashboard/complaint-chart")
        return f"comp={list(comp.keys())} inst={list(inst.keys())} orders={list(orders.keys())} chart={list(chart.keys())}"

    def serials(self):
        search = self.client.request("GET", "/api/serials/search", params={"query": "V1ASG731"})
        lookup = self.client.request("GET", "/api/serials/lookup", params={"serial_no": "V1ASG731-01A"})
        return f"search={len(search)} lookup_status={lookup.get('installation_status')}"

    def export_check(self, path, params=None):
        resp = self.client.request("GET", path, params=params)
        if not isinstance(resp, dict) or "length" not in resp:
            raise RuntimeError(f"Export {path} did not return file content")
        if resp["length"] <= 0:
            raise RuntimeError(f"Export {path} returned empty payload")
        return resp["length"]

    def item_masters(self):
        item = self.client.request(
            "POST",
            "/api/items",
            json_body={
                "item_code": f"{self.prefix}-ITEM",
                "item_name": f"{self.prefix} Item",
                "category": "AC",
                "brand": "QA",
                "unit": "pcs",
                "mrp": 1234.5,
                "is_active": True,
            },
            expected=(201,),
        )
        self.created["item_id"] = item["id"]
        listed = self.client.request("GET", "/api/items", params={"search": self.prefix})
        got = self.client.request("GET", f"/api/items/{item['id']}")
        updated = self.client.request("PUT", f"/api/items/{item['id']}", json_body={"brand": "QA-UPDATED", "mrp": 999.0})
        export_len = self.export_check("/api/items/export", {"search": self.prefix})
        self.client.request("DELETE", f"/api/items/{item['id']}", expected=(204,))
        return f"list={listed['total']} get={got['item_code']} update_brand={updated['brand']} export={export_len}"

    def couriers(self):
        courier = self.client.request(
            "POST",
            "/api/couriers",
            json_body={
                "courier_name": f"{self.prefix} Courier",
                "contact_name": "QA Courier",
                "contact_mobile": "9990002222",
                "email": "qa.courier@example.com",
                "address": "QA courier address",
            },
            expected=(201,),
        )
        self.created["courier_id"] = courier["id"]
        listed = self.client.request("GET", "/api/couriers", params={"search": self.prefix})
        got = self.client.request("GET", f"/api/couriers/{courier['id']}")
        updated = self.client.request("PUT", f"/api/couriers/{courier['id']}", json_body={"contact_name": "QA Courier Updated"})
        export_len = self.export_check("/api/couriers/export", {"search": self.prefix})
        self.client.request("DELETE", f"/api/couriers/{courier['id']}", expected=(204,))
        return f"list={listed['total']} get={got['courier_name']} update={updated['contact_name']} export={export_len}"

    def roles_crud(self):
        role = self.client.request(
            "POST",
            "/api/roles",
            json_body={"name": f"{self.prefix}-role", "description": "QA API test role"},
            expected=(201,),
        )
        self.created["role_id"] = role["id"]
        got = self.client.request("GET", f"/api/roles/{role['id']}")
        updated = self.client.request("PUT", f"/api/roles/{role['id']}", json_body={"description": "QA role updated"})
        modules = self.created.get("role_modules")
        module_name = None
        if isinstance(modules, dict):
            raw = modules.get("modules", [])
            if raw:
                first = raw[0]
                module_name = first["module"] if isinstance(first, dict) else str(first)
        permissions = [{"module": module_name or "complaints", "can_view": True, "can_create": True}]
        perm_resp = self.client.request("PUT", f"/api/roles/{role['id']}/permissions", json_body={"permissions": permissions})
        self.client.request("DELETE", f"/api/roles/{role['id']}", expected=(204,))
        return f"get={got['name']} update={updated['description']} perms={len(perm_resp)}"

    def users_crud(self):
        email = f"{self.prefix.lower()}@example.com"
        user = self.client.request(
            "POST",
            "/api/users",
            json_body={
                "name": f"{self.prefix} User",
                "email": email,
                "password": "TempPass123!",
                "role": "callcenter",
                "phone": "9990003333",
                "is_active": True,
            },
            expected=(201,),
        )
        user_id = user["id"]
        got = self.client.request("GET", f"/api/users/{user_id}")
        updated = self.client.request("PUT", f"/api/users/{user_id}", json_body={"name": f"{self.prefix} User Updated", "phone": "9990003334"})
        self.client.request("PUT", f"/api/users/{user_id}/reset-password", json_body={"new_password": "ResetPass123!"}, expected=(204,))

        temp = Client(BASE_URL)
        login1 = temp.request("POST", "/api/auth/login", json_body={"email": email, "password": "ResetPass123!"})
        temp.token = login1["access_token"]
        temp.request("PUT", "/api/auth/change-password", json_body={"current_password": "ResetPass123!", "new_password": "ChangedPass123!"})
        login2 = temp.request("POST", "/api/auth/login", json_body={"email": email, "password": "ChangedPass123!"})

        self.client.request("DELETE", f"/api/users/{user_id}", expected=(204,))
        return f"get={got['email']} update={updated['phone']} relogin={login2['user']['email']}"

    def complaints(self):
        complaint = self.client.request(
            "POST",
            "/api/complaints",
            json_body={
                "comp_date": "2026-07-31",
                "customer_name": f"{self.prefix} Complaint",
                "customer_mobile": "9990004444",
                "customer_email": "qa.complaint@example.com",
                "customer_address": "QA complaint address",
                "model_details": "AIR COOLER IDCCLR40L",
                "problem_description": "Cooling issue for backend regression",
                "query_type": "Service",
                "remark": "Created by API regression",
                "send_sms": False,
            },
            expected=(201,),
        )
        cid = complaint["id"]
        self.created["complaint_id"] = cid
        listed = self.client.request("GET", "/api/complaints", params={"customer_name": self.prefix})
        got = self.client.request("GET", f"/api/complaints/{cid}")
        updated = self.client.request("PUT", f"/api/complaints/{cid}", json_body={"remark": "Updated by API regression"})
        status_form = {
            "new_status": "Under Process",
            "assigned_engineer": self.engineer["id"],
            "remark": "Assigned during API regression",
        }
        files = {"document": ("sample-qa.pdf", self.sample_pdf_bytes)} if self.sample_pdf_bytes else None
        status_resp = self.client.request("PUT", f"/api/complaints/{cid}/status", form=status_form, files=files)
        action = self.client.request(
            "POST",
            f"/api/complaints/{cid}/action",
            json_body={"action_taken": "Request Sent", "remark": "API regression action"},
            expected=(201,),
        )
        history = self.client.request("GET", f"/api/complaints/{cid}/history")
        export_len = self.export_check("/api/complaints/export", {"customer_name": self.prefix})
        return f"list={listed['total']} get={got['comp_no']} update={updated['remark']} status={status_resp['status']} history={len(history)} export={export_len} action={action.get('message', 'ok')}"

    def calls(self):
        cid = self.created["complaint_id"]
        call = self.client.request(
            "POST",
            "/api/calls",
            json_body={
                "customer_name": f"{self.prefix} Caller",
                "customer_email": "qa.call@example.com",
                "phone": "9990005555",
                "call_type": "Inbound",
                "status": "Open",
                "priority": "High",
                "call_datetime": "2026-07-31T10:00:00",
                "followup_date": "2026-08-01T10:00:00",
                "notes": "Created by API regression",
                "follow_up_notes": "Initial follow-up",
                "complaint_id": cid,
            },
            expected=(201,),
        )
        call_id = call["id"]
        listed = self.client.request("GET", "/api/calls", params={"search": self.prefix})
        pending = self.client.request("GET", "/api/calls/pending-follow-ups", params={"complaint_id": cid})
        calendar = self.client.request("GET", "/api/calls/calendar-events", params={"complaint_id": cid})
        got = self.client.request("GET", f"/api/calls/{call_id}")
        updated = self.client.request("PUT", f"/api/calls/{call_id}", json_body={"status": "In Progress", "follow_up_notes": "Updated note"})
        transferred = self.client.request("POST", f"/api/calls/{call_id}/transfer", json_body={"transferred_to": self.engineer["id"], "transfer_notes": "QA transfer"})
        completed = self.client.request("POST", f"/api/calls/{call_id}/complete-followup")
        self.client.request("DELETE", f"/api/calls/{call_id}", expected=(204,))
        return f"list={listed['total']} pending={pending['total']} calendar={len(calendar)} get={got['ref_no']} update={updated['status']} transfer={transferred['is_transferred']} complete={completed['follow_up_status']}"

    def claims(self):
        claim = self.client.request(
            "POST",
            "/api/claims",
            json_body={
                "order_no": f"{self.prefix}-ORDER",
                "serial_number": f"{self.prefix}-SERIAL",
                "customer_name": f"{self.prefix} Claim",
                "customer_contact": "9990006666",
                "customer_email": "qa.claim@example.com",
                "notes": "Claim created by API regression",
                "bank_name": "QA Bank",
                "account_holder_name": "QA Holder",
                "account_number": "1234567890",
                "ifsc_code": "SBIN0001234",
            },
            expected=(201,),
        )
        claim_id = claim["id"]
        listed = self.client.request("GET", "/api/claims", params={"search": self.prefix})
        got = self.client.request("GET", f"/api/claims/{claim_id}")
        updated = self.client.request("PUT", f"/api/claims/{claim_id}", json_body={"notes": "Claim updated by API regression"})
        status = self.client.request("PUT", f"/api/claims/{claim_id}/status", json_body={"status": "Completed", "admin_remark": "QA closed"})
        export_len = self.export_check("/api/claims/export", {"search": self.prefix})
        self.client.request("DELETE", f"/api/claims/{claim_id}", expected=(204,))
        return f"list={listed['total']} get={got['claim_id']} update={updated['notes']} status={status['status']} export={export_len}"

    def orders(self):
        vendors = self.client.request("GET", "/api/orders/lookup/vendors")
        items = self.client.request("GET", "/api/orders/lookup/items")
        couriers = self.client.request("GET", "/api/orders/lookup/couriers")
        if not vendors or not items:
            raise RuntimeError("Order lookup data missing")

        vendor_id = vendors[0]["id"]
        item_id = items[0]["id"]
        courier_id = couriers[0]["id"] if couriers else None
        order_no = f"{self.prefix}-ORD"
        payload = {
            "order_no": order_no,
            "order_date": "2026-07-31",
            "oem_bill_no": f"{self.prefix}-OEM",
            "vendor_id": vendor_id,
            "customer_name": f"{self.prefix} Order Customer",
            "customer_contact": "9990007777",
            "customer_email": "qa.order@example.com",
            "customer_city": "Noida",
            "customer_state": "Uttar Pradesh",
            "customer_address": "QA order address",
            "courier_id": courier_id,
            "lrn_no": f"{self.prefix}-LRN",
            "vendor_bill_no": f"{self.prefix}-VBILL",
            "vendor_bill_date": "2026-07-31",
            "status": "Delivered",
            "expected_delivery_date": "2026-08-02",
            "actual_delivery_date": "2026-07-31",
            "items": [
                {
                    "item_id": item_id,
                    "serial_no": f"{self.prefix}-S1",
                    "serial_no_2": f"{self.prefix}-S2",
                    "item_qty": 1,
                    "pcb_warranty_years": 1,
                    "component_warranty_years": 2,
                    "machine_warranty_years": 3,
                    "free_service_count": 2,
                }
            ],
        }
        created = self.client.request(
            "POST",
            "/api/orders",
            form={"payload": json.dumps(payload)},
            expected=(201,),
        )
        order_id = created["id"]
        self.created["order_id"] = order_id
        self.created["order_item_id"] = created["items"][0]["id"]
        listed = self.client.request("GET", "/api/orders", params={"search": self.prefix})
        got = self.client.request("GET", f"/api/orders/{order_id}")
        updated = self.client.request("PUT", f"/api/orders/{order_id}", json_body={"customer_city": "Ghaziabad", "oem_bill_no": f"{self.prefix}-OEM-UPD"})
        export_len = self.export_check("/api/orders/export", {"search": self.prefix})
        submit = self.client.request(
            "POST",
            f"/api/orders/{order_id}/submit-serials",
            json_body={
                "order_id": order_id,
                "order_item_ids": [self.created["order_item_id"]],
                "selected_serials": [f"{self.created['order_item_id']}-serial1", f"{self.created['order_item_id']}-serial2"],
            },
        )
        inst_rows = self.client.request("GET", "/api/installations", params={"order_id": order_id, "per_page": 50})
        touched = inst_rows.get("items", [])
        if not touched:
            raise RuntimeError(f"No installation found after submit-serials: {submit}")
        self.created["installation_id"] = touched[0]["id"]
        return f"lookups=vendors:{len(vendors)} items:{len(items)} couriers:{len(couriers)} list={listed['total']} get={got['order_no']} update={updated['customer_city']} export={export_len} installations={len(touched)}"

    def installations(self):
        manual = self.client.request(
            "POST",
            "/api/installations",
            json_body={
                "customer_name": f"{self.prefix} Installation",
                "contact_number": "9990008888",
                "address": "QA installation address",
                "product_name": "QA Product",
                "request_date": "2026-07-31T12:00:00",
            },
            expected=(201,),
        )
        manual_id = manual["id"]
        listed = self.client.request("GET", "/api/installations", params={"search": self.prefix})
        got = self.client.request("GET", f"/api/installations/{manual_id}")
        updated = self.client.request("PUT", f"/api/installations/{manual_id}", json_body={"work_report": "Updated installation note", "status": "Pending"})
        assign_target = self.created["installation_id"]
        assigned = self.client.request(
            "POST",
            "/api/installations/bulk-assign",
            json_body={"assignments": [{"installation_id": assign_target, "engineer_id": self.engineer["id"]}]},
        )
        cancel_one = self.client.request("POST", f"/api/installations/{assign_target}/cancel")
        status_form = {
            "new_status": "Completed",
            "work_report": "Progress update from API regression",
        }
        files = {"document": ("sample-qa.pdf", self.sample_pdf_bytes)} if self.sample_pdf_bytes else None
        status = self.client.request("PUT", f"/api/installations/{manual_id}/status", form=status_form, files=files)
        cancel_bulk = self.client.request("POST", "/api/installations/bulk-cancel", json_body={"installation_ids": [manual_id]})
        self.client.request("DELETE", f"/api/installations/{manual_id}", expected=(204,))
        return f"list={listed['total']} get={got['id']} update={updated['status']} assign={assigned.get('updated', assigned)} status={status['status']} cancel_one={cancel_one.get('message', 'ok')} cancel_bulk={cancel_bulk.get('message', 'ok')}"

    def projects(self):
        project = self.client.request(
            "POST",
            "/api/projects",
            json_body={"title": f"{self.prefix} Project", "description": "QA project", "status": "Draft"},
            expected=(201,),
        )
        pid = project["id"]
        listed = self.client.request("GET", "/api/projects")
        got = self.client.request("GET", f"/api/projects/{pid}")
        updated = self.client.request("PATCH", f"/api/projects/{pid}", json_body={"status": "Active"})
        task = self.client.request(
            "POST",
            f"/api/projects/{pid}/tasks",
            json_body={"task_name": "QA Gather Responses", "task_type": "Gather Responses", "sequence": 1, "input_data": "{\"responses\":[{\"score\":5}]}"},
            expected=(201,),
        )
        tid = task["id"]
        task_upd = self.client.request("PATCH", f"/api/projects/{pid}/tasks/{tid}", json_body={"task_name": "QA Gather Responses Updated"})
        task_run = self.client.request("POST", f"/api/projects/{pid}/tasks/{tid}/run", json_body={})
        task_reset = self.client.request("POST", f"/api/projects/{pid}/tasks/{tid}/reset")
        project_run = self.client.request("POST", f"/api/projects/{pid}/run")
        if task_run.get("status") != "Completed" or project_run.get("status") != "Completed":
            raise RuntimeError(f"Task/project execution failed: task={task_run} project={project_run}")
        self.client.request("DELETE", f"/api/projects/{pid}/tasks/{tid}", expected=(204,))
        self.client.request("DELETE", f"/api/projects/{pid}", expected=(204,))
        return f"projects={len(listed)} detail_tasks={len(got['tasks'])} update={updated['status']} task_update={task_upd['task_name']} task_run={task_run['status']} reset={task_reset['status']} project_run={project_run['status']}"

    def market(self):
        dashboard = self.client.request("GET", "/api/market/dashboard")
        lookup = self.client.request("GET", "/api/market/users/lookup")
        users_before = self.client.request("GET", "/api/market/users")
        retailer = self.client.request(
            "POST",
            "/api/market/users",
            json_body={
                "name": f"{self.prefix} Retailer",
                "email": f"{self.prefix.lower()}-retailer@example.com",
                "phone": "9990009001",
                "address": "QA retailer address",
                "city": "Noida",
                "state": "UP",
                "role": "Retailer",
                "status": "Active",
                "fee_status": "Paid",
                "onboarding_fee": 1000,
            },
            expected=(201,),
        )
        distributor = self.client.request(
            "POST",
            "/api/market/users",
            json_body={
                "name": f"{self.prefix} Distributor",
                "email": f"{self.prefix.lower()}-distributor@example.com",
                "phone": "9990009002",
                "address": "QA distributor address",
                "city": "Delhi",
                "state": "Delhi",
                "role": "Distributor",
                "status": "Active",
                "fee_status": "Pending",
                "onboarding_fee": 1500,
            },
            expected=(201,),
        )
        retailer_upd = self.client.request("PUT", f"/api/market/users/{retailer['id']}", json_body={"city": "Ghaziabad"})

        category = self.client.request(
            "POST",
            "/api/market/categories",
            json_body={"name": f"{self.prefix} Category"},
            expected=(201,),
        )
        category_upd = self.client.request("PUT", f"/api/market/categories/{category['id']}", json_body={"name": f"{self.prefix} Category Updated"})

        item = self.client.request(
            "POST",
            "/api/market/items",
            json_body={
                "sku": f"{self.prefix}-SKU",
                "name": f"{self.prefix} Market Item",
                "company": "QA Co",
                "category_id": category["id"],
                "base_price": 2500,
                "mrp": 3000,
                "status": "Active",
                "stock_count": 25,
                "description": "QA market item",
            },
            expected=(201,),
        )
        item_upd = self.client.request("PUT", f"/api/market/items/{item['id']}", json_body={"stock_count": 30})

        order = self.client.request(
            "POST",
            "/api/market/orders",
            json_body={
                "retailer_id": retailer["id"],
                "distributor_id": distributor["id"],
                "status": "Pending",
                "notes": "QA market order",
                "items": [{"item_id": item["id"], "qty": 2, "unit_price": 2500}],
            },
            expected=(201,),
        )
        order_upd = self.client.request("PUT", f"/api/market/orders/{order['id']}", json_body={"status": "Approved", "notes": "QA market order updated"})

        self.client.request("DELETE", f"/api/market/orders/{order['id']}", expected=(204,))
        self.client.request("DELETE", f"/api/market/items/{item['id']}", expected=(204,))
        self.client.request("DELETE", f"/api/market/categories/{category['id']}", expected=(204,))
        self.client.request("DELETE", f"/api/market/users/{retailer['id']}", expected=(204,))
        self.client.request("DELETE", f"/api/market/users/{distributor['id']}", expected=(204,))
        return f"dashboard={list(dashboard.keys())} lookup={len(lookup)} users_before={users_before['total']} retailer={retailer_upd['city']} category={category_upd['name']} item_stock={item_upd['stock_count']} order={order_upd['status']}"

    def print_report(self):
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = total - passed
        print(json.dumps({"summary": {"total": total, "passed": passed, "failed": failed}, "results": self.results}, indent=2))


if __name__ == "__main__":
    sys.exit(Regression().run())
