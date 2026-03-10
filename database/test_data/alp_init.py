#!/usr/bin/env python
import os, logging, logging.config, sys
from config import server_setup
import api.system.api_utils as api_utils
from flask import Flask
import logging
import config.config as config

os.environ["PROJECT_DIR"] = os.environ.get("PROJECT_DIR", os.path.abspath(os.path.dirname(__file__)))

app_logger = server_setup.logging_setup()
app_logger.setLevel(logging.INFO) 

current_path = os.path.abspath(os.path.dirname(__file__))
sys.path.extend([current_path, '.'])

flask_app = Flask("API Logic Server", template_folder='ui/templates')
flask_app.config.from_object(config.Config)
flask_app.config.from_prefixed_env(prefix="APILOGICPROJECT")

args = server_setup.get_args(flask_app)

server_setup.api_logic_server_setup(flask_app, args)

from database.models import *
import safrs
from datetime import date
import os
os.environ['AGGREGATE_DEFAULTS'] = 'True'

with flask_app.app_context():
    safrs.DB.create_all()

    session = safrs.DB.session

    # ── Departments ───────────────────────────────────────────────────────────
    dept_federal = Department(name="Federal Programs", notes="Federal funding department")
    dept_state   = Department(name="State Operations", notes="State operations department")
    session.add_all([dept_federal, dept_state])
    session.flush()

    # ── GL Accounts ───────────────────────────────────────────────────────────
    fed_labor  = GlAccount(department_id=dept_federal.id, account_number="4001", name="Federal Labor")
    fed_equip  = GlAccount(department_id=dept_federal.id, account_number="4002", name="Federal Equipment")
    state_ops  = GlAccount(department_id=dept_state.id,   account_number="5001", name="State Operations")
    state_admin= GlAccount(department_id=dept_state.id,   account_number="5002", name="State Administration")
    session.add_all([fed_labor, fed_equip, state_ops, state_admin])
    session.flush()

    # ── Dept Charge Definitions (total_percent / is_active derived by rules) ──
    fed_charge_def = DeptChargeDefinition(
        department_id=dept_federal.id, name="Federal Standard Allocation",
        total_percent=0, is_active=0)
    state_charge_def = DeptChargeDefinition(
        department_id=dept_state.id, name="State Standard Allocation",
        total_percent=0, is_active=0)
    session.add_all([fed_charge_def, state_charge_def])
    session.flush()

    # Lines for Federal (60% labor, 40% equipment = 100%)
    session.add_all([
        DeptChargeDefinitionLine(dept_charge_definition_id=fed_charge_def.id,
                                  gl_account_id=fed_labor.id, percent=60),
        DeptChargeDefinitionLine(dept_charge_definition_id=fed_charge_def.id,
                                  gl_account_id=fed_equip.id, percent=40),
    ])

    # Lines for State (70% operations, 30% admin = 100%)
    session.add_all([
        DeptChargeDefinitionLine(dept_charge_definition_id=state_charge_def.id,
                                  gl_account_id=state_ops.id,  percent=70),
        DeptChargeDefinitionLine(dept_charge_definition_id=state_charge_def.id,
                                  gl_account_id=state_admin.id, percent=30),
    ])
    session.flush()

    # ── Project Funding Definition (total_percent / is_active derived by rules) 
    pfd = ProjectFundingDefinition(
        name="Infrastructure Project Funding",
        total_percent=0, is_active=0)
    session.add(pfd)
    session.flush()

    # Lines: Federal 60%, State 40% = 100%
    session.add_all([
        ProjectFundingLine(project_funding_definition_id=pfd.id,
                           department_id=dept_federal.id,
                           dept_charge_definition_id=fed_charge_def.id,
                           percent=60),
        ProjectFundingLine(project_funding_definition_id=pfd.id,
                           department_id=dept_state.id,
                           dept_charge_definition_id=state_charge_def.id,
                           percent=40),
    ])
    session.flush()

    # ── Project ───────────────────────────────────────────────────────────────
    bridge_project = Project(
        name="Highway Bridge Repair",
        project_funding_definition_id=pfd.id,
        notes="Critical infrastructure repair project")
    session.add(bridge_project)
    session.flush()

    # ── Charge (triggers cascade allocation via rules) ────────────────────────
    charge1 = Charge(
        project_id=bridge_project.id,
        description="Engineering Consulting Services",
        amount=100000,
        total_distributed_amount=0,
        charge_date="2026-03-09")
    session.add(charge1)
    session.flush()

    session.commit()
    app_logger.info("✅ Seed data committed successfully")
    app_logger.info(f"   charge1.total_distributed_amount = {charge1.total_distributed_amount}")


