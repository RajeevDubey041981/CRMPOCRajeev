-- SQL Server compatible script for the CRMPOC application
-- Run in SQL Server Management Studio (SSMS) or sqlcmd
-- This single script creates the tables and inserts basic seed data.

SET NOCOUNT ON;
GO

IF OBJECT_ID(N'dbo.workflow_tasks', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.workflow_tasks (
        id INT IDENTITY(1,1) PRIMARY KEY,
        project_id INT NOT NULL,
        task_name NVARCHAR(255) NOT NULL,
        task_type NVARCHAR(50) NOT NULL,
        sequence INT NOT NULL DEFAULT 1,
        status NVARCHAR(20) NOT NULL DEFAULT 'Pending',
        advisor_id NVARCHAR(100) NULL,
        input_data NTEXT NULL,
        output_data NTEXT NULL,
        error_message NTEXT NULL,
        started_at NVARCHAR(50) NULL,
        completed_at NVARCHAR(50) NULL,
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
END
GO

IF OBJECT_ID(N'dbo.projects', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.projects (
        id INT IDENTITY(1,1) PRIMARY KEY,
        title NVARCHAR(255) NOT NULL,
        description NTEXT NULL,
        status NVARCHAR(30) NOT NULL DEFAULT 'Draft',
        owner_id INT NULL,
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
END
GO

IF OBJECT_ID(N'dbo.market_order_items', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.market_order_items (
        id INT IDENTITY(1,1) PRIMARY KEY,
        order_id INT NOT NULL,
        item_id INT NULL,
        qty INT NOT NULL DEFAULT 1,
        unit_price DECIMAL(10,2) NULL,
        subtotal DECIMAL(12,2) NULL,
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
END
GO

IF OBJECT_ID(N'dbo.market_orders', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.market_orders (
        id INT IDENTITY(1,1) PRIMARY KEY,
        order_no NVARCHAR(50) NOT NULL UNIQUE,
        retailer_id INT NULL,
        distributor_id INT NULL,
        total_amount DECIMAL(12,2) NULL,
        status NVARCHAR(20) NOT NULL DEFAULT 'Pending',
        notes NTEXT NULL,
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
END
GO

IF OBJECT_ID(N'dbo.market_users', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.market_users (
        id INT IDENTITY(1,1) PRIMARY KEY,
        name NVARCHAR(255) NOT NULL,
        email NVARCHAR(255) NOT NULL UNIQUE,
        phone NVARCHAR(20) NULL,
        address NTEXT NULL,
        city NVARCHAR(100) NULL,
        state NVARCHAR(100) NULL,
        role NVARCHAR(50) NOT NULL DEFAULT 'Retailer',
        status NVARCHAR(20) NOT NULL DEFAULT 'Pending',
        fee_status NVARCHAR(20) NOT NULL DEFAULT 'Pending',
        onboarding_fee DECIMAL(10,2) NULL,
        joined_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
END
GO

IF OBJECT_ID(N'dbo.market_items', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.market_items (
        id INT IDENTITY(1,1) PRIMARY KEY,
        sku NVARCHAR(100) NOT NULL UNIQUE,
        name NVARCHAR(255) NOT NULL,
        company NVARCHAR(100) NULL,
        category_id INT NULL,
        base_price DECIMAL(10,2) NULL,
        mrp DECIMAL(10,2) NULL,
        image_path NVARCHAR(500) NULL,
        status NVARCHAR(20) NOT NULL DEFAULT 'Active',
        stock_count INT NOT NULL DEFAULT 0,
        description NTEXT NULL,
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
END
GO

IF OBJECT_ID(N'dbo.market_categories', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.market_categories (
        id INT IDENTITY(1,1) PRIMARY KEY,
        name NVARCHAR(255) NOT NULL,
        parent_id INT NULL,
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
END
GO

IF OBJECT_ID(N'dbo.claim_photos', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.claim_photos (
        id INT IDENTITY(1,1) PRIMARY KEY,
        claim_id INT NOT NULL,
        file_path NVARCHAR(500) NOT NULL,
        uploaded_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
END
GO

IF OBJECT_ID(N'dbo.claims', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.claims (
        id INT IDENTITY(1,1) PRIMARY KEY,
        claim_id NVARCHAR(100) NOT NULL UNIQUE,
        order_no NVARCHAR(255) NULL,
        serial_number NVARCHAR(100) NULL,
        order_item_id INT NULL,
        customer_name NVARCHAR(255) NULL,
        customer_contact NVARCHAR(20) NULL,
        customer_email NVARCHAR(255) NULL,
        status NVARCHAR(50) NOT NULL DEFAULT 'Processing',
        submitted_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        processed_by INT NULL,
        notes NTEXT NULL,
        bank_name NVARCHAR(100) NULL,
        account_holder_name NVARCHAR(255) NULL,
        account_number NVARCHAR(100) NULL,
        ifsc_code NVARCHAR(20) NULL,
        admin_remark NTEXT NULL,
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
END
GO

IF OBJECT_ID(N'dbo.calls', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.calls (
        id INT IDENTITY(1,1) PRIMARY KEY,
        ref_no NVARCHAR(100) NOT NULL UNIQUE,
        customer_name NVARCHAR(255) NULL,
        customer_email NVARCHAR(255) NULL,
        phone NVARCHAR(20) NULL,
        call_type NVARCHAR(20) NULL,
        status NVARCHAR(30) NULL,
        priority NVARCHAR(20) NOT NULL DEFAULT 'medium',
        assigned_to INT NULL,
        transferred_to INT NULL,
        is_transferred BIT NOT NULL DEFAULT 0,
        duration_secs INT NULL,
        call_datetime DATETIME2 NOT NULL,
        followup_date DATETIME2 NULL,
        notes NTEXT NULL,
        follow_up_notes NTEXT NULL,
        follow_up_status NVARCHAR(30) NULL,
        complaint_id INT NULL,
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
END
GO

IF OBJECT_ID(N'dbo.installation_requests', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.installation_requests (
        id INT IDENTITY(1,1) PRIMARY KEY,
        customer_name NVARCHAR(255) NOT NULL,
        contact_number NVARCHAR(20) NOT NULL,
        address NTEXT NULL,
        order_item_id INT NULL,
        product_name NVARCHAR(255) NULL,
        serial_no NVARCHAR(100) NULL,
        serial_no_2 NVARCHAR(100) NULL,
        request_date DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        assigned_engineer INT NULL,
        status NVARCHAR(50) NOT NULL DEFAULT 'Pending',
        installation_date DATETIME2 NULL,
        work_report NTEXT NULL,
        work_report_file_path NVARCHAR(500) NULL,
        settlement_approved_by INT NULL,
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
END
GO

IF OBJECT_ID(N'dbo.complaint_status_logs', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.complaint_status_logs (
        id INT IDENTITY(1,1) PRIMARY KEY,
        complaint_id INT NOT NULL,
        old_status NVARCHAR(50) NULL,
        new_status NVARCHAR(50) NULL,
        changed_by INT NULL,
        remark NTEXT NULL,
        document_path NVARCHAR(500) NULL,
        action_taken NVARCHAR(100) NULL,
        changed_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
END
GO

IF OBJECT_ID(N'dbo.complaints', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.complaints (
        id INT IDENTITY(1,1) PRIMARY KEY,
        comp_no NVARCHAR(100) NOT NULL UNIQUE,
        comp_date DATE NOT NULL DEFAULT CAST(GETDATE() AS DATE),
        customer_name NVARCHAR(255) NOT NULL,
        customer_mobile NVARCHAR(20) NOT NULL,
        customer_email NVARCHAR(255) NULL,
        customer_address NTEXT NULL,
        model_details NVARCHAR(255) NULL,
        problem_description NTEXT NULL,
        query_type NVARCHAR(50) NULL,
        status NVARCHAR(50) NOT NULL DEFAULT 'Pending',
        status_date DATETIME2 NULL,
        assigned_engineer INT NULL,
        remark NTEXT NULL,
        service_proof_path NVARCHAR(500) NULL,
        access_code NVARCHAR(100) NULL,
        send_sms BIT NOT NULL DEFAULT 1,
        created_by INT NULL,
        source NVARCHAR(50) NOT NULL DEFAULT 'callcenter',
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        deleted_at DATETIME2 NULL
    );
END
GO

IF OBJECT_ID(N'dbo.order_items', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.order_items (
        id INT IDENTITY(1,1) PRIMARY KEY,
        order_id INT NOT NULL,
        item_id INT NULL,
        serial_no NVARCHAR(100) NULL,
        serial_no_2 NVARCHAR(100) NULL,
        item_qty INT NOT NULL DEFAULT 1,
        pcb_warranty_years INT NULL,
        component_warranty_years INT NULL,
        machine_warranty_years INT NULL,
        free_service_count INT NOT NULL DEFAULT 0,
        service_consume_count INT NOT NULL DEFAULT 0,
        installation_status NVARCHAR(50) NOT NULL DEFAULT 'Not Requested',
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
END
GO

IF OBJECT_ID(N'dbo.orders', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.orders (
        id INT IDENTITY(1,1) PRIMARY KEY,
        order_no NVARCHAR(255) NULL UNIQUE,
        order_date DATE NOT NULL,
        oem_bill_no NVARCHAR(100) NULL,
        vendor_id INT NULL,
        customer_name NVARCHAR(255) NULL,
        customer_contact NVARCHAR(20) NULL,
        customer_email NVARCHAR(255) NULL,
        customer_city NVARCHAR(100) NULL,
        customer_state NVARCHAR(100) NULL,
        customer_address NTEXT NULL,
        courier_id INT NULL,
        lrn_no NVARCHAR(100) NULL,
        vendor_bill_no NVARCHAR(100) NULL,
        vendor_bill_date DATE NULL,
        status NVARCHAR(50) NOT NULL DEFAULT 'Pending',
        expected_delivery_date DATE NULL,
        actual_delivery_date DATE NULL,
        order_file_path NVARCHAR(500) NULL,
        created_by INT NULL,
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        deleted_at DATETIME2 NULL
    );
END
GO

IF OBJECT_ID(N'dbo.couriers', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.couriers (
        id INT IDENTITY(1,1) PRIMARY KEY,
        courier_name NVARCHAR(255) NOT NULL,
        contact_name NVARCHAR(255) NULL,
        contact_mobile NVARCHAR(20) NULL,
        email NVARCHAR(255) NULL,
        address NTEXT NULL,
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        deleted_at DATETIME2 NULL
    );
END
GO

IF OBJECT_ID(N'dbo.vendors', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.vendors (
        id INT IDENTITY(1,1) PRIMARY KEY,
        vendor_code NVARCHAR(50) NOT NULL UNIQUE,
        name_of_firm NVARCHAR(255) NOT NULL,
        contact_name NVARCHAR(255) NULL,
        contact_mobile NVARCHAR(20) NULL,
        email NVARCHAR(255) NULL,
        gst_no NVARCHAR(20) NULL,
        address NTEXT NULL,
        state NVARCHAR(100) NULL,
        district NVARCHAR(100) NULL,
        pincode NVARCHAR(10) NULL,
        latitude DECIMAL(10,8) NULL,
        longitude DECIMAL(11,8) NULL,
        is_active BIT NOT NULL DEFAULT 1,
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        deleted_at DATETIME2 NULL
    );
END
GO

IF OBJECT_ID(N'dbo.item_masters', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.item_masters (
        id INT IDENTITY(1,1) PRIMARY KEY,
        item_code NVARCHAR(100) NOT NULL UNIQUE,
        item_name NVARCHAR(255) NOT NULL,
        category NVARCHAR(100) NULL,
        description NTEXT NULL,
        brand NVARCHAR(100) NULL,
        unit NVARCHAR(50) NULL,
        hsn_code NVARCHAR(20) NULL,
        mrp DECIMAL(10,2) NULL,
        is_active BIT NOT NULL DEFAULT 1,
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        deleted_at DATETIME2 NULL
    );
END
GO

IF OBJECT_ID(N'dbo.permissions', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.permissions (
        id INT IDENTITY(1,1) PRIMARY KEY,
        role_id INT NOT NULL,
        module NVARCHAR(100) NOT NULL,
        sub_module NVARCHAR(100) NULL,
        can_view BIT NOT NULL DEFAULT 0,
        can_create BIT NOT NULL DEFAULT 0,
        can_edit BIT NOT NULL DEFAULT 0,
        can_delete BIT NOT NULL DEFAULT 0,
        can_export BIT NOT NULL DEFAULT 0
    );
END
GO

IF OBJECT_ID(N'dbo.roles', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.roles (
        id INT IDENTITY(1,1) PRIMARY KEY,
        name NVARCHAR(100) NOT NULL UNIQUE,
        description NTEXT NULL,
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
END
GO

IF OBJECT_ID(N'dbo.users', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.users (
        id INT IDENTITY(1,1) PRIMARY KEY,
        name NVARCHAR(255) NOT NULL,
        email NVARCHAR(255) NOT NULL UNIQUE,
        password_hash NVARCHAR(255) NOT NULL,
        role NVARCHAR(100) NOT NULL DEFAULT 'callcenter',
        phone NVARCHAR(20) NULL,
        is_active BIT NOT NULL DEFAULT 1,
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        deleted_at DATETIME2 NULL
    );
END
GO

-- Optional seed data
IF NOT EXISTS (SELECT 1 FROM dbo.roles WHERE name = 'admin')
BEGIN
    INSERT INTO dbo.roles (name, description) VALUES
        ('admin', 'Administrator — full access to all modules'),
        ('callcenter', 'Call Center — create/view complaints, log calls'),
        ('engineer', 'Engineer — view assigned complaints/installations, update status & work reports'),
        ('vendor', 'Vendor — read-only access to own orders'),
        ('public', 'Public User — submit complaint via public form (no login UI)');
END
GO

IF NOT EXISTS (SELECT 1 FROM dbo.users WHERE email = 'admin@indcool.com')
BEGIN
    INSERT INTO dbo.users (name, email, password_hash, role, phone, is_active)
    VALUES ('Administrator', 'admin@indcool.com', '$2b$12$4gQwV4lM5bQkPKD8RkY1Y.aqI0R8K5v6KpAxq6P6n4bX6J0NfREbW', 'admin', '9999999999', 1);
END
GO

IF NOT EXISTS (SELECT 1 FROM dbo.item_masters WHERE item_code = '8908012210436')
BEGIN
    INSERT INTO dbo.item_masters (item_code, item_name, category, is_active)
    VALUES ('8908012210436', 'SPLIT AC IDCACS18K5', 'AC', 1);
END
GO

IF NOT EXISTS (SELECT 1 FROM dbo.item_masters WHERE item_code = '8908012210443')
BEGIN
    INSERT INTO dbo.item_masters (item_code, item_name, category, is_active)
    VALUES ('8908012210443', 'WINDOW AC IDCACW15K3', 'AC', 1);
END
GO

IF NOT EXISTS (SELECT 1 FROM dbo.item_masters WHERE item_code = '8908012210450')
BEGIN
    INSERT INTO dbo.item_masters (item_code, item_name, category, is_active)
    VALUES ('8908012210450', 'GEYSER IDCGYS25L', 'Geyser', 1);
END
GO

PRINT 'SQL Server schema and seed data script completed successfully.';
GO
