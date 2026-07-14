"""National institution catalog and source coverage metadata.

Revision ID: 9f6a1c2d3e4f
Revises: 2e66bacc41d6
Create Date: 2026-07-13
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9f6a1c2d3e4f"
down_revision: Union[str, Sequence[str], None] = "2e66bacc41d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("institutions") as batch_op:
        batch_op.alter_column(
            "official_site_url",
            existing_type=sa.String(),
            nullable=True,
        )
        batch_op.add_column(sa.Column("official_code", sa.String(32), nullable=True))
        batch_op.add_column(sa.Column("official_name", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("official_initials", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("region", sa.String(16), nullable=True))
        batch_op.add_column(sa.Column("headquarters_city", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("municipality_code", sa.String(16), nullable=True))
        batch_op.add_column(sa.Column("administrative_category_code", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("administrative_category", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("academic_organization_code", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("academic_organization", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("census_situation", sa.String(64), nullable=True))
        batch_op.add_column(sa.Column("current_situation", sa.String(64), nullable=True))
        batch_op.add_column(sa.Column("eligibility_status", sa.String(32), nullable=True))
        batch_op.add_column(sa.Column("eligibility_reason", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("inventory_source_url", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("inventory_reference_date", sa.Date(), nullable=True))
        batch_op.add_column(sa.Column("source_discovery_status", sa.String(32), nullable=True))
        batch_op.add_column(sa.Column("source_discovery_notes", sa.Text(), nullable=True))
        batch_op.create_unique_constraint(
            "uq_institutions_official_code", ["official_code"]
        )

    # Empty strings can only represent the legacy NOT NULL placeholder. Once
    # the column is nullable again, restore the absence of an official site.
    op.execute(
        sa.text(
            "UPDATE institutions SET official_site_url = NULL "
            "WHERE official_site_url = ''"
        )
    )

    op.create_index("ix_institutions_official_code", "institutions", ["official_code"])
    op.create_index("ix_institutions_region", "institutions", ["region"])
    op.create_index(
        "ix_institutions_administrative_category_code",
        "institutions",
        ["administrative_category_code"],
    )
    op.create_index(
        "ix_institutions_academic_organization_code",
        "institutions",
        ["academic_organization_code"],
    )
    op.create_index(
        "ix_institutions_eligibility_status", "institutions", ["eligibility_status"]
    )
    op.create_index(
        "ix_institutions_source_discovery_status",
        "institutions",
        ["source_discovery_status"],
    )

    with op.batch_alter_table("monitored_sources") as batch_op:
        batch_op.add_column(sa.Column("catalog_source_id", sa.String(128), nullable=True))
        batch_op.add_column(sa.Column("normalized_url", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("content_type", sa.String(64), nullable=True))
        batch_op.add_column(sa.Column("recommended_spider", sa.String(32), nullable=True))
        batch_op.add_column(sa.Column("coverage_status", sa.String(32), nullable=True))
        batch_op.add_column(sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("verification_http_status", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("verification_final_url", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("verification_redirect_chain", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("verification_page_title", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("verification_evidence", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("verification_notes", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("priority", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("notice_categories", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("capture_validated_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("capture_evidence", sa.Text(), nullable=True))

    op.execute(
        sa.text(
            "UPDATE institutions "
            "SET eligibility_status = 'included_legacy', "
            "source_discovery_status = 'manual_review' "
            "WHERE eligibility_status IS NULL"
        )
    )
    op.execute(
        sa.text(
            "UPDATE monitored_sources "
            "SET normalized_url = url, coverage_status = 'manual_review' "
            "WHERE normalized_url IS NULL"
        )
    )

    with op.batch_alter_table("monitored_sources") as batch_op:
        batch_op.create_unique_constraint(
            "uq_monitored_sources_catalog_source_id", ["catalog_source_id"]
        )
        batch_op.create_unique_constraint(
            "uq_monitored_sources_institution_normalized_url",
            ["institution_id", "normalized_url"],
        )

    op.create_index(
        "ix_monitored_sources_catalog_source_id",
        "monitored_sources",
        ["catalog_source_id"],
    )
    op.create_index(
        "ix_monitored_sources_normalized_url", "monitored_sources", ["normalized_url"]
    )
    op.create_index(
        "ix_monitored_sources_coverage_status", "monitored_sources", ["coverage_status"]
    )


def downgrade() -> None:
    op.drop_index("ix_monitored_sources_coverage_status", table_name="monitored_sources")
    op.drop_index("ix_monitored_sources_normalized_url", table_name="monitored_sources")
    op.drop_index("ix_monitored_sources_catalog_source_id", table_name="monitored_sources")
    with op.batch_alter_table("monitored_sources") as batch_op:
        batch_op.drop_constraint(
            "uq_monitored_sources_institution_normalized_url", type_="unique"
        )
        batch_op.drop_constraint(
            "uq_monitored_sources_catalog_source_id", type_="unique"
        )
        batch_op.drop_column("capture_evidence")
        batch_op.drop_column("capture_validated_at")
        batch_op.drop_column("notice_categories")
        batch_op.drop_column("priority")
        batch_op.drop_column("verification_notes")
        batch_op.drop_column("verification_evidence")
        batch_op.drop_column("verification_page_title")
        batch_op.drop_column("verification_redirect_chain")
        batch_op.drop_column("verification_final_url")
        batch_op.drop_column("verification_http_status")
        batch_op.drop_column("last_verified_at")
        batch_op.drop_column("coverage_status")
        batch_op.drop_column("recommended_spider")
        batch_op.drop_column("content_type")
        batch_op.drop_column("normalized_url")
        batch_op.drop_column("catalog_source_id")

    # The legacy schema requires a non-null site. An empty string is a reversible
    # placeholder; the upgrade above restores it to NULL.
    op.execute(
        sa.text(
            "UPDATE institutions "
            "SET official_site_url = COALESCE(official_site_url, '') "
            "WHERE official_site_url IS NULL"
        )
    )

    op.drop_index("ix_institutions_source_discovery_status", table_name="institutions")
    op.drop_index("ix_institutions_eligibility_status", table_name="institutions")
    op.drop_index("ix_institutions_academic_organization_code", table_name="institutions")
    op.drop_index("ix_institutions_administrative_category_code", table_name="institutions")
    op.drop_index("ix_institutions_region", table_name="institutions")
    op.drop_index("ix_institutions_official_code", table_name="institutions")
    with op.batch_alter_table("institutions") as batch_op:
        batch_op.drop_constraint("uq_institutions_official_code", type_="unique")
        batch_op.drop_column("source_discovery_notes")
        batch_op.drop_column("source_discovery_status")
        batch_op.drop_column("inventory_reference_date")
        batch_op.drop_column("inventory_source_url")
        batch_op.drop_column("eligibility_reason")
        batch_op.drop_column("eligibility_status")
        batch_op.drop_column("current_situation")
        batch_op.drop_column("census_situation")
        batch_op.drop_column("academic_organization")
        batch_op.drop_column("academic_organization_code")
        batch_op.drop_column("administrative_category")
        batch_op.drop_column("administrative_category_code")
        batch_op.drop_column("municipality_code")
        batch_op.drop_column("headquarters_city")
        batch_op.drop_column("region")
        batch_op.drop_column("official_initials")
        batch_op.drop_column("official_name")
        batch_op.drop_column("official_code")
        batch_op.alter_column(
            "official_site_url",
            existing_type=sa.String(),
            nullable=False,
        )
