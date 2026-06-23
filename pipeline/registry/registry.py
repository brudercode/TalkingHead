#!/usr/bin/env python3
"""
Asset Registry CLI for EcoChiefs Pipeline
Manages 3D assets from source → refinement → approval → publication
"""

import sqlite3
import argparse
import sys
import os
import hashlib
import json
import uuid
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "registry.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


class Registry:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        """Connect to registry database"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def init(self):
        """Initialize registry database with schema"""
        if self.db_path.exists():
            print(f"⚠️  Registry already exists at {self.db_path}")
            response = input("Reinitialize? This will DELETE all data. (y/N): ")
            if response.lower() != 'y':
                print("Aborted.")
                return
            self.db_path.unlink()

        self.connect()
        with open(SCHEMA_PATH) as f:
            self.conn.executescript(f.read())
        self.conn.commit()
        print(f"✅ Registry initialized at {self.db_path}")
        self.close()

    def hash_file(self, path):
        """Calculate SHA-256 hash of file"""
        sha256 = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def ingest(self, source_path, identity_id, tool='manual', metadata=None):
        """Ingest a new asset into the registry"""
        self.connect()

        # Validate identity
        cur = self.conn.execute("SELECT 1 FROM identities WHERE identity_id = ?", (identity_id,))
        if not cur.fetchone():
            print(f"❌ Unknown identity: {identity_id}")
            self.close()
            return None

        # Calculate hash
        file_hash = self.hash_file(source_path)
        file_size = os.path.getsize(source_path)

        # Check for duplicate hash
        cur = self.conn.execute(
            "SELECT asset_id, source_path, state FROM assets WHERE file_hash = ?",
            (file_hash,)
        )
        existing = cur.fetchone()
        if existing:
            print(f"⚠️  Duplicate detected: {existing['source_path']} ({existing['state']})")
            print(f"   Asset ID: {existing['asset_id']}")
            self.close()
            return existing['asset_id']

        # Create new asset
        asset_id = str(uuid.uuid4())
        self.conn.execute(
            """INSERT INTO assets
               (asset_id, identity_id, source_tool, source_path, file_hash, file_size, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (asset_id, identity_id, tool, str(source_path), file_hash, file_size,
             json.dumps(metadata) if metadata else None)
        )

        # Log workflow
        self.conn.execute(
            """INSERT INTO workflows (asset_id, to_state, operator, notes)
               VALUES (?, 'pending', 'system', 'Ingested from source')""",
            (asset_id,)
        )

        self.conn.commit()
        print(f"✅ Ingested: {os.path.basename(source_path)}")
        print(f"   Asset ID: {asset_id}")
        print(f"   Identity: {identity_id}")
        print(f"   Hash: {file_hash[:16]}...")
        self.close()
        return asset_id

    def query(self, identity_id=None, state=None, limit=100):
        """Query assets"""
        self.connect()

        sql = "SELECT * FROM assets WHERE 1=1"
        params = []

        if identity_id:
            sql += " AND identity_id = ?"
            params.append(identity_id)

        if state:
            sql += " AND state = ?"
            params.append(state)

        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cur = self.conn.execute(sql, params)
        results = cur.fetchall()

        print(f"\n{'Asset ID':<38} {'Identity':<20} {'State':<12} {'Tool':<10} {'Created'}")
        print("=" * 120)

        for row in results:
            created = datetime.fromisoformat(row['created_at']).strftime('%Y-%m-%d %H:%M')
            print(f"{row['asset_id']:<38} {row['identity_id']:<20} {row['state']:<12} {row['source_tool']:<10} {created}")

        print(f"\nTotal: {len(results)} assets")
        self.close()

    def approve(self, asset_id, notes=None):
        """Approve an asset"""
        self.connect()

        # Update state
        self.conn.execute(
            "UPDATE assets SET state = 'approved', updated_at = CURRENT_TIMESTAMP WHERE asset_id = ?",
            (asset_id,)
        )

        # Log workflow
        self.conn.execute(
            """INSERT INTO workflows (asset_id, from_state, to_state, operator, notes)
               VALUES (?, 'pending', 'approved', 'manual', ?)""",
            (asset_id, notes)
        )

        self.conn.commit()
        print(f"✅ Approved: {asset_id}")
        if notes:
            print(f"   Notes: {notes}")
        self.close()

    def reject(self, asset_id, notes=None):
        """Reject an asset"""
        self.connect()

        self.conn.execute(
            "UPDATE assets SET state = 'rejected', updated_at = CURRENT_TIMESTAMP WHERE asset_id = ?",
            (asset_id,)
        )

        self.conn.execute(
            """INSERT INTO workflows (asset_id, from_state, to_state, operator, notes)
               VALUES (?, 'pending', 'rejected', 'manual', ?)""",
            (asset_id, notes)
        )

        self.conn.commit()
        print(f"❌ Rejected: {asset_id}")
        if notes:
            print(f"   Reason: {notes}")
        self.close()

    def publish(self, asset_id, web_path):
        """Mark asset as published"""
        self.connect()

        # Get asset info
        cur = self.conn.execute(
            "SELECT source_path, identity_id FROM assets WHERE asset_id = ? AND state = 'approved'",
            (asset_id,)
        )
        asset = cur.fetchone()

        if not asset:
            print(f"❌ Asset {asset_id} not found or not approved")
            self.close()
            return

        # Update state
        self.conn.execute(
            "UPDATE assets SET state = 'published', updated_at = CURRENT_TIMESTAMP WHERE asset_id = ?",
            (asset_id,)
        )

        # Log workflow
        self.conn.execute(
            """INSERT INTO workflows (asset_id, from_state, to_state, operator, notes)
               VALUES (?, 'approved', 'published', 'system', ?)""",
            (asset_id, f"Published to {web_path}")
        )

        self.conn.commit()
        print(f"✅ Published: {asset_id}")
        print(f"   Web path: {web_path}")
        print(f"   Source: {asset['source_path']}")
        self.close()

    def bind(self, asset_id, slot='avatar3d', canonical=False):
        """Bind asset to ArchCard slot"""
        self.connect()

        # Get asset info
        cur = self.conn.execute(
            "SELECT identity_id, source_path FROM assets WHERE asset_id = ? AND state = 'published'",
            (asset_id,)
        )
        asset = cur.fetchone()

        if not asset:
            print(f"❌ Asset {asset_id} not found or not published")
            self.close()
            return

        identity_id = asset['identity_id']
        identity_name = identity_id.split('.')[-1]  # e.g., 'taurus'
        web_path = f"/assets/{identity_name}/{identity_name}-{slot}.glb"

        # Insert binding
        self.conn.execute(
            """INSERT INTO card_bindings (asset_id, identity_id, slot, web_path, is_canonical)
               VALUES (?, ?, ?, ?, ?)""",
            (asset_id, identity_id, slot, web_path, 1 if canonical else 0)
        )

        self.conn.commit()
        print(f"✅ Bound to card slot: {slot}")
        print(f"   Identity: {identity_id}")
        print(f"   Web path: {web_path}")
        print(f"   Canonical: {'Yes' if canonical else 'No'}")
        self.close()

    def defect(self, asset_id, defect_type, severity, description):
        """Log a defect"""
        self.connect()

        self.conn.execute(
            """INSERT INTO defects (asset_id, defect_type, severity, description)
               VALUES (?, ?, ?, ?)""",
            (asset_id, defect_type, severity, description)
        )

        self.conn.commit()
        print(f"🐛 Defect logged for {asset_id}")
        print(f"   Type: {defect_type} ({severity})")
        print(f"   Description: {description}")
        self.close()

    def show(self, asset_id):
        """Show detailed asset information"""
        self.connect()

        # Get asset
        cur = self.conn.execute("SELECT * FROM assets WHERE asset_id = ?", (asset_id,))
        asset = cur.fetchone()

        if not asset:
            print(f"❌ Asset not found: {asset_id}")
            self.close()
            return

        print(f"\n{'='*60}")
        print(f"Asset ID: {asset['asset_id']}")
        print(f"Identity: {asset['identity_id']}")
        print(f"State: {asset['state']}")
        print(f"Source Tool: {asset['source_tool']}")
        print(f"Source Path: {asset['source_path']}")
        print(f"File Hash: {asset['file_hash']}")
        print(f"File Size: {asset['file_size']:,} bytes")
        print(f"Created: {asset['created_at']}")
        print(f"Updated: {asset['updated_at']}")

        if asset['metadata']:
            print(f"\nMetadata:")
            metadata = json.loads(asset['metadata'])
            for key, value in metadata.items():
                print(f"  {key}: {value}")

        # Workflow history
        cur = self.conn.execute(
            "SELECT * FROM workflows WHERE asset_id = ? ORDER BY timestamp",
            (asset_id,)
        )
        workflows = cur.fetchall()

        if workflows:
            print(f"\nWorkflow History:")
            for wf in workflows:
                arrow = f"{wf['from_state'] or 'NEW'} → {wf['to_state']}"
                print(f"  {wf['timestamp']}: {arrow}")
                if wf['notes']:
                    print(f"    Notes: {wf['notes']}")

        # Defects
        cur = self.conn.execute(
            "SELECT * FROM defects WHERE asset_id = ? ORDER BY created_at",
            (asset_id,)
        )
        defects = cur.fetchall()

        if defects:
            print(f"\nDefects:")
            for d in defects:
                print(f"  [{d['severity']}] {d['defect_type']} ({d['status']})")
                print(f"    {d['description']}")

        # Bindings
        cur = self.conn.execute(
            "SELECT * FROM card_bindings WHERE asset_id = ?",
            (asset_id,)
        )
        bindings = cur.fetchall()

        if bindings:
            print(f"\nCard Bindings:")
            for b in bindings:
                canonical = " (CANONICAL)" if b['is_canonical'] else ""
                print(f"  {b['slot']}: {b['web_path']}{canonical}")

        print(f"{'='*60}\n")
        self.close()


def main():
    parser = argparse.ArgumentParser(description="EcoChiefs Asset Registry CLI")
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # init
    subparsers.add_parser('init', help='Initialize registry database')

    # ingest
    ingest_parser = subparsers.add_parser('ingest', help='Ingest asset(s)')
    ingest_parser.add_argument('source_path', help='Path to GLB file or directory')
    ingest_parser.add_argument('--identity', required=True, help='Identity ID (e.g., ecochief.taurus)')
    ingest_parser.add_argument('--tool', default='manual', help='Source tool (default: manual)')

    # query
    query_parser = subparsers.add_parser('query', help='Query assets')
    query_parser.add_argument('--identity', help='Filter by identity')
    query_parser.add_argument('--state', help='Filter by state')
    query_parser.add_argument('--limit', type=int, default=100, help='Limit results')

    # approve
    approve_parser = subparsers.add_parser('approve', help='Approve asset')
    approve_parser.add_argument('asset_id', help='Asset ID')
    approve_parser.add_argument('--notes', help='Approval notes')

    # reject
    reject_parser = subparsers.add_parser('reject', help='Reject asset')
    reject_parser.add_argument('asset_id', help='Asset ID')
    reject_parser.add_argument('--notes', help='Rejection reason')

    # publish
    publish_parser = subparsers.add_parser('publish', help='Publish asset')
    publish_parser.add_argument('asset_id', help='Asset ID')
    publish_parser.add_argument('--web-path', required=True, help='Web path (e.g., /assets/taurus/model.glb)')

    # bind
    bind_parser = subparsers.add_parser('bind', help='Bind asset to card slot')
    bind_parser.add_argument('asset_id', help='Asset ID')
    bind_parser.add_argument('--slot', default='avatar3d', help='Slot name (default: avatar3d)')
    bind_parser.add_argument('--canonical', action='store_true', help='Set as canonical')

    # defect
    defect_parser = subparsers.add_parser('defect', help='Log defect')
    defect_parser.add_argument('asset_id', help='Asset ID')
    defect_parser.add_argument('--type', required=True, help='Defect type')
    defect_parser.add_argument('--severity', required=True, choices=['low', 'medium', 'high', 'blocker'])
    defect_parser.add_argument('--desc', required=True, help='Description')

    # show
    show_parser = subparsers.add_parser('show', help='Show asset details')
    show_parser.add_argument('asset_id', help='Asset ID')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    registry = Registry()

    if args.command == 'init':
        registry.init()

    elif args.command == 'ingest':
        source_path = Path(args.source_path)
        if source_path.is_dir():
            # Ingest all GLB files in directory
            glb_files = list(source_path.glob('**/*.glb'))
            print(f"Found {len(glb_files)} GLB files")
            for glb_file in glb_files:
                registry.ingest(glb_file, args.identity, args.tool)
        else:
            registry.ingest(source_path, args.identity, args.tool)

    elif args.command == 'query':
        registry.query(args.identity, args.state, args.limit)

    elif args.command == 'approve':
        registry.approve(args.asset_id, args.notes)

    elif args.command == 'reject':
        registry.reject(args.asset_id, args.notes)

    elif args.command == 'publish':
        registry.publish(args.asset_id, args.web_path)

    elif args.command == 'bind':
        registry.bind(args.asset_id, args.slot, args.canonical)

    elif args.command == 'defect':
        registry.defect(args.asset_id, args.type, args.severity, args.desc)

    elif args.command == 'show':
        registry.show(args.asset_id)


if __name__ == '__main__':
    main()
