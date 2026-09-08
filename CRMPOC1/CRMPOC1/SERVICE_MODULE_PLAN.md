# INDcool Service Module Analysis and Implementation Plan

## Current State Summary

The existing application already contains several building blocks that can be reused for a full service lifecycle module:

- `api/app/models/complaint.py`
  Current complaint tracking with customer details, engineer assignment, status changes, serial linkage, and status logs.
- `api/app/routers/complaints.py`
  CRUD, status updates, action logging, export, and serial history event creation for complaints.
- `ui/src/pages/complaints/*`
  Existing "New Complaint", list, detail, and status-edit UI that can be used as the visual baseline for call center service-request creation.
- `api/app/routers/orders.py`
  Searchable order and order-item data, vendor relationships, item codes, serial uniqueness protections, and vendor-facing flows.
- `api/app/routers/serials.py`
  Serial lookup and serial history pages already exist and should remain the canonical source for product and warranty-related history.
- `api/app/models/vendor.py`
  Vendor master exists and can be reused for vendor assignment.
- `api/app/models/payment.py`
  A payment transaction table exists, but it is currently too small for the service-payment workflow described in the requirements.
- `api/app/services/permissions.py` and `api/app/models/role.py`
  Role + permission model already supports per-module and per-submodule access.

## Key Gap

The current complaint module is a lightweight ticket tracker. It does not yet model:

- controlled service workflow states
- engineer vs vendor assignment history
- engineer observations and service approvals
- service completion details
- customer document upload workflow
- service-specific notifications
- service-specific payment requests and settlement separation
- dashboard metrics for service lifecycle stages

Because of that, the service module should be implemented as a dedicated service domain, not by overloading the existing complaint statuses and logs.

## Recommended Architecture

Use the current complaint creation experience as the call-center entry point, but persist service lifecycle data in new service-specific tables and APIs.

Recommended approach:

1. Keep the current `complaints` module stable for existing use cases.
2. Introduce a new `service_requests` domain for the lifecycle described in the requirement.
3. Reuse existing order, serial, vendor, user, file-upload, permission, and serial-history infrastructure.
4. Keep the UI visually aligned with the current complaint screens so adoption is smooth.

## Reusable Components

### API

- Complaint create form logic and request-number generation patterns from `api/app/routers/complaints.py`
- Upload handling from `api/app/services/file_service.py`
- Role authorization patterns from `api/app/services/permissions.py`
- Order, customer, and vendor lookup patterns from `api/app/routers/orders.py`
- Serial lookup and history integration from `api/app/routers/serials.py`
- Serial event audit creation from `api/app/services/serial_history.py`

### UI

- Form layout from `ui/src/pages/complaints/ComplaintCreate.jsx`
- Detail page structure from `ui/src/pages/complaints/ComplaintDetail.jsx`
- dashboard/table patterns from `ui/src/pages/VendorDashboard.jsx`, `ui/src/pages/Dashboard.jsx`, and existing list pages
- common components like `Modal`, `Pagination`, `StatusBadge`, and `SearchableSelect`

## Proposed Database Design

### 1. `service_requests`

Main service ticket table.

Suggested fields:

- `id`
- `request_no`
- `request_date`
- `query_type`
- `customer_name`
- `customer_mobile`
- `customer_email`
- `customer_address`
- `model_details`
- `problem_description`
- `additional_remarks`
- `status`
- `status_date`
- `source`
- `created_by`
- `order_id`
- `order_item_id`
- `serial_no`
- `service_type`
- `warranty_status`
- `assigned_engineer_id`
- `assigned_vendor_id`
- `requires_documents`
- `document_request_sent_at`
- `closed_at`

Notes:

- `assigned_engineer_id` and `assigned_vendor_id` should be mutually exclusive for active assignment.
- `order_item_id` should be the main link to existing order/serial data once identified.

### 2. `service_assignments`

Assignment history.

Suggested fields:

- `id`
- `service_request_id`
- `assignee_type` (`engineer` or `vendor`)
- `assignee_user_id`
- `assignee_vendor_id`
- `assigned_by`
- `assigned_at`
- `unassigned_at`
- `remarks`
- `is_active`

### 3. `service_observations`

Engineer/vendor diagnosis before approval.

Suggested fields:

- `id`
- `service_request_id`
- `submitted_by_user_id`
- `serial_no`
- `warranty_status`
- `service_type`
- `problem_found`
- `observation`
- `recommended_action`
- `parts_required_json`
- `estimated_service_charge`
- `estimated_parts_charge`
- `remarks`
- `submitted_at`

### 4. `service_approvals`

Approval or rejection by Indcool Service.

Suggested fields:

- `id`
- `service_request_id`
- `observation_id`
- `decision`
- `remarks`
- `approved_by`
- `approved_at`

### 5. `service_completions`

Actual work completion.

Suggested fields:

- `id`
- `service_request_id`
- `performed_by_type`
- `performed_by_user_id`
- `performed_by_vendor_id`
- `work_performed`
- `parts_replaced_json`
- `service_notes`
- `service_date`
- `customer_acknowledgement_path`
- `before_photos_json`
- `after_photos_json`
- `final_amount`
- `completion_remarks`
- `completed_at`

### 6. `service_documents`

Customer and engineer/vendor related document storage.

Suggested fields:

- `id`
- `service_request_id`
- `document_type`
- `file_path`
- `uploaded_by_type`
- `uploaded_by_user_id`
- `uploaded_by_customer_name`
- `status`
- `reviewed_by`
- `reviewed_at`
- `review_remarks`
- `uploaded_at`

### 7. `service_document_rules`

Configurable rules for required documents.

Suggested fields:

- `id`
- `service_type`
- `warranty_status`
- `query_type`
- `document_type`
- `is_required`
- `is_active`

### 8. `service_status_logs`

Dedicated workflow audit trail.

Suggested fields:

- `id`
- `service_request_id`
- `action`
- `old_status`
- `new_status`
- `performed_by`
- `performed_role`
- `remarks`
- `metadata_json`
- `created_at`

### 9. `service_payment_requests`

Service-linked payment request layer that can later bridge to existing payment transaction logic.

Suggested fields:

- `id`
- `service_request_id`
- `requested_by_type`
- `requested_by_user_id`
- `requested_by_vendor_id`
- `service_type`
- `customer_charge_amount`
- `settlement_service_amount`
- `settlement_parts_amount`
- `total_requested_amount`
- `payment_type`
- `remarks`
- `status`
- `processed_at`
- `created_at`

## Proposed Status Workflow

Recommended canonical service statuses:

- `New`
- `Service Team Review`
- `Assigned`
- `Engineer Visit`
- `Serial Verified`
- `Pending Service Approval`
- `Approved for Service`
- `Service In Progress`
- `Service Completed`
- `Payment Requested`
- `Payment Completed`
- `Closed`
- `Rejected`
- `Cancelled`

Supporting event types:

- `Reassigned`
- `Documents Requested`
- `Documents Uploaded`
- `Documents Reviewed`

These supporting events should live in logs, not as primary statuses.

## Warranty and Service Type Logic

Do not hard-code warranty logic into UI components.

Create a backend service function that:

- loads the linked `order_item`
- derives base dates from order delivery/order date
- computes warranty windows
- determines `IN WARRANTY` or `OUT OF WARRANTY`
- checks free-service eligibility using `free_service_count` and service-consumption history
- classifies service type as `Free Service`, `Warranty Service`, or `Paid Service`

This should be reusable from:

- service request detail
- engineer serial verification
- approval screen
- payment request screen

## API Changes

Create a new router set, for example `api/app/routers/services.py`, with endpoints like:

- `POST /api/services`
- `GET /api/services`
- `GET /api/services/{id}`
- `PUT /api/services/{id}`
- `POST /api/services/{id}/identify-customer`
- `POST /api/services/{id}/assign`
- `POST /api/services/{id}/verify-serial`
- `POST /api/services/{id}/observations`
- `POST /api/services/{id}/approval`
- `POST /api/services/{id}/completion`
- `POST /api/services/{id}/payment-request`
- `GET /api/services/{id}/history`
- `GET /api/services/{id}/documents`
- `POST /api/services/{id}/documents/upload`
- `POST /api/services/{id}/documents/request-link`
- `GET /api/services/dashboard/summary`

Also add supporting search endpoints:

- `GET /api/customers/search?mobile=&name=&order_no=`
- `GET /api/orders/{id}/service-context`
- `GET /api/engineers/lookup`
- `GET /api/vendors/lookup`

## UI Changes

### New Pages

- `ui/src/pages/services/ServiceRequestCreate.jsx`
- `ui/src/pages/services/ServiceRequestList.jsx`
- `ui/src/pages/services/ServiceRequestDetail.jsx`
- `ui/src/pages/services/ServiceAssignmentPanel.jsx`
- `ui/src/pages/services/ServiceObservationForm.jsx`
- `ui/src/pages/services/ServiceApprovalForm.jsx`
- `ui/src/pages/services/ServiceCompletionForm.jsx`
- `ui/src/pages/services/ServicePaymentRequestForm.jsx`
- `ui/src/pages/services/EngineerServiceDashboard.jsx`
- `ui/src/pages/services/ServiceTeamDashboard.jsx`

### Reuse Pattern

Use `ComplaintCreate.jsx` as the base for the call-center create screen:

- rename labels to service request terminology where appropriate
- keep the layout and styling consistent
- add document requirement summary after creation

## Roles and Permissions

Add or seed the following role behavior:

- `Call Center`
  Can create and view own service requests, but cannot assign or approve.
- `Indcool Service`
  New role or sub-role with full service workflow permissions.
- `Engineer`
  Can view assigned requests, verify serial, submit observations, complete service, and raise payment requests.
- `Vendor`
  Can only access requests assigned to that vendor.

Recommended permission module:

- module: `services`

Suggested actions:

- `can_view`
- `can_create`
- `can_edit`
- `can_assign`
- `can_approve`
- `can_complete`
- `can_request_payment`
- `can_review_documents`

The current permission table only stores the generic CRUD/export flags. For service-specific actions, either:

1. extend the permission table with new boolean columns, or
2. keep generic permissions in DB and enforce service-stage actions by role in the service module

Recommendation:

Short term, use role-gated service logic for stage actions.
Long term, extend permissions cleanly if this workflow will be heavily administered.

## Notifications and Customer Document Upload

The requirement needs asynchronous document visibility and notifications. The current codebase has a file upload service but not a notification subsystem.

Recommended implementation path:

### Phase 1

- generate secure customer document-upload token/link
- allow customer upload through a public or access-code-protected endpoint
- attach documents to the service request
- show document availability on service detail and assigned dashboard

### Phase 2

- add SMS/email integration
- add in-app notification records
- show unread document alerts for assigned engineer/vendor

## Serial History Integration

Every major service event should create serial history entries using the existing `create_serial_history_event(...)` helper.

Suggested serial-history events:

- service request created
- assignment changed
- serial verified
- observation submitted
- approval granted/rejected
- service completed
- payment requested
- payment completed
- request closed

This preserves the existing serial history page as the cross-module lifecycle view.

## Payment Integration

The existing `payment_transactions` model is too generic to directly satisfy the service-payment requirement, especially because:

- customer charge and engineer/vendor settlement must be separate
- service requests need a payment-request status trail
- free/warranty/paid service cases differ

Recommended approach:

- create `service_payment_requests`
- optionally create a bridge to `payment_transactions` when the request is actually processed
- do not collapse settlement and customer billing into one amount

## Incremental Delivery Plan

### Phase 1: Foundation

- add new service models, schemas, router, and migrations
- seed basic statuses
- seed `Indcool Service` role
- implement create/list/detail/history for service requests
- reuse current complaint-style UI for creation

### Phase 2: Customer and Product Context

- add customer/order search
- link order and order item
- add serial verification
- compute warranty status and service type

### Phase 3: Assignment and Observation

- assign to engineer or vendor
- store assignment history
- engineer/vendor dashboard
- observation submission

### Phase 4: Approval and Completion

- service-team approval/rejection
- completion capture
- parts and photos
- serial-history enrichment

### Phase 5: Documents and Notifications

- configurable document rules
- customer document upload link
- request-linked document repository
- assigned-user document visibility
- document upload notifications

### Phase 6: Payment and Closure

- service payment requests
- payment processing linkage
- closure workflow
- dashboard metrics and filters

## First Safe Implementation Slice

The smallest production-safe starting point is:

1. introduce `service_requests` and `service_status_logs`
2. create service request create/list/detail APIs
3. create a UI using the current complaint form layout
4. add controlled status transitions for:
   - `New`
   - `Service Team Review`
   - `Assigned`
5. expose service requests on a basic service dashboard

This gives the team a real service module entry point without prematurely locking in document, payment, or approval internals.

## Recommended Next Coding Step

Start implementation with:

- Alembic migration for `service_requests` and `service_status_logs`
- SQLAlchemy models
- Pydantic schemas
- `services` router with create/list/detail/history
- UI route and page set for service request creation and list/detail

That sequence aligns with the current architecture and keeps risk low.
