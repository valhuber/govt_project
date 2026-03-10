-- Government cost-allocation domain tables
-- Generated for: ApiLogicServer govt_project

CREATE TABLE department (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    notes TEXT
);

CREATE TABLE gl_account (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    department_id INTEGER NOT NULL REFERENCES department(id),
    account_number TEXT NOT NULL,
    name TEXT NOT NULL,
    notes TEXT
);

CREATE TABLE dept_charge_definition (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    department_id INTEGER NOT NULL REFERENCES department(id),
    name TEXT NOT NULL,
    total_percent NUMERIC(7,4) DEFAULT 0,
    is_active INTEGER DEFAULT 0,
    notes TEXT
);

CREATE TABLE dept_charge_definition_line (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dept_charge_definition_id INTEGER NOT NULL REFERENCES dept_charge_definition(id),
    gl_account_id INTEGER NOT NULL REFERENCES gl_account(id),
    percent NUMERIC(7,4) NOT NULL DEFAULT 0,
    notes TEXT
);

CREATE TABLE project_funding_definition (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    total_percent NUMERIC(7,4) DEFAULT 0,
    is_active INTEGER DEFAULT 0,
    notes TEXT
);

CREATE TABLE project_funding_line (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_funding_definition_id INTEGER NOT NULL REFERENCES project_funding_definition(id),
    department_id INTEGER NOT NULL REFERENCES department(id),
    dept_charge_definition_id INTEGER NOT NULL REFERENCES dept_charge_definition(id),
    percent NUMERIC(7,4) NOT NULL DEFAULT 0,
    notes TEXT
);

CREATE TABLE project (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    project_funding_definition_id INTEGER REFERENCES project_funding_definition(id),
    notes TEXT
);

CREATE TABLE charge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES project(id),
    description TEXT NOT NULL,
    amount NUMERIC(15,2) NOT NULL DEFAULT 0,
    total_distributed_amount NUMERIC(15,2) DEFAULT 0,
    charge_date TEXT,
    notes TEXT
);

CREATE TABLE charge_dept_allocation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    charge_id INTEGER NOT NULL REFERENCES charge(id),
    project_funding_line_id INTEGER REFERENCES project_funding_line(id),
    department_id INTEGER REFERENCES department(id),
    dept_charge_definition_id INTEGER REFERENCES dept_charge_definition(id),
    percent NUMERIC(7,4) DEFAULT 0,
    amount NUMERIC(15,2) DEFAULT 0,
    notes TEXT
);

CREATE TABLE charge_gl_allocation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    charge_dept_allocation_id INTEGER NOT NULL REFERENCES charge_dept_allocation(id),
    dept_charge_definition_line_id INTEGER REFERENCES dept_charge_definition_line(id),
    gl_account_id INTEGER REFERENCES gl_account(id),
    percent NUMERIC(7,4) DEFAULT 0,
    amount NUMERIC(15,2) DEFAULT 0,
    notes TEXT
);
