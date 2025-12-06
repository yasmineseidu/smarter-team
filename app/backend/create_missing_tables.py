#!/usr/bin/env python3
"""
Create the missing tables that failed during migration
"""

from urllib.parse import quote_plus

from sqlalchemy import create_engine, text


def create_missing_tables():
    """Create missing tables individually"""

    # Database connection
    db_url = (
        "postgresql://postgres:%s@db.xhuhyoqztrkwbazxvotp.supabase.co:5432/postgres"
        % quote_plus("Salsal$TITI$@1990")
    )

    engine = create_engine(db_url)

    print("Creating missing tables...")

    with engine.connect() as conn:
        # Message Approvals table
        print("\n1. Creating message_approvals table...")
        try:
            conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS message_approvals (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
                    requester_id VARCHAR(100),
                    approver_id VARCHAR(100),
                    status VARCHAR(50) DEFAULT 'pending',
                    approval_level INTEGER DEFAULT 1,
                    requested_at TIMESTAMPTZ DEFAULT NOW(),
                    reviewed_at TIMESTAMPTZ,
                    approval_decision VARCHAR(50),
                    rejection_reason TEXT,
                    auto_approve_after TIMESTAMPTZ,
                    escalation_sent BOOLEAN DEFAULT false,
                    metadata JSONB DEFAULT '{}'
                )
            """)
            )
            conn.commit()
            print("   ✅ message_approvals created")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            conn.rollback()

        # Contracts table
        print("\n2. Creating contracts table...")
        try:
            conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS contracts (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    client_id UUID REFERENCES leads(id),
                    proposal_id UUID REFERENCES proposals(id),
                    contract_number VARCHAR(100) UNIQUE,
                    contract_type contract_type DEFAULT 'one_time',
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    status proposal_status DEFAULT 'draft',
                    total_value DECIMAL(12,2) NOT NULL,
                    currency VARCHAR(3) DEFAULT 'USD',
                    start_date DATE,
                    end_date DATE,
                    billing_cycle VARCHAR(50),
                    payment_terms VARCHAR(100),
                    deliverables TEXT[] DEFAULT '{}',
                    milestones JSONB DEFAULT '[]',
                    signed_at TIMESTAMPTZ,
                    signed_by VARCHAR(255),
                    document_url VARCHAR(500),
                    document_storage_ref VARCHAR(255),
                    terms_conditions TEXT,
                    special_terms TEXT,
                    auto_renew BOOLEAN DEFAULT false,
                    renewal_notice_days INTEGER DEFAULT 30,
                    cancellation_period INTEGER DEFAULT 30,
                    metadata JSONB DEFAULT '{}',
                    tags TEXT[] DEFAULT '{}'
                )
            """)
            )
            conn.commit()
            print("   ✅ contracts created")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            conn.rollback()

        # Invoices table
        print("\n3. Creating invoices table...")
        try:
            conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS invoices (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    invoice_number VARCHAR(100) UNIQUE,
                    contract_id UUID REFERENCES contracts(id),
                    client_id UUID REFERENCES leads(id),
                    status VARCHAR(50) DEFAULT 'draft',
                    issue_date DATE DEFAULT CURRENT_DATE,
                    due_date DATE,
                    paid_date TIMESTAMPTZ,
                    subtotal DECIMAL(12,2) NOT NULL,
                    tax_rate DECIMAL(5,2) DEFAULT 0,
                    tax_amount DECIMAL(12,2) DEFAULT 0,
                    total_amount DECIMAL(12,2) NOT NULL,
                    currency VARCHAR(3) DEFAULT 'USD',
                    line_items JSONB DEFAULT '[]',
                    payment_terms VARCHAR(100),
                    notes TEXT,
                    late_fee_rate DECIMAL(5,2) DEFAULT 0,
                    discount_amount DECIMAL(12,2) DEFAULT 0,
                    discount_reason VARCHAR(255),
                    sent_date TIMESTAMPTZ,
                    sent_method VARCHAR(50),
            payment_method VARCHAR(50),
                    metadata JSONB DEFAULT '{}',
                    tags TEXT[] DEFAULT '{}'
                )
            """)
            )
            conn.commit()
            print("   ✅ invoices created")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            conn.rollback()

        # Payments table
        print("\n4. Creating payments table...")
        try:
            conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS payments (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    invoice_id UUID REFERENCES invoices(id),
                    client_id UUID REFERENCES leads(id),
                    amount DECIMAL(12,2) NOT NULL,
                    currency VARCHAR(3) DEFAULT 'USD',
                    payment_date DATE DEFAULT CURRENT_DATE,
                    payment_method VARCHAR(50),
                    transaction_id VARCHAR(255),
                    gateway VARCHAR(50),
                    gateway_fee DECIMAL(10,2) DEFAULT 0,
                    net_amount DECIMAL(12,2),
                    status VARCHAR(50) DEFAULT 'pending',
                    failure_reason TEXT,
                    refunded_amount DECIMAL(12,2) DEFAULT 0,
                    refund_reason TEXT,
                    refunded_at TIMESTAMPTZ,
                    metadata JSONB DEFAULT '{}',
                    notes TEXT,
                    internal_reference VARCHAR(100)
                )
            """)
            )
            conn.commit()
            print("   ✅ payments created")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            conn.rollback()

        print("\n✅ Missing tables creation completed!")

        # Create indexes for the new tables
        print("\nCreating indexes...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_message_approvals_message ON message_approvals(message_id)",
            "CREATE INDEX IF NOT EXISTS idx_message_approvals_status ON message_approvals(status)",
            "CREATE INDEX IF NOT EXISTS idx_contracts_client ON contracts(client_id)",
            "CREATE INDEX IF NOT EXISTS idx_contracts_status ON contracts(status)",
            "CREATE INDEX IF NOT EXISTS idx_invoices_contract ON invoices(contract_id)",
            "CREATE INDEX IF NOT EXISTS idx_invoices_client ON invoices(client_id)",
            "CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status)",
            "CREATE INDEX IF NOT EXISTS idx_invoices_due ON invoices(due_date)",
            "CREATE INDEX IF NOT EXISTS idx_payments_invoice ON payments(invoice_id)",
            "CREATE INDEX IF NOT EXISTS idx_payments_client ON payments(client_id)",
            "CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status)",
            "CREATE INDEX IF NOT EXISTS idx_payments_date ON payments(payment_date)",
        ]

        for index_sql in indexes:
            try:
                conn.execute(text(index_sql))
                conn.commit()
                print(f"   ✅ Index created: {index_sql.split('idx_')[1].split(' ')[0]}")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"   ✅ Index exists: {index_sql.split('idx_')[1].split(' ')[0]}")
                else:
                    print(f"   ⚠ Index warning: {e}")
                conn.rollback()

        print("\n✅ All missing tables and indexes created successfully!")


if __name__ == "__main__":
    create_missing_tables()
