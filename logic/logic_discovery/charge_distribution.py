"""
Govt Cost-Allocation Logic
==========================
Two-level cascade allocation: Charge → ChargeDeptAllocation → ChargeGlAllocation

Rule map
--------
DeptChargeDefinition
    total_percent  = sum(DeptChargeDefinitionLine.percent)
    is_active      = 1 when total_percent == 100

ProjectFundingDefinition
    total_percent  = sum(ProjectFundingLine.percent)
    is_active      = 1 when total_percent == 100

Charge
    CONSTRAINT: project's ProjectFundingDefinition must be active
    total_distributed_amount = sum(ChargeDeptAllocation.amount)

ChargeDeptAllocation (Level-1 allocation)
    percent  = copy from ProjectFundingLine.percent
    amount   = charge.amount × percent / 100

ChargeGlAllocation (Level-2 allocation)
    percent  = copy from DeptChargeDefinitionLine.percent
    amount   = charge_dept_allocation.amount × percent / 100
"""
from decimal import Decimal
from logic_bank.logic_bank import Rule
from logic_bank.extensions.allocate import Allocate
from logic_bank.exec_row_logic.logic_row import LogicRow
from database import models


# ── Level-1 recipient function ────────────────────────────────────────────────

def funding_lines_for_charge(provider: LogicRow):
    """Returns all ProjectFundingLines for this charge's project's funding definition."""
    project = provider.row.project
    pfd = project.project_funding_definition if project else None
    if pfd is None:
        return []
    return provider.session.query(models.ProjectFundingLine)\
        .filter(models.ProjectFundingLine.project_funding_definition_id == pfd.id)\
        .all()


# ── Level-2 recipient function ────────────────────────────────────────────────

def charge_def_lines_for_dept_allocation(provider: LogicRow):
    """Returns DeptChargeDefinitionLines for this dept allocation's charge definition."""
    funding_line = provider.row.project_funding_line
    if funding_line is None or funding_line.dept_charge_definition_id is None:
        return []
    return provider.session.query(models.DeptChargeDefinitionLine)\
        .filter(models.DeptChargeDefinitionLine.dept_charge_definition_id ==
                funding_line.dept_charge_definition_id)\
        .all()


# ── Custom allocators ─────────────────────────────────────────────────────────

def allocate_charge_to_dept(allocation_logic_row, provider_logic_row) -> bool:
    """
    Level-1 allocator: pre-sets percent AND amount before insert so that the
    Level-2 EarlyRowEvent (which fires before copy/formula rules on this row)
    sees the correct amount value when computing ChargeGlAllocation.amount.
    """
    allocation = allocation_logic_row.row
    funding_line = allocation_logic_row.row.project_funding_line  # linked by Allocate.link()
    charge = provider_logic_row.row

    allocation.department_id = funding_line.department_id
    allocation.dept_charge_definition_id = funding_line.dept_charge_definition_id
    allocation.percent = funding_line.percent
    allocation.amount = (
        Decimal(str(charge.amount or 0)) * Decimal(str(funding_line.percent or 0)) / Decimal(100)
    )
    allocation_logic_row.insert(reason="Allocate charge to department")
    return True  # non-draining: always process all recipients


def allocate_dept_to_gl(allocation_logic_row, provider_logic_row) -> bool:
    """
    Level-2 allocator: pre-sets percent AND amount before insert using the
    dept allocation amount (already set by Level-1 allocator above).
    """
    allocation = allocation_logic_row.row
    defn_line = allocation_logic_row.row.dept_charge_definition_line  # linked by Allocate.link()
    dept_alloc = provider_logic_row.row

    allocation.gl_account_id = defn_line.gl_account_id
    allocation.percent = defn_line.percent
    allocation.amount = (
        Decimal(str(dept_alloc.amount or 0)) * Decimal(str(defn_line.percent or 0)) / Decimal(100)
    )
    allocation_logic_row.insert(reason="Allocate department amount to GL account")
    return True


# ── Logic declarations ────────────────────────────────────────────────────────

def declare_logic():

    # ── DeptChargeDefinition ─────────────────────────────────────────────────
    Rule.sum(derive=models.DeptChargeDefinition.total_percent,
             as_sum_of=models.DeptChargeDefinitionLine.percent)

    Rule.formula(derive=models.DeptChargeDefinition.is_active,
                 as_expression=lambda row: 1 if row.total_percent == 100 else 0)

    # ── ProjectFundingDefinition ─────────────────────────────────────────────
    Rule.sum(derive=models.ProjectFundingDefinition.total_percent,
             as_sum_of=models.ProjectFundingLine.percent)

    Rule.formula(derive=models.ProjectFundingDefinition.is_active,
                 as_expression=lambda row: 1 if row.total_percent == 100 else 0)

    # ── Charge constraint ────────────────────────────────────────────────────
    Rule.constraint(
        validate=models.Charge,
        as_condition=lambda row: (
            row.project is None
            or row.project.project_funding_definition is None
            or row.project.project_funding_definition.is_active == 1
        ),
        error_msg="Charge rejected: Project's ProjectFundingDefinition must be active (total_percent must equal 100)"
    )

    # ── ChargeDeptAllocation (Level-1) ────────────────────────────────────────
    Rule.copy(derive=models.ChargeDeptAllocation.percent,
              from_parent=models.ProjectFundingLine.percent)

    Rule.formula(derive=models.ChargeDeptAllocation.amount,
                 as_expression=lambda row:
                     row.charge.amount * row.percent / Decimal(100)
                     if row.charge and row.percent is not None else Decimal(0))

    Rule.sum(derive=models.Charge.total_distributed_amount,
             as_sum_of=models.ChargeDeptAllocation.amount)

    # ── ChargeGlAllocation (Level-2) ──────────────────────────────────────────
    Rule.copy(derive=models.ChargeGlAllocation.percent,
              from_parent=models.DeptChargeDefinitionLine.percent)

    Rule.formula(derive=models.ChargeGlAllocation.amount,
                 as_expression=lambda row:
                     row.charge_dept_allocation.amount * row.percent / Decimal(100)
                     if row.charge_dept_allocation and row.percent is not None else Decimal(0))

    # ── Level-1 Allocate: Charge → ChargeDeptAllocation ──────────────────────
    Allocate(provider=models.Charge,
             recipients=funding_lines_for_charge,
             creating_allocation=models.ChargeDeptAllocation,
             while_calling_allocator=allocate_charge_to_dept)

    # ── Level-2 Allocate: ChargeDeptAllocation → ChargeGlAllocation ──────────
    # (fires automatically as each ChargeDeptAllocation is inserted by Level-1)
    Allocate(provider=models.ChargeDeptAllocation,
             recipients=charge_def_lines_for_dept_allocation,
             creating_allocation=models.ChargeGlAllocation,
             while_calling_allocator=allocate_dept_to_gl)
